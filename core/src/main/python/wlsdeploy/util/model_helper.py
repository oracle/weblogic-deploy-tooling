"""
Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging import platform_logger

_class_name = "model_helper"
_logger = platform_logger.PlatformLogger('wlsdeploy.model.helper')

# Helper methods for WDT model (Jython-compatible)


def is_delete_name(name):
    """
    Determines if the specified name is flagged for deletion with the "!" prefix.
    :param name: the name to be checked
    :return: True if the name is prefixed, false otherwise
    """
    return name.startswith("!")


def get_delete_item_name(name):
    """
    Returns the WLST name of the item to be deleted.
    Removes the "!" prefix from the name. An exception is thrown if the name is not prefixed.
    :param name: the prefixed model name of the item to be deleted
    :return: the model name of the item to be deleted
    """
    _method_name = 'get_delete_item_name'

    if is_delete_name(name):
        return name[1:]

    ex = exception_helper.create_deploy_exception('WLSDPLY-09111', name)
    _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
    raise ex


def get_delete_name(name):
    """
    Returns the delete name for the specified name by adding a "!" prefix.
    :param name: the name be adjusted
    :return: the delete name for the name
    """
    return "!" + name
