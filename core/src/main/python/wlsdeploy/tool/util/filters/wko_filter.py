# Copyright (c) 2021, Oracle Corporation and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# ------------
# Description:
# ------------
# WDT filters to prepare a model for use with WKO, using the createDomain or prepareModel tools.
# These operations can be invoked as a single call, or independently of each other.
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.util.filters.model_traverse import ModelTraverse


def filter_model(model, model_context):
    """
    Perform the following operations on the specified model:
    - Remove any online-only attributes
    - Check if servers in a cluster have different ports
    :param model: the model to be filtered
    :param model_context: used by nested filters
    """
    filter_online_attributes(model, model_context)
    check_clustered_server_ports(model, model_context)


def filter_online_attributes(model, model_context):
    """
    Remove any online-only attributes from the specified model.
    :param model: the model to be filtered
    :param model_context: used to configure aliases
    """
    online_filter = OnlineAttributeFilter(model_context, ExceptionType.PREPARE)
    online_filter.traverse_model(model)


def check_clustered_server_ports(model, model_context):
    """
    Set the CalculatedListenPorts attribute to false for dynamic clusters in the specified model.
    Warn if servers in a static cluster have different ports in the specified model.
    :param model: the model to be filtered
    :param model_context: unused, passed by filter_helper if called independently
    """
    print("CHECK_CLUSTERED SERVER PORTS")


class OnlineAttributeFilter(ModelTraverse):
    """
    Traverse the model and remove any online-only attributes.
    """
    _class_name = 'OnlineAttributeFilter'

    def __init__(self, model_context, exception_type):
        # use OFFLINE regardless of tool configuration
        ModelTraverse.__init__(self, model_context, WlstModes.OFFLINE, exception_type)

    # Override
    def unrecognized_field(self, model_dict, key, model_location):
        """
        If the attribute name has status ValidationCodes.VERSION_INVALID, it is a valid attribute sometimes,
        but not for offline mode in this WLS version.
        """
        _method_name = 'unrecognized_field'

        result, message = self._aliases.is_valid_model_attribute_name(model_location, key)
        if result == ValidationCodes.VERSION_INVALID:
            path = self._aliases.get_model_folder_path(model_location)
            self._logger.info('WLSDPLY-20033', key, path, class_name=self._class_name, method_name=_method_name)
            del model_dict[key]
