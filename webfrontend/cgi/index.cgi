#!/usr/bin/perl

# Copyright 2017 Christian Woerstenfeld, git@loxberry.woerstenfeld.de
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

use CGI::Carp qw(fatalsToBrowser);
use CGI qw/:standard/;
use Config::Simple;
use File::HomeDir;
#use Data::Dumper;
use HTML::Entities;
use Cwd 'abs_path';
use warnings;
use strict;
no  strict "refs"; # we need it for template system

##########################################################################
# Variables
##########################################################################
my  $cgi = new CGI;
our $cfg;
our $plugin_cfg;
our $phrase;
our $namef;
our $value;
our %query;
our $lang;
our $template_title;
our $help;
our @help;
our $helptext="";
our $helplink;
our $installfolder;
our $languagefile;
our @language_strings;
our $version;
our $error;
our $output;
our $message;
our $nexturl;
our $do="form";
my  $home = File::HomeDir->my_home;
our $psubfolder;
our $pname;
our $languagefileplugin;
our $phraseplugin;
our %Config;
our @config_params;
our $ups_params_list="";
our @ups_params="";
##########################################################################
# Read Settings
##########################################################################

# Version of this script
$version = "0.3";


# Figure out in which subfolder we are installed
$psubfolder = abs_path($0);
$psubfolder =~ s/(.*)\/(.*)\/(.*)$/$2/g;

# Start with header
print "Content-Type: text/html\n\n"; 

# Read general config
$cfg            = new Config::Simple("$home/config/system/general.cfg");
$installfolder  = $cfg->param("BASE.INSTALLFOLDER");
$lang           = $cfg->param("BASE.LANG");

# Get known Tags from plugin config
$plugin_cfg 		= new Config::Simple(syntax => 'ini');
$plugin_cfg 		= Config::Simple->import_from("$installfolder/config/plugins/$psubfolder/apc_ups.cfg", \%Config)  or die Config::Simple->error();
$pname          = $plugin_cfg->param("SCRIPTNAME");


# Everything from URL
foreach (split(/&/,$ENV{'QUERY_STRING'}))
{
  ($namef,$value) = split(/=/,$_,2);
  $namef =~ tr/+/ /;
  $namef =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
  $value =~ tr/+/ /;
  $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
  $query{$namef} = $value;
}

# Set parameters coming in - get over post
if ( !$query{'lang'} )         { if ( param('lang')         ) { $lang         = quotemeta(param('lang'));         } else { $lang         = $lang;  } } else { $lang         = quotemeta($query{'lang'});         }
if ( !$query{'do'} )           { if ( param('do')           ) { $do           = quotemeta(param('do'));           } else { $do           = "form"; } } else { $do           = quotemeta($query{'do'});           }


# Init Language
# Clean up lang variable
  $lang         =~ tr/a-z//cd;
  $lang         = substr($lang,0,2);
  # If there's no language phrases file for choosed language, use german as default
  if (!-e "$installfolder/templates/system/$lang/language.dat")
  {
    $lang = "de";
  }

# Read translations / phrases
  $languagefile       = "$installfolder/templates/system/$lang/language.dat";
  $phrase             = new Config::Simple($languagefile);
  $languagefileplugin = "$installfolder/templates/plugins/$psubfolder/$lang/language.dat";
  $phraseplugin       = new Config::Simple($languagefileplugin);
  foreach my $key (keys %{ $phraseplugin->vars() } )
  {
    (my $cfg_section,my $cfg_varname) = split(/\./,$key,2);
    push @language_strings, $cfg_varname;
  }
  foreach our $template_string (@language_strings)
  {
    ${$template_string} = $phraseplugin->param($template_string);
  }

##########################################################################
# Main program
##########################################################################

  &form;
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
		$template_title = $phrase->param("TXT0000") . ": " . $pname;

		# Print Template header
		&lbheader;

    @ups_params =split(/\n/,`/sbin/apcaccess status 2>&1`);
		foreach (@ups_params)
		{
			my $parameter 	= $_;
	    $parameter =~ s/([\n])//g;
	    $parameter =~ s/ /&nbsp;/g;
			$ups_params_list .= $parameter.'<br/>';
		}

  	# Parse page
		open(F,"$installfolder/templates/plugins/$psubfolder/$lang/settings.html") || die "Missing template plugins/$psubfolder/$lang/settings.html";
		while (<F>) 
		{
			$_ =~ s/<!--\$(.*?)-->/${$1}/g;
		  print $_;
		}
		close(F);

		# Parse page footer		
		&footer;
		exit;
	}


#####################################################
# Error-Sub
#####################################################

	sub error 
	{
		$template_title = $phrase->param("TXT0000") . " - " . $phrase->param("TXT0028");
		
		&lbheader;
		open(F,"$installfolder/templates/system/$lang/error.html") || die "Missing template system/$lang/error.html";
    while (<F>) 
    {
      $_ =~ s/<!--\$(.*?)-->/${$1}/g;
      print $_;
    }
		close(F);
		&footer;
		exit;
	}

#####################################################
# Page-Header-Sub
#####################################################

	sub lbheader 
	{
		 # Create Help page
	  $helplink = "http://www.loxwiki.eu/display/LOXBERRY/APC-UPS";
	  open(F,"$installfolder/templates/plugins/$psubfolder/$lang/help.html") || die "Missing template plugins/$psubfolder/$lang/help.html";
	    @help = <F>;
	    foreach (@help)
	    {
	      $_ =~ s/<!--\$psubfolder-->/$psubfolder/g;
	      s/[\n\r]/ /g;
	      $_ =~ s/<!--\$(.*?)-->/${$1}/g;
	      $helptext = $helptext . $_;
	    }
	  close(F);
	  open(F,"$installfolder/templates/system/$lang/header.html") || die "Missing template system/$lang/header.html";
	    while (<F>) 
	    {
	      $_ =~ s/<!--\$(.*?)-->/${$1}/g;
	      print $_;
	    }
	  close(F);
	}

#####################################################
# Footer
#####################################################

	sub footer 
	{
	  open(F,"$installfolder/templates/system/$lang/footer.html") || die "Missing template system/$lang/footer.html";
	    while (<F>) 
	    {
	      $_ =~ s/<!--\$(.*?)-->/${$1}/g;
	      print $_;
	    }
	  close(F);
	}
