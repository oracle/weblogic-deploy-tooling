#!/bin/sh
# *****************************************************************************
# compareModel.sh
#
# Copyright (c) 2020, Oracle Corporation and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       compareModel.sh - WLS Deploy tool to compare two models
#
#     DESCRIPTION
#       This script compares two models. The models compared must be both yaml or both json
#
# This script uses the following variables:
#
# JAVA_HOME             - The location of the JDK to use.  The caller must set
#                         this variable to a valid Java 7 (or later) JDK.
#


usage() {
  echo ""
  echo "Usage: $1 [-help]"
  echo "          -oracle_home <oracle_home> <model file 1> <model file 2>"
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="modelDiff"; export WLSDEPLOY_PROGRAM_NAME

scriptName=`basename $0`
scriptPath=$(dirname "$0")
scriptArgs=$*

. $scriptPath/shared.sh

umask 27

# verify -oracle_home is passed

#if [ $# -ne 4 ] ; then
#  usage
#  exit 0
#fi
#
#if [ ! -f $3 ] ; then
#  echo "Model File $3 doesn't exist or not accessible"
#  exit 1
#fi
#
#if [ ! -f $4 ] ; then
#  echo "Model File $4 doesn't exist or not accessible"
#  exit 1
#fi
#
#if [ ${3: -5} == ".yaml" ] ; then
#  if [ ${4: -5} != ".yaml" ] ; then
#    echo "Model files must be of the same extension"
#    exit 1
#  fi
#elif [ ${3: -5} == ".json" ] ; then
#  if [ ${4: -5} != ".json" ] ; then
#    echo "Model files must be of the same extension"
#    exit 1
#  fi
#else
#  echo "Model files must be either ended with json or yaml extension"
#  exit 1
#fi

checkJythonArgs "$@"



# Java 7 is required, no encryption is used
javaSetup 7

runJython model_diff.py
