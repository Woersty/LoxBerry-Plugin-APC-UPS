#!/usr/bin/perl

# Copyright 2016-2019 Christian Woerstenfeld, git@loxberry.woerstenfeld.de
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


##########################################################################
# Modules
##########################################################################
use LoxBerry::Web;
use LoxBerry::Log;
use CGI::Carp qw(fatalsToBrowser);
use CGI qw/:standard/;
use HTML::Entities;
use warnings;
no  warnings 'uninitialized';
use strict;
no  strict "refs"; 

##########################################################################
# Variables
##########################################################################
my $languagefile				= "language.ini";
my $maintemplatefilename 		= "settings.html";
my $template_title				= "";
my $helpurl 					= "https://www.loxwiki.eu/display/LOXBERRY/APC-UPS";
my $log 						= LoxBerry::Log->new ( name => 'Admin-UI' ); 
##########################################################################
# Read Settings
##########################################################################

# Init plugin infos
my $version = LoxBerry::System::pluginversion();
my $plugin 	= LoxBerry::System::plugindata();
my $lang 	= lblanguage();

# Set Debug for LoxBerry Modules if loglevel is 7
$LoxBerry::System::DEBUG 	= 1 if $plugin->{PLUGINDB_LOGLEVEL} eq 7;
$LoxBerry::Web::DEBUG 		= 1 if $plugin->{PLUGINDB_LOGLEVEL} eq 7;
$log->loglevel($plugin->{PLUGINDB_LOGLEVEL});

# Start Logfile
LOGSTART "";
LOGOK    "Version: ".$version if $plugin->{PLUGINDB_LOGLEVEL} ge 5;
LOGDEB   "Language is: " . $lang;

# Init template
my $maintemplate = HTML::Template->new(
	filename => $lbptemplatedir . "/" . $maintemplatefilename,
	global_vars => 1,
	loop_context_vars => 1,
	die_on_bad_params=> 0,
	%htmltemplate_options,
	debug => 1 );

# Read language
my %L = LoxBerry::System::readlanguage($maintemplate, $languagefile);

# Check notifications
LOGDEB "Check for pending notifications for: " . $lbpplugindir . " " . $L{'APC_UPS.MY_NAME'};
my $notifications = LoxBerry::Log::get_notifications_html($lbpplugindir, $L{'APC_UPS.MY_NAME'});
LOGDEB "Notifications are:\n".encode_entities($notifications) if $notifications;
LOGDEB "No notifications pending." if !$notifications;

# The page title read from language file + our name
$template_title = $L{"APC_UPS.MY_NAME"};

# Start page
LoxBerry::Web::lbheader($template_title, $helpurl);

# Init UPS parameter
my @ups_params;
my $ups_params_list;

# Read data from UPS
@ups_params =split(/\n/,`/sbin/apcaccess status 2>&1`);

# Parse data (just for view on admin page)
foreach (@ups_params)
{
	my $parameter 	= $_;
    $parameter =~ s/([\n])//g;
    $parameter =~ s/ /&nbsp;/g;
	$ups_params_list .= $parameter.'<br/>';
}

# Fill template
$maintemplate->param( "LBPPLUGINDIR" , $lbpplugindir);
$maintemplate->param( "LOGO_ICON"	 , get_plugin_icon(64));
$maintemplate->param( "VERSION"		 , $version);
$maintemplate->param( "NOTIFICATIONS", $notifications);
$maintemplate->param("HTMLPATH"      , "/plugins/".$lbpplugindir."/");
$maintemplate->param("UPS_PARAMS" => $ups_params_list);

# Print template
print $maintemplate->output();

# Close page
LoxBerry::Web::lbfooter();

# Close log and exit
LOGEND "";
exit;
