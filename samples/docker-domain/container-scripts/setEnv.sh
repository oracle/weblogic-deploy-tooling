#!/bin/bash
#
# Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
# The Universal Permissive License (UPL), Version 1.0
#
# Set the Domain environment variables.

if [ ! -e "$WDT_VARIABLE" ]; then
    echo "A properties file with variable definitions should be supplied."
    goto envexit
fi

DOMAIN_NAME=`awk '{print $1}' $WDT_VARIABLE | grep ^DOMAIN_NAME= | cut -d "=" -f2`
if [ -n "$DOMAIN_NAME" ]; then
    export DOMAIN_NAME
fi

ADMIN_HOST=`awk '{print $1}' $WDT_VARIABLE | grep ^ADMIN_HOST= | cut -d "=" -f2`
if [ -n "$ADMIN_HOST" ]; then
    export ADMIN_HOST
fi

ADMIN_PORT=`awk '{print $1}' $WDT_VARIABLE | grep ^ADMIN_PORT= | cut -d "=" -f2`
if [ -n "$ADMIN_PORT" ]; then
    export ADMIN_PORT
fi

MS_PORT=`awk '{print $1}' $WDT_VARIABLE | grep ^MS_PORT= | cut -d "=" -f2`
if [ -n "$MS_PORT" ]; then
    export MS_PORT
fi

DEBUG_PORT=`awk '{print $1}' $WDT_VARIABLE | grep ^MS_PORT= | cut -d "=" -f2`
if [ -n "$DEBUG_PORT" ]; then
    export DEBUG_PORT
fi

envexit:
