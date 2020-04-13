#!/bin/sh
# *****************************************************************************
# compareModel.sh
#
# Copyright (c) 2020, Oracle Corporation and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       compareModel.sh - WLS Deploy tool to compare two models
#
#     DESCRIPTION
#       This script compares two models. The models compared must be both yaml or both json
#
# This script uses the following variables:
#
# JAVA_HOME             - The location of the JDK to use.  The caller must set
#                         this variable to a valid Java 7 (or later) JDK.
#


usage() {
  echo ""
  echo "Usage: $1 [-help]"
  echo "          -oracle_home <oracle_home> "
  echo "          [-compare_model_output_dir <output_dir> write the outputs to the directory specified]"
  echo "          [                        diffed_model.json - json output of the differences between the models]"
  echo "          [                        diffed_model.yaml - yaml output of the differences between the models]"
  echo "          [                        model_diff_stdout - stdout of the tool compareModel ]"
  echo "          [                        model_diff_rc - comma separated return code for the differences ]"
  echo "          <model 1> <model2>      Must be the last two arguments and must be same extensions (yaml or json)"
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="modelDiff"; export WLSDEPLOY_PROGRAM_NAME

scriptName=`basename $0`
scriptPath=$(dirname "$0")
scriptArgs=$*

. $scriptPath/shared.sh

umask 27

checkJythonArgs "$@"

# Java 7 is required, no encryption is used
javaSetup 7

runJython model_diff.py
