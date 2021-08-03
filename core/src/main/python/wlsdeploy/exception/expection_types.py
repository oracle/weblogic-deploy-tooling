"""
Copyright (c) 2017, 2021, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.util.enum import Enum

ExceptionType = Enum([
    'ALIAS',
    'CLA',
    'COMPARE',
    'CREATE',
    'DEPLOY',
    'DISCOVER',
    'ENCRYPTION',
    'JSON',
    'PREPARE',
    'PY_WLST',
    'TRANSLATE',
    'VALIDATE',
    'VARIABLE',
    'WLS_DEPLOY_ARCHIVE_IO',
    'YAML'
])
