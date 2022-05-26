#!/bin/sh
# *****************************************************************************
# discoverDomain.sh
#
# Copyright (c) 2017, 2021, Oracle Corporation and/or its affiliates.  All rights reserved.
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
# WLSDEPLOY_HOME        - The location of the WLS Deploy installation.
#                         If the caller sets this, the callers location will be
#                         honored provided it is an existing directory.
#                         Otherwise, the location will be calculated from the
#                         location of this script.
#
# WLSDEPLOY_PROPERTIES  - Extra system properties to pass to WLST.  The caller
#                         can use this environment variable to add additional
#                         system properties to the WLST environment.
#

usage() {
  echo ""
  echo "Usage: $1 [-help]"
  echo "          [-oracle_home <oracle_home>]"
  echo "          -domain_home <domain_home>"
  echo "          [-archive_file <archive_file>]"
  echo "          [-skip_archive]"
  echo "          [-model_file <model_file>]"
  echo "          [-variable_file <variable_file>]"
  echo "          [-domain_type <domain_type>]"
  echo "          [-admin_pass_env <admin_pass_env>]"
  echo "          [-admin_pass_file <admin_pass_file>]"
  echo "          [-wlst_path <wlst_path>]"
  echo "          [-java_home <java_home>]"
  echo "          [-target <target>"
  echo "           -output_dir <output_dir>"
  echo "          ]"
  echo "          [-admin_url <admin_url>"
  echo "           -admin_user <admin_user>"
  echo "          ]"
  echo ""
  echo "    where:"
  echo "        oracle_home     - the existing Oracle Home directory for the domain."
  echo "                          This is required unless the ORACLE_HOME environment"
  echo "                          variable is set."
  echo ""
  echo "        domain_home     - the domain home directory"
  echo ""
  echo "        archive_file    - the path to the archive file to use"
  echo ""
  echo "        skip_archive    - Do not generate the archive file. The archive file command will be ignored"
  echo "                          The file references in the model will be the local domain file names"
  echo ""
  echo "        remote          - Discover the remote domain. Do not generate an archive file. However, The file "
  echo "                          references in the model are structured as if they are in an archive. A list of these files "
  echo "                          will be generated."
  echo ""
  echo "        model_file      - the location of the model file to use; "
  echo "                          the default is to get the model from the archive"
  echo ""
  echo "        variable_file   - the location of the variable file to write "
  echo "                          properties by the variable injector. If this "
  echo "                          argument is used, by default all the credentials "
  echo "                          in the discovered model will be replaced by a token "
  echo "                          and a property written to this file"
  echo ""
  echo "        domain_type     - the type of domain (e.g., WLS, JRF)."
  echo "                          Used to locate wlst.cmd if -wlst_path not specified"
  echo ""
  echo "        admin_pass_file  - An alternative to entering the admin passphrase at a prompt. The value "
  echo "                          ENVIRONMENT VARIABLE name that WDT will use to retrieve the passphrase. "
  echo ""
  echo "        admin_pass_env  - An alternative to entering the admin passphrase at a prompt. The value "
  echo "                          ENVIRONMENT VARIABLE name that WDT will use to retrieve the passphrase. "
  echo ""
  echo "        wlst_path       - the Oracle Home subdirectory of the wlst.cmd"
  echo "                          script to use (e.g., <ORACLE_HOME>/soa)"
  echo ""
  echo "        java_home       - overrides the JAVA_HOME value when discovering"
  echo "                          domain values to be replaced with the java home global token"
  echo ""
  echo "        target          - targeting platform (k8s, etc.)"
  echo ""
  echo "        output_dir      - output directory for -target <target>"
  echo ""
  echo "        admin_url       - the admin server URL (used for online deploy)"
  echo ""
  echo "        admin_user      - the admin username (used for online deploy)"
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="discoverDomain"; export WLSDEPLOY_PROGRAM_NAME

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

runWlst discover.py "$@"
