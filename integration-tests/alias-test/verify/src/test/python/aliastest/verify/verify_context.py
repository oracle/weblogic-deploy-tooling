"""
Copyright (c) 2021, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from aliastest.verify import constants

from wlsdeploy.aliases.wlst_modes import WlstModes


class VerifyModelContext(object):
    def __init__(self, program_name, wlst_mode, arg_map):
        """
        Create a new context to hold the runtime information for the verify step.
        :param program_name: the program name, used for logging
        :param arg_map: all the arguments passed to the tool
        """
        self._program_name = program_name
        self._wlst_mode = wlst_mode
        self._wl_version = None
        self._generated_dir = None
        self._output_dir = None

        self.__copy_from_args(arg_map)

    def __copy_from_args(self, arg_map):
        if constants.WLS_VERSION_SWITCH in arg_map:
            self._wl_version = arg_map[constants.WLS_VERSION_SWITCH]
        if constants.GENERATED_DIR_SWITCH in arg_map:
            self._generated_dir = arg_map[constants.GENERATED_DIR_SWITCH]
        if constants.OUTPUT_DIR_SWITCH in arg_map:
            self._output_dir = arg_map[constants.OUTPUT_DIR_SWITCH]

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

    def is_wlst_online(self):
        """
        Determine if the tool was started using WLST online mode
        :return: True if the tool is in online mode
        """
        return self._wlst_mode == WlstModes.ONLINE

    def is_wlst_offline(self):
        """
        Determine if the tool was started using WLST offline mode
        :return: True if the tool is in offline mode
        """
        return self._wlst_mode == WlstModes.OFFLINE

    def get_generated_dir(self):
        return self._generated_dir

    def get_output_dir(self):
        return self._output_dir

    #
    # Override methods
    #
    def replace_token_string(self, string_value):
        return string_value

    def tokenize_path(self, path):
        return path

    def tokenize_classpath(self, value):
        return value

    def is_using_encryption(self):
        return False
