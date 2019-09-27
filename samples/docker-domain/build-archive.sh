#!/bin/sh
#
#Copyright (c) 2018, 2019, Oracle Corporation and/or its affiliates. All rights reserved.
#
#Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
rm -Rf archive
mkdir -p archive/wlsdeploy/applications
cd simple-app
jar cvf ../archive/wlsdeploy/applications/simple-app.war *
cd ../archive
jar cvf ../archive.zip *
