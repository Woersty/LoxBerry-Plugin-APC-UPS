
echo `date +"%b  %e %H:%M:%S "`"Check, if APC UPS Daemon is running"                                                                                          
CS_PID=`ps -ef|grep "/sbin/apcupsd"|grep -v grep |awk -F" " '{ print $2 }'`                                                                           
if [ -z "$CS_PID" ]
then
	echo "Not running => ok"
else
	echo "Process ID $CS_PID found, killing it"
	kill -9 $CS_PID;
fi
	
(ls -1 REPLACEBYBASEFOLDER/data/plugins/REPLACEBYSUBFOLDER/)|while read script; do 
echo "Replace /etc/apcupsd/$script with Symlink to REPLACEBYBASEFOLDER/data/plugins/REPLACEBYSUBFOLDER/$script" 
rm /etc/apcupsd/$script
ln -s REPLACEBYBASEFOLDER/data/plugins/REPLACEBYSUBFOLDER/$script /etc/apcupsd/$script 
echo "Replace /etc/apcupsd by REPLACEBYBASEFOLDER/data/plugins/REPLACEBYSUBFOLDER in $script" 
/bin/sed -i "s#/etc/apcupsd#REPLACEBYBASEFOLDER/data/plugins/REPLACEBYSUBFOLDER#" REPLACEBYBASEFOLDER/data/plugins/REPLACEBYSUBFOLDER/$script
done
/bin/sed -i "s#ISCONFIGURED=no#ISCONFIGURED=yes#" /etc/default/apcupsd
/bin/sed -i "s#/etc/apcupsd/powerfail#REPLACEBYBASEFOLDER/data/plugins/REPLACEBYSUBFOLDER/powerfail#" /etc/init.d/apcupsd

systemctl daemon-reload
echo "Restarting APC UPS Daemon"
/etc/init.d/apcupsd restart >/dev/null 2>&1

exit 0
