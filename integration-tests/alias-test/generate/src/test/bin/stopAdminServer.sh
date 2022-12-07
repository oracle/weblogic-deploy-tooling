#!/usr/bin/env sh
#
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
# The Universal Permissive License (UPL), Version 1.0
#

if [ -z "${DOMAIN_HOME}" ]; then
    echo "DOMAIN_HOME environment variable must be set" >&2
    exit 1
fi

if [ -z "${JAVA_HOME}" ]; then
    echo "JAVA_HOME environment variable must be set" >&2
    exit 1
fi
export JAVA_HOME

scriptPath=$(dirname "$0")

. "${scriptPath}/helpers.sh"

ADMIN_URL=$(getT3AdminUrl)
ADMIN_USER=$1
ADMIN_PASS=$2

if [ -z "${ADMIN_USER}" ]; then
  ADMIN_USER=weblogic
fi
if [ -z "${ADMIN_PASS}" ]; then
  ADMIN_PASS=welcome1
fi

READY_APP_URL="$(getHttpAdminUrl)/weblogic/ready"
no_proxy=$(getNoProxyValue); export no_proxy
echo "no_proxy value is set to ${no_proxy}"

ready_status=$(curl -sw '%{http_code}' "${READY_APP_URL}")
if [ "${ready_status}" = "000" ]; then
  echo "Admin Server is not running...nothing to do"
  exit 0
fi

nohup "${DOMAIN_HOME}/bin/stopWebLogic.sh" "${ADMIN_USER}" "${ADMIN_PASS}" "${ADMIN_URL}" > ${DOMAIN_HOME}/shutdown.out &

echo "Waiting for 10 seconds before polling for admin server shutdown at ${READY_APP_URL}"
sleep 10


i=0
while [ $i -lt 60 ]; do
  echo "Checking admin server shutdown (i = $i)"
  return_code=$(curl -sw '%{http_code}' -o /dev/null "${READY_APP_URL}")
  if [ "${return_code}" = "000" ]; then
    echo "Admin Server is shut down"
    exit 0
  else
    echo "Admin Server is still running (Ready app return code ${return_code})...sleeping for 5 seconds"
    sleep 5
  fi
  i=$(( $i+1 ))
done

echo "failed to shut down admin server" >&2
exit 1
