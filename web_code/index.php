<?php
require_once('includes/common_top.php');
require_once('includes/common.php');

if( !isset($_SESSION['xnatview.authinfo']) ) {
   header('Location: login.php?target=' . urlencode($_SERVER['PHP_SELF']));
}

$base_url = getBaseUrl();
$xnatview = getXnatViewOptions();

$auth = $_SESSION['xnatview.authinfo'];
$auth_json = json_encode(array(
	'username' => $auth['user'], 
	'password' => $auth['pass'],
   'instance' => $auth['server']
));

$xnatview_path = '../python/xnat_view_script.py';


?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
   <head>
      <title>XNAT View</title>
      <!-- styles -->
      <link rel="stylesheet" type="text/css" href="css/index.css?nocache=1" />
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
   "dojox/layout/resources/FloatingPane.css",
	"dojox/widget/RollingList/RollingList.css"
);
foreach($dojo_styles as $style) {
   echo "<link rel='stylesheet' type='text/css' href='$dojo_base/$style' />\n";
}

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
   $base_url . 'libs/galleria/themes/classic/galleria.classic.js' => null 
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
      <script type="text/javascript">
<?php
// pass server options to included javascript
echo '      var xnatview = ', json_encode($xnatview, JSON_FORCE_OBJECT), ';'
?>
      </script>
      <script type="text/javascript" src="js/index.dojo.js"></script>
   </head>
   <body class='claro'>
		
		<div id='top_controls'>
		   <div style='float: right;'><a href='login.php?logout=1'>Logout</a></div>
		   <div style='clear: both;'></div>
		</div>
		<!--  select widgets -->
	   	<div id='selection_container' 
	   		data-dojo-type='dijit.layout.SplitContainer'
	   		data-dojo-props='
	   			activeSizing: true,
	   			layoutAlign: "client",
	   			orientation: "horizontal",
	   			sizerWidth: 5
	   		'>
<?php
// BEGIN DYNAMIC OUTPUT

// each has a DataGrid(ObjectStore(MemoryStore))
$stypes = array('project', 'subject', 'experiment');
foreach( $stypes as $stype ) {
   $store = $stype . 'Store';
   $adapter = $stype . 'StoreAdapter';
   $grid_id = $stype . 'Select';
   $label = ucwords($stype);
?>
	<div data-dojo-id='<?php echo $store;?>' data-dojo-type='dojo.store.Memory'></div>
	<div data-dojo-id='<?php echo $adapter;?>' 
			data-dojo-type='dojo.data.ObjectStore'
			data-dojo-props='objectStore: <?php echo $store;?>'>
	</div>
	
   <div id='<?php echo $grid_id;?>' class='singleSelect' 
   			data-dojo-type='dojox.grid.DataGrid'
   			data-dojo-props='
   				store: <?php echo $adapter;?>,
   				clientSort: true,
   				selectionMode: "single",
   				errorMessage: "ERROR LOADING DATA",
   				structure: [{field: "id", name: "<?php echo $label;?>", width: "auto"}],
   				query: {id: "*"}'>
   	</div>
<?php  
}

// RESUME NORMAL OUTPUT
?>
	<div data-dojo-id='scanStore' data-dojo-type='dojo.store.Memory'></div>
	<div data-dojo-id='scanStoreAdapter' 
			data-dojo-type='dojo.data.ObjectStore'
			data-dojo-props='objectStore: scanStore'>
	</div>
	
   <div id='scanSelect'
   			data-dojo-type='dojox.grid.DataGrid'
   			data-dojo-props='
   				store: scanStoreAdapter,
   				clientSort: true,
   				selectionMode: "single",
   				errorMessage: "ERROR LOADING DATA",
   				structure: [
   					{field: "id", name: "Scan"},
   					{field: "scan_type", name: "Type"},
   					{field: "scan_frames", name: "Frames"},
   					{field: "scan_tr", name: "TR"},
   					{field: "scan_te", name: "TE"},
   					{field: "x_res", name: "X Res"},
   					{field: "y_res", name: "Y Res"},
   					{field: "z_res", name: "Z Res", width: "auto"}
   				],
   				query: {id: "*"}'>
   	</div>
		</div>
   </body>
</html>
