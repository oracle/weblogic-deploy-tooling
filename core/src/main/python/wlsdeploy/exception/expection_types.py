"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
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
