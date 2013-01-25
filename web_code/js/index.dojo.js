// need configuration from the server script
var xnatview = xnatview || {};
if( typeof xnatview.config === 'undefined' ) {
	console.log('No config in xnatview.', xnatview);
	throw {message: 'No xnatview.pageConfig', xnatview: xnatview};
}

// legacy data api
dojo.require('dojo.data.ItemFileReadStore');
dojo.require('dojo.data.ItemFileWriteStore');
dojo.require('dojo.data.ObjectStore');

// new data store api
dojo.require('dojo.store.Memory');
dojo.require('dojo.store.Observable');

// layout
dojo.require("dojox.layout.GridContainer");
dojo.require('dojox.layout.TableContainer');
dojo.require('dijit.layout.ContentPane');
dojo.require('dijit.layout.SplitContainer');

// widgets
dojo.require("dijit.dijit");
dojo.require('dijit.form.Select');
dojo.require('dijit.form.MultiSelect');
dojo.require('dijit.Tree');
dojo.require('dijit.tree.TreeStoreModel');
dojo.require('dojox.grid.DataGrid');
dojo.require('dijit.Dialog');
dojo.require('dijit.TooltipDialog');
//dojo.require('dijit.form.HorizontalSlider');

// experimental widgets
dojo.require('dojox.layout.FloatingPane');

dojo.require('dojo.ready');

var ConstrainedFloatingPane;
//var ConstrainedFloatingPane = dojo.declare([dojox.layout.FloatingPane], {
//   postCreate: function() {
//      this.inherited(arguments);
//      this.moveable = new dojo.dnd.move.constrainedMoveable(
//         this.domNode, {
//            handle: this.focusNode,
//            within: true,
//            constraints: function() { return dojo.coords(dojo.body()); },
//         }
//      );
//   }
//});

var _nextPaneId = 0;
var XnatView = function() {
    this._init();
};
XnatView.prototype = {
   _init: function() {
      var self = this;
      var select = dijit.byId('projectSelect');
      var areValidSelections = function() {
         var i, ilen, obj;
         try {
            for( i = 0, ilen = arguments.length; i < ilen; ++i ) {
               obj = arguments[i];
               if( !(obj && 'id' in obj) )
                  return false;
            }
            return true;
         } catch (e) {
            console.log("areValidSelections: error checking object.");
            console.log("obj, arguments, e", obj, arguments, e);
            return false;
         }
      };
      
      dojo.connect(select, 'onSelectionChanged', select, function() {
         var project = self._getSelected(this);
         if( areValidSelections(project) && project.id !== this._lastSelected ) {
            this._lastSelected = project.id; // dojo is firing change on every click, regardless of actual change
            self.fetchSubjects(project.id);
         }
      });
      
      select = dijit.byId('subjectSelect');
      dojo.connect(select, 'onSelectionChanged', select, function() {
         var subject = self._getSelected(this);
         var project = self._getSelected('projectSelect');
         if( areValidSelections(project, subject) && subject.id !== this._lastSelected ) {
            this._lastSelected = subject.id;
            self.fetchExperiments(project.id, subject.id);
         }
      });
      
      select = dijit.byId('experimentSelect');
      dojo.connect(select, 'onSelectionChanged', select, function() {
         var project = self._getSelected('projectSelect'),
             subject = self._getSelected('subjectSelect'),
          experiment = self._getSelected(this);
         if( areValidSelections(project, subject, experiment) && experiment.id !== this._lastSelected) {
        	 this._lastSelected = experiment.id;
            self.fetchScans(project.id, subject.id, experiment.id);
         }
      });
      
      var nextPaneId = 0;
      select = dijit.byId('scanSelect');
      dojo.connect(select, 'onRowDblClick', select, function(evt) {
         var project = self._getSelected('projectSelect'),
             subject = self._getSelected('subjectSelect'),
          experiment = self._getSelected('experimentSelect');
                scan = this.getItem(evt.rowIndex);
          if( areValidSelections(project, subject, experiment, scan) ) {
             self.fetchScanImageInfo(project.id, subject.id, experiment.id, scan.id);
          }
      });
   },
   
   _clearSelects: function(selects) {
      if( !(selects && selects.length) )
         return;
      var select, i, ilen;
      for( i = 0, ilen = selects.length; i < ilen; ++i ) {
         select = selects[i];
         if( typeof(select) === 'string' )
            select = dijit.byId(select);
         this._refreshSelect(select);
      }
   },
   
   _refreshSelect: function(select, items, selectFirst) {
      var firstItem;
      
      // defaults
      items = items || [];
      if( typeof(selectFirst) === 'undefined' )
         selectFirst = true;
      
      var adapter = select.get('store');
      var store = adapter.objectStore;
      
      adapter.clearOnClose = true;
      adapter.close();
      
      // update with the new data
      store.setData(items);
      select.set('store', adapter);
      
      // FIXME sort() forces the DataGrid to refresh
      select.sort();
      
      // auto-select the first item if requested
      if( selectFirst ) {
         firstItem = select.getItem(0);
         if( firstItem ) {
            select.selection.deselectAll(); // ensure onSelectionChange will fire 
            select.selection.select(firstItem);
         }
      }
   },
   
   _getSelected: function(select) {
      if( typeof(select) === 'string' )
         select = dijit.byId(select);
      var items = select.selection.getSelected();
      if( items.length )
         return items[0];
      return null;
   },

   fetchProjects: function() {
      this._clearSelects(["projectSelect", "subjectSelect", "experimentSelect", "scanSelect"]);
      var self = this;
      var setProjects = function(p) { self.setProjects(p); };
      $.ajax({
         url: xnatview.config.projectUrl,
         dataType: 'json',
         success: setProjects
      });
   },
   
	setProjects: function(projects) {
	   projects = projects || [];
	   
	   // FIXME adjust for server format
	   for( var i=0, ilen=projects.length; i<ilen; ++i ) {
	      var p = projects[i];
	      if( 'project_name' in p ) {
	         p.id = p.name = p.project_name;
	      }
	   }
	   
	   this._refreshSelect(dijit.byId('projectSelect'), projects, true);
	},
	
   fetchSubjects: function(project) {
       this._clearSelects(["subjectSelect", "experimentSelect", "scanSelect"]);
       
       var reqData = { project_name: project };
       
       var self = this;
       var setSubjects = function(s) { self.setSubjects(s); };
       $.ajax({
          url: xnatview.config.subjectUrl,
          data: reqData,
          dataType: 'json',
          success: setSubjects
       });
   },
   
   setSubjects: function(subjects) {
      subjects = subjects || [];
      
      // FIXME adjust for server format
      for( var i=0, ilen=subjects.length; i<ilen; ++i ) {
         var s = subjects[i];
         if( 'subject_label' in s )
            s.id = s.name = s.subject_label;
      }
      
      this._refreshSelect(dijit.byId('subjectSelect'), subjects, true);
   },
   
   fetchExperiments: function(project, subject) {
      this._clearSelects(["experimentSelect", "scanSelect"]);
      
      var reqData = {};
      reqData.project_name = project;
      reqData.subject_label = subject;
      
      var self = this;
      var setExperiments = function(e) { self.setExperiments(e); };
      $.ajax({
         url: xnatview.config.experimentUrl,
         data: reqData,
         dataType: 'json',
         success: setExperiments
      });
   },
   
   setExperiments: function(experiments) {
      experiments = experiments || [];
      
      // FIXME adjust for server format
      for( var i=0, ilen=experiments.length; i<ilen; ++i ) {
         var e = experiments[i];
         if( 'experiment_label' in e )
            e.id = e.name = e.experiment_label;
      }
      
      this._refreshSelect(dijit.byId('experimentSelect'), experiments, true);
   },
   
   fetchScans: function(project, subject, experiment) {
      this._clearSelects(["scanSelect"]);
      
      var reqData = {};
      reqData.project_name = project;
      reqData.subject_label = subject;
      reqData.experiment_label = experiment;
      
      var self = this;
      var setScans = function(s) { self.setScans(s); };

      $.ajax({
         url: xnatview.config.scanUrl,
         data: reqData,
         dataType: 'json',
         success: setScans
      });
   },
   
   setScans: function(scans) {
      var scanSelect = dijit.byId('scanSelect'), i, ilen;
      scans = scans || [];
      
      // FIXME adjust for server format
      for( i=0, ilen=scans.length; i<ilen; ++i ) {
         var s = scans[i];
         if( 'scan_id' in s )
            s.id = s.name = s.scan_id;
      }
      
      this._refreshSelect(scanSelect, scans, false);
   },
   
   fetchScanImageInfo: function(project, subject, experiment, scan) {

      var targetUrl = $.merge([xnatview.config.scanGalleryUrl], 
         $.makeArray(arguments).map(escape)
      ).join('/') + '?in_frame=1';
      var gallery = $('<div />').css({
         position: 'relative',
         top: 0, left: 0,
         width: '100%',
         height: '100%',
      }).append($('<iframe />').
         attr('src', targetUrl).
         css({
            position: 'absolute',
            top: 0, left: 0, border: 0,
            width: '100%',
            height: '100%',
         })   
      );
      var title = '<span style="font-size: 10px;">[Project: ' + project + '] [Subject: ' + subject + '] [Experiment: ' + experiment + '] [Scan: ' + scan + ']</span>';
      
      var dialogContainer = $('<div />').css('position', 'relative')[0];
      dojo.body().appendChild(dialogContainer);
      var dialog = new ConstrainedFloatingPane({
         title: title,
         style: "position:absolute;top:0;left:0;bottom:0;right:0;min-width:600px;min-height:500px;width:600px;height:500px",
         resizable: true,
         maxable: true,
         content: gallery[0]
      }, dialogContainer);
      dialog.startup();
      dialog.show();
   },
   
   showScanImage: function(scan, info) {
      
   }
};

// init when ready
dojo.ready(function() {
    dojo.require('dojox.image.ThumbnailPicker');
    dojo.require('dijit.form.HorizontalSlider');
    
    ConstrainedFloatingPane = dojo.declare('xnatview/ConstrainedFloatingPane', [dojox.layout.FloatingPane], {
       postCreate: function() {
          this.inherited(arguments);
          this.moveable = new dojo.dnd.move.constrainedMoveable(
             this.domNode, {
                handle: this.focusNode,
                within: true,
                constraints: function() { return dojo.coords(dojo.body()); },
             }
          );
       }
    });
    
    var xnatview = new XnatView();
    xnatview.fetchProjects();
});