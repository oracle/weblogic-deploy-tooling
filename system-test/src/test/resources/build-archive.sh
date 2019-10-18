#!/bin/sh
#
#Copyright (c) 2018, 2019, Oracle and/or its affiliates. All rights reserved.
#
#Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
#
rm -Rf src/test/resources/archive
mkdir -p src/test/resources/archive/wlsdeploy/applications
cd ../samples/docker-domain/simple-app
jar cvf ../../../system-test/src/test/resources/archive/wlsdeploy/applications/simple-app.war  *
cd ../../../system-test/src/test/resources/archive
jar cvf ../archive.zip *
