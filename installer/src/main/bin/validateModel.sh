#!/bin/sh
# *****************************************************************************
# validateModel.sh
#
# Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
# The Universal Permissive License (UPL), Version 1.0
#
#     NAME
#       validateModel.sh - WLS Deploy tool to validate artifacts and print usage
#
#     DESCRIPTION
#       This script validates the model, archive structure and print usage
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
#     - -domain_type        The type of domain to create. This argument is
#                           is optional.  If not specified, it defaults to WLS.
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
  echo "          -oracle_home <oracle-home>"
  echo "          [-print_usage <context> [-attributes_only|-folders_only|-recursive] ]"
  echo "          [-model_file <model-file>]"
  echo "          [-variable_file <variable-file>]"
  echo "          [-archive_file <archive-file>]"
  echo "          [-target_version <target-version>]"
  echo "          [-target_mode <target-mode>]"
  echo "          [-domain_type <domain-type>]"
  echo "          [-wlst_path <wlst-path>]"
  echo ""
  echo "    where:"
  echo "        oracle-home     - the existing Oracle Home directory for the domain"
  echo ""
  echo "        context         - specify the context for printing out the model structure."
  echo "                          By default, the specified folder attributes and subfolder"
  echo "                          names are printed.  Use one of the optional control"
  echo "                          switches to customize the behavior.  Note that the"
  echo "                          control switches are mutually exclusive."
  echo ""
  echo "        model-file      - the location of the model file to use if not using"
  echo "                          the -print_usage functionality.  If not specified,"
  echo "                          the tool will look for the model in the archive."
  echo "                          If the model is not found, validation will only"
  echo "                          validate the artifacts provided."
  echo ""
  echo "        variable-file   - the location of the property file containing"
  echo "                          the variable values for all variables used in"
  echo "                          the model if not using the -print_usage functionality."
  echo "                          If the variable file is not provided, validation will"
  echo "                          only validate the artifacts provided."
  echo ""
  echo "        archive-file    - the path to the archive file to use if not using the"
  echo "                          -print_usage functionality.  If the archive file is"
  echo "                          not provided, validation will only validate the"
  echo "                          artifacts provided."
  echo ""
  echo "        target-version  - the target version of WebLogic Server the tool"
  echo "                          should use to validate the model content.  This"
  echo "                          version number can be different than the version"
  echo "                          being used to run the tool.  If not specified, the"
  echo "                          tool will validate against the version being used"
  echo "                          to run the tool."
  echo ""
  echo "        target-mode     - the target WLST mode that the tool should use to"
  echo "                          validate the model content.  The only valid values"
  echo "                          are online or offline.  If not specified, the tool"
  echo "                          defaults to WLST offline mode."
  echo ""
  echo "        domain-type     - the type of domain (e.g., WLS, JRF)."
  echo "                          Used to locate wlst.cmd if wlst-path not specified"
  echo ""
  echo "        wlst-path       - the Oracle Home subdirectory of the wlst.cmd"
  echo "                          script to use (e.g., ^<ORACLE_HOME^>/soa)"
  echo ""
}

umask 27

WLSDEPLOY_PROGRAM_NAME="validateModel"; export WLSDEPLOY_PROGRAM_NAME

if [ "${WLSDEPLOY_HOME}" = "" ]; then
    BASEDIR="$( cd "$( dirname $0 )" && pwd )"
    WLSDEPLOY_HOME=`cd "${BASEDIR}/.." ; pwd`
    export WLSDEPLOY_HOME
elif [ ! -d ${WLSDEPLOY_HOME} ]; then
    echo "Specified WLSDEPLOY_HOME of ${WLSDEPLOY_HOME} does not exist" >&2
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
        -domain_type)
        DOMAIN_TYPE="$2"
        shift
        ;;
        -wlst_path)
        WLST_PATH_DIR="$2"
        shift
        ;;
        *)
        # unknown option
        ;;
    esac
    shift # past arg or value
done

# default DOMAIN_TYPE

if [ -z "${DOMAIN_TYPE}" ]; then
    DOMAIN_TYPE="WLS"
    SCRIPT_ARGS="${SCRIPT_ARGS} -domain_type $DOMAIN_TYPE"
fi

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

#
# If the WLST_PATH_DIR is specified, validate that it contains the wlst.cmd script
#
if [ "${WLST_PATH_DIR}" != "" ]; then
    if [ ! -d ${WLST_PATH_DIR} ]; then
        echo "WLST_PATH_DIR specified does not exist: ${WLST_PATH_DIR}" >&2
        exit 98
    fi
    WLST=${WLST_PATH_DIR}/common/bin/wlst.sh
    if [ ! -x "${WLST}" ]; then
        echo "WLST executable ${WLST} not found under specified WLST_PATH_DIR: ${WLST_PATH_DIR}" >&2
        exit 98
    fi
    CLASSPATH=${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar; export CLASSPATH
    WLST_EXT_CLASSPATH=${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar; export WLST_EXT_CLASSPATH
else
    WLST=""
    if [ -x ${ORACLE_HOME}/oracle_common/common/bin/wlst.sh ]; then
        WLST=${ORACLE_HOME}/oracle_common/common/bin/wlst.sh
        CLASSPATH=${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar; export CLASSPATH
        WLST_EXT_CLASSPATH=${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar; export WLST_EXT_CLASSPATH
    elif [ -x ${ORACLE_HOME}/wlserver_10.3/common/bin/wlst.sh ]; then
        WLST=${ORACLE_HOME}/wlserver_10.3/common/bin/wlst.sh
        CLASSPATH=${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar; export CLASSPATH
    elif [ -x ${ORACLE_HOME}/wlserver_12.1/common/bin/wlst.sh ]; then
        WLST=${ORACLE_HOME}/wlserver_12.1/common/bin/wlst.sh
        CLASSPATH=${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar; export CLASSPATH
    elif [ -x ${ORACLE_HOME}/wlserver/common/bin/wlst.sh -a -f ${ORACLE_HOME}/wlserver/.product.properties ]; then
        WLST=${ORACLE_HOME}/wlserver/common/bin/wlst.sh
        CLASSPATH=${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar; export CLASSPATH
    fi

    if [ "${WLST}" = "" ]; then
        echo "Unable to determine WLS version in ${ORACLE_HOME} to determine WLST shell script to call" >&2
        exit 98
    fi
fi

LOG_CONFIG_CLASS=oracle.weblogic.deploy.logging.WLSDeployLoggingConfig
WLST_PROPERTIES=-Dcom.oracle.cie.script.throwException=true
WLST_PROPERTIES="-Djava.util.logging.config.class=${LOG_CONFIG_CLASS} ${WLST_PROPERTIES} ${WLSDEPLOY_PROPERTIES}"
export WLST_PROPERTIES

if [ "${WLSDEPLOY_LOG_PROPERTIES}" = "" ]; then
    WLSDEPLOY_LOG_PROPERTIES=${WLSDEPLOY_HOME}/etc/logging.properties; export WLSDEPLOY_LOG_PROPERTIES
fi

if [ "${WLSDEPLOY_LOG_DIRECTORY}" = "" ]; then
    WLSDEPLOY_LOG_DIRECTORY=${WLSDEPLOY_HOME}/logs; export WLSDEPLOY_LOG_DIRECTORY
fi

echo "JAVA_HOME = ${JAVA_HOME}"
echo "WLST_EXT_CLASSPATH = ${WLST_EXT_CLASSPATH}"
echo "CLASSPATH = ${CLASSPATH}"
echo "WLST_PROPERTIES = ${WLST_PROPERTIES}"

PY_SCRIPTS_PATH=${WLSDEPLOY_HOME}/lib/python
echo "${WLST} ${PY_SCRIPTS_PATH}/validate.py ${SCRIPT_ARGS}"

"${WLST}" "${PY_SCRIPTS_PATH}/validate.py" ${SCRIPT_ARGS}

RETURN_CODE=$?
if [ ${RETURN_CODE} -eq 100 ]; then
  usage `basename $0`
  RETURN_CODE=0
elif [ ${RETURN_CODE} -eq 99 ]; then
  usage `basename $0`
  echo ""
  echo "validateModel.sh failed due to the usage error shown above" >&2
elif [ ${RETURN_CODE} -eq 98 ]; then
  echo ""
  echo "validateModel.sh failed due to a parameter validation error" >&2
elif [ ${RETURN_CODE} -eq 2 ]; then
  echo ""
  echo "validateModel.sh failed (exit code = ${RETURN_CODE})" >&2
elif [ ${RETURN_CODE} -eq 1 ]; then
  echo ""
  echo "validateModel.sh completed but with some issues (exit code = ${RETURN_CODE})" >&2
elif [ ${RETURN_CODE} -eq 0 ]; then
  echo ""
  echo "validateModel.sh completed successfully (exit code = ${RETURN_CODE})"
else
  # Unexpected return code so just print the message and exit...
  echo ""
  echo "validateModel.sh failed (exit code = ${RETURN_CODE})" >&2
fi
exit ${RETURN_CODE}
