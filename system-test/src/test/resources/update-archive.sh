#!/bin/sh
#
# Copyright (c) 2022, Oracle and/or its affiliates.
#
# Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
#
set -e
projectDir=$(pwd)
archiveDir=${projectDir}/target/resources
cd "$archiveDir"
cp archive.zip archive2.zip
mkdir temp
cd temp
jar xf ../archive2.zip
touch dummy.html
jar uf wlsdeploy/applications/simple-app.war dummy.html
jar uf ../archive2.zip wlsdeploy/applications/simple-app.war


