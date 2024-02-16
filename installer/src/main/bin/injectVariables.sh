#!/bin/sh
# *****************************************************************************
# injectVariables.sh
#
# Copyright (c) 2017, 2024, Oracle and/or its affiliates.
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
# WLSDEPLOY_PROPERTIES  - Extra system properties to pass to Java.  The caller
#                         can use this environment variable to add additional
#                         system properties to the Java environment.
#

usage() {
  echo ""
  echo "Usage: $1 [-help]"
  echo "          [-oracle_home <oracle_home>]"
  echo "          -model_file <model_file>"
  echo "          [-variable_injector_file <variable_injector_file>]"
  echo "          [-variable_properties_file <variable_file>]"
  echo ""
  echo "    where:"
  echo "        oracle_home     - the existing Oracle Home directory for the domain."
  echo "                          This argument is required unless the ORACLE_HOME"
  echo "                          environment variable is set."
  echo ""
  echo "        model_file      - the location of the model file in which variables will"
  echo "                          be injected.  This argument is required."
  echo ""
  echo "        variable_injector_file - the location of the variable injector file"
  echo "                          which contains the variable injector keywords for this"
  echo "                          model injection run. If this argument is not provided,"
  echo "                          the model_variable_injector.json file must exist in"
  echo "                          the lib directory in the WLSDEPLOY_HOME location."
  echo ""
  echo "        variable_file   - the location of the property file in which to store"
  echo "                          any variable names injected into the model."
  echo "                          If this command-line argument is not used,"
  echo "                          the variable properties will be located and named"
  echo "                          based on the model file name and location."
  echo "                          If the variable file exists, new variable values"
  echo "                          will be appended to the file."
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="injectVariables"; export WLSDEPLOY_PROGRAM_NAME

scriptName=`basename "$0"`
scriptPath=`dirname "$0"`

. "$scriptPath/shared.sh"

umask 27

checkJythonArgs "$@"

# Java 7 is required, no encryption is used
javaSetup 7

runJython variable_inject.py "$@"
