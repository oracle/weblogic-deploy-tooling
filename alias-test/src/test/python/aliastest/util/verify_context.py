"""
Copyright (c) 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.util.cla_utils import CommandLineArgUtil

class VerifyContext(object):

    def __init__(self, program_name, arg_map):
        """
        Create a new context to hold the runtime information for the verify step.
        :param program_name: the program name, used for logging
        :param arg_map: all the arguments passed to the tool
        """
        self._program_name = program_name
        self._wl_version = None
        self._wlst_mode = None
        self.__copy_from_args(arg_map)

        return

    def __copy_from_args(self, arg_map):

        if '-wls_version' in arg_map:
            self._wl_version = arg_map['-wls_version']

        if CommandLineArgUtil.TARGET_MODE_SWITCH in arg_map:
            wlst_mode_string = arg_map[CommandLineArgUtil.TARGET_MODE_SWITCH]
            if type(wlst_mode_string) == int:
                self._wlst_mode = wlst_mode_string
            else:
                if wlst_mode_string.lower() == 'online':
                    self._wlst_mode = WlstModes.ONLINE
                else:
                    self._wlst_mode = WlstModes.OFFLINE

    def get_target_wls_version(self):
        """
        Get the target WebLogic version.
        :return: the target WebLogic version
        """
        return self._wl_version

    def get_target_wlst_mode(self):
        """
        Get the target WLST mode.
        :return: the target WLST mode
        """
        return self._wlst_mode

    def replace_token_string(self, string_value):
        return string_value

    def tokenize_path(self, path):
        return path

    def is_using_encryption(self):
        return False