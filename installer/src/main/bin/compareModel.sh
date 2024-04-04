#!/bin/sh
# *****************************************************************************
# compareModel.sh
#
# Copyright (c) 2020, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       compareModel.sh - WLS Deploy tool to compare two models  (new vs old)
#
#     DESCRIPTION
#       This script compares two models. The models compared must be both yaml or both json files
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
  echo "          [-output_dir <output_dir>]"
  echo "          [-variable_file <variable file>]"
  echo "          <new_model> <old_model>"
  echo ""
  echo "    where:"
  echo ""
  echo "        oracle_home     - the existing Oracle Home directory for the domain."
  echo "                          This argument is required unless the ORACLE_HOME"
  echo "                          environment variable is set."
  echo ""
  echo "        output_dir      - the directory to which the output files are written:"
  echo "                            diffed_model.json - differences in JSON."
  echo "                            diffed_model.yaml - differences in YAML."
  echo "                            compare_model_stdout - compareModel tool stdout."
  echo ""
  echo "        variable_file   - the location of the property file containing the"
  echo "                          values for variables used in the model. This can"
  echo "                          also be specified as a comma-separated list of"
  echo "                          property files, where each successive set of"
  echo "                          properties layers on top of the previous ones."
  echo ""
  echo "        new_model       - the newer model to use for comparison."
  echo ""
  echo "        old_model       - the older model to use for comparison."
  echo ""
  echo "    NOTE: The model files being compared must be in the same format"
  echo "          (i.e., JSON or YAML)."
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="compareModel"; export WLSDEPLOY_PROGRAM_NAME

scriptName=`basename "$0"`
scriptPath=`dirname "$0"`

. "$scriptPath/shared.sh"

umask 27

checkJythonArgs "$@"

# Java 7 is required, no encryption is used
javaSetup 7

runJython compare_model.py "$@"
