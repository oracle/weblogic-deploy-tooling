#!/bin/sh
# *****************************************************************************
# verifySSH.sh
#
# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       verifySSH.sh - WLS Deploy tool to verify the environment's SSH configuration.
#
#     DESCRIPTION
#       This script attempts to establish an SSH connection with the provided
#       configuration and, optionally, download and/or upload a test file.
#
# This script uses the following variables:
#
# JAVA_HOME             - The path to the Java Home directory used by the ORACLE HOME.
#                         This overrides the JAVA_HOME value when locating attributes
#                         which will be replaced with the java home global token in the model
#
# WLSDEPLOY_PROPERTIES  - Extra system properties to pass to WLST.  The caller
#                         can use this environment variable to add additional
#                         system properties to the WLST environment.
#

usage() {
  echo ""
  echo "Usage: $1 [-help]"
  echo "          [-oracle_home <oracle_home>]"
  echo "          -ssh_host <ssh_host> [-ssh_port <ssh_port>]"
  echo "          [-ssh_user <ssh_user>]"
  echo "          ["
  echo "           -ssh_pass_env <ssh_pass_env> |"
  echo "           -ssh_pass_file <ssh_pass_file> |"
  echo "           -ssh_pass_prompt"
  echo "          ]"
  echo "          [-ssh_private_key <ssh_private_key>]"
  echo "          ["
  echo "           -ssh_private_key_pass_env <ssh_private_key_pass_env> |"
  echo "           -ssh_private_key_pass_file <ssh_private_key_pass_file> |"
  echo "           -ssh_private_key_pass_prompt"
  echo "          ]"
  echo "          [-remote_test_file <remote_test_file> -local_output_dir <local_output_dir>]"
  echo "          [-local_test_file <local_test_file> -remote_output_dir <remote_output_dir>]"
  echo "          [-wlst_path <wlst_path>]"
  echo ""
  echo "    where:"
  echo "        oracle_home     - the existing Oracle Home directory for the domain."
  echo "                          This argument is required unless the ORACLE_HOME"
  echo "                          environment variable is set."
  echo ""
  echo "        ssh_host        - the hostname or IP address of the remote machine.  This"
  echo "                          argument is required."
  echo ""
  echo "        ssh_port        - the port number to use to connect to the remote machine."
  echo "                          This argument is optional and defaults to 22, if not"
  echo "                          specified."
  echo ""
  echo "        ssh_user        - the SSH user name on the remote machine.  This argument"
  echo "                          is optional and defaults to the current user on the"
  echo "                          local machine, as determined by the user.name Java"
  echo "                          system property."
  echo ""
  echo "        ssh_pass_env    - An alternative to entering the SSH user's password"
  echo "                          at a prompt. The value is an ENVIRONMENT VARIABLE"
  echo "                          name that WDT will use to retrieve the password."
  echo "                          This argument should only be used when using"
  echo "                          username/password-based authentication."
  echo ""
  echo "        ssh_pass_file   - An alternative to entering SSH user's password"
  echo "                          at a prompt. The value is the name of a file with a"
  echo "                          string value which WDT will read to retrieve the"
  echo "                          password.  This argument should only be used"
  echo "                          when using username/password-based authentication."
  echo ""
  echo "        ssh_private_key - the path to the private key to use for SSH"
  echo "                          authentication.  This argument is optional and defaults"
  echo "                          to the normal default SSH key (e.g., ~/.ssh/id_rsa)."
  echo "                          This argument should only be used when using"
  echo "                          public key-based authentication."
  echo ""
  echo "        ssh_private_key_pass_env - An alternative to entering the private key"
  echo "                          passphrase at a prompt. The value is an ENVIRONMENT"
  echo "                          VARIABLE name that WDT will use to retrieve the"
  echo "                          password.  This argument should only be used when"
  echo "                          using public key-based authentication and the"
  echo "                          private key is encrypted with a passphrase."
  echo ""
  echo "        ssh_private_key_pass_file - An alternative to entering SSH private key"
  echo "                          passphrase at a prompt. The value is the name of a"
  echo "                          file with a string value which WDT will read to"
  echo "                          retrieve the password.  This argument should only be"
  echo "                          used when using username/password-based"
  echo "                          authentication and the private key is encrypted with"
  echo "                          a passphrase."
  echo ""
  echo "        wlst_path       - the Oracle Home subdirectory of the wlst.sh"
  echo "                          script to use (e.g., <ORACLE_HOME>/soa)."
  echo ""
  echo "    The -ssh_pass_prompt argument tells WDT to prompt for the SSH user's"
  echo "    password and read it from standard input.  This is also useful for"
  echo "    scripts that want to pipe the value into the tool's standard input."
  echo ""
  echo "    The -ssh_private_key_pass_prompt argument tells WDT to prompt for the"
  echo "    private key passphrase and read it from standard input. This is also"
  echo "    useful for scripts that want to pipe the value into the tool's"
  echo "    standard input."
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="verifySSH"; export WLSDEPLOY_PROGRAM_NAME

scriptName=$(basename "$0")
scriptPath=$(dirname "$0")

. "$scriptPath/shared.sh"

umask 27

checkArgs "$@"

minJdkVersion=7
if [ "$USE_ENCRYPTION" == "true" ]; then
  minJdkVersion=8
fi

# required Java version is dependent on use of encryption
javaSetup $minJdkVersion

runWlst verify_ssh.py "$@"
