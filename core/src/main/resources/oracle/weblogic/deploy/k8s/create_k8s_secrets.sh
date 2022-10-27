#!/bin/bash

set -eu

# {{{topComment}}}
NAMESPACE={{{namespace}}}
DOMAIN_UID={{{domainUid}}}

LONG_SECRETS=()

function check_secret_name {
  if [ ${#1} -gt 63 ]; then
    LONG_SECRETS+=($1)
  fi
}

function create_k8s_secret {
  SECRET_NAME=${DOMAIN_UID}-$1
  check_secret_name ${SECRET_NAME}
  kubectl -n $NAMESPACE delete secret ${SECRET_NAME} --ignore-not-found
  kubectl -n $NAMESPACE create secret generic ${SECRET_NAME} --from-literal=password=$2
  kubectl -n $NAMESPACE label secret ${SECRET_NAME} weblogic.domainUID=${DOMAIN_UID}
}

function create_paired_k8s_secret {
  SECRET_NAME=${DOMAIN_UID}-$1
  check_secret_name ${SECRET_NAME}
  kubectl -n $NAMESPACE delete secret ${SECRET_NAME} --ignore-not-found
  kubectl -n $NAMESPACE create secret generic ${SECRET_NAME} --from-literal=username=$2 --from-literal=password=$3
  kubectl -n $NAMESPACE label secret ${SECRET_NAME} weblogic.domainUID=${DOMAIN_UID}
}
{{#pairedSecrets}}

{{#comments}}
# {{{comment}}}
{{/comments}}
create_paired_k8s_secret {{{secretName}}} "{{{user}}}" {{{password}}}
{{/pairedSecrets}}
{{#secrets}}

{{#comments}}
# {{{comment}}}
{{/comments}}
create_k8s_secret {{{secretName}}} {{{password}}}
{{/secrets}}

LONG_SECRETS_COUNT=${#LONG_SECRETS[@]}
if [ ${LONG_SECRETS_COUNT} -gt 0 ]; then
  echo ""
  echo "{{{longMessage}}}"
  for NAME in "${LONG_SECRETS[@]}"; do
    echo "  ${NAME}"
  done
  echo ""
{{#longMessageDetails}}
  echo "{{{text}}}"
{{/longMessageDetails}}
fi
