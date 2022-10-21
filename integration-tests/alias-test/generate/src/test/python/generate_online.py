"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import sys
import traceback

import java.lang.System as System
import java.util.logging.Level as Level
import oracle.weblogic.deploy.json.JsonException as JJsonException

pathname = os.path.join(os.environ['TEST_HOME'], 'python')
sys.path.append(pathname)
pathname = os.path.join(os.environ['WLSDEPLOY_HOME'], 'lib', 'python')
sys.path.append(pathname)

sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))
print sys.path

from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.json.json_translator import JsonToPython
from wlsdeploy.json.json_translator import PythonToJson
from wlsdeploy.logging.platform_logger import PlatformLogger

import aliastest.generate.generator_wlst as generator_wlst
import aliastest.generate.utils as generator_utils
from aliastest.generate.generator_online import OnlineGenerator

__logger = PlatformLogger('test.aliases.generate.online')
__logger.set_level(Level.FINEST)
CLASS_NAME = 'generate_online'


def persist_file(model_context, dictionary):
    """
    Persist the generated online dictionary to the test files location and generated file name.
    :param model_context: containing the test files location
    :param dictionary: generated dictionary
    :return: File name for persisted dictionary
    """
    _method_name = 'persist_file'
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)

    output_file = generator_utils.get_output_file_name(model_context, 'online')
    __logger.info('Persist generated online dictionary to {0}', output_file,
                  class_name=CLASS_NAME, method_name=_method_name)
    try:
        json_writer = PythonToJson(dictionary)
        json_writer.write_to_json_file(output_file)
    except JJsonException, ex:
        __logger.severe('Failed to write online data to {0}: {1}', output_file, ex.getMessage(),
                        error=ex, class_name=CLASS_NAME, method_name=_method_name)
        raise ex

    __logger.exiting(result=output_file, class_name=CLASS_NAME, method_name=_method_name)
    return output_file


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


def load_sc_provider_dict(model_context):
    _method_name = 'load_sc_provider_dict'
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)

    sc_file_name = generator_utils.get_output_file_name(model_context, 'SC')
    try:
        json_reader = JsonToPython(sc_file_name)
        dictionary = json_reader.parse()
    except JJsonException, ex:
        __logger.severe('Failed to read security configuration from {0}: {1}', sc_file_name, ex.getMessage(),
                        error=ex, class_name=CLASS_NAME, method_name=_method_name)
        raise ex

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=len(dictionary))
    return dictionary


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
        sc_provider_dict = load_sc_provider_dict(online_model_context)
        online_dictionary = generate_online(online_model_context, sc_provider_dict)
        if len(online_dictionary) == 0:
            __logger.severe('Nothing generated for security configuration',
                            class_name=CLASS_NAME, method_name=_method_name)
            system_exit = 1
        else:
            result = persist_file(online_model_context, online_dictionary)
            __logger.info('Security configuration generated and saved to {0}', result,
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
