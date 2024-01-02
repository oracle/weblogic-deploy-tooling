#!/bin/sh
# *****************************************************************************
# discoverDomain.sh
#
# Copyright (c) 2017, 2023, Oracle Corporation and/or its affiliates.  All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       discoverDomain.sh - WLS Deploy tool to discover a domain.
#
#     DESCRIPTION
#       This script discovers the model of an existing domain and gathers
#       the binaries needed to recreate the domain elsewhere with all of
#       its applications and resources configured.
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
  echo "          [-domain_home <domain_home>]"
  echo "          -model_file <model_file>"
  echo "          <-archive_file <archive_file> | -skip_archive | -remote>"
  echo "          [-variable_file <variable_file>]"
  echo "          [-domain_type <domain_type>]"
  echo "          [-wlst_path <wlst_path>]"
  echo "          [-java_home <java_home>]"
  echo "          [-target <target>"
  echo "           -output_dir <output_dir>"
  echo "          ]"
  echo "          [-admin_url <admin_url>"
  echo "           -admin_user <admin_user>"
  echo "           -admin_pass_env <admin_pass_env> | -admin_pass_file <admin_pass_file>"
  echo "          ]"
  echo "          [-ssh_host <ssh_host>"
  echo "           -ssh_port <ssh_port>"
  echo "           -ssh_user <ssh_user>"
  echo "           -ssh_pass <ssh_pass>"
  echo "           -ssh_pass_env <ssh_pass_env> | -ssh_pass_file <ssh_pass_file> | -ssh_pass_prompt"
  echo "           -ssh_private_key <ssh_private_key>"
  echo "           -ssh_private_key_pass_env <ssh_private_key_pass_env> | -ssh_private_key_pass_file <ssh_private_key_pass_file> | -ssh_private_key_pass_prompt"
  echo "           -remote_domain_home <remote_domain_home>"
  echo "          ]"
  echo ""
  echo "    where:"
  echo "        oracle_home     - the existing Oracle Home directory for the domain."
  echo "                          This argument is required unless the ORACLE_HOME"
  echo "                          environment variable is set."
  echo ""
  echo "        domain_home     - the domain home directory.  This argument is"
  echo "                          required if -remote option is not specified"
  echo ""
  echo "        model_file      - the location of the model file to use.  This argument"
  echo "                          is required."
  echo ""
  echo "        archive_file    - the path to the archive file to use."
  echo ""
  echo "        variable_file   - the location of the variable file to write properties"
  echo "                          with the variable injector. If this argument is used,"
  echo "                          by default all the credentials in the discovered model"
  echo "                          will be replaced by a token and a property written to"
  echo "                          this file."
  echo ""
  echo "        domain_type     - the type of domain (e.g., WLS, JRF)."
  echo "                          Used to locate wlst.cmd if -wlst_path not specified."
  echo ""
  echo "        wlst_path       - the Oracle Home subdirectory of the wlst.sh"
  echo "                          script to use (e.g., <ORACLE_HOME>/soa)."
  echo ""
  echo "        java_home       - overrides the JAVA_HOME value when discovering domain"
  echo "                          values to be replaced with the java home global token."
  echo ""
  echo "        target          - the target output type. The default is wko."
  echo ""
  echo "        output_dir      - output directory for -target <target>."
  echo ""
  echo "        admin_url       - the admin server URL (used for online discover)."
  echo ""
  echo "        admin_user      - the admin username (used for online discover)."
  echo ""
  echo "        admin_pass_env  - An alternative to entering the admin password at a"
  echo "                          prompt. The value is an ENVIRONMENT VARIABLE name"
  echo "                          that WDT will use to retrieve the password."
  echo ""
  echo "        admin_pass_file - An alternative to entering the admin password at a"
  echo "                          prompt. The value is the name of a file with a"
  echo "                          string value which WDT will read to retrieve the"
  echo "                          password."
  echo ""
  echo "        ssh_host        - the host name for admin server when SSH protocol is used to collect resources"
  echo "                          from the admin server host."
  echo ""
  echo "        ssh_port        - the SSH port number for the admin server host."
  echo ""
  echo "        ssh_user        - the SSH user name for the admin server host."
  echo ""
  echo "        ssh_pass_env    - An alternative to entering the SSH password at the prompt.  The value is specified"
  echo "                          in an ENVIRONMENT VARIABLE name that WDT will use to retrieve the password"
  echo ""
  echo "        ssh_pass_file   - An alternative to entering the SSH password at the prompt.  The value is the name of"
  echo "                          a file with a string value which WDT will read to retrieve the password."
  echo ""
  echo "        ssh_pass_prompt - Prompt for the SSH password."
  echo ""
  echo "        ssh_private_key - the private key to use for connecting to the admin server host using SSH."
  echo ""
  echo "        ssh_private_key_pass_env - An alternative to entering the SSH private keystore password at the prompt."
  echo "                                   The value is specified in an ENVIRONMENT VARIABLE name that WDT will use"
  echo "                                   to retrieve the password"
  echo ""
  echo "        ssh_private_key_pass_file - An alternative to entering the SSH private keystore password at the prompt."
  echo "                                    The value is the name of a file with a string value which WDT will read"
  echo "                                    to retrieve the password."
  echo ""
  echo "        ssh_private_key_pass_prompt - Prompt for the SSH private keystore password."
  echo ""
  echo "        remote_domain_home - the domain home reside in the remote SSH host for the admin server."
  echo ""
  echo "    The -skip_archive argument suppresses the generation of the archive file."
  echo "    If present, the -archive_file argument will be ignored and the file"
  echo "    references in the model will be the names from the discovered domain's"
  echo "    local file system."
  echo ""
  echo "    The -remote argument, which only works in online mode, tells WDT to discover"
  echo "    the domain from a remote server.  Since there is no access to the remote"
  echo "    server's file system, no archive file will be generated.  However, the file"
  echo "    references in the model will contain the values pointing into the archive"
  echo "    file (which the user must construct separately).  With this option, the"
  echo "    -domain_home value should be the remote server's domain home path.  This"
  echo "    allows discover domain to tokenize any file system references containing"
  echo "    the domain home path."
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="discoverDomain"; export WLSDEPLOY_PROGRAM_NAME

scriptName=`basename "$0"`
scriptPath=`dirname "$0"`

. "$scriptPath/shared.sh"

umask 27

checkArgs "$@"

minJdkVersion=7
if [ "$USE_ENCRYPTION" = "true" ]; then
  minJdkVersion=8
fi

# required Java version is dependent on use of encryption
javaSetup $minJdkVersion

runWlst discover.py "$@"
