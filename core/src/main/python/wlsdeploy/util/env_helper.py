"""
Copyright (c) 2023, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.

Helper class to work around bugs in Jython 2.2.1 where environment variables with
newline characters mess up the os.environ data structure.
"""
import os

from java.lang import System
from oracle.weblogic.deploy.util import StringUtils

def getenv(env_var_name, default_value=None):
    if StringUtils.isEmpty(env_var_name):
        return default_value
    elif env_var_name in os.environ:
        return os.environ[env_var_name]
    else:
        retval = System.getenv(env_var_name)
        if retval is None:
            return default_value
        return retval

def has_env(env_var_name):
    if StringUtils.isEmpty(env_var_name):
        return False
    elif env_var_name in os.environ:
        return True
    else:
        return System.getenv(env_var_name) is not None
