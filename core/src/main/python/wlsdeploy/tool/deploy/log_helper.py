"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

from wlsdeploy.logging.platform_logger import PlatformLogger

_logger = PlatformLogger('wlsdeploy.deploy')


def log_updating_folder(type_name, parent_type, parent_name, is_add, class_name, method_name):
    if is_add:
        if parent_type is None:
            _logger.info('WLSDPLY-09127', type_name, class_name=class_name, method_name=method_name)
        elif parent_name is None:
            _logger.info('WLSDPLY-09128', type_name, parent_type, class_name=class_name, method_name=method_name)
        else:
            _logger.info('WLSDPLY-09129', type_name, parent_type, parent_name, class_name=class_name,
                         method_name=method_name)
    else:
        if parent_type is None:
            _logger.info('WLSDPLY-09121', type_name, class_name=class_name, method_name=method_name)
        elif parent_name is None:
            _logger.info('WLSDPLY-09122', type_name, parent_type, class_name=class_name, method_name=method_name)
        else:
            _logger.info('WLSDPLY-09123', type_name, parent_type, parent_name, class_name=class_name,
                         method_name=method_name)


def log_updating_named_folder(type_name, folder_name, parent_type, parent_name, is_add, class_name, method_name):
    if is_add:
        if parent_type is None:
            _logger.info('WLSDPLY-09130', type_name, folder_name, class_name=class_name, method_name=method_name)
        elif parent_name is None:
            _logger.info('WLSDPLY-09131', type_name, folder_name, parent_type, class_name=class_name,
                         method_name=method_name)
        else:
            _logger.info('WLSDPLY-09132', type_name, folder_name, parent_type, parent_name,
                         class_name=class_name, method_name=method_name)
    else:
        if parent_type is None:
            _logger.info('WLSDPLY-09124', type_name, folder_name, class_name=class_name, method_name=method_name)
        elif parent_name is None:
            _logger.info('WLSDPLY-09125', type_name, folder_name, parent_type, class_name=class_name,
                                method_name=method_name)
        else:
            _logger.info('WLSDPLY-09126', type_name, folder_name, parent_type, parent_name,
                         class_name=class_name, method_name=method_name)

