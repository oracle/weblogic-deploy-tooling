"""
Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util.weblogic_helper import WebLogicHelper

_class_name = "MBeanGetter"

_logger = PlatformLogger('wlsdeploy.mbean.getter')


class MBeanGetter(object):
    """
    Contains methods to help retrieve the wlst MBeans at the specific location.
    """

    def __init__(self, aliases, exception_type, logger=_logger):
        self.__logger = logger
        self.__exception_type = exception_type
        self.__alias_helper = AliasHelper(aliases, self.__logger, exception_type)
        self.__wlst_helper = WlstHelper(self.__logger, exception_type)
        self.__wls_version = WebLogicHelper(self.__logger).get_actual_weblogic_version()
        return

    def get_class_name(self):
        return _class_name

    def get_valid_provider_name_list(self, location):
        """
        This version of offline wlst installs default security providers with no name. If a name does not exist for
        a provider mbean, the string 'Provider' is returned. Bug 29217589 opened on this problem. This only
        occurs in 10.3.x and 12.1.1 in offline mode.
        :param location: current location context
        :return: mbean name list excluding any 'Provider' name.
        """
        _method_name = 'get_valid_provider_name_list'
        self.__logger.entering(location.get_folder_path(), class_name=_class_name, method_name=_method_name)

        filtered_list = []
        path_to_bean = self.__alias_helper.get_wlst_list_path(location)
        name_list = self.__wlst_helper.lsc()
        self.__logger.finer('WLSDPLY-06201', path_to_bean, name_list, class_name=_class_name, method_name=_method_name)
        for name in name_list:
            if name == 'Provider':
                self.__logger.warning('WLSDPLY-06200', path_to_bean, self.__wls_version, class_name=_class_name,
                                      method_name=_method_name)
            else:
                filtered_list.append(name)
        self.__logger.exiting(class_name=_class_name, method_name=_method_name, result=filtered_list)
        return filtered_list
