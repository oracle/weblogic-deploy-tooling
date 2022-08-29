#!/bin/sh
#
# Copyright (c) 2018, 2022, Oracle and/or its affiliates.
#
# Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
#
projectDir=$(pwd)
archiveDir=${projectDir}/target/resources/archive
rm -Rf "$archiveDir"
mkdir -p "$archiveDir"/wlsdeploy/applications
cd "$projectDir"/src/test/resources/archive/simple-app || exit
jar cvf "$archiveDir"/wlsdeploy/applications/simple-app.war  ./*
cd "$archiveDir" || exit
jar cvf ../archive.zip ./*
