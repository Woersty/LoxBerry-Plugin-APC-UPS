#!/bin/sh

# Bashscript which is executed by bash *AFTER* complete installation is done
# (but *BEFORE* postupdate). Use with caution and remember, that all systems
# may be different! Better to do this in your own Pluginscript if possible.
#
# Exit code must be 0 if executed successfull.
#
# Will be executed as user "loxberry".
#
# We add 5 arguments when executing the script:
# command <TEMPFOLDER> <NAME> <FOLDER> <VERSION> <BASEFOLDER>

ARGV2=$2 # Second argument is Plugin-Name for scipts etc.
ARGV3=$3 # Third argument is Plugin installation folder
ARGV5=$5 # Fifth argument is Base folder of LoxBerry

/bin/sed -i "s#REPLACEBYSUBFOLDER#$ARGV3#"                    $ARGV5/system/daemons/plugins/$ARGV2
/bin/sed -i "s#REPLACEBYSUBFOLDER#$ARGV3#"                    $ARGV5/system/daemons/plugins/$ARGV2
/bin/sed -i "s#REPLACEBYBASEFOLDER#$ARGV5#"                   $ARGV5/system/daemons/plugins/$ARGV2
/bin/sed -i "s#REPLACEBYBASEFOLDER#$ARGV5#"                   $ARGV5/system/daemons/plugins/$ARGV2
/bin/sed -i "s#REPLACEBYBASEFOLDER#$ARGV5#"                   $ARGV5/data/plugins/$ARGV3/apcupsd.conf
/bin/sed -i "s#REPLACEBYSUBFOLDER#$ARGV3#"                    $ARGV5/data/plugins/$ARGV3/apcupsd.conf
/bin/sed -i "s#REPLACEBYDATADIR#$ARGV5/data/plugins/$ARGV3#"  $ARGV5/data/plugins/$ARGV3/apccontrol
chmod +x $ARGV5/data/plugins/$ARGV3/*
chmod -x $ARGV5/data/plugins/$ARGV3/*.conf
chmod -x $ARGV5/data/plugins/$ARGV3/*.tgz 2>/dev/null

# Exit with Status 0
exit 0
