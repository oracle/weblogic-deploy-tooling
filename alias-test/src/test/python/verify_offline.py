"""
Copyright (c) 2020, 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import sys
import java.lang.StackOverflowError as StackOverflowError
import java.util.logging.Level as Level

pathname = os.path.join(os.environ['TEST_HOME'], 'python')
sys.path.append(pathname)
pathname = os.path.join(os.environ['WLSDEPLOY_HOME'], 'lib', 'python')
sys.path.append(pathname)
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.aliases.wlst_modes import WlstModes

import aliastest.util.all_utils as all_utils
from aliastest.verify.verifier import Verifier


__logger = PlatformLogger('test.aliases', resource_bundle_name='aliastest_rb')
__logger.set_level(Level.FINEST)
CLASS_NAME = 'verify_offline'


def get_dictionary(model_context):
    _method_name = 'get_dictionary'
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)
    dictionary = all_utils.get_dictionary_from_json_file(
        all_utils.filename(all_utils.generated_filename(), WlstModes.from_value(model_context.get_target_wlst_mode()),
            model_context.get_target_wls_version().replace('.', '')))
    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)
    return dictionary


def verify_offline_dictionary(model_context):
    _method_name = 'verify_offline_dictionary'
    __logger.entering(model_context, class_name=CLASS_NAME, method_name=_method_name)
    mode = all_utils.str_mode(model_context)
    __logger.info('WLSDPLYST-01002', mode, class_name=CLASS_NAME, method_name=_method_name)
    offline_dictionary = get_dictionary(model_context)
    errs, warn = Verifier(model_context, offline_dictionary).verify()
    log_status(mode, _method_name, errs, warn)
    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)


def log_status(mode, method_name, errs, warn):
    success = True
    if errs > 0:
        success = False
        __logger.info('WLSDPLYST-01004', mode, errs, class_name=CLASS_NAME, method_name=method_name)
    if warn > 0:
        success = False
        __logger.info('WLSDPLYST-01005', mode, warn, class_name=CLASS_NAME, method_name=method_name)
    if success:
        __logger.info('WLSDPLYST-01006', mode, class_name=CLASS_NAME, method_name=method_name)


def main(args):
    _method_name = 'main'
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)
    kwargs = all_utils.kwargs_map(args)
    all_utils.populate_test_files_location(kwargs)
    offline_model_context = all_utils.populate_model_context('verify_offline', WlstModes.OFFLINE, kwargs)
    try:
        verify_offline_dictionary(offline_model_context)
    except StackOverflowError:
        __logger.severe('WLSDPLYST-01010')
    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)


if __name__ == 'main' or __name__ == '__main__':
    main(sys.argv)
