#!/bin/sh
# *****************************************************************************
# validateModel.sh
#
# Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
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
# WLSDEPLOY_HOME        - The location of the WLS Deploy installation.
#                         If the caller sets this, the callers location will be
#                         honored provided it is an existing directory.
#                         Otherwise, the location will be calculated from the
#                         location of this script.
#
# WLSDEPLOY_PROPERTIES  - Extra system properties to pass to Java.  The caller
#                         can use this environment variable to add additional
#                         system properties to the Java environment.
#

usage() {
  echo ""
  echo "Usage: $1 [-help]"
  echo "          [-oracle_home <oracle_home>]"
  echo "          [-model_file <model_file>]"
  echo "          [-variable_file <variable_file>]"
  echo "          [-archive_file <archive_file>]"
  echo "          [-target <target>]"
  echo "          [-target_version <target_version>]"
  echo "          [-target_mode <target_mode>]"
  echo "          [-method <method>]"
  echo ""
  echo "    where:"
  echo "        oracle_home     - the existing Oracle Home directory for the domain."
  echo "                          This is required unless the ORACLE_HOME environment"
  echo "                          variable is set."
  echo ""
  echo "        model_file      - the location of the model file to use.  This can also be specified as a"
  echo "                          comma-separated list of model locations, where each successive model layers"
  echo "                          on top of the previous ones.  If not specified, the tool will look for the"
  echo "                          model in the archive.  If the model is not found, validation will only"
  echo "                          validate the artifacts provided."
  echo ""
  echo "        variable_file   - the location of the property file containing"
  echo "                          the variable values for all variables used in the model."
  echo "                          If the variable file is not provided, validation will"
  echo "                          only validate the artifacts provided."
  echo ""
  echo "        archive_file    - the path to the archive file to use.  If the archive file is"
  echo "                          not provided, validation will only validate the"
  echo "                          artifacts provided.  This can also be specified as a"
  echo "                          comma-separated list of archive files.  The overlapping contents in"
  echo "                          each archive take precedence over previous archives in the list."
  echo ""
  echo "        target          - target platform (wko, etc.)."
  echo "                          this determines the structure of the kubernetes section."
  echo ""
  echo "        target_version  - the target version of WebLogic Server the tool"
  echo "                          should use to validate the model content.  This"
  echo "                          version number can be different than the version"
  echo "                          being used to run the tool.  If not specified, the"
  echo "                          tool will validate against the version being used"
  echo "                          to run the tool."
  echo ""
  echo "        target_mode     - the target WLST mode that the tool should use to"
  echo "                          validate the model content.  The only valid values"
  echo "                          are online or offline.  If not specified, the tool"
  echo "                          defaults to WLST offline mode."
  echo ""
  echo "        method          - the validation method to apply. Options: lax, strict. "
  echo "                          The lax method will skip validation of external model references like @@FILE@@"
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="validateModel"; export WLSDEPLOY_PROGRAM_NAME

scriptName=$(basename "$0")
scriptPath=$(dirname "$0")

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
