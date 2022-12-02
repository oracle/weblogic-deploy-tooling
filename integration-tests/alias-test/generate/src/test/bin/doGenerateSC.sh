#!/usr/bin/env sh
# *****************************************************************************
# doGenerateSC.sh
#
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
# The Universal Permissive License (UPL), Version 1.0
#
#     NAME
#       doGenerateSC.sh - generate a JSON file with Security Configuration Provider types.
#
#     DESCRIPTION
#       This script connects to the admin server and collects the names of the different
#       provider types that are installed by the WLS template. The information is persisted
#       to a file and read in by the generate jobs.
#
#
# This script uses the following command-line arguments directly, the rest
# of the arguments are passed down to the underlying python program:
#
#     - -oracle_home        The location of the Oracle Home version for the generate job.
#     - -output_dir         The location where to store the generated files and reports
#                           and where to read the generated files to create the reports.
#     - -domain_home        The directory where the domain is installed
#     - -admin_user         The WebLogic Server admin username
#     - -admin_pass         The WebLogic Server admin password
#     - -admin_url          The running Admin Server URL
#     - -status_dir         The directory where the successful completion status file will be created.
#
# This script uses the following variables:
#
# JAVA_HOME            - The location of the JDK to use.  The caller must set
#                        this variable to a valid Java 7 (or later) JDK.
#
# TEST_HOME            - The location of the WLS Deploy Alias System Test installation.
#
# WLSDEPLOY_HOME       - The location of the WLS Deploy installation.
#
# WLSDEPLOY_PROPERTIES - Extra system properties to pass to WLST.  The caller
#                        can use this environment variable to add additional
#                        system properties to the WLST environment.
#

scriptPath="$(dirname "$0")"
BASEDIR="$(pwd)"

. "${scriptPath}/helpers.sh"

WLSDEPLOY_PROGRAM_NAME="alias_test_generate_sc"; export WLSDEPLOY_PROGRAM_NAME

if [ "${WLSDEPLOY_HOME}" = "" ]; then
    echo "WLSDEPLOY_HOME environment variable must be set" >&2
    exit 1
fi

if [ ! -d ${TEST_HOME} ]; then
    echo "Specified TEST_HOME of ${TEST_HOME} does not exist"
    exit 1
fi

if [ "${JAVA_HOME}" = "" ]; then
  echo "Please set the JAVA_HOME environment variable to point to a Java installation compatible with the WebLogic version" >&2
  exit 1
fi

#
# Find the args required to determine the WLST script to run
#
ADMIN_URL=$(getT3AdminUrl)
ADMIN_USER=weblogic
ADMIN_PASS=welcome1
OUTPUT_DIR="${BASEDIR}/target"
STATUS_DIR=""

while [ $# -gt 1 ]; do
    key="$1"
    case $key in
        -oracle_home)
          ORACLE_HOME="$2"
          shift
        ;;
        -domain_home)
          DOMAIN_HOME="$2"
          shift
        ;;
        -output_dir)
          OUTPUT_DIR="$2"
          shift
        ;;
        -status_dir)
          STATUS_DIR="$2"
          shift
        ;;
        -admin_user)
          ADMIN_USER="$2"
          shift
        ;;
        -admin_pass)
          ADMIN_PASS="$2"
          shift
        ;;
        -admin_url)
          ADMIN_URL="$2"
          shift
        ;;
        *)
        # unknown option
        ;;
    esac
    shift # past arg or value
done

#
# Check for values of required arguments for this script to continue.
# The underlying WLST script has other required arguments.
#
echo "ORACLE_HOME=${ORACLE_HOME}"
if [ "${ORACLE_HOME}" = "" ]; then
    echo "Required argument -oracle_home not provided" >&2
    exit 1
fi

echo "DOMAIN_HOME=${DOMAIN_HOME}"
if [ "${DOMAIN_HOME}" = "" ]; then
    echo "Required argument -domain_home not provided" >&2
    exit 1
fi

echo "OUTPUT_DIR=${OUTPUT_DIR}"
mkdir -p "${OUTPUT_DIR}"

if [ -z "${STATUS_DIR}" ]; then
  STATUS_DIR="${OUTPUT_DIR}/generate-status"
fi

#
# Remove any existing status directory since this is the first script in the series.
#
rm -rf "${STATUS_DIR}"
mkdir -p "${STATUS_DIR}"

#
# Find WLST
#
WLST=
if [ -f "${ORACLE_HOME}/oracle_common/common/bin/wlst.sh" ]; then
  WLST="${ORACLE_HOME}/oracle_common/common/bin/wlst.sh"
  WLST_EXT_CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar:${TEST_HOME}/resources"; export WLST_EXT_CLASSPATH
  # No need to export CLASSPATH in this case, just putting it here for printing below...
  CLASSPATH="${WLST_EXT_CLASSPATH}"
elif [ -f "${ORACLE_HOME}/wlserver_10.3/common/bin/wlst.sh" ]; then
  WLST="${ORACLE_HOME}/wlserver_10.3/common/bin/wlst.sh"
  CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar:${TEST_HOME}/resources"; export CLASSPATH
elif [ -f "${ORACLE_HOME}/wlserver_12.1/common/bin/wlst.sh" ]; then
  WLST="${ORACLE_HOME}/wlserver_12.1/common/bin/wlst.sh"
  CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar:${TEST_HOME}/resources"; export CLASSPATH
elif [ -f "${ORACLE_HOME}/wlserver/common/bin/wlst.sh" ] && [ -f "${ORACLE_HOME}/wlserver/.product.properties" ]; then
  WLST="${ORACLE_HOME}/wlserver/common/bin/wlst.sh"
  CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar:${TEST_HOME}/resources"; export CLASSPATH
else
  echo "Unable to locate wlst.sh script in ORACLE_HOME ${ORACLE_HOME}" >&2
  exit 1
fi

LOG_CONFIG_CLASS=oracle.weblogic.deploy.logging.WLSDeployLoggingConfig
WLST_PROPERTIES=-Dcom.oracle.cie.script.throwException=true
WLST_PROPERTIES="-Djava.util.logging.config.class=${LOG_CONFIG_CLASS} ${WLST_PROPERTIES}"
WLST_PROPERTIES="${WLST_PROPERTIES} ${WLSDEPLOY_PROPERTIES}"
export WLST_PROPERTIES

if [ "${WLSDEPLOY_LOG_PROPERTIES}" = "" ]; then
    WLSDEPLOY_LOG_PROPERTIES=${WLSDEPLOY_HOME}/etc/logging.properties
fi
export WLSDEPLOY_LOG_PROPERTIES


if [ "${WLSDEPLOY_LOG_DIRECTORY}" = "" ]; then
    WLSDEPLOY_LOG_DIRECTORY=${WLSDEPLOY_HOME}/logs; export WLSDEPLOY_LOG_DIRECTORY
fi

echo "JAVA_HOME = ${JAVA_HOME}"
echo "CLASSPATH = ${CLASSPATH}"
echo "JAVA_PROPERTIES = ${JAVA_PROPERTIES}"

PY_SCRIPTS_PATH=${TEST_HOME}/python

echo "${WLST} ${PY_SCRIPTS_PATH}/generate_sc.py \
    -oracle_home ${ORACLE_HOME} \
    -domain_home ${DOMAIN_HOME} \
    -output_dir ${OUTPUT_DIR} \
    -admin_user ${ADMIN_USER} \
    -admin_pass ${ADMIN_PASS} \
    -admin_url ${ADMIN_URL}"
"${WLST}" "${PY_SCRIPTS_PATH}/generate_sc.py" \
    -oracle_home "${ORACLE_HOME}" \
    -domain_home "${DOMAIN_HOME}" \
    -output_dir "${OUTPUT_DIR}" \
    -admin_user "${ADMIN_USER}" \
    -admin_pass "${ADMIN_PASS}" \
    -admin_url "${ADMIN_URL}"

RETURN_CODE=$?
if [ "${RETURN_CODE}" = "0" ]; then
  echo "doGenerateSC.sh completed successfully"
  touch "${STATUS_DIR}/doGenerateSC"
else
  echo "doGenerateSC.sh failed (exit code = ${RETURN_CODE})"
fi
exit ${RETURN_CODE}
