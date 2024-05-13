#!/bin/sh
# *****************************************************************************
# createDomain.sh
#
# Copyright (c) 2017, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       createDomain.sh - WLS Deploy tool to create empty domains.
#
#     DESCRIPTION
#       This script creates domains with basic servers, clusters, and 
#       machine configuration as specified by the model and the domain
#       templates.  Any domain types requiring RCU schemas will require
#       the RCU schemas to exist before running this script.
#
# This script uses the following variables:
#
# JAVA_HOME             - The location of the JDK to use.  The caller must set
#                         this variable to a valid Java 7 (or later) JDK.
#
# WLSDEPLOY_PROPERTIES  - Extra system properties to pass to WLST.  The caller
#                         can use this environment variable to add additional
#                         system properties to the WLST environment.
#

usage() {
  echo ""
  echo "Usage: $1 [-help] [-use_encryption] [-run_rcu]"
  echo "          [-oracle_home <oracle_home>]"
  echo "          -model_file <model_file>"
  echo "          <-domain_parent <domain_parent> | -domain_home <domain_home>>"
  echo "          [-domain_type <domain_type>]"
  echo "          [-java_home <java_home>]"
  echo "          [-archive_file <archive_file>]"
  echo "          [-variable_file <variable_file>]"
  echo "          [-opss_wallet <opss_wallet_file>]"
  echo "          [-opss_wallet_passphrase_env <opss_wallet_passphrase_env>]"
  echo "          [-opss_wallet_passphrase_file <opss_wallet_passphrase_file>]"
  echo "          [-passphrase_env <passphrase_env>]"
  echo "          [-passphrase_file <passphrase_file>]"
  echo "          [-passphrase_prompt]"
  echo "          [-wlst_path <wlst_path>]"
  echo ""
  echo "    where:"
  echo "        oracle_home     - the existing Oracle Home directory for the domain."
  echo "                          This argument is required unless the ORACLE_HOME"
  echo "                          environment variable is set."
  echo ""
  echo "        model_file      - the location of the model file to use.  This can also"
  echo "                          be specified as a comma-separated list of model"
  echo "                          locations, where each successive model layers on top"
  echo "                          of the previous ones.  This argument is required."
  echo ""
  echo "        domain_parent   - the parent directory where the domain should be"
  echo "                          created.  The domain name from the model will be"
  echo "                          appended to this location to become the domain home."
  echo "                          This argument is required unless -domain_home is"
  echo "                          provided."
  echo ""
  echo "        domain_home     - the full directory where the domain should be created."
  echo "                          This is used in cases where the domain name is"
  echo "                          different from the domain home directory name.  This"
  echo "                          argument is required unless -domain_parent is"
  echo "                          provided."
  echo ""
  echo "        domain_type     - the type of domain (e.g., WLS, JRF).  This controls"
  echo "                          the domain templates and template resource targeting."
  echo "                          Also used to locate wlst.cmd if -wlst_path not"
  echo "                          specified. If not specified, the default domain type"
  echo "                          is WLS."
  echo ""
  echo "        java_home       - the Java Home to use for the new domain.  If not"
  echo "                          specified, it defaults to the value of the JAVA_HOME"
  echo "                          environment variable."
  echo ""
  echo "        archive_file    - the path to the archive file to use.  This can also"
  echo "                          be specified as a comma-separated list of archive"
  echo "                          files.  The overlapping contents in each archive take"
  echo "                          precedence over previous archives in the list."
  echo ""
  echo "        variable_file   - the location of the property file containing the"
  echo "                          values for variables used in the model. This can also"
  echo "                          be specified as a comma-separated list of property"
  echo "                          files, where each successive set of properties layers"
  echo "                          on top of the previous ones."
  echo ""
  echo "        passphrase_env  - An alternative to entering the encryption passphrase"
  echo "                          at a prompt. The value is an ENVIRONMENT VARIABLE name"
  echo "                          that WDT will use to retrieve the passphrase."
  echo ""
  echo "        passphrase_file - An alternative to entering the encryption passphrase"
  echo "                          at a prompt. The value is the name of a file with a"
  echo "                          string value which WDT will read to retrieve the"
  echo "                          passphrase."
  echo ""
  echo "        opss_wallet_file - The path to the Oracle wallet containing the domain"
  echo "                           encryption key to use to reconnect the new domain to"
  echo "                           the existing RCU schemas."
  echo ""
  echo "        opss_wallet_passphrase_env - An alternative to entering the OPSS"
  echo "                          wallet passphrase at a prompt. The value is an"
  echo "                          ENVIRONMENT VARIABLE name that WDT will use to"
  echo "                          retrieve the passphrase."
  echo ""
  echo "        opss_wallet_passphrase_file - An alternative to entering the OPSS"
  echo "                          wallet passphrase at a prompt. The value is the name"
  echo "                          of a file with a string value which WDT will read to"
  echo "                          retrieve the passphrase."
  echo ""
  echo "        wlst_path       - the Oracle Home subdirectory of the wlst.sh"
  echo "                          script to use (e.g., <ORACLE_HOME>/soa)."
  echo ""
  echo "    The -run_rcu switch tells the program to run RCU to create the database"
  echo "    schemas specified by the domain type using the specified RCU prefix."
  echo "    Running RCU will drop any existing schemas with the same RCU prefix"
  echo "    if they exist prior to trying to create them so be forewarned."
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="createDomain"; export WLSDEPLOY_PROGRAM_NAME

scriptName=`basename "$0"`
scriptPath=`dirname "$0"`

. "$scriptPath/shared.sh"

umask 27

checkArgs "$@"

# required Java version and patch level is dependent on use of encryption.
# later versions of JDK 7 support encryption so let WDT figure it out.
minJdkVersion=7
javaSetup $minJdkVersion

runWlst create.py "$@"
