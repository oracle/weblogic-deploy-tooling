#!/bin/sh
# *****************************************************************************
# encryptModel.sh
#
# Copyright (c) 2017, 2023, Oracle  and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       encryptModel.sh - WLS Deploy tool to encrypt the password fields in
#                         the model and any referenced variables.
#
#     DESCRIPTION
#       This script searches the model file and variable file, if provided,
#       looking for password fields and encrypts them using the supplied
#       passphrase.  This passphrase must be passed to other tools in
#       order for them to be able to decrypt the passwords.  Please note
#       this feature requires JDK 1.8 or higher due to the encryption
#       algorithms selected.
#
# This script uses the following variables:
#
# JAVA_HOME             - The location of the JDK to use.  The caller must set
#                         this variable to a valid Java 8 (or later) JDK.
#
# WLSDEPLOY_PROPERTIES  - Extra system properties to pass to Java.  The caller
#                         can use this environment variable to add additional
#                         system properties to the Java environment.
#

usage() {
  echo ""
  echo "Usage: $1 [-help] [-manual]"
  echo "          [-oracle_home <oracle_home>]"
  echo "          [-model_file <model_file>]"
  echo "          [-variable_file <variable_file>]"
  echo "          [-passphrase_env <passphrase_env>]"
  echo "          [-passphrase_file <passphrase_file>]"
  echo "          [-passphrase_prompt]"
  echo ""
  echo "    where:"
  echo "        oracle_home     - the existing Oracle Home directory for the domain."
  echo "                          This is required unless the ORACLE_HOME environment"
  echo "                          variable is set."
  echo ""
  echo "        model_file      - the location of the model file. This can also be a"
  echo "                          comma-separated list of locations of a set"
  echo "                          of models. All models will be written back to the"
  echo "                          original locations."
  echo ""
  echo "        variable_file   - the location and name of the property file containing"
  echo "                          the variable values for all variables used in"
  echo "                          the model(s)."
  echo ""
  echo "        passphrase_env  - An alternative to entering the encryption passphrase"
  echo "                          at a prompt. The value is an ENVIRONMENT VARIABLE name"
  echo "                          that WDT will use to retrieve the passphrase."
  echo ""
  echo "        passphrase_file - An alternative to entering the encryption passphrase"
  echo "                          at a prompt. The value is the name of a file with a"
  echo "                          string value which WDT will read to retrieve the"
  echo "                          passphrase."
  echo ""
  echo "    The -manual switch can be used to run the tool without a model and get"
  echo "    the encrypted value for a single password."
  echo ""
  echo "    NOTE: This tool requires the use of JDK version 1.8 or higher."
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="encryptModel"; export WLSDEPLOY_PROGRAM_NAME

scriptName=`basename "$0"`
scriptPath=`dirname "$0"`

. "$scriptPath/shared.sh"

umask 27

checkJythonArgs "$@"

# required Java version and patch level is dependent on use of encryption.
# later versions of JDK 7 support encryption so let WDT figure it out.
minJdkVersion=7
javaSetup $minJdkVersion

runJython encrypt.py "$@"
