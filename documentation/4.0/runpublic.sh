#!/bin/bash

# Copyright (c) 2019, 2022, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

# 1313 is the hugo default port
port=${1:-1313}

hugo server -b http://$(hostname).$(dnsdomainname):$port/weblogic-deploy-tooling -D --bind=$(hostname).$(dnsdomainname) -p $port
