#!/bin/sh
# *****************************************************************************
# archiveHelper.sh
#
# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       archiveHelper.sh - WLS Deploy tool to support creating and editing an archive file.
#
#     DESCRIPTION
#       This script provides add, extract, list, and replace functionality for
#       working with an archive file.
#
# This script uses the following variables:
#
# JAVA_HOME             - The location of the JDK to use.  The caller must set
#                         this variable to a valid Java 7 (or later) JDK.
#

WLSDEPLOY_PROGRAM_NAME="archiveHelper"; export WLSDEPLOY_PROGRAM_NAME

scriptPath=`dirname "$0"`

. "$scriptPath/shared.sh"

umask 27
minJdkVersion=7

WLSDEPLOY_LOG_HANDLERS="java.util.logging.FileHandler"; export WLSDEPLOY_LOG_HANDLERS
javaOnlySetup $minJdkVersion "quiet"

"${JAVA_HOME}/bin/java" "-Djava.util.logging.config.class=${LOG_CONFIG_CLASS}" oracle.weblogic.deploy.tool.ArchiveHelper "$@"
