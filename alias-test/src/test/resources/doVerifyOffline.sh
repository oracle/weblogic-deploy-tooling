#!/bin/sh
# *****************************************************************************
# doVerifyOffline.sh
#
# Copyright (c) 2021, Oracle and/or its affiliates.
# The Universal Permissive License (UPL), Version 1.0
#
#     NAME
#       doVerifyOffline.sh - alias test to verify the domain MBeans and attributes
#                            against WDT alias definitions
#
#     DESCRIPTION
#       This script verifies offline mode of a specific version of WebLogic Server alias definitions.
#       It compares the offline WebLogic version JSON file created by the generate step against the
#       definitions.
#
#
# This script uses the following command-line arguments directly, the rest
# of the arguments are passed down to the underlying python program:
#
#     - -testfiles_path     The location where to store the generated files and reports
#                           and where to read the generated files to create the reports.
#     - -wls_version        The version of WebLogic formatted such as 12.2.1.4.0
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
# PYTHON_HOME          - The location of the 2.7.0 or 2.7.2 jython jar that this tool will run with

usage() {
  echo ""
  echo "Usage: $1 [-help]"
  echo "          -testfiles_path <testfiles-path>"
  echo "          -wls_version <wls-version>"
  echo ""
  echo "    where:"
  echo "        testfiles-path  - location to store to / read from the generated files and to store the report files"
  echo ""
  echo "        wls-version     - the version of WebLogic Server to be verified formatted such as 12.2.1.4.0,"
  echo ""
}
scriptName=`basename $0`
scriptPath=$(dirname "$0")
scriptArgs=$*
umask 27

WLSDEPLOY_PROGRAM_NAME="aliases_tests"; export WLSDEPLOY_PROGRAM_NAME

if [ "${WLSDEPLOY_HOME}" = "" ]; then
    echo "WLSDEPLOY_HOME environment variable must be set" >&2
    exit 2
elif [ ! -d ${WLSDEPLOY_HOME} ]; then
    echo "Specified WLSDEPLOY_HOME of ${WLSDEPLOY_HOME} does not exist" >&2
    exit 2
fi

if [ "${TEST_HOME}" = "" ]; then
    SET TEST_HOME=${WLSDEPLOY_HOME}/test
    export TEST_HOME
if [ ! -d ${TEST_HOME} ]; then
    echo "Specified TEST_HOME of ${TEST_HOME} does not exist" >&2
    exit 2
fi

if [ "${PYTHON_HOME}" = "" ]; then
    SET PYTHON_HOME=${WLSDEPLOY_HOME}/test
    export PYTHON_HOME
if [ ! -d ${PYTHON_HOME} ]; then
    echo "Specified PYTHON_HOME of ${PYTHON_HOME} does not exist" >&2
    exit 2
fi

#
# Make sure that the JAVA_HOME environment variable is set to point to a
# JDK 7 or higher JVM (and that it isn't OpenJDK).
#
if [ "${JAVA_HOME}" = "" ]; then
  echo "Please set the JAVA_HOME environment variable to point to a Java 7 installation" >&2
  exit 2
elif [ ! -d "${JAVA_HOME}" ]; then
  echo "Your JAVA_HOME environment variable to points to a non-existent directory: ${JAVA_HOME}" >&2
  exit 2
fi

if [ -x "${JAVA_HOME}/bin/java" ]; then
  JAVA_EXE=${JAVA_HOME}/bin/java
else
  echo "Java executable at ${JAVA_HOME}/bin/java either does not exist or is not executable" >&2
  exit 2
fi

JVM_OUTPUT=`${JAVA_EXE} -version 2>&1`
case "${JVM_OUTPUT}" in
  *OpenJDK*)
    echo "JAVA_HOME ${JAVA_HOME} contains OpenJDK, which is not supported" >&2
    exit 2
    ;;
esac

JVM_FULL_VERSION=`${JAVA_EXE} -fullversion 2>&1 | awk -F "\"" '{ print $2 }'`
JVM_VERSION=`echo ${JVM_FULL_VERSION} | awk -F "." '{ print $2 }'`

if [ ${JVM_VERSION} -lt 7 ]; then
  echo "You are using an unsupported JDK version ${JVM_FULL_VERSION}" >&2
  exit 2
else
  echo "JDK version is ${JVM_FULL_VERSION}"
fi

#
# Check to see if no args were given and print the usage message
#
if [[ $# = 0 ]]; then
  usage `basename $0`
  exit 0
fi

SCRIPT_ARGS="$*"

#
# Find the args required to determine the WLST script to run
#
while [[ $# > 1 ]]; do
    key="$1"
    case $key in
        -help)
        usage `basename $0`
        exit 0
        ;;
        -wls_version)
        WLS_VERSION="$2"
        shift
        ;;
        -testfiles_path)
        TESTFILES_LOCATION="$2"
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

if [ "${WLS_VERSION}" = "" ]; then
    echo "Required argument WLS_VERSION not provided" >&2
    usage `basename $0`
    exit 99

if [ "${TESTFILES_LOCATION}" = "" ]; then
    echo "Required argument TESTFILES_LOCATION not provided" >&2
    usage `basename $0`
    exit 99
elif [ ! -d ${TESTFILES_LOCATION} ]; then
    echo "The specified TESTFILES_LOCATION does not exist: ${TESTFILES_LOCATION}" >&2
    exit 98
fi

variableSetup

JAVA_PROPERTIES="-Djava.util.logging.config.class=${LOG_CONFIG_CLASS}"
JAVA_PROPERTIES="${JAVA_PROPERTIES} -Dpython.cachedir.skip=true"
JAVA_PROPERTIES="${JAVA_PROPERTIES} -Dpython.path=${PYTHON_HOME}/Lib"
JAVA_PROPERTIES="${JAVA_PROPERTIES} -Dpython.console="
JAVA_PROPERTIES="${JAVA_PROPERTIES}  ${WLSDEPLOY_PROPERTIES}"
export JAVA_PROPERTIES

CLASSPATH=${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar:${TEST_HOME}/resources;${PYTHON_HOME}/jython.jar


LOG_CONFIG_CLASS=oracle.weblogic.deploy.logging.WLSDeployLoggingConfig

if [ "${WLSDEPLOY_LOG_PROPERTIES}" = "" ]; then
    WLSDEPLOY_LOG_PROPERTIES=${WLSDEPLOY_HOME}/etc/logging.properties; export WLSDEPLOY_LOG_PROPERTIES
fi

if [ "${WLSDEPLOY_LOG_DIRECTORY}" = "" ]; then
    WLSDEPLOY_LOG_DIRECTORY=${WLSDEPLOY_HOME}/logs; export WLSDEPLOY_LOG_DIRECTORY
fi

echo "JAVA_HOME = ${JAVA_HOME}"
echo "CLASSPATH = ${CLASSPATH}"
echo "JAVA_PROPERTIES = ${JAVA_PROPERTIES}"

PY_SCRIPTS_PATH=${WLSDEPLOY_HOME}/lib/python

echo \
${JAVA_HOME}/bin/java -cp ${CLASSPATH} \
    ${JAVA_PROPERTIES} \
    org.python.util.jython \
    "${PY_SCRIPTS_PATH}/verify_offline.py" ${scriptArgs}

${JAVA_HOME}/bin/java -cp ${CLASSPATH} \
    ${JAVA_PROPERTIES} \
    org.python.util.jython \
    "${PY_SCRIPTS_PATH}/verify_offline.py" ${scriptArgs}

RETURN_CODE=$?
if [ ${RETURN_CODE} -eq 100 ]; then
  usage `basename $0`
  RETURN_CODE=0
elif [ ${RETURN_CODE} -eq 99 ]; then
  usage `basename $0`
  echo ""
  echo "doVerifyOffline.sh failed due to the usage error shown above" >&2
elif [ ${RETURN_CODE} -eq 98 ]; then
  echo ""
  echo "doVerifyOffline.sh failed due to a parameter validation error" >&2
elif [ ${RETURN_CODE} -eq 2 ]; then
  echo ""
  echo "doVerifyOffline.sh failed (exit code = ${RETURN_CODE})" >&2
elif [ ${RETURN_CODE} -eq 1 ]; then
  echo ""
  echo "doVerifyOffline.sh completed but with some issues (exit code = ${RETURN_CODE})" >&2
elif [ ${RETURN_CODE} -eq 0 ]; then
  echo ""
  echo "doVerifyOffline.sh completed successfully (exit code = ${RETURN_CODE})"
else
  # Unexpected return code so just print the message and exit...
  echo ""
  echo "doVerifyOffline.sh failed (exit code = ${RETURN_CODE})" >&2
fi
exit ${RETURN_CODE}
