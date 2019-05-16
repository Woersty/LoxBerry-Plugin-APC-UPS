<?php
// LoxBerry APC-UPS Plugin
// Christian Woerstenfeld - git@loxberry.woerstenfeld.de

// Calculate running time
$start =  microtime(true);	

// Go to the right directory
chdir(dirname($_SERVER['PHP_SELF']));

// Include System Lib
require_once "loxberry_system.php";
require_once "loxberry_log.php";

// Load language
$L = LBSystem::readlanguage("language.ini");

// Load plugin data
$plugindata = LBSystem::plugindata();

// Configure + Init Logfile
$logfilename			= 	LBPLOGDIR."/apc_ups_".date("Y-m-d_H\hi\ms\s",time()).".log";
$params = [ "name" 		=> 	$L["LOGGING.LOG_GROUPNAME_PLUGIN"],
			"filename" 	=> 	$logfilename,
    		"addtime" 	=> 	1];
$log 	= LBLog::newLog ($params);

// Configure error handling 
ini_set("display_errors", false);      		// Do not display in browser			
ini_set("error_log"		, $logfilename);	// Pass errors to logfile
ini_set("log_errors"	, 1);				// Log errors

// Debug / Log function
function debug($line,$message = "", $loglevel = 7)
{
	global $L,$plugindata,$logfilename;
	if ( $plugindata['PLUGINDB_LOGLEVEL'] >= intval($loglevel) )  
	{
		$message = preg_replace('/["]/','',$message); // Remove quotes => https://github.com/mschlenstedt/Loxberry/issues/655
		$raw_message = $message;
		if ( $plugindata['PLUGINDB_LOGLEVEL'] == 7 && $L["ERRORS.LINE"] != "" ) $message .= " ".$L["ERRORS.LINE"]." ".$line;
		if ( isset($message) && $message != "" ) 
		{
			switch ($loglevel)
			{
			    case 0:
			        // OFF
			        break;
			    case 1:
			    	$message = "<ALERT>".$message;
			        LOGALERT  (         $message);
					array_push($summary,$message);
			        break;
			    case 2:
			    	$message = "<CRITICAL>".$message;
			        LOGCRIT   (         $message);
					array_push($summary,$message);
			        break;
			    case 3:
			    	$message = "<ERROR>".$message;
			        LOGERR    (         $message);
					array_push($summary,$message);
			        break;
			    case 4:
			    	$message = "<WARNING>".$message;
			        LOGWARN   (         $message);
					array_push($summary,$message);
			        break;
			    case 5:
			    	$message = "<OK>".$message;
			        LOGOK     (         $message);
			        break;
			    case 6:
			    	$message = "<INFO>".$message;
			        LOGINF   (         $message);
			        break;
			    case 7:
			    default:
			    	$message = $message;
			        LOGDEB   (         $message);
			        break;
			}
			if ( $loglevel <= 4 ) 
			{
				$search  = array('<ALERT>', '<CRITICAL>', '<ERROR>','<WARNING>');
				$replace = array($L["LOGGING.NOTIFY_LOGLEVEL1"],$L["LOGGING.NOTIFY_LOGLEVEL2"],$L["LOGGING.NOTIFY_LOGLEVEL3"],$L["LOGGING.NOTIFY_LOGLEVEL4"],);
				$notification = array (
				"PACKAGE" => LBPPLUGINDIR,
				"NAME" => $L['APC_UPS.MY_NAME'],
				"MESSAGE" => str_replace($search, $replace, $raw_message),
				"SEVERITY" => 3,
				"LOGFILE"	=> $logfilename);
				notify_ext ($notification);
				return;
			}
		}
	}
	return;
}

// Start logging
LOGSTART ("");
$message = $L["LOGGING.LOG_PLUGIN_CALLED"];
$log->LOGTITLE($message);

// Language info for Log
debug(__line__,count($L)." ".$L["LOGGING.LOG_LANGUAGE_STRINGS_READ"],6);

// Read UPS data
@exec('/sbin/apcaccess status 2>&1',$result,$retval);

// Build XML page body
header("Content-type: text/xml");
echo "<?xml version='1.0' encoding='UTF-8'?>\n";
echo "<root>\n";
echo " <timestamp>".time()."</timestamp>\n";
echo " <date_RFC822>".date(DATE_RFC822)."</date_RFC822>\n";

// If ok, parse data - else exit and close XML
if ( $retval != 0 )  
{
	$message = $L["ERRORS.ERR01_XML_NO_DATA"];
	$log->LOGTITLE($message);
	echo " <error>".$message."</error>\n";
	echo " <errorcode>".$retval."</errorcode>\n";
	echo " <errorinfo>".htmlentities(join("\n",$result))."</errorinfo>\n";
	echo " <execution>".round( ( microtime(true) - $start ),5 )." s</execution>\n";
	echo " <status>ERROR</status>\n";
	echo "</root>\n";
	debug(__line__,$message,3);
	LOGEND ("");
	exit(1);
} 
else
{
	$message = $L["LOGGING.LOG_XML_DATA_OK"];
	debug(__line__,$message,5);
	debug(__line__,join("\n",$result));
}

// Loop through each parameter
$output = " <UPS>\n";
foreach ($result as $lines) 
{
	$values = explode(": ",$lines);  
	$values[0] = str_replace(" ","_",trim($values[0]));
	if ( $values[0] <> "" )
	{ 
		$output .= "   <$values[0]>".trim($values[1])."</$values[0]>\n";
	}
}
$output .= " </UPS>\n";
$output .= " <execution>".round( ( microtime(true) - $start ),5 )." s</execution>\n";
$output .= "</root>\n";
$message = $L["LOGGING.LOG_XML_DATA_SEND"];

if ( $plugindata['PLUGINDB_LOGLEVEL'] == 7 ) 
{
	debug(__line__,$message."\n".htmlentities($output),5);
}
else
{
	debug(__line__,$message,5);
}

// Send XML data to requester
echo $output;

// Plugin finished
$message = $L["LOGGING.LOG_PLUGIN_FINISHED"];
$log->LOGTITLE($message);
LOGOK ($message);
LOGEND ("");
exit(0);
