#!/bin/bash ex

# Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
# The Universal Permissive License (UPL), Version 1.0
 BUILD_ARG=''
 if [ $# > 1 ]; then
   PROPERTIES_FILE=$1
 fi

if [ ! -e "${PROPERTIES_FILE}" ]; then
    echo "A properties file with variable definitions should be supplied."
fi

echo Export environment variables from the ${PROPERTIES_FILE} properties file

DOMAIN_DIR=`awk '{print $1}' $PROPERTIES_FILE | grep ^DOMAIN_NAME= | cut -d "=" -f2`
if [ ! -n "$DOMAIN_DIR" ]; then  
   if [ -n "$DOMAIN_NAME" ]; then
      DOMAIN_DIR=$DOMAIN_NAME
   fi
fi
if [ -n "$DOMAIN_DIR" ]; then
     export DOMAIN_DIR
     echo DOMAIN_DIR=$DOMAIN_DIR
     BUILD_ARG="$BUILD_ARG --build-arg DOMAIN_DIR=$DOMAIN_DIR"
fi

ADMIN_HOST=`awk '{print $1}' $PROPERTIES_FILE | grep ^ADMIN_HOST= | cut -d "=" -f2`
if [ -n "$ADMIN_HOST" ]; then
    export ADMIN_HOST
    echo ADMIN_HOST=$ADMIN_HOST
    BUILD_ARG="$BUILD_ARG --build-arg ADMIN_HOST=$ADMIN_HOST"
fi

ADMIN_PORT=`awk '{print $1}' $PROPERTIES_FILE | grep ^ADMIN_PORT= | cut -d "=" -f2`
if [ -n "$ADMIN_PORT" ]; then
    export ADMIN_PORT
    echo ADMIN_PORT=$ADMIN_PORT
    BUILD_ARG="$BUILD_ARG --build-arg ADMIN_PORT=$ADMIN_PORT"
fi

MS_PORT=`awk '{print $1}' $PROPERTIES_FILE | grep ^MS_PORT= | cut -d "=" -f2`
if [ -n "$MS_PORT" ]; then
    export MS_PORT echo MS_PORT=$MS_PORT BUILD_ARG="$BUILD_ARG --build-arg MS_PORT=$MS_PORT" fi

DEBUG_PORT=`awk '{print $1}' $PROPERTIES_FILE | grep ^DEBUG_PORT= | cut -d "=" -f2`
if [ -n "$DEBUG_PORT" ]; then
    export DEBUG_PORT
    echo DEBUG_PORT=$DEBUG_PORT
    BUILD_ARG="$BUILD_ARG --build-arg DEBUG_PORT=$DEBUG_PORT"
fi

echo BUILD_ARG=$BUILD_ARG
