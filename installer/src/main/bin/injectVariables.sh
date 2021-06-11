#!/bin/sh
# *****************************************************************************
# injectVariables.sh
#
# Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       injectVariables.sh - WLS Deploy tool to inject variables into the model
#
#     DESCRIPTION
#           This script will inject variable tokens into the model and persist the variables to the
#           indicated variable file. This can be run against a model that has injected variables. Any
#           injected variables will not be replaced. If the existing variable file was provided, the
#           new injected variables will be appended to the file.
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
  echo "          -model_file <model_file> | -archive_file <archive_file>"
  echo "          [-variable_injector_file <variable_injector_file>]"
  echo "          [-variable_keywords_file <variable_keywords_file>]"
  echo "          [-variable_properties_file <variable_file>]"
  echo ""
  echo "    where:"
  echo "         oracle_home     - the existing Oracle Home directory for the domain."
  echo "                           This is required unless the ORACLE_HOME environment"
  echo "                           variable is set."
  echo ""
  echo "         model_file      - the location of the model file in which variables will be injected."
  echo "                           If not specified, the tool will look for the model"
  echo "                           in the archive file. Either the model_file or the archive_file argument must be provided."
  echo ""
  echo "         archive_file    - the path to the archive file that contains a model in which the variables"
  echo "                           will be injected. If the -model_file argument is used, this argument will be"
  echo "                           ignored. The archive file must contain a valid model."
  echo ""
  echo "         variable_injector_file  - the location of the variable injector file which contains the variable"
  echo "                           injector keywords for this model injection run. If this argument is not provided,"
  echo "                           the model_variable_injector.json file must exist in the lib directory in the"
  echo "                           WLSDEPLOY_HOME location."
  echo ""
  echo "         variable_keywords_file   - this argument overrides the INSTALLED version of the allowed variable keywords"
  echo "                           for the variable injector. This argument is for advanced usage only. The installed"
  echo "                           keywords file is located in the lib directory of WLSDEPLOY_HOME location."
  echo ""
  echo "         variable_file   - the location of the property file in which to store any variable names injected"
  echo "                           into the model. This argument overrides the value in the model injector file."
  echo "                           If the variable file is not listed in the model injector file, and this command"
  echo "                           line argument is not used, the variable properties will be located and named"
  echo "                           based on the model file or archive file name and location."
  echo "                           If the variable file exists, new variable values will be appended to the file."
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="injectVariables"; export WLSDEPLOY_PROGRAM_NAME

scriptName=$(basename "$0")
scriptPath=$(dirname "$0")

. "$scriptPath/shared.sh"

umask 27

checkJythonArgs "$@"

# Java 7 is required, no encryption is used
javaSetup 7

runJython variable_inject.py "$@"
