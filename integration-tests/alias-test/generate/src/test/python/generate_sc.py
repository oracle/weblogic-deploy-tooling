"""
Copyright (c) 2021, 2022, Oracle Corporation and/or its affiliates.
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

import aliastest.generate.generator_security_configuration as generator_security_configuration
import aliastest.generate.generator_wlst as generator_wlst
import aliastest.generate.utils as generator_utils


__logger = PlatformLogger('test.aliases.generate.sc')
__logger.set_level(Level.FINEST)
CLASS_NAME = 'generate_sc'


def generate_sc(model_context):
    """
    Generate the online dictionary describing all the MBeans and MBean attributes for a specific weblogic
    version and WLST mode.
    :param model_context: contains the kwargs and other information
    :return: generated online dictionary
    """
    _method_name = 'generate_sc'
    __logger.entering(model_context, class_name=CLASS_NAME, method_name=_method_name)
    provider_map = generator_security_configuration.populate_security_types(model_context)
    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)
    return provider_map


def main(args):
    """
    Entry point for generate_online
    :param args: kwargs from the command line
    """
    _method_name = 'main'
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)

    generator_wlst.wlst_functions = globals()
    generate_args = generator_utils.get_generate_args_map(args)
    online_model_context = generator_utils.get_model_context('generate_sc', WlstModes.ONLINE, generate_args)

    admin_url = online_model_context.get_admin_url()
    admin_user = online_model_context.get_admin_user()
    admin_pass = online_model_context.get_admin_password()

    system_exit = 0
    connected = False
    # Jython 2.2.1 is brain-dead and only accepts try/except or try/finally so you do what you have to do...
    try:
        try:
            generator_wlst.connect(admin_user, admin_pass, admin_url)
            connected = True
            generator_wlst.wlst_silence()
            online_dictionary = generate_sc(online_model_context)
            if len(online_dictionary) == 0:
                __logger.severe('Nothing generated for security configuration',
                                class_name=CLASS_NAME, method_name=_method_name)
                system_exit = 1
            else:
                result = generator_utils.persist_file(online_model_context, online_dictionary, 'SC')
                __logger.info('Security configuration generated and saved to {0}', result,
                              class_name=CLASS_NAME, method_name=_method_name)
        except:
            __logger.severe('Unhandled exception occurred', class_name=CLASS_NAME, method_name=_method_name)
            print(dir(traceback))
            traceback.print_exc()
            system_exit = 1
    finally:
        if connected:
            generator_wlst.disconnect()

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)
    System.exit(system_exit)


if __name__ == 'main' or __name__ == '__main__':
    main(sys.argv)
