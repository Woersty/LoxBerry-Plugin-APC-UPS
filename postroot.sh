
echo `date +"%b  %e %H:%M:%S "`"Check, if APC UPS Daemon is running"                                                                                          
CS_PID=`ps -ef|grep "/sbin/apcupsd"|grep -v grep |awk -F" " '{ print $2 }'`                                                                           
if [ -z "$CS_PID" ]
then
	echo "Not running => ok"
else
	echo "Process ID $CS_PID found, killing it"
	kill -9 $CS_PID;
fi
	
echo `$ARGV5/system/daemons/plugins/$ARGV2`

exit 0
