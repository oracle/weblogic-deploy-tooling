#!/usr/bin/env sh
#
# Copyright (c) 2022, Oracle and/or its affiliates.
# The Universal Permissive License (UPL), Version 1.0
#
# The purpose of this script is to determine if the two verification phases completed
# successfully, and stop the build if they did not.

scriptPath="$(dirname "$0")"
BASEDIR="$(pwd)"

. "${scriptPath}/helpers.sh"

STATUS_DIR=""
while [ $# -gt 1 ]; do
    key="$1"
    case $key in
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

if [ -z "${STATUS_DIR}" ]; then
  STATUS_DIR="${BASEDIR}/target/verify-status"
fi

if [ ! -d "${STATUS_DIR}" ]; then
  echo "Verification status directory ${STATUS_DIR} does not exist" >&2
  exit 1
fi

EXIT_CODE=0
if [ ! -f "${STATUS_DIR}/doVerifyOnline" ]; then
  echo "Online status ${STATUS_DIR}/doVerifyOnline does not exist so please review the report for error details" >&2
  EXIT_CODE=1
fi

if [ ! -f "${STATUS_DIR}/doVerifyOffline" ]; then
  echo "Offline status ${STATUS_DIR}/doVerifyOffline does not exist so please review the report for error details" >&2
  EXIT_CODE=1
fi

if [ ${EXIT_CODE} -ne 0 ]; then
  echo "Verification tests returned errors so failing the Maven build" >&2
  exit ${EXIT_CODE}
else
  echo "Verification tests passed"
fi
