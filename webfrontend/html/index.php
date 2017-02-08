<?php
// LoxBerry APC-UPS Plugin
// © git@loxberry.woerstenfeld.de
// 08.02.2017 22:53:31
// v0.1

// Start timer to measure script execution time
$start = microtime(true);

// Configure directories and Logfile path 
$psubdir              =array_pop(array_filter(explode('/',pathinfo($_SERVER["SCRIPT_FILENAME"],PATHINFO_DIRNAME))));
$mydir                =pathinfo($_SERVER["SCRIPT_FILENAME"],PATHINFO_DIRNAME);
$pluginlogfile        =$mydir."/../../../../log/plugins/$psubdir/apc_ups.log";

// Configure error handling 
ini_set("display_errors", false);       						// Do not display in browser			
ini_set("error_log", $pluginlogfile);								// Pass errors to logfile
ini_set("log_errors", 1);														// Log errors

// Set default for 'mode' if not existent in request variables
if (!isset($_REQUEST["mode"])) { $_REQUEST["mode"] = 'normal'; }

// Check mode for downloading or displaying or deleting logfile
if($_REQUEST["mode"] == "download_logfile")
{
  if (file_exists($pluginlogfile))
  {
    error_log( date('Y-m-d H:i:s ')."[LOG] Download logfile\n", 3, $pluginlogfile);
    header('Content-Description: File Transfer');
    header('Content-Type: text/plain');
    header('Content-Disposition: attachment; filename="'.basename($pluginlogfile).'"');
    header('Expires: 0');
    header('Cache-Control: must-revalidate');
    header('Pragma: public');
    header('Content-Length: ' . filesize($pluginlogfile));
    readfile($pluginlogfile);
  }
  else
  {
    error_log( date('Y-m-d H:i:s ')."[ERR] E0001: Error reading logfile!\n", 3, $pluginlogfile);
    die("ERROR E0001: Error reading logfile.");
  }
  exit;
}
else if($_REQUEST["mode"] == "show_logfile")
{
  if (file_exists($pluginlogfile))
  {
    error_log( date('Y-m-d H:i:s ')."[LOG] Show logfile\n", 3, $pluginlogfile);
    header('Content-Description: File Transfer');
    header('Content-Type: text/plain');
    header('Content-Disposition: inline; filename="'.basename($pluginlogfile).'"');
    header('Expires: 0');
    header('Cache-Control: must-revalidate');
    header('Pragma: public');
    header('Content-Length: ' . filesize($pluginlogfile));
    readfile($pluginlogfile);
  }
  else
  {
    error_log( date('Y-m-d H:i:s ')."[ERR] E0001: Error reading logfile!\n", 3, $pluginlogfile);
    die("ERROR E0001: Error reading logfile.");
  }
  exit;
}
else if($_REQUEST["mode"] == "empty_logfile")
{
  if (file_exists($pluginlogfile))
  {
    $f = @fopen("$pluginlogfile", "r+");
    if ($f !== false)
    {
      ftruncate($f, 0);
      fclose($f);
      error_log( date('Y-m-d H:i:s ')."[LOG] Logfile content successfully deleted.\n", 3, $pluginlogfile);
      echo "Logfile content successfully deleted.\n";
    }
    else
    {
      error_log( date('Y-m-d H:i:s ')."[ERR] E0002: Logfile content not deleted due to problems doing it.\n", 3, $pluginlogfile);
      die("ERROR E0002: Logfile content not deleted due to problems doing it.");
    }
  }
  else
  {
    error_log( date('Y-m-d H:i:s ')."[ERR] E0001: Error reading logfile!\n", 3, $pluginlogfile);
    die("ERROR E0001: Error reading logfile.");
  }
  exit;
}
$string_array = explode(PHP_EOL,shell_exec ('/sbin/apcaccess status 2>&1'));  

// Build XML page body
header("Content-type: text/xml");
echo "<?xml version='1.0' encoding='UTF-8'?>\n";
echo "<root>\n";
echo " <timestamp>".time()."</timestamp>\n";
echo " <date_RFC822>".date(DATE_RFC822)."</date_RFC822>\n";

// If no data was read, exit
if ( count($string_array) == 0) 
{
	echo " <error>Got no data from UPS</error>\n";
  echo " <execution>".round( ( microtime(true) - $start ),5 )." s</execution>\n";
  echo " <status>ERROR</status>\n";
  echo "</root>\n";
  error_log( date('Y-m-d H:i:s ')."[ERR] E0006: Got no data from UPS\n", 3, $pluginlogfile);
  exit(1);
} 

// Loop trough each parameter
echo " <UPS>\n";
foreach ($string_array as $lines) 
{
  $values = explode(": ",$lines);  
	$values[0] = str_replace(" ","_",trim($values[0]));
	if ( $values[0] <> "" )
	{ 
		echo "   <$values[0]>".trim($values[1])."</$values[0]>\n";
	}
}
echo " </UPS>\n";
echo " <execution>".round( ( microtime(true) - $start ),5 )." s</execution>\n";
echo "</root>\n";
exit(0);
