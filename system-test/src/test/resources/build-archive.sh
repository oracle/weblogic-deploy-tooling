#!/bin/sh
#
# Copyright (c) 2018, 2020, Oracle and/or its affiliates.
#
# Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
#
projectDir=$(pwd)
archiveDir=${projectDir}/target/resources/archive
rm -Rf $archiveDir
mkdir -p $archiveDir/wlsdeploy/applications
cd ../samples/docker-domain/simple-app
jar cvf $archiveDir/wlsdeploy/applications/simple-app.war  *
cd $archiveDir
jar cvf ../archive.zip *
