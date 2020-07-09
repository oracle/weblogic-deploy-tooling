#!/bin/sh
# *****************************************************************************
# updateDomain.sh
#
# Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       updateDomain.sh - WLS Deploy tool to update an existing domain.
#
#     DESCRIPTION
#       This script updates the domain configuration, adds resources, and
#       deploys applications.
#
# This script uses the following variables:
#
# JAVA_HOME             - The location of the JDK to use.  The caller must set
#                         this variable to a valid Java 7 (or later) JDK.
#
# WLSDEPLOY_HOME        - The location of the WLS Deploy installation.
#                         If the caller sets this, the callers location will be
#                         honored provided it is an existing directory.
#                         Otherwise, the location will be calculated from the
#                         location of this script.
#
# WLSDEPLOY_PROPERTIES  - Extra system properties to pass to WLST.  The caller
#                         can use this environment variable to add additional
#                         system properties to the WLST environment.
#

usage() {
  echo ""
  echo "Usage: $1 [-help] [-use_encryption]"
  echo "          [-oracle_home <oracle_home>]"
  echo "          -domain_home <domain_home>"
  echo "          [-archive_file <archive_file>]"
  echo "          [-model_file <model_file>]"
  echo "          [-variable_file <variable_file>]"
  echo "          [-domain_type <domain_type>]"
  echo "          [-wlst_path <wlst_path>]"
  echo "          [-rollback_if_require_restart]"
  echo "          [-admin_url <admin_url>"
  echo "           -admin_user <admin_user>"
  echo "          ]"
  echo ""
  echo "    where:"
  echo "        oracle_home     - the existing Oracle Home directory for the domain."
  echo "                          This is required unless the ORACLE_HOME environment"
  echo "                          variable is set."
  echo ""
  echo "        domain_home     - the domain home directory"
  echo ""
  echo "        archive_file    - the path to the archive file to use.  If the -model_file"
  echo "                          argument is not specified, the model file in this archive"
  echo "                          will be used.  This can also be specified as a"
  echo "                          comma-separated list of archive files.  The overlapping contents in"
  echo "                          each archive take precedence over previous archives in the list."
  echo ""
  echo "        model_file      - the location of the model file to use.  This can also be specified as a"
  echo "                          comma-separated list of model locations, where each successive model layers"
  echo "                          on top of the previous ones."
  echo ""
  echo "        variable_file   - the location of the property file containing the values for variables used in"
  echo "                          the model. This can also be specified as a comma-separated list of property files,"
  echo "                          where each successive set of properties layers on top of the previous ones."
  echo ""
  echo "        domain_type     - the type of domain (e.g., WLS, JRF)."
  echo "                          Used to locate wlst.cmd if -wlst_path not specified"
  echo ""
  echo "        wlst_path       - the Oracle Home subdirectory of the wlst.cmd"
  echo "                          script to use (e.g., <ORACLE_HOME>/soa)"
  echo ""
  echo "        admin_url       - the admin server URL (used for online deploy)"
  echo ""
  echo "        admin_user      - the admin username (used for online deploy)"
  echo ""
  echo "        rollback_if_require_restart      - rollback the changes if the update requires domain restart"
  echo ""
  echo "    The -use_encryption switch tells the program that one or more of the"
  echo "    passwords in the model or variables files are encrypted.  The program will"
  echo "    prompt for the decryption passphrase to use to decrypt the passwords."
  echo "    Please note that Java 8 or higher is required when using this feature."
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="updateDomain"; export WLSDEPLOY_PROGRAM_NAME

scriptName=`basename $0`
scriptPath=$(dirname "$0")
scriptArgs=$*

. $scriptPath/shared.sh

umask 27

checkArgs "$@"

minJdkVersion=7
if [ "$USE_ENCRYPTION" == "true" ]; then
  minJdkVersion=8
fi

# required Java version is dependent on use of encryption
javaSetup $minJdkVersion

runWlst update.py
