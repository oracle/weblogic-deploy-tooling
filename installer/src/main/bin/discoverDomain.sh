#!/bin/sh
# *****************************************************************************
# discoverDomain.sh
#
# Copyright (c) 2017, 2024, Oracle and/or its affiliates.
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
  echo "           -ssh_pass_env <ssh_pass_env> | -ssh_pass_file <ssh_pass_file> | -ssh_pass_prompt"
  echo "           -ssh_private_key <ssh_private_key>"
  echo "           -ssh_private_key_pass_env <ssh_private_key_pass_env> | -ssh_private_key_pass_file <ssh_private_key_pass_file> | -ssh_private_key_pass_prompt"
  echo "          ]"
  echo "          [ -discover_passwords"
  echo "            -passphrase_env <passphrase_env> | -passphrase_file <passphrase_file> | -passphrase_prompt"
  echo "          ]"
  echo "          [ -discover_security_provider_data <discover_security_provider_scope>"
  echo "            -passphrase_env <passphrase_env> | -passphrase_file <passphrase_file> | -passphrase_prompt"
  echo "          ]"
  echo "          [ -discover_opss_wallet"
  echo "            [-opss_wallet_passphrase_env <opss_wallet_passphrase_env> | -opss_wallet_passphrase_file <opss_wallet_passphrase_file>]"
  echo "            -passphrase_env <passphrase_env> | -passphrase_file <passphrase_file> | -passphrase_prompt"
  echo "          ]"
  echo ""
  echo "    where:"
  echo "        oracle_home     - the existing Oracle Home directory for the domain."
  echo "                          This argument is required unless the ORACLE_HOME"
  echo "                          environment variable is set."
  echo ""
  echo "        domain_home     - the domain home directory.  This argument is"
  echo "                          required if running in offline mode."
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
  echo "        ssh_host        - the host name for admin server when SSH protocol is"
  echo "                          used to collect resources from the admin server host."
  echo ""
  echo "        ssh_port        - the SSH port number for the admin server host."
  echo ""
  echo "        ssh_user        - the SSH user name for the admin server host."
  echo ""
  echo "        ssh_pass_env    - An alternative to entering the SSH password at the"
  echo "                          prompt.  The value is specifiedin an ENVIRONMENT"
  echo "                          VARIABLE name that WDT will use to retrieve the"
  echo "                          password."
  echo ""
  echo "        ssh_pass_file   - An alternative to entering the SSH password at the"
  echo "                          prompt.  The value is the name of a file with a"
  echo "                          string value which WDT will read to retrieve the"
  echo "                          password."
  echo ""
  echo "        ssh_pass_prompt - Prompt for the SSH password."
  echo ""
  echo "        ssh_private_key - the private key to use for connecting to the admin"
  echo "                          server host using SSH."
  echo ""
  echo "        ssh_private_key_pass_env - An alternative to entering the SSH private"
  echo "                          keystore password at the prompt. The value is"
  echo "                          specified in an ENVIRONMENT VARIABLE name that WDT"
  echo "                          will use to retrieve the password."
  echo ""
  echo "        ssh_private_key_pass_file - An alternative to entering the SSH"
  echo "                          private keystore password at the prompt.  The"
  echo "                          value is the name of a file with a string value"
  echo "                          which WDT will read to retrieve the password."
  echo ""
  echo "        ssh_private_key_pass_prompt - Prompt for the SSH private keystore"
  echo "                          password."
  echo ""
  echo "        passphrase_env  - An alternative to entering the model encryption"
  echo "                          passphrase at the prompt. The value is specified"
  echo "                          in an ENVIRONMENT VARIABLE name that WDT will use"
  echo "                          to retrieve the password."
  echo ""
  echo "        passphrase_file - An alternative to entering the model encryption"
  echo "                          passphrase at the prompt.  The value is the"
  echo "                          name of a file with a string value which WDT will"
  echo "                          read to retrieve the password."
  echo ""
  echo "        discover_security_provider_scope - Which providers to discover."
  echo "                          Legal values are ALL, DefaultAuthenticator,"
  echo "                          XACMLAuthorizer, XACMLRoleMapper, and"
  echo "                          DefaultCredentialMapper.  Use a comma to separate"
  echo "                          providers to discover."
  echo ""
  echo "        opss_wallet_passphrase_env - An alternative to entering the OPSS"
  echo "                          wallet passphrase at the prompt.  The value is"
  echo "                          specified in an ENVIRONMENT VARIABLE name that"
  echo "                          WDT will use to retrieve the passphrase."
  echo ""
  echo "        opss_wallet_passphrase_file - An alternative to entering the OPSS"
  echo "                          wallet passphrase at the prompt.  The value is"
  echo "                          the name of a file with a string value which WDT"
  echo "                          will read to retrieve the passphrase."
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
  echo "    file (which the user must construct separately)."
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="discoverDomain"; export WLSDEPLOY_PROGRAM_NAME

scriptName=`basename "$0"`
scriptPath=`dirname "$0"`

. "$scriptPath/shared.sh"

umask 27

checkArgs "$@"

# required Java version and patch level is dependent on use of encryption.
# later versions of JDK 7 support encryption so let WDT figure it out.
minJdkVersion=7
javaSetup $minJdkVersion

runWlst discover.py "$@"
