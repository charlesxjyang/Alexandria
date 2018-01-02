<?php
 
 
function Connect()
{
 $dbhost = "127.0.0.1";
 $dbuser = "public";
 $dbpass = "youseeberkeley";
 $dbname = "alexandria";
 
 // Create connection
 $conn = new mysqli($dbhost, $dbuser, $dbpass, $dbname);

 if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
 } 
 
 return $conn;
}
 
?>