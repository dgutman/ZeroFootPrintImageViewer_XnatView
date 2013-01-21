<?php
// FIXME: namespace this stuff

/**
 * Gets the base (absolute) URL for top-level script.
 * 
 * @return string the base URL
 */
function getBaseUrl() {
   static $base_url = null;
   if( $base_url === null ) {
      $base_url = getHostUrl() . dirname($_SERVER['SCRIPT_NAME']) . '/';
   }
   return $base_url;
}

/**
 * Gets the URL base for the host, with no trailing slash.
 * @return string the host URL
 */
function getHostUrl() {
   static $host_url = null;
   if( $host_url === null ) {
      $port = ':' . $_SERVER['SERVER_PORT'];
      if( !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off' ) {
       $protocol = 'https';
       if( $port === ':443' )
          $port = '';
      } else {
       $protocol = 'http';
       if( $port === ':80' )
          $port = '';
      }
      
      $host_url = $protocol . '://' . $_SERVER['SERVER_NAME'] . $port;
   }
   return $host_url;
}

/**
 * Gets the xnatview configuration options.  
 * 
 * Intended to be serialized to the client-side scripts, but may also be 
 * used for server-side options.  Session handling must be started 
 * for authentication info to be included.
 * 
 * @return array nested associative arrays
 */
function getXnatViewOptions() {
   static $xnatview = null;
   if( $xnatview === null ) {
      $base_url = getBaseUrl();
      $auth = $_SESSION['xnatview.authinfo'];
      if( !is_array($auth) ) {
         $auth = array_fill_keys(array('user', 'pass', 'server'), '');
      }
      $xnatview_path = $base_url . '../python/xnat_view_script.py';
      
      // pass server options to included javascript
      $xnatview = array(
       'config' => array(
        'projectUrl' => "$xnatview_path/get_projects",
        'subjectUrl' => "$xnatview_path/get_subjects",
        'experimentUrl' => "$xnatview_path/get_experiments",
        'scanUrl' => "$xnatview_path/get_scans",
        'dicomUrl' => "$xnatview_path/get_dicom_scans",
        'scanGalleryUrl' => $base_url . 'scan_gallery.php',
        'authJson' => array(
         'username' => $auth['user'],
         'password' => $auth['pass'],
         'instance' => $auth['server'],
        ),
       ),
      );
   }
   return $xnatview;
}