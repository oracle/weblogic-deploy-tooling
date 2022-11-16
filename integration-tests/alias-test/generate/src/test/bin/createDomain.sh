#!/usr/bin/env sh
#
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
# The Universal Permissive License (UPL), Version 1.0
#

if [ -z "${ORACLE_HOME}" ]; then
    echo "ORACLE_HOME environment variable must be set" >&2
    exit 1
fi

if [ -z "${JAVA_HOME}" ]; then
  echo "Please set the JAVA_HOME environment variable to point to a Java installation compatible with the WebLogic version" >&2
  exit 1
fi

if [ -z "${WLSDEPLOY_HOME}" ]; then
    echo "WLSDEPLOY_HOME environment variable must be set" >&2
    exit 1
fi

# Process command-line args
WDT_MODEL=""
WDT_ARCHIVE=""
DOMAIN_PARENT_DIR=""
while [ $# -gt 1 ]; do
    key="$1"
    case $key in
        -model_file)
          WDT_MODEL="$2"
          shift
        ;;
        -archive_file)
          WDT_ARCHIVE="$2"
          shift
        ;;
        -domain_parent)
          DOMAIN_PARENT_DIR="$2"
          shift
        ;;
        *)
        # unknown option
        ;;
    esac
    shift # past arg or value
done

# Verify command-line args
if [ -z "${WDT_MODEL}" ]; then
  echo "Required command-line argument -model_file was not specified" >&2
  exit 1
elif [ ! -f "${WDT_MODEL}" ]; then
  echo "Specified model file does not exist: ${WDT_MODEL}"
  exit 1
fi

if [ -z "${WDT_ARCHIVE}" ]; then
  echo "Required command-line argument -archive_file was not specified" >&2
  exit 1
elif [ ! -f "${WDT_ARCHIVE}" ]; then
  echo "Specified archive file does not exist: ${WDT_ARCHIVE}"
  exit 1
fi

if [ -z "${DOMAIN_PARENT_DIR}" ]; then
  echo "Required command-line argument -domain_parent was not specified" >&2
  exit 1
fi

# Clean up any old domain directory
rm -rf "${DOMAIN_PARENT_DIR}"
mkdir -p "${DOMAIN_PARENT_DIR}"

"${WLSDEPLOY_HOME}/bin/createDomain.sh" \
  -oracle_home "${ORACLE_HOME}" \
  -domain_parent "${DOMAIN_PARENT_DIR}" \
  -model_file "${WDT_MODEL}" \
  -archive_file "${WDT_ARCHIVE}"

RETURN_CODE=$?
if [ "${RETURN_CODE}" != "0" ]; then
  echo "createDomain failed with exit code ${RETURN_CODE}" >&2
  exit ${RETURN_CODE}
fi
