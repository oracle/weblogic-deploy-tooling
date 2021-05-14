#!/bin/sh
# *****************************************************************************
# compareModel.sh
#
# Copyright (c) 2020, Oracle Corporation and/or its affiliates.
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
# WLSDEPLOY_HOME        - The location of the WLS Deploy installation.
#                         If the caller sets this, the callers location will be
#                         honored provided it is an existing directory.
#                         Otherwise, the location will be calculated from the
#                         location of this script.
#
# WLSDEPLOY_PROPERTIES  - Extra system properties to pass to Java.  The caller
#                         can use this environment variable to add additional
#                         system properties to the Java environment.



usage() {
  echo ""
  echo "Usage: $1 [-help]"
  echo "          [-oracle_home <oracle_home> required unless the ORACLE_HOME environment variable is set]"
  echo "          [-output_dir <output_dir> write the outputs to the directory specified]"
  echo "          [                        diffed_model.json - json output of the differences between the models]"
  echo "          [                        diffed_model.yaml - yaml output of the differences between the models]"
  echo "          [                        compare_model_stdout - stdout of the tool compareModel ]"
  echo "          [-variable_file <variable file>  variable file used for macro substitution]"
  echo "          <new model> <old model>      Must be the last two arguments and must be same extensions (yaml or json)"
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="compareModel"; export WLSDEPLOY_PROGRAM_NAME

scriptName=$(basename "$0")
scriptPath=$(dirname "$0")

. "$scriptPath/shared.sh"

umask 27

checkJythonArgs "$@"

# Java 7 is required, no encryption is used
javaSetup 7

runJython compare_model.py "$@"
