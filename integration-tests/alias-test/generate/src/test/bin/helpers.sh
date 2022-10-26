#!/usr/bin/env sh
#
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
# The Universal Permissive License (UPL), Version 1.0
#

getHostName() {
  if ! result=$(hostname); then
    # Probably running inside a Docker container
    if [ -n "${HOSTNAME}" ]; then
      result="${HOSTNAME}"
    elif [ -n "${HOST}" ]; then
      result="${HOST}"
    else
      echo "Failed to determine the hostname" >&2
      exit 1
    fi
  fi

  #
  # macOS is brain-dead and can only resolve its own hostname
  # if .local is appended...
  #
  platform=$(uname)
  if [ "${platform}" = "Darwin" ]; then
    result="${result}.local"
  fi

  echo "${result}"
}

getT3AdminUrl() {
  if ! hostname=$(getHostName); then
    exit 1
  fi
  echo "t3://${hostname}:7001"
}

getHttpAdminUrl() {
  if ! hostname=$(getHostName); then
    exit 1
  fi
  echo "http://${hostname}:7001"
}

getNoProxyValue() {
  hostname=$(getHostName)
  if [ -z "${no_proxy}" ]; then
    result=${hostname}
  else
    result="${no_proxy},${hostname}"
  fi
  echo "${result}"
}

isAdminServerRunning() {
  return_code=$(curl -sw '%{http_code}' "${READY_APP_URL}")
  if [ "${return_code}" = "000" ]; then
    echo "false"
  else
    echo "true"
  fi
}
