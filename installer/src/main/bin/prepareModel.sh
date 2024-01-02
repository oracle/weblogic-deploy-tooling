#!/bin/sh
# *****************************************************************************
# prepareModel.sh
#
# Copyright (c) 2020, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       prepareModel.sh - prepare the model(s) for deploying to a target environment,
#                         such as WebLogic Kubernetes Operator.
#
#     DESCRIPTION
#       This script applies a target configuration to the specified model(s), and creates any scripts
#       or configuration files that are required.
#
# This script uses the following variables:
#
# JAVA_HOME             - The location of the JDK to use.  The caller must set
#                         this variable to a valid Java 7 (or later) JDK.
#
# WLSDEPLOY_PROPERTIES  - Extra system properties to pass to Java.  The caller
#                         can use this environment variable to add additional
#                         system properties to the Java environment.

usage() {
  echo ""
  echo "Usage: $1 [-help]"
  echo "          [-oracle_home <oracle_home>]"
  echo "          -model_file <model_file>"
  echo "          -target <target_name>"
  echo "          -output_dir <output_dir>"
  echo "          [-variable_file <variable_file>]"
  echo "          [-archive_file <archive_file>]"
  echo ""
  echo "    where:"
  echo "        oracle_home   - the existing Oracle Home directory for the domain."
  echo "                        This argument is required unless the ORACLE_HOME"
  echo "                        environment variable is set."
  echo ""
  echo "        model_file    - the location of the model file to use.  This can also"
  echo "                        be specified as a comma-separated list of model"
  echo "                        locations, where each successive model layers on top"
  echo "                        of the previous ones.  This argument is required."
  echo ""
  echo "        target        - the target output type. This argument is required."
  echo ""
  echo "        output_dir    - the location for the target output files.  This argument"
  echo "                        is required."
  echo ""
  echo "        variable_file - the location of the property file containing the values"
  echo "                        for variables used in the model.  This can also be"
  echo "                        specified as a comma-separated list of property files,"
  echo "                        where each successive set of properties layers on top"
  echo "                        of the previous ones."
  echo ""
  echo "        archive_file  - the path to the archive file to use.  This can also be"
  echo "                        specified as a comma-separated list of archive files."
  echo "                        The overlapping contents in each archive take precedence"
  echo "                        over previous archives in the list."
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="prepareModel"; export WLSDEPLOY_PROGRAM_NAME

scriptName=`basename "$0"`
scriptPath=`dirname "$0"`

. "$scriptPath/shared.sh"

umask 27

checkJythonArgs "$@"

# Java 7 is required, no encryption is used
javaSetup 7

runJython prepare_model.py "$@"
