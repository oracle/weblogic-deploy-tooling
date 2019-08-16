"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.util.enum import Enum

ExceptionType = Enum([
    'ALIAS',
    'CLA',
    'CREATE',
    'DEPLOY',
    'DISCOVER',
    'ENCRYPTION',
    'JSON',
    'PY_WLST',
    'TRANSLATE',
    'VALIDATE',
    'VARIABLE',
    'WLS_DEPLOY_ARCHIVE_IO',
    'YAML'
])
