<?php
require('includes/common_top.php');
require_once('includes/common.php');

function verifyAuthentication($username, $pass, $server) {
   $xnatview = getXnatViewOptions();
   $auth_url = $xnatview['config']['authUrl'] . '?' . 
      http_build_query(array('username' => $username, 'password' => $pass, 'instance' => $server));
      
   $cookie = session_name() . '=' . session_id();
   $ch = curl_init($auth_url);
   curl_setopt_array($ch, array(
      CURLOPT_RETURNTRANSFER => true,
      CURLOPT_FOLLOWLOCATION => true,
      CURLOPT_MAXREDIRS => 3, // we're not actually expecting redirects now
      CURLOPT_FAILONERROR => true,
      CURLOPT_CONNECTTIMEOUT => 30, // 30 seconds
      CURLOPT_COOKIE => $cookie,
   ));

   $result = curl_exec($ch);
   if( $result === false ) {
      return false;
   }
   $auth = json_decode($result, true);
   if( $auth === null ) {
      error_log('Unexpected authentication result: ' . $result);
      return false;
   }
   
   # pass on the cookie and remember it
   list($pysessname, $pysessid) = $auth['session'];
   setcookie($pysessname, $pysessid, 0, '/');
   $_SESSION['xnatview.authinfo'] = array(
      'pysessname' => $pysessname,
      'pysessid' => $pysessid,
   );
   
   return $auth['authenticated'];
}

// get recent servers or init defaults
if( isset($_SESSION['xnatview.servers']) ) {
   $servers = $_SESSION['xnatview.servers'];
}
if( !is_array($servers) ) {
   $servers = array(
      'http://xnat.cci.emory.edu:8080/xnat' => 1,
      'https://central.xnat.org' => 1
   );
   $_SESSION['xnatview.servers'] = $servers;
}

$target = 'index.php';
$form_action = $_SERVER['PHP_SELF'];
if( !empty($_GET['target']) ) {
   $target = $_GET['target'];
   $form_action .= '?target=' . urlencode($target);
}

if( $_POST['submitted'] ) {
   // remember the new server
   $server = trim($_POST['server']);
   if( $server ) {
      $servers[$server] = 1;
      $_SESSION['xnatview.servers'] = $servers;
   }
   
   if( !verifyAuthentication($_POST['username'], $_POST['password'], $server) ) {
      $error_msg = "Invalid login information.";
   } else {
      header('Location: ' . $target);
   }
}

?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
   <head>
      <title>XNAT View Login</title>
      <!--  javascript includes -->
      <script src="//ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js" type="text/javascript"></script>
      <script src="http://ajax.googleapis.com/ajax/libs/dojo/1.7.1/dojo/dojo.js" type="text/javascript"
            data-dojo-config="parseOnLoad: true"></script>
      <link rel="stylesheet" type="text/css" href="http://ajax.googleapis.com/ajax/libs/dojo/1.7.1/dojo/resources/dojo.css"> 
      <link rel="stylesheet" type="text/css" href="http://ajax.googleapis.com/ajax/libs/dojo/1.7.1/dijit/themes/claro/claro.css">
      <link rel="stylesheet" type="text/css" href="css/login.css" />
      <script type="text/javascript">

      dojo.require('dijit.layout.BorderContainer');
      dojo.require('dojox.layout.TableContainer');
      
      dojo.require('dijit.form.Form');
      dojo.require('dijit.form.TextBox');
      dojo.require('dijit.form.ComboBox');
      dojo.require('dijit.form.Button');
      
      dojo.require('dojo.store.Memory');
      dojo.require('dojo.ready');

      dojo.ready(function() {
          // FIXME: dynamic server instances
          var server = dijit.byId('server');
<?php
$data = array();
foreach( $servers as $server => $flag ) {
   $data[] = array('value' => $server);
}
$data = json_encode($data);
?>
          var data = <?php echo $data;?>;
          var store = new dojo.store.Memory(data);
          store.setData(data);
          server.set('store', store);

            $('#login_box').css('visibility', 'visible');
      });
      </script>
   </head>
   <body class='claro'>
      <noscript>
         <strong style='color: red;'>This site requires Javascript to function properly.</strong>
      </noscript>
      <div id='login_box' style='visibility: hidden;'>	
   		<form id='login_form' action='<?php echo htmlspecialchars($form_action); ?>' method='post'
   				data-dojo-type='dijit.form.Form'>
   			<input name='submitted' type='hidden' value='true' />
      		<div id='login_title'>XNAT View</div>
      <?php 
      if( $error_msg ) {
         echo "<div style='color: red; font-weight: bold; margin: auto;'>$error_msg</div>\n"; 
      }?>
      		<div id='form_box' data-dojo-type='dojox.layout.TableContainer'
      				data-dojo-props="cols:1, showLabels:true, labelWidth:40, customClass:'loginForm'">
<!--      			<label for='username'>User:</label>-->
      			<input id='username' name='username' type='text' 
      				data-dojo-type='dijit.form.TextBox' title='User:' />
<!--      			<label for='password'>Password:</label>-->
      			<input id='password' name='password' type='password' title='Password:'  
      				data-dojo-type='dijit.form.TextBox' />
<!--      			<label for='server'>Server:</label>-->
      			<select id='server' name='server' title='Server:' data-dojo-type='dijit.form.ComboBox'
      					data-dojo-props='searchAttr: "value"'>
      			</select>
      		</div>
      		<div id='form_buttons' data-dojo-type='dojox.layout.TableContainer'
      				data-dojo-props='cols:2, showLabels:false, customClass:"loginButtons"'>
      			<input id='login_button' name='login_button' type='submit' label='Login'
      					data-dojo-type='dijit.form.Button' />
      			<input id='guest_button' name='guest_button' type='button' label='Guest'
      					data-dojo-type='dijit.form.Button' />
      		</div>
      	</form>
      </div>
   </body>
</html>
