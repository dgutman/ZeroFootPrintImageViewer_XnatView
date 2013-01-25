<?php
session_start();

if( !empty($_GET['logout']) ) {
   unset($_SESSION['xnatview.authinfo']);
}

