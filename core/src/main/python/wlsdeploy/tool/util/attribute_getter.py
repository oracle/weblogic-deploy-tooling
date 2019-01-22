"""
Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper


class AttributeGetter(object):
    """
    Contains the methods that will get the values for specific wlst attributes.
    These wlst attributes require the special processing. The method knows whether
    to get the value from the provided attribute LSA list, or to retrieve it
    using a GET or some other mechanism.
    """

    _class_name = "AttributeGetter"

    def __init__(self, aliases, logger, exception_type, wlst_mode=WlstModes.OFFLINE):
        self.__logger = logger
        self.__exception_type = exception_type
        self.__wlst_mode = wlst_mode
        self.__alias_helper = AliasHelper(aliases, self.__logger, exception_type)
        return


