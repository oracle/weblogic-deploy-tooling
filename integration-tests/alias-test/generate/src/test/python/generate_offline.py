"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import copy
import os
import sys
import traceback

import java.lang.System as System
import java.util.logging.Level as Level

pathname = os.path.join(os.environ['TEST_HOME'], 'python')
sys.path.append(pathname)
pathname = os.path.join(os.environ['WLSDEPLOY_HOME'], 'lib', 'python')
sys.path.append(pathname)

sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))
print 'WLSDEPLOY_HOME=', sys.path

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.aliases.wlst_modes import WlstModes

import aliastest.generate.generator_wlst as generator_wlst
import aliastest.generate.utils as generator_utils
from aliastest.generate.generator_offline import OfflineGenerator

__logger = PlatformLogger('test.aliases.generate.offline')
__logger.set_level(Level.FINEST)
CLASS_NAME = 'generate_offline'


def generate_offline(model_context, sc_provider_dict, online_dictionary):
    _method_name = 'generate_offline'
    __logger.entering(model_context, class_name=CLASS_NAME, method_name=_method_name)

    online_dictionary_copy = copy.deepcopy(online_dictionary)
    __logger.info('Generate offline dictionary', class_name=CLASS_NAME, method_name=_method_name)
    offline_dictionary = OfflineGenerator(model_context, sc_provider_dict, online_dictionary_copy).generate()

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)
    return offline_dictionary


def main(args):
    _method_name = 'main'
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)

    generator_wlst.wlst_functions = globals()
    generate_args = generator_utils.get_generate_args_map(args)
    offline_model_context = generator_utils.get_model_context('generate_offline', WlstModes.OFFLINE, generate_args)

    system_exit = 0
    try:
        generator_wlst.wlst_silence()
        sc_provider_dict = generator_utils.load_sc_provider_dict(offline_model_context)
        online_dict = generator_utils.load_online_dict(offline_model_context)
        offline_dictionary = generate_offline(offline_model_context, sc_provider_dict, online_dict)
        if len(offline_dictionary) == 0:
            __logger.severe('Nothing generated for offline', class_name=CLASS_NAME, method_name=_method_name)
            system_exit = 1
        else:
            result = generator_utils.persist_file(offline_model_context, offline_dictionary, 'Offline')
            __logger.info('Offline generated and saved to {0}', result,
                          class_name=CLASS_NAME, method_name=_method_name)
    except:
        __logger.severe('Unhandled exception occurred', class_name=CLASS_NAME, method_name=_method_name)
        print dir(traceback)
        traceback.print_exc()
        system_exit = 1

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=system_exit)
    System.exit(system_exit)


if __name__ == 'main' or __name__ == '__main__':
    main(sys.argv)
