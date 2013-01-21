//legacy data api
dojo.require('dojo.data.ItemFileReadStore');
dojo.require('dojo.data.ItemFileWriteStore');
dojo.require('dojo.data.ObjectStore');

//new data store api
dojo.require('dojo.store.Memory');
dojo.require('dojo.store.Observable');

dojo.require('dijit.form.HorizontalSlider');

dojo.require('dojo.ready');

dojo.ready(function() {   
   var isElType = function(el, tag) {
      var result = false;
      if( typeof(el) === 'object' && 'tagName' in el ) {
         result = new RegExp(tag, 'i').test(el.tagName);
      }
      return result;
   };
   
   /**
    * Required options (should be set before calling applyEffects):
    *   targetImg: the target image element to process
    *  onComplete: callback function for when processing completes
    *
    * Optional options:
    *   createTime: the creation time of this request, defaults to current
    *   zoom: the zoom level, defaults to 1 (no zoom) FIXME this doesn't do anything right now
    *   contrast: the contrast level, defaults to 0 (no adjustment)
    * brightness: the brightness level, defaults to 0 (no adjustment)
    */
   function ImageProcessRequest(options) {
      
      this.targetImg = options.targetImg;
      this.onComplete = options.onComplete;
      
      this.createTime = typeof(options.createTime) !== 'undefined' ? Number(options.createTime) : new Date().getTime();
      this.zoom = typeof(options.zoom) !== 'undefined' ? Number(options.zoom) : 1;
      this.contrast = typeof(options.contrast !== 'undefined') ? Number(options.contrast) : 0;
      this.brightness = typeof(options.brightness !== 'undefined') ? Number(options.brightness) : 0;
      
      this.completeTime = null;
      this.resultImage = null;
      
      this._useClone = true;
      this._useLoadEvent = false;
      this._logEvents = false;
      
      this._status = 'CREATED';
   };
   ImageProcessRequest.prototype = {
      _log: function(msg) {
         if( this._logEvents ) console.log(this, arguments.length > 1 ? arguments : msg);
      },
      applyEffects: function() {
         this._startTime = new Date().getTime();
         this._status = 'STARTING';
         this._log("IPR.applyEffects: Starting.");
         
         // check for problem or no action necessary
         if( !isElType(this.targetImg, 'img') ) {
            this._completed('ERR_NO_TARGET', 'IPR.applyEffects: No target to process.');
            return;
         } else if ( !this._needsProcessing() ) {
            this.resultImage = this.targetImg;
            this._completed('OK_NO_ACTION', "IPR.applyEffects: No processing needed.");
            return;
         }
        
         var $img = $(this.targetImg);
         this._targetWidth = $img.width();
         this._targetHeight = $img.height();
         
         this._doCloneImage($img);
      },
      
      _doCloneImage: function($img) {
         if( this._useClone ) {
            this._$cloneImg = $img.clone().
               css({width: '', height: ''}).
               removeAttr('width').removeAttr('height');
         } else {
            this._$cloneImg = $('<img').attr('src', $img.attr('src'));
         }
         
         var proxy = $.proxy(this, '_imageReady');
         if( this._useLoadEvent ) {
            this._$cloneImg.bind('load', proxy);
         } else {
            window.setTimeout(proxy, 0);
         }
      },
      
      _completed: function(status, logMessage) {
         this.completeTime = new Date().getTime();
         this._status = status;
         
         if( status.substring(0,2) === 'OK' && typeof(this.onComplete) === 'function' )
            this.onComplete(this);
         
         this._log(logMessage || "IPR._completed.");
      },
      
      _needsProcessing: function() {
         return this.zoom !== 1 || this.contrast !== 0 || this.brightness !== 0;
      },
      
      _imageReady: function(evt) {
         var newImg, clonedCanvas;
         
         this._status = 'SRC_IMG_READY';
         this._log("IPR._imageReady", evt);
         if( typeof(evt) !== 'object' ) {
            this._$cloneImg.unbind(evt);
         }
          
         var newImg = Pixastic.process(this._$cloneImg[0], 'brightness', {
            brightness: this.brightness,
            contrast: this.contrast
         });
         if( newImg === false ) {
            this._completed('ERR_PIXASTIC_FAILED', "IPR._imageReady: Pixastic.process failed.");
            return;
         }
         
         if( isElType(newImg, 'img') ) {
            // IE will return the original <img>, restore dimensions
            $(newImg).attr({width: this._targetWidth, height: this._targetHeight}).
               css({width: this._targetWidth + "px", height: this._targetHeight + "px"});
            this.resultImage = newImg;
            this._completed('OK_IMG_RESULT', 'IPR._imageReady: <img> result, IE 7?');
         } else if ( isElType(newImg, 'canvas') ) {
            // HTML 5 browsers will give a <canvas>, have to draw to a new one
            // to restore the dimensions
            clonedCanvas = $(newImg).clone().
               attr({width: this._targetWidth, height: this._targetHeight}).
               css({
                  width: this._targetWidth + "px",
                  height: this._targetHeight + "px",
                  left: 0, right: 0, top: 0, bottom: 0
               })[0];
            cloneContext = clonedCanvas.getContext('2d');
            cloneContext.drawImage(newImg, 0, 0, newImg.width, newImg.height, 
               0, 0, this._targetWidth, this._targetHeight);
            
            this.resultImage = clonedCanvas;
            this._completed('OK_CANVAS_RESULT', 'IPR._imageReady: <canvas> result, HTML 5');
         } else {
            this._completed('ERR_UNEXPECTED_RESULT', 'IPR._imageReady: Unexpected result type.');
//            console.log(newImg);
            console.log('evt, this._$cloneImg, newImg', evt, this._$cloneImg, newImg);
         }
      },
   };
   
   /** Prototype methods for extending galleria.io */
   var galleryMethods = {
         _fireProcessRequest: function(img) {
            img = img || this.getActiveImage();
            if( !isElType(img, 'img') ) {
               console.log('fireProcessRequest: No active image.');
               return;
            }
            
            var sliders = this._sliders,
               request = new ImageProcessRequest({
                  targetImg: img,
                  onComplete: $.proxy(this, '_imageProcessed'),
                  contrast: sliders.contrast.value,
                  brightness: sliders.brightness.value
            });
            request.applyEffects();
         },
         
         _imageProcessed: function(req) {
            var targetImg = req.targetImg,
              resultImage = req.resultImage,
                 reqTime = req.createTime,
                 $img = $(targetImg),
                 $layer = $img.parent().find('.galleria-layer');
            
            // first event?
            if( this._lastRequestTime === null )
               this._lastRequestTime = req.createTime;
            
            // older than one we already handled?
            if( req.createTime < self._lastRequestTime ) {
               console.log("WARN: Ignoring old processing request.");
               return;
            }
                  
            // layer seems to start with 'display: none;', make it show
            if( $layer.css('display') !== 'block' ) {
               $layer.css('display', 'block').css('overflow', 'hidden');
            }
            
            if( isElType(resultImage, 'img') ) {
               $layer.empty(); // make sure no old canvas lingers
               if( targetImg !== resultImage ) {
                  console.log("Replacing...", targetImg, resultImage);
                  $(targetImg).replaceWith(resultImage);
               }
            } else if( isElType(resultImage, 'canvas') ) {
               // clear and fill the layer
               $layer.empty().append(resultImage);
            } else {
               console.log("No result or unexpected type.", req);
            }
         },
         
         _resetSliders: function() {
            this._sliders.contrast.set('value', 0);
            this._sliders.brightness.set('value',  0);
            this.trigger('resize');
         },
   };
   var galleryExtend = function(options) {
      $.extend(this, galleryMethods);
      
      console.log('galleryExtend', this);
      
      this.attachKeyboard({
          left: this.prev, // applies the native prev() function
          right: this.next
      });
      
      this._lastRequestTime = null;
      
      var self = this,
         fireProcessRequest = function(evt) {
            if( typeof(evt) === 'object' && 'imageTarget' in evt )
               self._fireProcessRequest(evt.imageTarget);
            else
               self._fireProcessRequest();
         };
         
      var $stage = gallery.find('.galleria-stage'),
         $thumbs = gallery.find('.galleria-thumbnails-container'),
         stageHeight = $stage.height(),
         thumbHeight = $thumbs.height(),
         $container = gallery.find('.galleria-container');
      
      var $controls = $('<table style="width: 100%"><tr><td style="text-align: center">&nbsp;</td><td>Contrast</td><td>Brightness</td></tr><tr><td><div /></td><td><div /></td><td><div /></td></tr></table>').
            attr('class', 'galleria-controls').
            css({position: 'absolute', 
               bottom:'60px', height: '60px',
               left: '0', right: '0'
            });
      $controls.find('td').css({'text-align': 'center'}).
         slice(1, 3).css({width: '50%', color: 'white'});
      
      var sliders = $controls.find('div');
      
      $stage.css('bottom', '120px'); // classic theme is 60px normally
       
      this._sliders = {};
      this._sliders.resetButton = new dijit.form.Button({
         label: "Reset",
         onClick: function() { self._resetSliders(); },
      }, sliders[0]);

      this._sliders.contrast = new dijit.form.HorizontalSlider({
         value: 0,
         minimum: -1,
         maximum: 10,
         discreteValues: 200,
         intermediateChanges: true,
         onChange: fireProcessRequest,
      }, sliders[1]);
      this._sliders.contrast.startup();
      

      this._sliders.brightness = new dijit.form.HorizontalSlider({
         value: 0,
         minimum: -150,
         maximum: 150,
         discreteValues: 301,
         intermediateChanges: true,
         onChange: fireProcessRequest,
      }, sliders[2]);
      this._sliders.brightness.startup();
      
      $container.find('.galleria-thumbnails-container').after($controls);
      
      this.trigger('resize');
      
      this.bind('rescale', function(){window.setTimeout(fireProcessRequest, 10);});
      this.bind('loadfinish', fireProcessRequest);
   };
   
   var gallery = $('#scanGallery');
   gallery.galleria({
      transition: 'fade',
      imageCrop: false,
      responsive: true,
      _showInfo: true,
      extend: galleryExtend
   });
});
