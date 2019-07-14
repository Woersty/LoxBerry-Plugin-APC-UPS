<?php
# APC-UPS-Plugin eMailer
require_once "loxberry_system.php";
require_once "loxberry_log.php";
$logfileprefix			= LBPLOGDIR."/apc_ups_mail_";
$logfilesuffix			= ".txt";
$logfilename			= $logfileprefix.date("Y-m-d_H\hi\ms\s",time()).$logfilesuffix;
$L						= LBSystem::readlanguage("language.ini");
$mail_config_file   	= LBSCONFIGDIR."/mail.json";
$plugindata 			= LBSystem::plugindata();
$params = [
	"name" => $L["LOGGING.LOG_GROUPNAME_MAIL"],
    "filename" => $logfilename,
    "addtime" => 1];
    
$log = LBLog::newLog ($params);
LOGSTART ($L["LOGGING.LOG_MAIL_START_TEXT"]);

// Error Reporting 
error_reporting(E_ALL);     
ini_set("display_errors", false);        
ini_set("log_errors", 1);

function debug($line,$message = "", $loglevel = 7)
{
	global $L, $plugindata, $logfilename;
	if ( $plugindata['PLUGINDB_LOGLEVEL'] >= intval($loglevel) )  
	{
		$message = preg_replace('/["]/','',$message); // Remove quotes => https://github.com/mschlenstedt/Loxberry/issues/655
		$raw_message = $message;
		if ( $plugindata['PLUGINDB_LOGLEVEL'] >= 6 && $L["ERRORS.LINE"] != "" ) $message .= " ".$L["ERRORS.LINE"]." ".$line;
		if ( isset($message) && $message != "" ) 
		{

			switch ($loglevel)
			{
			    case 0:
			        // OFF
			        break;
			    case 1:
			    	$message = "<ALERT> ".$message;
			        LOGALERT  (         $message);
			        break;
			    case 2:
			    	$message = "<CRITICAL> ".$message;
			        LOGCRIT   (         $message);
			        break;
			    case 3:
			    	$message = "<ERROR> ".$message;
			        LOGERR    (         $message);
			        break;
			    case 4:
			    	$message = "<WARNING> ".$message;
			        LOGWARN   (         $message);
			        break;
			    case 5:
			    	$message = "<OK> ".$message;
			        LOGOK     (         $message);
			        break;
			    case 6:
			    	$message = "<INFO> ".$message;
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
				$replace = array($L["LOGGING.NOTIFY_LOGLEVEL1"],$L["LOGGING.NOTIFY_LOGLEVEL2"],$L["LOGGING.NOTIFY_LOGLEVEL3"]);
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

$scriptname = "";
$mailtext=str_ireplace("<scriptname>",$scriptname,$L["SCRIPTS.unknown"]);
$emoji = "=E2=9D=93"; # Red ?
if (isset($argv[1])) 
{
	$scriptname = "$argv[1]";
    $log_scriptname = str_ireplace("<scriptname>",$scriptname,$L["SCRIPTS.unknown"]);
	switch ($scriptname)
			{
			    case 'commfailure':
			    case 'killpower':
					$emoji = "=E2=9D=8C"; # Fail X
		        	$mailtext=str_ireplace("<host>","$argv[2]",str_ireplace("<UPS>","$argv[3]",$L["SCRIPTS.$scriptname"]));
		        	$log_scriptname = $scriptname;
		        	break;

			    case 'offbattery':
			    case 'commok':
					$emoji = "=E2=9C=85"; # OK V
		        	$mailtext=str_ireplace("<host>","$argv[2]",str_ireplace("<UPS>","$argv[3]",$L["SCRIPTS.$scriptname"]));
		        	$log_scriptname = $scriptname;
		    	    break;

			    case 'changeme':
					$emoji = "=E2=9D=97"; # Red !
		        	$mailtext=str_ireplace("<host>","$argv[2]",str_ireplace("<UPS>","$argv[3]",$L["SCRIPTS.$scriptname"]));
					@exec("/sbin/apcaccess status", $retArr, $retVal);
					if ( $retVal == 0 )
					{
						$statustext = join("\n",$retArr);
						debug(__line__,$statustext);
						$mailtext .= $statustext;
					}
					$log_scriptname = $scriptname;
			        break;

			    case 'onbattery':
					$emoji = "=E2=9D=97"; # Red !
		        	$mailtext=str_ireplace("<host>","$argv[2]",str_ireplace("<UPS>","$argv[3]",$L["SCRIPTS.$scriptname"]));
		        	$log_scriptname = $scriptname;
			        break;

				case 'powerout':
				case 'mainsback':
				case 'failing':
				case 'timeout':
				case 'loadlimit':
				case 'runlimit':
				case 'doreboot':
				case 'doshutdown':
				case 'annoyme':
				case 'emergency':
				case 'remotedown':
				case 'startselftest':
				case 'endselftest':
				case 'battdetach':
				case 'battattach':
				    $emoji = "=E2=9D=94"; # White ?
				    $mailtext=str_ireplace("<scriptname>",$scriptname,$L["SCRIPTS.not_yet_supported"]);
				    $log_scriptname = $L["SCRIPTS.not_yet_supported"];
			        break;

			    default:
				    $emoji = "=E2=9D=94"; # White ?
				    $mailtext=str_ireplace("<scriptname>",$scriptname,$L["SCRIPTS.unknown"]);
			        break;
			}
}

if (is_readable($mail_config_file)) 
{
	debug(__line__,$L["LOGGING.READ_MAIL_CONFIG"]." => ".$mail_config_file,6);
	$mail_cfg  = json_decode(file_get_contents($mail_config_file), true);
}
else
{
	debug(__line__,$L["ERRORS.ERR02_READ_MAIL_CONFIG"]." => ".$mail_config_file,6);
	$mail_config_file   = LBSCONFIGDIR."/mail.cfg";
	debug(__line__,$L["LOGGING.TRY_OLD_MAIL_CONFIG"]." => ".$mail_config_file,6);

	if (is_readable($mail_config_file)) 
	{
		debug(__line__,$L["LOGGING.MAIL_CONFIG_OK"]." => ".$mail_config_file,5);
		$mail_cfg    = parse_ini_file($mail_config_file,true);
	}
}

if ( !isset($mail_cfg) )
{
	debug(__line__,$L["ERRORS.ERR02_READ_MAIL_CONFIG"],4);
}
else
{
	debug(__line__,$L["LOGGING.MAIL_CONFIG_OK"]." [".$mail_cfg['SMTP']['SMTPSERVER'].":".$mail_cfg['SMTP']['PORT']."]",6);
	if ( $mail_cfg['SMTP']['ISCONFIGURED'] == "0" )
	{
		debug(__line__,$L["LOGGING.MAIL_NOT_CONFIGURED"],5);
	}
	else
	{
		$datetime    = new DateTime;
		$datetime->getTimestamp();
		$outer_boundary= md5("o".time());
		$inner_boundary= md5("i".time());
		$htmlpic="";
		$mailFromName   = $L["MAIL.FROM_NAME"];  // Sender name fix from Language file
		if ( isset($mail_cfg['SMTP']['EMAIL']) )
		{
		  $mailFrom =	trim(str_ireplace('"',"",$mail_cfg['SMTP']['EMAIL']));
		  if ( !isset($mailFromName) )
		  {
		      $mailFromName   = "\"LoxBerry\"";  // Sender name
		  }
		}
		$mailTo = $mailFrom;
		$html = "From: ".$mailFromName." <".$mailFrom.">
To: ".$mailTo."  
Subject: =?utf-8?Q? ".$emoji." ".str_ireplace("<MY_NAME>",$L["APC_UPS.MY_NAME"],str_ireplace("<scriptname>",$scriptname,$L["MAIL.SUBJECT"]))." ?=   
MIME-Version: 1.0
Content-Type: multipart/alternative;
 boundary=\"------------".$outer_boundary."\"

This is a multi-part message in MIME format.
--------------".$outer_boundary."
Content-Type: text/plain; charset=utf-8; format=flowed
Content-Transfer-Encoding: 8bit





".strip_tags( str_ireplace("<MY_NAME>",$L["APC_UPS.MY_NAME"],$L["MAIL.BODY"]))."\n\n\n".$mailtext."


\n\n\n\n--\n".strip_tags($L["MAIL.SIGNATURE"])."

--------------".$outer_boundary."
Content-Type: multipart/related;
 boundary=\"------------".$inner_boundary."\"


--------------".$inner_boundary."
Content-Type: text/html; charset=utf-8
Content-Transfer-Encoding: 8bit

<html>
  <head>
    <meta http-equiv=\"content-type\" content=\"text/html; charset=utf-8\">
  </head>
  <body style=\"margin:0px;\" text=\"#000000\" bgcolor=\"#FFFFFF\">
  
";
			$htmlpicdata="";
			$inline  =  'inline';
			$email_image_part =  "\n<img src=\"cid:logo_".$datetime->format("Y-m-d_i\hh\mH\s")."\" alt=\"[Logo]\" />\n<br>";
			$htmlpic 	 .= $email_image_part;
			$htmlpicdata .= "--------------".$inner_boundary."
Content-Type: image/jpeg; name=\"logo_".$datetime->format("Y-m-d_i\hh\mH\s").".png\"
Content-Transfer-Encoding: base64
Content-ID: <logo_".$datetime->format("Y-m-d_i\hh\mH\s").">
Content-Disposition: ".$inline."; filename=\"logo_".$datetime->format("Y-m-d_i\hh\mH\s").".png\"

".chunk_split(base64_encode(file_get_contents(dirname($_SERVER['PHP_SELF']).'/logo.png')))."\n";
		$html .= $htmlpic;
		$html .= "<div style=\"padding:10px;\"><font face=\"Verdana\">".str_ireplace("<MY_NAME>",$L["APC_UPS.MY_NAME"],$L["MAIL.BODY"])."<br><hr><br>";
		$html .= $mailtext;
		$html .="<br><br><br>\n\n--<br>".$L["MAIL.SIGNATURE"]." </font></div></body></html>\n\n";
		$html .= $htmlpicdata;
		$html .= "--------------".$inner_boundary."--\n\n";
		$html .= "--------------".$outer_boundary."--\n\n";
		$tmpfname = tempnam("/tmp", "msbackup_mail_");
		$handle = fopen($tmpfname, "w") or debug(__line__,$L["ERRORS.ERR03_OPEN_MAIL_TMP_FILE"]." ".$tmpfname,4);
		fwrite($handle, $html) or debug(__line__,$L["ERRORS.ERR04_WRITE_MAIL_TMP_FILE"]." ".$tmpfname,4);
		fclose($handle);
		@exec("/usr/sbin/sendmail -v -t 2>&1 < $tmpfname ",$resultarray,$retval);
		$result = preg_grep( "/sendmail\:/i" , $resultarray );
		if($retval != 0 || count($result) > 0 )
		{
			debug(__line__,$L["ERRORS.ERR06_ERR_SEND_MAIL"],3);
			$log->LOGTITLE($L["ERRORS.ERR06_ERR_SEND_MAIL"]." [".$argv[3]."@".$argv[2]."=>".$log_scriptname."]");
		}
		else
		{
			debug(__line__,$L["LOGGING.SEND_MAIL_OK"],5);
			$log->LOGTITLE($L["LOGGING.SEND_MAIL_OK"]." [".$argv[3]."@".$argv[2]."=>".$log_scriptname."]");
		}
   		debug(__line__,"".htmlspecialchars(join("\n",$resultarray)),7);
		unlink($tmpfname) or debug(__line__,$L["ERRORS.ERR05_DEL_MAIL_TMP_FILE"]." ".$tmpfname,4);
	}		
}
LOGEND (" ");
exit;
