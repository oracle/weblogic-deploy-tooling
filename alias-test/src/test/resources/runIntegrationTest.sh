#!/bin/sh
# *****************************************************************************
# runIntegrationTest.sh
#
# Copyright (c) 2021, Oracle and/or its affiliates.
# The Universal Permissive License (UPL), Version 1.0
#
#     NAME
#       runIntegrationTest.sh - Run the online and offline verify jobs
#
#     DESCRIPTION
#       Copy the latest WebLogic Deploy Tool into Docker container and
#       Run the offline and online verify jobs using the generated json
#       in the docker image.
#
# This script uses the following command-line arguments directly, the rest
# of the arguments are passed down to the underlying python program:
#
#     - -testfiles_path     The location where to store the generated files and reports
#                           and where to read the generated files to create the reports.
#     - -wls_version        The version of WebLogic formatted such as 12.2.1.4.0
#
# This script uses the following variables:
#
# JAVA_HOME            - The location of the JDK to use.  The caller must set
#                        this variable to a valid Java 7 (or later) JDK.
#
# WLSDEPLOY_HOME       - The location of the WLS Deploy installation.
#
# WLSDEPLOY_BASE       - The volume mounted to the container -the container mounted name
#
# TEST_HOME            - The location of the WLS Deploy Alias System Test installation.
#
# PYTHON_HOME          - The location of the 2.7.0 or 2.7.2 jython jar that this tool will run with
pwd
rm -rf ${WLSDEPLOY_BASE}/weblogic-deploy
unzip installer/target/weblogic-deploy.zip -d ${WLSDEPLOY_BASE}
ls -l ${TESTFILES_HOME}
echo WLS_VERSION=${WLS_VERSION}
${TEST_HOME}/resources/doVerifyOnline.sh $*
${TEST_HOME}/resources/doVerifyOffline.sh $*
RETURN_CODE=$?
exit ${RETURN_CODE}
