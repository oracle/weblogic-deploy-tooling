"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Methods and constants for building Kubernetes resource files,
including domain resource configuration for WebLogic Kubernetes Operator.
"""

# Kubernetes secret with admin name and password is <domainUid>-weblogic-credentials
WEBLOGIC_CREDENTIALS_SECRET_SUFFIX = '-weblogic-credentials'
