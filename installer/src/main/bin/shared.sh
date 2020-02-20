#!/bin/sh
# *****************************************************************************
# shared.sh
#
# Copyright (c) 2020, Oracle Corporation and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       shared.cmd - shared script for use with WebLogic Deploy Tooling.
#
#     DESCRIPTION
#       This script contains shared functions for use with WDT scripts.
#

javaSetup() {
    # Make sure that the JAVA_HOME environment variable is set to point to a
    # JDK with the specified level or higher (and that it isn't OpenJDK).
    # read: JAVA_HOME

    minJdkVersion=$1

    if [ -z "${JAVA_HOME}" ]; then
      echo "Please set the JAVA_HOME environment variable to point to a Java $minJdkVersion installation" >&2
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

    JVM_FULL_VERSION=`${JAVA_EXE} -fullversion 2>&1 | awk -F"\"" '{ print $2 }'`
    # set JVM version to the major version, unless equal to 1, like 1.8.0, then use the minor version
    JVM_VERSION=`echo ${JVM_FULL_VERSION} | awk -F"." '{ print $1 }'`

    if [ "${JVM_VERSION}" -eq "1" ]; then
      JVM_VERSION=`echo ${JVM_FULL_VERSION} | awk -F"." '{ print $2 }'`
    fi

    if [ ${JVM_VERSION} -lt $minJdkVersion ]; then
      echo "You are using an unsupported JDK version ${JVM_FULL_VERSION}" >&2
      exit 2
    else
      echo "JDK version is ${JVM_FULL_VERSION}"
    fi
}

checkJythonArgs() {
    # verify that required arg -oracle_home is set.

    # if no args were given and print the usage message
    if [ "$#" -eq "0" ]; then
      usage `basename $0`
      exit 0
    fi

    # check for -help and -oracle_home
    while [ "$#" -gt "1" ]; do
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
    if [ -z "${ORACLE_HOME}" ]; then
        echo "Required argument -oracle_home not provided" >&2
        usage `basename $0`
        exit 99
    elif [ ! -d ${ORACLE_HOME} ]; then
        echo "The specified -oracle_home directory does not exist: ${ORACLE_HOME}" >&2
        exit 98
    fi
}

loggerSetup() {
    # set up variables for logger configuration. see WLSDeployLoggingConfig.java

    LOG_CONFIG_CLASS=oracle.weblogic.deploy.logging.WLSDeployCustomizeLoggingConfig
    WLSDEPLOY_LOG_HANDLER=oracle.weblogic.deploy.logging.SummaryHandler

    if [ -z "${WLSDEPLOY_LOG_PROPERTIES}" ]; then
        WLSDEPLOY_LOG_PROPERTIES=${WLSDEPLOY_HOME}/etc/logging.properties; export WLSDEPLOY_LOG_PROPERTIES
    fi

    if [ -z "${WLSDEPLOY_LOG_DIRECTORY}" ]; then
        WLSDEPLOY_LOG_DIRECTORY=${WLSDEPLOY_HOME}/logs; export WLSDEPLOY_LOG_DIRECTORY
    fi

    if [ -z "${WLSDEPLOY_LOG_HANDLERS}" ]; then
        WLSDEPLOY_LOG_HANDLERS=${WLSDEPLOY_LOG_HANDLER}; export WLSDEPLOY_LOG_HANDLERS
    fi
}

wlsDeployHomeSetup() {
    # set the WLSDEPLOY_HOME variable. if it was already set, verify that it is valid

    if [ -z "${WLSDEPLOY_HOME}" ]; then
        BASEDIR="$( cd "$( dirname $0 )" && pwd )"
        WLSDEPLOY_HOME=`cd "${BASEDIR}/.." ; pwd`
        export WLSDEPLOY_HOME
    elif [ ! -d ${WLSDEPLOY_HOME} ]; then
        echo "Specified WLSDEPLOY_HOME of ${WLSDEPLOY_HOME} does not exist" >&2
        exit 2
    fi
}

runJython() {
    # run a jython script, without WLST.
    jythonScript=$1

    # set up Oracle directory, logger, classpath

    ORACLE_SERVER_DIR=
    if [ -x ${ORACLE_HOME}/wlserver_10.3 ]; then
        ORACLE_SERVER_DIR=${ORACLE_HOME}/wlserver_10.3
    elif [ -x ${ORACLE_HOME}/wlserver_12.1 ]; then
        ORACLE_SERVER_DIR=${ORACLE_HOME}/wlserver_12.1
    else
        ORACLE_SERVER_DIR=${ORACLE_HOME}/wlserver
    fi

    wlsDeployHomeSetup
    loggerSetup

    JAVA_PROPERTIES="-Djava.util.logging.config.class=${LOG_CONFIG_CLASS}"
    JAVA_PROPERTIES="${JAVA_PROPERTIES} -Dpython.cachedir.skip=true"
    JAVA_PROPERTIES="${JAVA_PROPERTIES} -Dpython.path=${ORACLE_SERVER_DIR}/common/wlst/modules/jython-modules.jar/Lib"
    JAVA_PROPERTIES="${JAVA_PROPERTIES} -Dpython.console="
    JAVA_PROPERTIES="${JAVA_PROPERTIES}  ${WLSDEPLOY_PROPERTIES}"
    export JAVA_PROPERTIES

    CLASSPATH=${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar
    CLASSPATH=${CLASSPATH}:${ORACLE_SERVER_DIR}/server/lib/weblogic.jar

    # print the configuration, and run the script

    echo "JAVA_HOME = ${JAVA_HOME}"
    echo "CLASSPATH = ${CLASSPATH}"
    echo "JAVA_PROPERTIES = ${JAVA_PROPERTIES}"

    PY_SCRIPTS_PATH=${WLSDEPLOY_HOME}/lib/python

    echo \
    ${JAVA_HOME}/bin/java -cp ${CLASSPATH} \
        ${JAVA_PROPERTIES} \
        org.python.util.jython \
        "${PY_SCRIPTS_PATH}/$jythonScript" ${scriptArgs}

    ${JAVA_HOME}/bin/java -cp ${CLASSPATH} \
        ${JAVA_PROPERTIES} \
        org.python.util.jython \
        "${PY_SCRIPTS_PATH}/$jythonScript" ${scriptArgs}

    RETURN_CODE=$?
    checkExitCode ${RETURN_CODE}
    exit ${RETURN_CODE}
}

checkExitCode() {
    # print a message for the exit code passed in.
    # assume that SCRIPT_NAME environment variable was set by the caller.
    returnCode=$1

    if [ $returnCode -eq 103 ]; then
      echo ""
      echo "$scriptName completed successfully but the domain requires a restart for the changes to take effect (exit code = ${RETURN_CODE})"
    elif [ $returnCode -eq 102 ]; then
      echo ""
      echo "$scriptName completed successfully but the affected servers require a restart (exit code = ${RETURN_CODE})"
    elif [ $returnCode -eq 101 ]; then
      echo ""
      echo "$scriptName was unable to complete due to configuration changes that require a domain restart.  Please restart the domain and re-invoke the $scriptName script with the same arguments (exit code = ${RETURN_CODE})"
    elif [ $returnCode -eq 100 ]; then
      usage `basename $0`
    elif [ $returnCode -eq 99 ]; then
      usage `basename $0`
      echo ""
      echo "$scriptName failed due to the usage error shown above" >&2
    elif [ $returnCode -eq 98 ]; then
      echo ""
      echo "$scriptName failed due to a parameter validation error" >&2
    elif [ $returnCode -eq 2 ]; then
      echo ""
      echo "$scriptName failed (exit code = $returnCode)" >&2
    elif [ $returnCode -eq 1 ]; then
      echo ""
      echo "$scriptName completed but with some issues (exit code = $returnCode)" >&2
    elif [ $returnCode -eq 0 ]; then
      echo ""
      echo "$scriptName completed successfully (exit code = $returnCode)"
    else
      # Unexpected return code so just print the message and exit...
      echo ""
      echo "$scriptName failed (exit code = $returnCode)" >&2
    fi
}
