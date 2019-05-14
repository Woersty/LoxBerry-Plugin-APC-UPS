#!/bin/bash

ARGV0=$0 # Zero argument is shell command
ARGV1=$1 # First argument is temp folder during install
ARGV2=$2 # Second argument is Plugin-Name for scipts etc.
ARGV3=$3 # Third argument is Plugin installation folder
ARGV4=$4 # Forth argument is Plugin version
ARGV5=$5 # Fifth argument is Base folder of LoxBerry

echo "<INFO> Creating temporary folders for upgrading"
mkdir -p /tmp/$ARGV1\_upgrade/log
mkdir -p /tmp/$ARGV1\_upgrade/data
shopt -s dotglob

echo "<INFO> Backing up existing scripts"
mv -v $ARGV5/data/plugins/$ARGV3/* /tmp/$ARGV1\_upgrade/data/

echo "<INFO> Backing up existing log files"
mv -v $ARGV5/log/plugins/$ARGV3/* /tmp/$ARGV1\_upgrade/log/

# Exit with Status 0
exit 0
