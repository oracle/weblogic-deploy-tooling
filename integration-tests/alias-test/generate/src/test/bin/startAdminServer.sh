#!/usr/bin/env sh
#
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
# The Universal Permissive License (UPL), Version 1.0
#

if [ -z "${DOMAIN_HOME}" ]; then
    echo "ORACLE_HOME environment variable must be set" >&2
    exit 1
fi

if [ -z "${JAVA_HOME}" ]; then
    echo "JAVA_HOME environment variable must be set" >&2
    exit 1
fi
export JAVA_HOME

scriptPath=$(dirname "$0")

. "${scriptPath}/helpers.sh"

ADMIN_URL=$(getHttpAdminUrl)
READY_APP_URL="${ADMIN_URL}/weblogic/ready"
no_proxy=$(getNoProxyValue); export no_proxy
echo "no_proxy value is set to ${no_proxy}"

LOGDIR="${DOMAIN_HOME}/servers/AdminServer/logs"
mkdir -p "${LOGDIR}"

nohup "${DOMAIN_HOME}/startWebLogic.sh" > "${LOGDIR}/AdminServer.out" 2> "${LOGDIR}/AdminServer.err" &

echo "Waiting for 10 seconds before polling for admin server readiness at ${READY_APP_URL}"
sleep 10


i=0
while [ $i -lt 60 ]; do
  echo "Checking admin server readiness (i = $i)"
  return_code=$(curl -sw '%{http_code}' "${READY_APP_URL}")
  if [ "${return_code}" = "200" ]; then
    echo "Admin Server is ready"
    exit 0
  else
    echo "Ready app return code ${return_code}...sleeping for 5 seconds"
    sleep 5
  fi
  i=$(( $i+1 ))
done

echo "failed to start admin server" >&2
exit 1
