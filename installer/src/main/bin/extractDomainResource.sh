#!/bin/sh
# *****************************************************************************
# extractDomainResource.sh
#
# Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
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
  echo "Usage: $1 [-help] [-use_encryption]"
  echo "          [-oracle_home <oracle_home>]"
  echo "          [-domain_home <domain_home>]"
  echo "          [-output_dir <output_dir>]"
  echo "          [-target <target>]"
  echo "          [-domain_resource_file <domain_resource_file>]"
  echo "          [-archive_file <archive_file>]"
  echo "          [-model_file <model_file>]"
  echo "          [-variable_file <variable_file>]"
  echo ""
  echo "    where:"
  echo "        oracle_home     - the existing Oracle Home directory for the domain."
  echo "                          This is required unless the ORACLE_HOME environment"
  echo "                          variable is set."
  echo ""
  echo "        domain_home     - the domain home directory to be used in output files."
  echo "                          This will override any value in the model."
  echo ""
  echo "        output_dir      - the location for the target output files."
  echo ""
  echo "        target          - the target output type. The default is wko."
  echo ""
  echo "        domain_resource_file - the location of the extracted domain resource file."
  echo "                               This is deprecated, use -output_dir to specify output location"
  echo ""
  echo "        archive_file    - the path to the archive file to use  If the -model_file"
  echo "                          argument is not specified, the model file in this archive"
  echo "                          will be used.  This can also be specified as a"
  echo "                          comma-separated list of archive files.  The overlapping contents in"
  echo "                          each archive take precedence over previous archives in the list."
  echo ""
  echo "        model_file      - the location of the model file to use.  This can also be specified as a"
  echo "                          comma-separated list of model locations, where each successive model layers"
  echo "                          on top of the previous ones."
  echo ""
  echo "        variable_file   - the location of the property file containing the values for variables used in"
  echo "                          the model. This can also be specified as a comma-separated list of property files,"
  echo "                          where each successive set of properties layers on top of the previous ones."
  echo ""
  echo "    The -use_encryption switch tells the program that one or more of the"
  echo "    passwords in the model or variables files are encrypted.  The program will"
  echo "    prompt for the decryption passphrase to use to decrypt the passwords."
  echo "    Please note that Java 8 or higher is required when using this feature."
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="extractDomainResource"; export WLSDEPLOY_PROGRAM_NAME

scriptName=$(basename "$0")
scriptPath=$(dirname "$0")

. "$scriptPath/shared.sh"

umask 27

checkJythonArgs "$@"

minJdkVersion=7
if [ "$USE_ENCRYPTION" == "true" ]; then
  minJdkVersion=8
fi

# required Java version is dependent on use of encryption
javaSetup $minJdkVersion

runJython extract_resource.py "$@"
