"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
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
print sys.path

from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger

import aliastest.generate.generator_wlst as generator_wlst
import aliastest.generate.utils as generator_utils
from aliastest.generate.generator_online import OnlineGenerator

__logger = PlatformLogger('test.aliases.generate.online')
__logger.set_level(Level.FINEST)
CLASS_NAME = 'generate_online'


def generate_online(model_context, sc_provider_dict):
    """
    Generate the online dictionary describing all the MBeans and MBean attributes for the WebLogic Server version.
    :param model_context: the model context
    :param sc_provider_dict: the security provider dictionary
    :return: generated online dictionary
    """
    _method_name = 'generate_online'
    __logger.entering(model_context, class_name=CLASS_NAME, method_name=_method_name)

    __logger.info('Generate online dictionary', class_name=CLASS_NAME,
                  method_name=_method_name)
    online_dictionary = OnlineGenerator(model_context, sc_provider_dict).generate()

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)
    return online_dictionary


def main(args):
    """
    Entry point for generate_online
    :param args: kwargs from the command line
    """
    _method_name = 'main'

    generator_wlst.wlst_functions = globals()
    generate_args = generator_utils.get_generate_args_map(args)
    online_model_context = generator_utils.get_model_context('generate_sc', WlstModes.ONLINE, generate_args)

    admin_url = online_model_context.get_admin_url()
    admin_user = online_model_context.get_admin_user()
    admin_pass = online_model_context.get_admin_password()

    system_exit = 0
    connected = False
    try:
        generator_wlst.connect(admin_user, admin_pass, admin_url)
        connected = True
        generator_wlst.wlst_silence()
        sc_provider_dict = generator_utils.load_sc_provider_dict(online_model_context)
        online_dictionary = generate_online(online_model_context, sc_provider_dict)
        if len(online_dictionary) == 0:
            __logger.severe('Nothing generated for online',
                            class_name=CLASS_NAME, method_name=_method_name)
            system_exit = 1
        else:
            result = generator_utils.persist_file(online_model_context, online_dictionary, 'Online')
            __logger.info('Online generated and saved to {0}', result,
                          class_name=CLASS_NAME, method_name=_method_name)
    except:
        __logger.severe('Unhandled exception occurred', class_name=CLASS_NAME, method_name=_method_name)
        print(dir(traceback))
        traceback.print_exc()
        system_exit = 1

    if connected:
        generator_wlst.disconnect()

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)
    System.exit(system_exit)


if __name__ == 'main' or __name__ == '__main__':
    main(sys.argv)
