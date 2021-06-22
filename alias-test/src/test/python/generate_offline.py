"""
Copyright (c) 2020, 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import copy
import os
import sys

import java.lang.System as System
import java.util.logging.Level as Level
import java.util.logging.Logger as Logger

pathname = os.path.join(os.environ['TEST_HOME'], 'python')
sys.path.append(pathname)
pathname = os.path.join(os.environ['WLSDEPLOY_HOME'], 'lib', 'python')
sys.path.append(pathname)

sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))
print 'WLSDEPLOY_HOME=', sys.path

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.aliases.wlst_modes import WlstModes

import aliastest.generate.generator_wlst as generator_wlst
import aliastest.generate.generator_helper as generator_helper
import aliastest.generate.generator_security_configuration as generator_security_configuration
import aliastest.util.all_utils as all_utils
from aliastest.generate.generator_offline import OfflineGenerator

# __handlers = __logger.getHandlers()
__logger = PlatformLogger('test.aliases', resource_bundle_name='aliastest_rb')
__logger.set_level(Level.FINEST)
CLASS_NAME = 'generate_offline'
domain_home = os.environ['DOMAIN_HOME']

generator_wlst.wlst_functions = globals()
generator_wlst.wlst_silence()


def get_dictionary():
    _method_name = 'get_dictionary'
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)
    dictionary = \
        all_utils.get_dictionary_from_json_file(all_utils.filename(generator_helper.filename(),
                                                                   WlstModes.from_value(WlstModes.ONLINE),
                                                                   generator_wlst.wls_version().replace('.', '')))
    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=len(dictionary))
    return dictionary


def load_provider_map():
    _method_name = 'load_provider_map'
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)
    dictionary = \
        all_utils.get_dictionary_from_json_file(all_utils.filename(generator_helper.filename(),
                                                                   'SC',
                                                                   generator_wlst.wls_version().replace('.', '')))
    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=len(dictionary))
    return dictionary


def persist_file(model_context, dictionary):
    _method_name = 'persist_file'
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)
    filename = all_utils.filename(generator_helper.filename(), all_utils.str_mode(model_context),
                                  generator_wlst.wls_version().replace('.', ''))
    __logger.info('WLSDPLYST-01001', all_utils.str_mode(model_context), filename, class_name=CLASS_NAME,
                  method_name=_method_name)
    all_utils.create_json_file(dictionary, filename)
    __logger.exiting(result=filename, class_name=CLASS_NAME, method_name=_method_name)
    return filename


def generate_offline(model_context, online_dictionary):
    _method_name = 'generate_offline'
    __logger.entering(model_context, class_name=CLASS_NAME, method_name=_method_name)
    online_dictionary_copy = copy.deepcopy(online_dictionary)
    __logger.info('WLSDPLYST-01000', all_utils.str_mode(model_context), class_name=CLASS_NAME, method_name=_method_name)
    offline_dictionary = OfflineGenerator(model_context, online_dictionary_copy).generate()
    persist_file(model_context, offline_dictionary)
    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)
    return offline_dictionary


def main(args):
    import traceback
    _method_name = 'main'
    generator_wlst.wlst_functions = globals()
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)
    system_exit = 0
    kwargs = all_utils.kwargs_map(args)
    all_utils.populate_test_files_location(kwargs)
    # all_utils.setup_logger_overrides(__logger)
    all_utils.set_domain_home_arg(kwargs, domain_home)
    offline_model_context = all_utils.populate_model_context('generate_offline', WlstModes.OFFLINE, kwargs)
    try:
        generator_wlst.wlst_silence()
        generator_security_configuration.providers_map = load_provider_map()
        offline_dictionary = generate_offline(offline_model_context, get_dictionary())
        if len(offline_dictionary) == 0:
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
