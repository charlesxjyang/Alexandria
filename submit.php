<?php
 
require 'connection.php';
$conn    = Connect();
$first   = $conn->real_escape_string($_POST['first']);
$last    = $conn->real_escape_string($_POST['last']);
$org     = $conn->real_escape_string($_POST['org']);
$email   = $conn->real_escape_string($_POST['email']);
$queries = $conn->real_escape_string($_POST['query']);

$query   = "INSERT into queries (first,last,org,email,query,time) VALUES('$first','$last','$org','$email','$queries', now())";

$success = $conn->query($query);
 
if (!$success) {
    die("Couldn't enter data: ".$conn->error);
}
 
echo "Thank You For Contacting Us <br>";
 
$conn->close();
 
?>