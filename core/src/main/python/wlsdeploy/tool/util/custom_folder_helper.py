"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper


class CustomFolderHelper(object):
    """
    Shared code for custom (user-defined) folders in the model.
    These require special handling, since they do not have alias definitions.
    """
    __class_name = 'CustomFolderHelper'

    def __init__(self, aliases, logger, exception_type):
        self.logger = logger
        self.exception_type = exception_type
        self.alias_helper = AliasHelper(aliases, self.logger, self.exception_type)
        self.wlst_helper = WlstHelper(self.logger, self.exception_type)

    def update_security_folder(self, location, model_name, model_nodes):
        """
        Update the specified security model nodes in WLST.
        :param location: the location of the folder's parent
        :param model_name: the model name of the folder to be updated
        :param model_nodes: a child model nodes of the folder to be updated
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'update_security_folder'

        self.logger.entering(str(location), model_name, class_name=self.__class_name, method_name=_method_name)

        self.logger.info('WLSDPLY-12124', model_name, self.alias_helper.get_model_folder_path(location),
                         class_name=self.__class_name, method_name=_method_name)
