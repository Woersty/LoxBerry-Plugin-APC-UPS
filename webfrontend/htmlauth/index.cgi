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

use LoxBerry::Storage;
use File::Basename;
use LoxBerry::Web;
use LoxBerry::Log;
use CGI::Carp qw(fatalsToBrowser);
use CGI qw/:standard/;
use Config::Simple '-strict';
use HTML::Entities;
#use Cwd 'abs_path';
use warnings;
no warnings 'uninitialized';
use strict;
no  strict "refs"; 
require Time::Piece;

##########################################################################
# Variables
##########################################################################
my %Config;
my $languagefile				= "language.ini";
my $maintemplatefilename 		= "settings.html";
my $helptemplatefilename		= "help.html";
my $template_title;
my $helpurl 					= "https://www.loxwiki.eu/display/LOXBERRY/APC-UPS";
my $log 						= LoxBerry::Log->new ( name => 'Admin-UI' ); 
##########################################################################
# Read Settings
##########################################################################

# Version 
my $version = LoxBerry::System::pluginversion();
my $plugin = LoxBerry::System::plugindata();
$LoxBerry::System::DEBUG 	= 1 if $plugin->{PLUGINDB_LOGLEVEL} eq 7;
$LoxBerry::Web::DEBUG 		= 1 if $plugin->{PLUGINDB_LOGLEVEL} eq 7;
$log->loglevel($plugin->{PLUGINDB_LOGLEVEL});
LOGSTART "";
LOGOK "Version: ".$version   if $plugin->{PLUGINDB_LOGLEVEL} ge 5;
my $lang = lblanguage();
LOGDEB   "Language is: " . $lang;
my %L = LoxBerry::System::readlanguage();
my $maintemplate = HTML::Template->new(
		filename => $lbptemplatedir . "/" . $maintemplatefilename,
		global_vars => 1,
		loop_context_vars => 1,
		die_on_bad_params=> 0,
		%htmltemplate_options,
		debug => 1
		);
my %L = LoxBerry::System::readlanguage($maintemplate, $languagefile);
$maintemplate->param( "LBPPLUGINDIR"			, $lbpplugindir);
$maintemplate->param( "LOGO_ICON"				, get_plugin_icon(64) );
$maintemplate->param( "VERSION"					, $version);

LOGDEB "Check for pending notifications for: " . $lbpplugindir . " " . $L{'APC_UPS.MY_NAME'};
my $notifications = LoxBerry::Log::get_notifications_html($lbpplugindir, $L{'APC_UPS.MY_NAME'});
LOGDEB "Notifications are:\n".encode_entities($notifications) if $notifications;
LOGDEB "No notifications pending." if !$notifications;
$maintemplate->param( "NOTIFICATIONS" , $notifications);


##########################################################################
# Main program
##########################################################################

LOGDEB "Call page";
&form;

LOGEND "";
exit;

#####################################################
# 
# Subroutines
#
#####################################################

#####################################################
# Form-Sub
#####################################################

	sub form 
	{
		# The page title read from language file + our name
		$template_title = $L{"APC_UPS.MY_NAME"};

		# Print Template header
		LoxBerry::Web::lbheader($template_title, $helpurl, $helptemplatefilename);

		$maintemplate->param("HTMLPATH" => "/plugins/".$lbpplugindir."/");
		
		my @ups_params;
		my $ups_params_list;
	    @ups_params =split(/\n/,`/sbin/apcaccess status 2>&1`);
		foreach (@ups_params)
		{
			my $parameter 	= $_;
		    $parameter =~ s/([\n])//g;
		    $parameter =~ s/ /&nbsp;/g;
			$ups_params_list .= $parameter.'<br/>';
		}
		$maintemplate->param("UPS_PARAMS" => $ups_params_list);
	
    	print $maintemplate->output();
		LoxBerry::Web::lbfooter();
	}








