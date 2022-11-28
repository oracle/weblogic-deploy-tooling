#!/bin/sh
# *****************************************************************************
# doVerifyOnline.sh
#
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
# The Universal Permissive License (UPL), Version 1.0
#
#     NAME
#       doVerifyOnline.sh - alias test to verify the domain MBeans and attributes
#                           against WDT alias definitions
#
#     DESCRIPTION
#       This script verifies online mode of a specific version of WebLogic Server
#       alias definitions.  It compares the online WebLogic version JSON file
#       created by the generate step against the definitions.
#
#
# This script uses the following command-line arguments directly, the rest
# of the arguments are passed down to the underlying python program:
#
#     - -generated_dir      The location where to find the generated files.
#     - -output_dir         The location where to place the output report.
#     - -wls_version        The version of WebLogic formatted such as 12.2.1.4.0.210930
#     - -status_dir         The directory where the successful completion status file will be created.
#
# This script uses the following variables:
#
# JAVA_HOME            - The location of the JDK to use.  The caller must set
#                        this variable to a valid Java 7 (or later) JDK.
#
# WLSDEPLOY_HOME       - The location of the WLS Deploy installation.
#
#
# TEST_HOME            - The location of the WLS Deploy Alias System Test installation.
#
scriptPath=$(dirname "$0")
BASEDIR=$(pwd)

. "${scriptPath}/helpers.sh"

WLSDEPLOY_PROGRAM_NAME="alias_test_verify_online"; export WLSDEPLOY_PROGRAM_NAME

if [ "${WLSDEPLOY_HOME}" = "" ]; then
    echo "WLSDEPLOY_HOME environment variable must be set" >&2
    exit 1
elif [ ! -d "${WLSDEPLOY_HOME}" ]; then
    echo "Specified WLSDEPLOY_HOME of ${WLSDEPLOY_HOME} does not exist" >&2
    exit 1
fi

if [ ! -d "${TEST_HOME}" ]; then
    echo "Specified TEST_HOME of ${TEST_HOME} does not exist"
    exit 1
fi

if [ -z "${JAVA_HOME}" ]; then
  echo "Please set the JAVA_HOME environment variable to point to a Java installation" >&2
  exit 1
fi

#
# Find the args required to determine the WLST script to run
#
WLS_VERSION=""
OUTPUT_DIR="${BASEDIR}/target"
GENERATED_DIR="${BASEDIR}/target"
STATUS_DIR=""
while [ $# -gt 1 ]; do
    key="$1"
    case $key in
        -wls_version)
            WLS_VERSION="$2"
            shift
        ;;
        -output_dir)
            OUTPUT_DIR="$2"
            shift
        ;;
        -generated_dir)
            GENERATED_DIR="$2"
            shift
        ;;
        -status_dir)
          STATUS_DIR="$2"
          shift
        ;;
        *)
        # unknown option
        ;;
    esac
    shift # past arg or value
done

if [ -z "${WLS_VERSION}" ]; then
    echo "Required argument -wls_version not provided"
    exit 1
else
    echo "WLS_VERSION=${WLS_VERSION}"
fi

echo "OUTPUT_DIR=${OUTPUT_DIR}"
if [ ! -d "${OUTPUT_DIR}" ]; then
    echo "The specified -output_dir ${OUTPUT_DIR} does not exist" >&2
    exit 1
fi

if [ -z "${STATUS_DIR}" ]; then
  STATUS_DIR="${OUTPUT_DIR}/verify-status"
fi

#
# Remove any existing status directory since this is the first script in the series.
#
rm -rf "${STATUS_DIR}"
mkdir -p "${STATUS_DIR}"

expected_file_name="${GENERATED_DIR}/$(getOnlineGeneratedFileName "${WLS_VERSION}")"
if [ ! -f  "${expected_file_name}" ]; then
    echo "Expected generated file for WLS version ${WLS_VERSION} does not exist: ${expected_file_name}" >&2
    exit 1
fi

LOG_CONFIG_CLASS=oracle.weblogic.deploy.logging.WLSDeployLoggingConfig
JAVA_PROPERTIES="-Djava.util.logging.config.class=${LOG_CONFIG_CLASS}"
JAVA_PROPERTIES="${JAVA_PROPERTIES} -Dpython.cachedir.skip=true"
JAVA_PROPERTIES="${JAVA_PROPERTIES} -Dpython.console="
JAVA_PROPERTIES="${JAVA_PROPERTIES}  ${WLSDEPLOY_PROPERTIES}"
export JAVA_PROPERTIES

CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar:${TEST_HOME}/resources:${BASEDIR}/target/jython-standalone.jar"

if [ -z "${WLSDEPLOY_LOG_PROPERTIES}" ]; then
    WLSDEPLOY_LOG_PROPERTIES="${WLSDEPLOY_HOME}/etc/logging.properties"
fi
export WLSDEPLOY_LOG_PROPERTIES

if [ -z "${WLSDEPLOY_LOG_DIRECTORY}" ]; then
    WLSDEPLOY_LOG_DIRECTORY="${WLSDEPLOY_HOME}/logs"
    export WLSDEPLOY_LOG_DIRECTORY
fi

export WLSDEPLOY_USE_UNICODE=false

echo "JAVA_HOME = ${JAVA_HOME}"
echo "CLASSPATH = ${CLASSPATH}"
echo "JAVA_PROPERTIES = ${JAVA_PROPERTIES}"

PY_SCRIPTS_PATH="${TEST_HOME}/python"

echo "${JAVA_HOME}/bin/java -cp ${CLASSPATH} ${JAVA_PROPERTIES} \
    org.python.util.jython ${PY_SCRIPTS_PATH}/verify_online.py \
    -wls_version ${WLS_VERSION} \
    -generated_dir ${GENERATED_DIR} \
    -output_dir ${OUTPUT_DIR}"

"${JAVA_HOME}/bin/java" -cp "${CLASSPATH}" ${JAVA_PROPERTIES} \
    org.python.util.jython "${PY_SCRIPTS_PATH}/verify_online.py" \
    -wls_version "${WLS_VERSION}" \
    -generated_dir "${GENERATED_DIR}" \
    -output_dir "${OUTPUT_DIR}"

RETURN_CODE=$?
if [ "${RETURN_CODE}" = "0" ]; then
  echo "doVerifyOnline.sh completed successfully"
  touch "${STATUS_DIR}/doVerifyOnline"
else
  echo "doVerifyOnline.sh failed (exit code = ${RETURN_CODE})"
fi

exit ${RETURN_CODE}
