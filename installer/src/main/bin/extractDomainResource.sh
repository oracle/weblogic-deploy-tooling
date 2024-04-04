#!/bin/sh
# *****************************************************************************
# extractDomainResource.sh
#
# Copyright (c) 2020, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       extractDomainResource.sh - Create a domain resource file for Kubernetes deployment.
#
#     DESCRIPTION
#       This script creates a domain resource file for Kubernetes deployment.
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
  echo "Usage: $1 [-help] [-use_encryption]"
  echo "          [-oracle_home <oracle_home>]"
  echo "          -model_file <model_file>"
  echo "          -output_dir <output_dir>"
  echo "          [-domain_home <domain_home>]"
  echo "          [-target <target>]"
  echo "          [-variable_file <variable_file>]"
  echo ""
  echo "    where:"
  echo "        oracle_home   - the existing Oracle Home directory for the domain."
  echo "                        This argument is required unless the ORACLE_HOME"
  echo "                         environment variable is set."
  echo ""
  echo "        model_file    - the location of the model file to use.  This can also"
  echo "                        be specified as a comma-separated list of model"
  echo "                        locations, where each successive model layers on top"
  echo "                        of the previous ones.  This argument is required."
  echo ""
  echo "        output_dir    - the location for the target output files.  This argument"
  echo "                        is required."
  echo ""
  echo "        domain_home   - the domain home directory to be used in output files."
  echo "                        This will override any value in the model."
  echo ""
  echo "        target        - the target output type. The default is wko."
  echo ""
  echo "        variable_file - the location of the property file containing the"
  echo "                        values for variables used in the model. This can also"
  echo "                        be specified as a comma-separated list of property"
  echo "                        files, where each successive set of properties layers"
  echo "                        on top of the previous ones."
  echo ""
  echo "    The -use_encryption switch tells the program that one or more of the"
  echo "    passwords in the model or variables files are encrypted.  The program will"
  echo "    prompt for the decryption passphrase to use to decrypt the passwords."
  echo "    Please note that Java 8 or higher is required when using this feature."
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="extractDomainResource"; export WLSDEPLOY_PROGRAM_NAME

scriptName=`basename "$0"`
scriptPath=`dirname "$0"`

. "$scriptPath/shared.sh"

umask 27

checkJythonArgs "$@"

minJdkVersion=7
if [ "$USE_ENCRYPTION" = "true" ]; then
  minJdkVersion=8
fi

# required Java version is dependent on use of encryption
javaSetup $minJdkVersion

runJython extract_resource.py "$@"
