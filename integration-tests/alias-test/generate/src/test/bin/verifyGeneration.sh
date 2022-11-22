#!/usr/bin/env sh
#
# Copyright (c) 2022, Oracle and/or its affiliates.
# The Universal Permissive License (UPL), Version 1.0
#
# The purpose of this script is to determine if the three generation phases completed
# successfully, and stop the build if they did not create their status files.

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
  STATUS_DIR="${BASEDIR}/target/generate-status"
fi

if [ ! -d "${STATUS_DIR}" ]; then
  echo "Generation status directory ${STATUS_DIR} does not exist" >&2
  exit 1
elif [ ! -f "${STATUS_DIR}/doGenerateSC" ]; then
  echo "Security Configuration Generation status ${STATUS_DIR}/doGenerateSC does not exist" >&2
  exit 1
elif [ ! -f "${STATUS_DIR}/doGenerateOnline" ]; then
  echo "Online Generation status ${STATUS_DIR}/doGenerateOnline does not exist" >&2
  exit 1
elif [ ! -f "${STATUS_DIR}/doGenerateOffline" ]; then
  echo "Offline Generation status ${STATUS_DIR}/doGenerateOffline does not exist" >&2
  exit 1
fi
