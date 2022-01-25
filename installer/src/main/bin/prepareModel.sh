#!/bin/sh
# *****************************************************************************
# prepareModel.sh
#
# Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
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
  echo "          -model_file <model list>  model files"
  echo "          -target <target_name>  name of target configuration, such as k8s"
  echo "          -output_dir <output_dir>  write the outputs to the directory specified"
  echo "          [-variable_file <variable file>  variable file used for macro substitution]"
  echo "          [-archive_file <archive file>  archive file used for validation and filtering based on specified target]"
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="prepareModel"; export WLSDEPLOY_PROGRAM_NAME

scriptName=$(basename "$0")
scriptPath=$(dirname "$0")

. "$scriptPath/shared.sh"

umask 27

checkJythonArgs "$@"

# Java 7 is required, no encryption is used
javaSetup 7

runJython prepare_model.py "$@"
