#!/usr/bin/env sh

set -eu

# {{{topComment}}}
NAMESPACE={{{namespace}}}
DOMAIN_UID={{{domainUid}}}

LONG_SECRETS=""

check_secret_name() {
  if [ ${#1} -gt {{{maxSecretLength}}} ]; then
    LONG_SECRETS="${LONG_SECRETS} $1"
  fi
}

create_k8s_secret() {
  SECRET_NAME=${DOMAIN_UID}-$1
  check_secret_name "${SECRET_NAME}"
  kubectl -n $NAMESPACE delete secret "${SECRET_NAME}" --ignore-not-found

  shift

  K8S_COMMAND="kubectl -n $NAMESPACE create secret generic ${SECRET_NAME}"
  for var in "${@}"
  do
    K8S_COMMAND="${K8S_COMMAND} --from-literal=${var}"
  done
  $K8S_COMMAND

  kubectl -n $NAMESPACE label secret "${SECRET_NAME}" weblogic.domainUID=${DOMAIN_UID}
}
{{#secrets}}

{{#comments}}
# {{{comment}}}
{{/comments}}
create_k8s_secret {{{secretName}}} {{{secretPairs}}}
{{/secrets}}

LONG_SECRETS_COUNT=`echo "${LONG_SECRETS}" | wc -w | xargs`
if [ "${LONG_SECRETS_COUNT}" -gt 0 ]; then
  echo ""
  echo "{{{longMessage}}}"
  for NAME in ${LONG_SECRETS}; do
    echo "  ${NAME}"
  done
  echo ""
{{#longMessageDetails}}
  echo "{{{text}}}"
{{/longMessageDetails}}
fi
