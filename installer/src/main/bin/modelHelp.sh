#!/bin/sh
# *****************************************************************************
# modelHelp.sh
#
# Copyright (c) 2020, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#     NAME
#       modelHelp.sh - WLS Deploy tool to list the folders and
#                      attributes available at a specific location
#                      in the domain model.
#
#     DESCRIPTION
#       This script uses the alias framework to determine which attributes
#       and folders are available at a specific location in the model.
#
# This script uses the following variables:
#
# JAVA_HOME             - The location of the JDK to use.  The caller must set
#                         this variable to a valid Java 7 (or later) JDK.
#
# WLSDEPLOY_PROPERTIES  - Extra system properties to pass to Java.  The caller
#                         can use this environment variable to add additional
#                         system properties to the Java environment.
#

usage() {
  echo ""
  echo "Usage: $1 [-help]"
  echo "          [-oracle_home <oracle_home>]"
  echo "          [-target <target>]"
  echo "          [-attributes_only | -folders_only | -recursive]"
  echo "          [<model_path>]"
  echo ""
  echo "    where:"
  echo "        oracle_home - an existing Oracle Home directory.  This is required"
  echo "                      unless the ORACLE_HOME environment variable is set."
  echo ""
  echo "        target      - target platform (wko, etc.)."
  echo "                      this determines the structure of the kubernetes section."
  echo ""
  echo "        model_path  - the path to the model element to be examined."
  echo "                      The format is [<section>:][/<folder>]*"
  echo ""
  echo "    By default, the tool will display the folders and attributes for the"
  echo "    specified model path."
  echo ""
  echo "    The -attributes_only switch will cause the tool to list only the attributes"
  echo "    for the specified model path."
  echo ""
  echo "    The -folders_only switch will cause the tool to list only the folders"
  echo "    for the specified model path."
  echo ""
  echo "    The -recursive switch will cause the tool to list only the folders"
  echo "    for the specified model path, and recursively include the folders below"
  echo "    that path."
  echo ""
  echo "    If no model path is specified, the tool to enter an interactive mode."
  echo ""
  echo "    model_path examples:"
  echo "        resources:/JDBCSystemResource/JdbcResource"
  echo "        /JDBCSystemResource/JdbcResource"
  echo "        resources:"
  echo "        resources"
  echo "        top  (this will list the top-level section names)"
  echo ""
}

WLSDEPLOY_PROGRAM_NAME="modelHelp"; export WLSDEPLOY_PROGRAM_NAME

scriptName=`basename "$0"`
scriptPath=`dirname "$0"`

. "$scriptPath/shared.sh"

umask 27

checkJythonArgs "$@"

# Java 7 is required, no encryption is used
javaSetup 7

runJython model_help.py "$@"
