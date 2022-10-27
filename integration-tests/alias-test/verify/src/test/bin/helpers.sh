#!/usr/bin/env sh
#
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
# The Universal Permissive License (UPL), Version 1.0
#
getOnlineGeneratedFileName() {
    wls_version="$1"
    if [ -z "${wls_version}" ]; then
        echo "Unable to compute online generated file name due to missing wls_version arg" >&2
        exit 1
    fi
    echo "generatedOnline-${wls_version}.json"
}

getOfflineGeneratedFileName() {
    wls_version="$1"
    if [ -z "${wls_version}" ]; then
        echo "Unable to compute offline generated file name due to missing wls_version arg" >&2
        exit 1
    fi
    echo "generatedOffline-${wls_version}.json"
}
