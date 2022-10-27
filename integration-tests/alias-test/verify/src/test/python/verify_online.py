"""
Copyright (c) 2020, 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import sys
import traceback

import java.lang.Exception as JException
import java.lang.StackOverflowError as StackOverflowError
import java.lang.System as System
import java.util.logging.Level as Level

pathname = os.path.join(os.environ['TEST_HOME'], 'python')
sys.path.append(pathname)
pathname = os.path.join(os.environ['WLSDEPLOY_HOME'], 'lib', 'python')
sys.path.append(pathname)
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.aliases.wlst_modes import WlstModes

from aliastest.verify.verifier import Verifier
import aliastest.verify.utils as verify_utils


__logger = PlatformLogger('test.aliases.verify.online')
__logger.set_level(Level.FINEST)
CLASS_NAME = 'verify_online'


def verify_online_aliases(model_context, generated_online_dict):
    _method_name = 'verify_online_aliases'
    __logger.entering(model_context, class_name=CLASS_NAME, method_name=_method_name)

    __logger.info('Verify online aliases', class_name=CLASS_NAME, method_name=_method_name)
    verify_results = Verifier(model_context, generated_online_dict).verify()

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)
    return verify_results


def get_report_file_name(model_context):
    return os.path.join(model_context.get_output_dir(), verify_utils.get_report_file_name(model_context))


def main(args):
    _method_name = 'main'
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)

    verify_args_map = verify_utils.get_verify_args_map(args)
    online_model_context = verify_utils.get_model_context('verify_online', WlstModes.ONLINE, verify_args_map)

    try:
        generated_online_dictionary = verify_utils.load_generated_online_dict(online_model_context)
        verify_results = verify_online_aliases(online_model_context, generated_online_dictionary)
        verify_results.write_to_logger(__logger)
        verify_results.write_report_file(get_report_file_name(online_model_context))
        system_exit = verify_results.get_exit_code()
    except (StackOverflowError, Exception, JException), e:
        __logger.severe('Verifying the online aliases failed', error=e, class_name=CLASS_NAME, method_name=_method_name)
        print(dir(traceback))
        traceback.print_exc()
        system_exit = 1

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=system_exit)
    System.exit(system_exit)


if __name__ == 'main' or __name__ == '__main__':
    main(sys.argv)
