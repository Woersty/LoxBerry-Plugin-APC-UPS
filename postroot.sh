#!/bin/sh

echo `date +"%b  %e %H:%M:%S "`"Check, if APC UPS Daemon is running"                                                                                          
CS_PID=`ps -ef|grep "/sbin/apcupsd"|grep -v grep |awk -F" " '{ print $2 }'`                                                                           
if [ -z "$CS_PID" ]
then
	echo "Not running => ok"
else
	echo "Process ID $CS_PID found, killing it"
	kill -9 $CS_PID;
fi
	
ARGV0=$0 # Zero argument is shell command
ARGV1=$1 # First argument is temp folder during install
ARGV2=$2 # Second argument is Plugin-Name for scipts etc.
ARGV3=$3 # Third argument is Plugin installation folder
ARGV4=$4 # Forth argument is Plugin version
ARGV5=$5 # Fifth argument is Base folder of LoxBerry
$ARGV5/system/daemons/plugins/$ARGV2

exit 0
