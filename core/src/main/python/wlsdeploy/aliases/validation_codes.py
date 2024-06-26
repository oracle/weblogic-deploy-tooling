"""
Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The ValidationCodes enum module
"""
from wlsdeploy.util.enum import Enum

#
# Only INVALID, CONTEXT_INVALID, and VALID should ever be exposed outside the aliases module.
#
ValidationCodes = Enum(['INVALID', 'CONTEXT_INVALID', 'VERSION_INVALID', 'MODE_INVALID', 'VALID'])
