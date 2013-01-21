<?php
require_once('includes/common.php');

function _fatal_error($error_msg) {
   die("<html><body><span style='font-weight: bold; color: red;'>$error_msg</span></body></html>");
}

session_start();

$base_url = getBaseUrl();
$xnatview = getXnatViewOptions();

$in_frame = isset($_REQUEST['in_frame']) && (bool)$_REQUEST['in_frame'];

$deeplink_url = $_SERVER['PHP_SELF'];

// strip '/' (plus the default whitespace characters)
$path_info = trim($_SERVER['PATH_INFO'], "/ \t\n\r\0\x0B");
$path_info = array_filter(explode('/', $path_info));
if( count($path_info) < 4 ) {
   _fatal_error("Invalid scan URL.");
} else {
   list($project, $subject, $experiment, $scan) = $path_info;
}

// construct the deeplink url
$deeplink_url = getHostUrl() . $_SERVER['REQUEST_URI'];
$qpos = strpos($deeplink_url, "?");
if( $qpos !== false )
   $deeplink_url = substr($deeplink_url, 0, $qpos);
$qpos = strpos($deeplink_url, "#");
if( $qpos !== false )
   $deeplink_url = substr($deeplink_url, 0, $qpos);
$xnatview['config']['galleryScanLink'] = $deeplink_url;

// FIXME: check for the particular project/scan/etc
$is_authorized = isset($_SESSION['xnatview.authinfo']);
if( !$is_authorized ) {
   if( !$in_frame ) {
      header('Location: ' . $base_url . 'login.php?target=' . urlencode($_SERVER['PHP_SELF']));
      return;
   } else {
      _fatal_error('You are not authorized to view this scan.  Make sure you are logged in with proper credentials.');
   }
}

// hit our backend script to retrieve scan image info
$get_scans_url = $xnatview['config']['dicomUrl'];
$req_params = $xnatview['config']['authJson'];
$req_params['project_name'] = $project;
$req_params['subject_label'] = $subject;
$req_params['experiment_label'] = $experiment;
$req_params['scan_id'] = $scan;

$get_scans_url .= '?' . http_build_query($req_params);

$ch = curl_init($get_scans_url);
curl_setopt_array($ch, array(
 CURLOPT_RETURNTRANSFER => true,
 CURLOPT_FOLLOWLOCATION => true,
 CURLOPT_MAXREDIRS => 3, // we're not actually expecting redirects now
 CURLOPT_FAILONERROR => true,
 CURLOPT_CONNECTTIMEOUT => 30, // 30 seconds
));

$result = curl_exec($ch);
curl_close($ch);
unset($ch);
if( $result === false ) {
   // FIXME should log error info
   _fatal_error("Unexpected error fetching the scan data.");
}

// now parse the XML
$xml = new SimpleXMLElement($result);
$img_tags = $xml->xpath('//image');
if( empty($img_tags) ) {
   _fatal_error("No scan images were found.");
}

// construct the gallery container
ob_start();
echo "<div id='scanGallery'>\n";
foreach( $img_tags as $img_tag ) {
   echo "\t<a href='", htmlspecialchars($img_tag['fullImage']), "'>";
   echo "<img src='", htmlspecialchars($img_tag['thumbnailImage']), "' ";
   echo "title='", htmlspecialchars($img_tag['title']), "' /></a>\n";
}
echo "</div>\n";
$gallery_html = ob_get_clean();


// begin main page now
?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
   <head>
      <title>XNAT View - View Scan</title>
<?php
// CSS includes
$dojo_base = 'http://ajax.googleapis.com/ajax/libs/dojo/1.7.1';
//$dojo_base = 'http://download.dojotoolkit.org/release-1.7.1/dojo-release-1.7.1';
$dojo_styles = array(
   "dojo/resources/dojo.css",
   "dijit/themes/claro/claro.css",
   "dojox/widget/SortList/SortList.css",
   "dojox/grid/resources/claroGrid.css",
   "dojox/layout/resources/GridContainer.css",
   "dojox/layout/resources/ResizeHandle.css",
   "dojox/widget/RollingList/RollingList.css"
);
foreach($dojo_styles as $style) {
   echo "<link rel='stylesheet' type='text/css' href='$dojo_base/$style' />\n";
}

?>
      <link rel='stylesheet' type='text/css' href='<?php echo $base_url . 'css/common.css'; ?>' />
      <link rel='stylesheet' type='text/css' href='<?php echo $base_url . 'css/scan_gallery.css'; ?>' />
      <style type="text/css">
      </style>
      <script type="text/javascript">
<?php
   echo '      var xnatview = ', json_encode($xnatview, JSON_FORCE_OBJECT), ';';
?>
      </script>
<?php
 
// Javascript includes
$js_includes = array(
   '//ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js' => null,
   '//ajax.googleapis.com/ajax/libs/jqueryui/1.8.18/jquery-ui.js' => null,
   $base_url . 'libs/pixastic/pixastic.core.js' => null,
   $base_url . 'libs/pixastic/pixastic.jquery.js' => null,
   $base_url . 'libs/pixastic/actions/brightness.js' => null,
   $base_url . 'libs/pixastic/actions/lighten.js' => null,
   $dojo_base . '/dojo/dojo.js.uncompressed.js' => array('data-dojo-config' => 'parseOnLoad: true'),
   $base_url . 'libs/galleria/galleria-1.2.7.js' => null,
   $base_url . 'libs/galleria/themes/classic/galleria.classic.js' => null,
   $base_url . 'js/scan_gallery.js' => null
);
echo "<!-- javascript includes -->\n";
foreach( $js_includes as $href => $attrs ) {
   echo '<script type="text/javascript" src="', $href, '"';
   if( is_array($attrs) ) {
      foreach( $attrs as $key => $val ) {
         echo ' ', $key, '="', $val, '"';
      }
   }
   echo "></script>\n";
}
?>
   </head>
   <body class="claro">
      <div id="scanLink"><?php 
   $deeplink_url = htmlspecialchars($deeplink_url);
   echo "Deep link: <a target='_blank' href='$deeplink_url'>$deeplink_url</a>";
?>
      </div>
      <?php echo $gallery_html; ?>
   </body>
</html>