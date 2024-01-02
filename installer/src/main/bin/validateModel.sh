#!/bin/sh
# *****************************************************************************
# validateModel.sh
#
# Copyright (c) 2017, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       validateModel.sh - WLS Deploy tool to validate artifacts
#
#     DESCRIPTION
#       This script validates the model and archive structure
#
# This script uses the following variables:
#
# JAVA_HOME             - The location of the JDK to use.  The caller must set
#                         this variable to a valid Java 7 (or later) JDK.
#
# WLSDEPLOY_PROPERTIES  - Extra system properties to pass to Java.  The caller
#                         can use this environment variable to add additional
#                         system properties to the Java environment.
#

usage() {
  echo ""
  echo "Usage: $1 [-help]"
  echo "          [-oracle_home <oracle_home>]"
  echo "          -model_file <model_file>"
  echo "          [-variable_file <variable_file>]"
  echo "          [-archive_file <archive_file>]"
  echo "          [-target <target>]"
  echo "          [-target_version <target_version>]"
  echo "          [-target_mode <target_mode>]"
  echo "          [-domain_type <domain_type>]"
  echo "          [-method <method>]"
  echo ""
  echo "    where:"
  echo "        oracle_home    - the existing Oracle Home directory for the domain."
  echo "                         This argument is required unless the ORACLE_HOME"
  echo "                         environment variable is set."
  echo ""
  echo "        model_file     - the location of the model file to use.  This can also"
  echo "                         be specified as a comma-separated list of model"
  echo "                         locations, where each successive model layers on top"
  echo "                         of the previous ones.  This argument is required."
  echo ""
  echo "        variable_file  - the location of the property file containing the"
  echo "                         variable values for all variables used in the model."
  echo "                         If the variable file is not provided, validation will"
  echo "                         only validate the artifacts provided."
  echo ""
  echo "        archive_file   - the path to the archive file to use.  If the archive"
  echo "                         file is not provided, validation will only validate the"
  echo "                         artifacts provided.  This can also be specified as a"
  echo "                         comma-separated list of archive files.  The overlapping"
  echo "                         contents in each archive take precedence over previous"
  echo "                         archives in the list."
  echo ""
  echo "        target         - target platform (wko, etc.).  This determines the"
  echo "                         structure of the kubernetes section."
  echo ""
  echo "        target_version - the target version of WebLogic Server the tool"
  echo "                         should use to validate the model content.  This"
  echo "                         version number can be different than the version"
  echo "                         being used to run the tool.  If not specified, the"
  echo "                         tool will validate against the version being used"
  echo "                         to run the tool."
  echo ""
  echo "        target_mode    - the target WLST mode that the tool should use to"
  echo "                         validate the model content.  The only valid values"
  echo "                         are online or offline.  If not specified, the tool"
  echo "                         defaults to WLST offline mode."
  echo ""
  echo "        domain_type    - the type of domain (e.g., WLS, JRF).  If not specified,"
  echo "                         the default is WLS."
  echo ""
  echo "        method         - the validation method to apply. Options: lax, strict."
  echo "                         The lax method will skip validation of external model"
  echo "                         references like @@FILE@@."
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="validateModel"; export WLSDEPLOY_PROGRAM_NAME

scriptName=`basename "$0"`
scriptPath=`dirname "$0"`

. "$scriptPath/shared.sh"

umask 27

# check for deprecated -print_usage argument
for arg in "$@"
do
    if [ "$arg" = "-print_usage" ]; then
        echo ""
        echo "The -print_usage functionality has been moved to modelHelp.sh"
        exit 99
    fi
done

checkJythonArgs "$@"

# Java 7 is required, no encryption is used
javaSetup 7

runJython validate.py "$@"
