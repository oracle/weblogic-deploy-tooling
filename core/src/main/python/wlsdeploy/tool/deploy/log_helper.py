"""
Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from wlsdeploy.logging.platform_logger import PlatformLogger

_logger = PlatformLogger('wlsdeploy.deploy')


def log_updating_folder(type_name, parent_type, parent_name, is_add, class_name, method_name):
    """
    Log a message indicating that a folder is being updated or added.
    The type of the folder and the type and name of its parent are logged, if present.
    :param type_name: the type of the folder being updated
    :param parent_type: the type of the folder's parent
    :param parent_name: the name of the folder's parent
    :param is_add: true if the folder is being added
    :param class_name: the class name of the caller
    :param method_name: the method name of the caller
    """
    if is_add:
        if parent_type is None:
            _logger.info('WLSDPLY-09600', type_name, class_name=class_name, method_name=method_name)
        elif parent_name is None:
            _logger.info('WLSDPLY-09601', type_name, parent_type, class_name=class_name, method_name=method_name)
        else:
            _logger.info('WLSDPLY-09602', type_name, parent_type, parent_name, class_name=class_name,
                         method_name=method_name)
    else:
        if parent_type is None:
            _logger.info('WLSDPLY-20013', type_name, class_name=class_name, method_name=method_name)
        elif parent_name is None:
            _logger.info('WLSDPLY-09603', type_name, parent_type, class_name=class_name, method_name=method_name)
        else:
            _logger.info('WLSDPLY-09604', type_name, parent_type, parent_name, class_name=class_name,
                         method_name=method_name)


def log_updating_named_folder(type_name, folder_name, parent_type, parent_name, is_add, class_name, method_name):
    """
    Log a message indicating that a named folder is being updated or added.
    The type and name of the folder and its parent are logged, if present.
    :param type_name: the type of the folder being updated
    :param folder_name: the name of the folder being updated
    :param parent_type: the type of the folder's parent
    :param parent_name: the name of the folder's parent
    :param is_add: true if the folder is being added
    :param class_name: the class name of the caller
    :param method_name: the method name of the caller
    """
    if is_add:
        if parent_type is None:
            _logger.info('WLSDPLY-09605', type_name, folder_name, class_name=class_name, method_name=method_name)
        elif parent_name is None:
            _logger.info('WLSDPLY-09606', type_name, folder_name, parent_type, class_name=class_name,
                         method_name=method_name)
        else:
            _logger.info('WLSDPLY-09607', type_name, folder_name, parent_type, parent_name,
                         class_name=class_name, method_name=method_name)
    else:
        if parent_type is None:
            _logger.info('WLSDPLY-09608', type_name, folder_name, class_name=class_name, method_name=method_name)
        elif parent_name is None:
            _logger.info('WLSDPLY-09609', type_name, folder_name, parent_type, class_name=class_name,
                         method_name=method_name)
        else:
            _logger.info('WLSDPLY-09610', type_name, folder_name, parent_type, parent_name,
                         class_name=class_name, method_name=method_name)

