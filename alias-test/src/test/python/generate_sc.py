"""
Copyright (c) 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import sys

import java.lang.System as System
import java.util.logging.Level as Level

pathname = os.path.join(os.environ['TEST_HOME'], 'python')
sys.path.append(pathname)
pathname = os.path.join(os.environ['WLSDEPLOY_HOME'], 'lib', 'python')
sys.path.append(pathname)

sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))
print sys.path

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.aliases.wlst_modes import WlstModes

import aliastest.generate.generator_security_configuration as generator_security_configuration
import aliastest.generate.generator_wlst as generator_wlst
import aliastest.generate.generator_helper as generator_helper
import aliastest.util.all_utils as all_utils
from aliastest.generate.generator_online import OnlineGenerator


__logger = PlatformLogger('test.aliases.generate', resource_bundle_name='aliastest_rb')
__logger.set_level(Level.FINEST)
CLASS_NAME = 'generate_sc'


def persist_file(model_context, dictionary):
    """
    Persist the generated online dictionary to the test files location and generated file name.
    :param model_context: containing the test files location
    :param dictionary: generated dictionary
    :return: File name for persisted dictionary
    """
    _method_name = 'persist_file'
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)
    filename = all_utils.filename(generator_helper.filename(), 'SC',
                                  generator_wlst.wls_version().replace('.',''))
    __logger.info('WLSDPLYST-01001', all_utils.str_mode(model_context), filename, class_name=CLASS_NAME,
                  method_name=_method_name)
    all_utils.create_json_file(dictionary, filename)
    __logger.exiting(result=filename, class_name=CLASS_NAME, method_name=_method_name)
    return filename


def generate_sc(model_context):
    """
    Generate the online dictionary describing all the MBeans and MBean attributes for a specific weblogic
    version and WLST mode.
    :param model_context: contains the kwargs and other information
    :return: generated online dictionary
    """
    _method_name = 'generate_online'
    __logger.entering(model_context, class_name=CLASS_NAME, method_name=_method_name)
    online_dictionary = dict()
    __logger.info('WLSDPLYST-01000', all_utils.str_mode(model_context), class_name=CLASS_NAME,
                  method_name=_method_name)
    provider_map = generator_security_configuration.populate_security_types()
    persist_file(model_context, provider_map)
    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)
    return online_dictionary


def main(args):
    """
    Entry point for generate_online
    :param args: kwargs from the command line
    """
    import traceback
    _method_name = 'main'

    generator_wlst.wlst_functions = globals()
    generator_wlst.connect('weblogic', 'welcome1', 't3://localhost:7001')
    ls_list = generator_wlst.lsc()
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)
    system_exit = 0
    kwargs = all_utils.kwargs_map(args)
    all_utils.populate_test_files_location(kwargs)
    # all_utils.setup_logger_overrides(__logger)
    online_model_context = all_utils.populate_model_context('generate_online', WlstModes.ONLINE, kwargs)
    try:
        generator_wlst.wlst_silence()
        online_dictionary = generate_sc(online_model_context)
        generator_wlst.disconnect()
        if len(online_dictionary) == 0:
            __logger.severe('Nothing generated in online - ending with rc={0}', system_exit,
                            class_name=CLASS_NAME, method_name=_method_name)
            System.exit(1)
    except:
        __logger.severe('Unhandled exception occurred', system_exit,
                        class_name=CLASS_NAME, method_name=_method_name)
        print dir(traceback)
        traceback.print_exc()
        System.exit(2)

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)
    System.exit(0)


if __name__ == 'main' or __name__ == '__main__':
    main(sys.argv)
