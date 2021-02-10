#!/bin/sh
# *****************************************************************************
# doVerifyOnline.sh
#
# Copyright (c) 2021, Oracle and/or its affiliates.
# The Universal Permissive License (UPL), Version 1.0
#
#     NAME
#       doVerifyOnline.sh - alias test to verify the domain MBeans and attributes
#                            against WDT alias definitions
#
#     DESCRIPTION
#       This script verifies online mode of a specific version of WebLogic Server alias definitions.
#       It compares the online WebLogic version JSON file created by the generate step against the
#       definitions.
#
#
# This script uses the following command-line arguments directly, the rest
# of the arguments are passed down to the underlying python program:
#
#     - -oracle_home        The directory of the existing Oracle Home to use.
#                           This directory must exist and it is the caller^'s
#                           responsibility to verify that it does. This
#                           argument is required.
#
#     - -testfiles_path     The location where to store the generated files and reports
#                           and where to read the generated files to create the reports.
#  
#     - -admin_url          The URL of the admin server to be used for generating the online 
#                           information for the designated oracle-home (they must match) and
#                           to seed the offline generated files.
#
#     - -admin_user         The userid to connect to the admin server
#           
#     - -admin_pass         The password to connect to the admin server
#                 
#     - -wlst_path          The path to the Oracle Home product directory under
#                           which to find the wlst.cmd script.  This is only
#                           needed for pre-12.2.1 upper stack products like SOA.
#
#                           For example, for SOA 12.1.3, -wlst_path should be
#                           specified as $ORACLE_HOME/soa
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

usage() {
  echo ""
  echo "Usage: $1 [-help]"
  echo "          -oracle_home <oracle-home>"
  echo "          -testfiles_path <testfiles-path>"
  echo "          -admin_url <admin-url>"
  echo "          -admin_user <admin-user>"
  echo "          -admin_pass <admin-pass>" 
  echo "          [-wlst_path <wlst-path>]"
  echo ""
  echo "    where:"
  echo "        oracle-home     - the existing Oracle Home directory for the domain"
  echo ""
  echo "        testfiles-path  - location to store to / read from the generated files and to store the report files"
  echo ""
  echo "        model-file      - the location of the model file to use,"
  echo "                          the default is to get the model from the archive"
  echo ""
  echo "        domain-type     - the type of domain (e.g., WLS, JRF)."
  echo "                          Used to locate wlst.cmd if wlst-path not specified"
  echo ""
  echo "        admin-url       - the system test admin server URL"
  echo ""
  echo "        admin-user      - the system test admin username"
  echo ""
  echo "        admin-pass      - the system test admin password"
  echo ""
  echo "        wlst-path       - the Oracle Home subdirectory of the wlst.cmd"
  echo "                          script to use (e.g., <ORACLE_HOME>/soa)"
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
        -oracle_home)
        ORACLE_HOME="$2"
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
if [ "${ORACLE_HOME}" = "" ]; then
    echo "Required argument ORACLE_HOME not provided" >&2
    usage `basename $0`
    exit 99
elif [ ! -d ${ORACLE_HOME} ]; then
    echo "The specified ORACLE_HOME does not exist: ${ORACLE_HOME}" >&2
    exit 98
fi
if [ "${TESTFILES_LOCATION}" = "" ]; then
    echo "Required argument TESTFILES_LOCATION not provided" >&2
    usage `basename $0`
    exit 99
elif [ ! -d ${TESTFILES_LOCATION} ]; then
    echo "The specified TESTFILES_LOCATION does not exist: ${TESTFILES_LOCATION}" >&2
    exit 98
fi

ORACLE_SERVER_DIR=
if [ -x ${ORACLE_HOME}/wlserver_10.3 ]; then
    ORACLE_SERVER_DIR=${ORACLE_HOME}/wlserver_10.3
elif [ -x ${ORACLE_HOME}/wlserver_12.1 ]; then
    ORACLE_SERVER_DIR=${ORACLE_HOME}/wlserver_12.1
else
    ORACLE_SERVER_DIR=${ORACLE_HOME}/wlserver
fi

variableSetup

JAVA_PROPERTIES="-Djava.util.logging.config.class=${LOG_CONFIG_CLASS}"
JAVA_PROPERTIES="${JAVA_PROPERTIES} -Dpython.cachedir.skip=true"
JAVA_PROPERTIES="${JAVA_PROPERTIES} -Dpython.path=${ORACLE_SERVER_DIR}/common/wlst/modules/jython-modules.jar/Lib"
JAVA_PROPERTIES="${JAVA_PROPERTIES} -Dpython.console="
JAVA_PROPERTIES="${JAVA_PROPERTIES}  ${WLSDEPLOY_PROPERTIES}"
export JAVA_PROPERTIES

CLASSPATH=${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar:${TEST_HOME}/resources;
CLASSPATH=${CLASSPATH}:${ORACLE_SERVER_DIR}/server/lib/weblogic.jar


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
  echo "doVerifyOnline.sh failed due to the usage error shown above" >&2
elif [ ${RETURN_CODE} -eq 98 ]; then
  echo ""
  echo "doVerifyOnline.sh failed due to a parameter validation error" >&2
elif [ ${RETURN_CODE} -eq 2 ]; then
  echo ""
  echo "doVerifyOnline.sh failed (exit code = ${RETURN_CODE})" >&2
elif [ ${RETURN_CODE} -eq 1 ]; then
  echo ""
  echo "doVerifyOnline.sh completed but with some issues (exit code = ${RETURN_CODE})" >&2
elif [ ${RETURN_CODE} -eq 0 ]; then
  echo ""
  echo "doVerifyOnline.sh completed successfully (exit code = ${RETURN_CODE})"
else
  # Unexpected return code so just print the message and exit...
  echo ""
  echo "doVerifyOnline.sh failed (exit code = ${RETURN_CODE})" >&2
fi
exit ${RETURN_CODE}
