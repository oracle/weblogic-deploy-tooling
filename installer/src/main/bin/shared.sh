#!/bin/sh
# *****************************************************************************
# shared.sh
#
# Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
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

    minJdkVersion=$1

    if [ -z "${JAVA_HOME}" ]; then
      echo "Please set the JAVA_HOME environment variable to point to a Java $minJdkVersion (or higher) installation" >&2
      exit 2
    elif [ ! -d "${JAVA_HOME}" ]; then
      echo "Your JAVA_HOME environment variable to points to a non-existent directory: ${JAVA_HOME}" >&2
      exit 2
    fi

    if [ -x "${JAVA_HOME}/bin/java" ]; then
      JAVA_EXE="${JAVA_HOME}/bin/java"
    else
      echo "Java executable at ${JAVA_HOME}/bin/java either does not exist or is not executable" >&2
      exit 2
    fi

    JVM_OUTPUT=`"${JAVA_EXE}" -version 2>&1`

    case "${JVM_OUTPUT}" in
      *GraalVM*)
        setOracleVersion
        if [ -z "${ORACLE_VERSION}" ] || [ ${ORACLE_VER_ONE} -lt 14 ] || [ ${ORACLE_VER_ONE} -eq 14 ] && [ ${ORACLE_VER_THREE} -lt 2 ]; then
          echo "JAVA_HOME ${JAVA_HOME} contains GraalVM OpenJDK, which is not supported before 14.1.2" >&2
          exit 2
        fi
        ;;
      *OpenJDK*)
        echo "JAVA_HOME ${JAVA_HOME} contains OpenJDK, which is not supported" >&2
        exit 2
        ;;

    esac


    JVM_FULL_VERSION=`"${JAVA_EXE}" -fullversion 2>&1 | awk -F"\"" '{ print $2 }'`

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

setOracleVersion() {
  ORACLE_VERSION=`"${JAVA_HOME}/bin/java" -cp "$ORACLE_HOME/wlserver/server/lib/weblogic.jar" weblogic.version | grep "WebLogic Server" | cut -d " " -f3 2>&1`
  ORACLE_VER_ONE=`echo ${ORACLE_VERSION} | cut -d "." -f1`
  ORACLE_VER_THREE=`echo ${ORACLE_VERSION} | cut -d "." -f3`
  echo ORACLE_VERSION=$ORACLE_VERSION
}

checkArgs() {
    checkJythonArgs $*
}

checkJythonArgs() {
    # verify that ORACLE_HOME is set, or -oracle_home is provided.
    # if -help is provided, display usage.
    # if -use_encryption is provided, set USE_ENCRYPTION to true
    # if -wlst_path is provided, set WLST_PATH_DIR
    # the calling script must have a usage() method.

    # if no args were given and print the usage message
    if [ "$#" -eq "0" ]; then
      usage `basename "$0"`
      exit 0
    fi

    ORACLE_HOME_ARG=""

    # check for -help and -oracle_home
    while [ "$#" -gt "0" ]; do
        key="$1"
        case $key in
            -help)
            usage `basename "$0"`
            exit 0
            ;;
            -oracle_home)
            ORACLE_HOME_ARG="$2"
            shift
            ;;
            -wlst_path)
            WLST_PATH_DIR="$2"
            shift
            ;;
            -use_encryption)
            USE_ENCRYPTION="true"
            ;;
            *)
            # unknown option
            ;;
        esac
        shift # past arg or value
    done

    if [ -n "${ORACLE_HOME_ARG}" ]; then
        ORACLE_HOME="${ORACLE_HOME_ARG}"
    elif [ -n "${ORACLE_HOME}" ]; then
        # if -oracle_home argument was not found, but ORACLE_HOME was set in environment,
        # add the -oracle_home argument with the environment value.
        # put it at the beginning to protect trailing arguments.
	      OHARG="-oracle_home "
	      OHARG_VALUE="${ORACLE_HOME}"
    fi

    #
    # Check for values of required arguments for this script to continue.
    # The underlying WLST script has other required arguments.
    #
    if [ -z "${ORACLE_HOME}" ]; then
        echo "-oracle_home not provided, and ORACLE_HOME not set" >&2
        usage `basename "$0"`
        exit 99
    elif [ ! -d "${ORACLE_HOME}" ]; then
        echo "The specified Oracle home directory does not exist: ${ORACLE_HOME}" >&2
        exit 98
    fi
}

variableSetup() {
    # set up variables for WLST or Jython execution

    # set the WLSDEPLOY_HOME variable. if it was already set, verify that it is valid

    if [ -z "${WLSDEPLOY_HOME}" ]; then
        BASEDIR="$( cd "$( dirname "$0" )" && pwd )"
        WLSDEPLOY_HOME=`cd "${BASEDIR}/.." ; pwd`
        export WLSDEPLOY_HOME
    elif [ ! -d "${WLSDEPLOY_HOME}" ]; then
        echo "Specified WLSDEPLOY_HOME of ${WLSDEPLOY_HOME} does not exist" >&2
        exit 2
    fi

    # set up logger configuration, see WLSDeployLoggingConfig.java

    LOG_CONFIG_CLASS=oracle.weblogic.deploy.logging.WLSDeployLoggingConfig

    if [ -z "${WLSDEPLOY_LOG_PROPERTIES}" ]; then
        WLSDEPLOY_LOG_PROPERTIES="${WLSDEPLOY_HOME}/etc/logging.properties"; export WLSDEPLOY_LOG_PROPERTIES
    fi

    if [ -z "${WLSDEPLOY_LOG_DIRECTORY}" ]; then
        WLSDEPLOY_LOG_DIRECTORY="${WLSDEPLOY_HOME}/logs"; export WLSDEPLOY_LOG_DIRECTORY
    fi
}

runWlst() {
    # run a WLST script.
    wlstScript=$1
    # save first argument in wlstScript, and discard argument from $@
    shift

    variableSetup

    # set WLST variable to the WLST executable.
    # set CLASSPATH and WLST_CLASSPATH to include the WDT core JAR file.
    # if the WLST_PATH_DIR was set, verify and use that value.

    if [ -n "${WLST_PATH_DIR}" ]; then
        if [ ! -d "${WLST_PATH_DIR}" ]; then
            echo "Specified -wlst_path directory does not exist: ${WLST_PATH_DIR}" >&2
            exit 98
        fi
        WLST="${WLST_PATH_DIR}/common/bin/wlst.sh"
        if [ ! -x "${WLST}" ]; then
            echo "WLST executable ${WLST} not found under -wlst_path directory: ${WLST_PATH_DIR}" >&2
            exit 98
        fi
        CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar"; export CLASSPATH
        if [ ! -z "${WLST_EXT_CLASSPATH}" ]; then
          WLST_EXT_CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar:${WLST_EXT_CLASSPATH}"; export WLST_EXT_CLASSPATH
        else
          WLST_EXT_CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar"; export WLST_EXT_CLASSPATH
        fi
    else
        # if WLST_PATH_DIR was not set, find the WLST executable in one of the known ORACLE_HOME locations.

        WLST=""
        if [ -x "${ORACLE_HOME}/oracle_common/common/bin/wlst.sh" ]; then
            WLST="${ORACLE_HOME}/oracle_common/common/bin/wlst.sh"
            CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar"; export CLASSPATH
          if [ ! -z "${WLST_EXT_CLASSPATH}" ]; then
            WLST_EXT_CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar:${WLST_EXT_CLASSPATH}"
            export WLST_EXT_CLASSPATH
          else
            WLST_EXT_CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar"; export WLST_EXT_CLASSPATH
          fi
        elif [ -x "${ORACLE_HOME}/wlserver_10.3/common/bin/wlst.sh" ]; then
            WLST="${ORACLE_HOME}/wlserver_10.3/common/bin/wlst.sh"
            CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar"; export CLASSPATH
        elif [ -x "${ORACLE_HOME}/wlserver_12.1/common/bin/wlst.sh" ]; then
            WLST="${ORACLE_HOME}/wlserver_12.1/common/bin/wlst.sh"
            CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar"; export CLASSPATH
        elif [ -x "${ORACLE_HOME}/wlserver/common/bin/wlst.sh" -a -f "${ORACLE_HOME}/wlserver/.product.properties" ]; then
            WLST="${ORACLE_HOME}/wlserver/common/bin/wlst.sh"
            CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar"; export CLASSPATH
        fi


        if [ -z "${WLST}" ]; then
            echo "Unable to determine WLS version in ${ORACLE_HOME} to determine WLST shell script to call" >&2
            exit 98
        fi
    fi

    WLST_PROPERTIES=-Dcom.oracle.cie.script.throwException=true
    WLST_PROPERTIES="${WLST_PROPERTIES} -Djava.util.logging.config.class=${LOG_CONFIG_CLASS}"
    WLST_PROPERTIES="${WLST_PROPERTIES} ${WLSDEPLOY_PROPERTIES}"
    export WLST_PROPERTIES

    # print the configuration, and run the script

    echo "JAVA_HOME = ${JAVA_HOME}"
    echo "WLST_EXT_CLASSPATH = ${WLST_EXT_CLASSPATH}"
    echo "CLASSPATH = ${CLASSPATH}"
    echo "WLST_PROPERTIES = ${WLST_PROPERTIES}"

    PY_SCRIPTS_PATH="${WLSDEPLOY_HOME}/lib/python"
    if [ -z "${OHARG_VALUE}" ] ; then
      echo "${WLST} ${PY_SCRIPTS_PATH}/$wlstScript" "$@"
      "${WLST}" "${PY_SCRIPTS_PATH}/$wlstScript" "$@"
    else
      echo "${WLST} ${PY_SCRIPTS_PATH}/$wlstScript $OHARG ${OHARG_VALUE}" "$@"
      "${WLST}" "${PY_SCRIPTS_PATH}/$wlstScript" $OHARG "${OHARG_VALUE}" "$@"
    fi

    RETURN_CODE=$?
    checkExitCode ${RETURN_CODE}
    exit ${RETURN_CODE}
}

runJython() {
    # run a jython script, without WLST.
    jythonScript=$1
    # save first argument in jythonScript, and discard argument from $@
    shift

    # set up Oracle directory, logger, classpath

    ORACLE_SERVER_DIR=
    if [ -x "${ORACLE_HOME}/wlserver_10.3" ]; then
        ORACLE_SERVER_DIR="${ORACLE_HOME}/wlserver_10.3"
    elif [ -x "${ORACLE_HOME}/wlserver_12.1" ]; then
        ORACLE_SERVER_DIR="${ORACLE_HOME}/wlserver_12.1"
    else
        ORACLE_SERVER_DIR="${ORACLE_HOME}/wlserver"
    fi

    variableSetup

    JAVA_PROPERTIES="-Djava.util.logging.config.class=${LOG_CONFIG_CLASS}"
    JAVA_PROPERTIES="${JAVA_PROPERTIES} -Dpython.cachedir.skip=true"
    JAVA_PROPERTIES="${JAVA_PROPERTIES} -Dpython.console="
    JAVA_PROPERTIES="${JAVA_PROPERTIES} ${WLSDEPLOY_PROPERTIES}"
    export JAVA_PROPERTIES
    CLASSPATH="${WLSDEPLOY_HOME}/lib/weblogic-deploy-core.jar:$ORACLE_SERVER_DIR/server/lib/weblogic.jar"

    # print the configuration, and run the script

    echo "JAVA_HOME = ${JAVA_HOME}"
    echo "CLASSPATH = ${CLASSPATH}"
    echo "JAVA_PROPERTIES = ${JAVA_PROPERTIES}"

    PY_SCRIPTS_PATH="${WLSDEPLOY_HOME}/lib/python"

    if [ -z "${OHARG_VALUE}" ] ; then
      echo \
      "${JAVA_HOME}/bin/java -cp ${CLASSPATH} \
          $JAVA_PROPERTIES \
          -Dpython.path=$ORACLE_SERVER_DIR/common/wlst/modules/jython-modules.jar/Lib \
          org.python.util.jython \
          ${PY_SCRIPTS_PATH}/$jythonScript" "$@"

      "${JAVA_HOME}/bin/java" -cp "$CLASSPATH" \
          $JAVA_PROPERTIES  \
          -Dpython.path="$ORACLE_SERVER_DIR/common/wlst/modules/jython-modules.jar/Lib" \
          org.python.util.jython \
          "${PY_SCRIPTS_PATH}/$jythonScript" "$@"
    else
      echo \
      "${JAVA_HOME}/bin/java -cp ${CLASSPATH} \
          $JAVA_PROPERTIES \
          -Dpython.path=$ORACLE_SERVER_DIR/common/wlst/modules/jython-modules.jar/Lib \
          org.python.util.jython \
          ${PY_SCRIPTS_PATH}/$jythonScript $OHARG ${OHARG_VALUE}" "$@"
          
      "${JAVA_HOME}/bin/java" -cp "$CLASSPATH" \
          $JAVA_PROPERTIES  \
          -Dpython.path="$ORACLE_SERVER_DIR/common/wlst/modules/jython-modules.jar/Lib" \
          org.python.util.jython \
          "${PY_SCRIPTS_PATH}/$jythonScript" $OHARG "${OHARG_VALUE}" "$@"
    fi

    RETURN_CODE=$?
    checkExitCode ${RETURN_CODE}
    exit ${RETURN_CODE}
}

checkExitCode() {
    # print a message for the exit code passed in.
    # calling script must have assigned the scriptName variable.
    # calling script must have a usage() method.

    returnCode=$1

    if [ $returnCode -eq 104 ]; then
      echo ""
      echo "$scriptName completed successfully but the domain changes have been canceled because -cancel_changes_if_restart_required is specified (exit code = ${RETURN_CODE})"
    elif [ $returnCode -eq 103 ]; then
      echo ""
      echo "$scriptName completed successfully but the domain requires a restart for the changes to take effect (exit code = ${RETURN_CODE})"
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
