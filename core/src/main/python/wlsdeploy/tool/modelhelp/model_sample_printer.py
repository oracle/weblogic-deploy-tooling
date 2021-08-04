"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import KNOWN_TOPLEVEL_MODEL_SECTIONS
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.tool.modelhelp import model_help_utils
from wlsdeploy.tool.modelhelp.model_help_utils import ControlOptions
from wlsdeploy.exception import exception_helper

_class_name = "ModelSamplePrinter"


class ModelSamplePrinter(object):
    """
    Class for printing the recognized model metadata as a model sample.
    """

    def __init__(self, aliases, logger):
        """
        :param aliases: A reference to an Aliases class instance
        :param logger: A reference to the platform logger to write to, if a log entry needs to be made
        """
        self._logger = logger
        self._aliases = aliases

    def print_model_sample(self, model_path_tokens, control_option):
        """
        Prints out a model sample for the given model path tokens.
        :param model_path_tokens: a list of folder tokens indicating a model location
        :param control_option: a command-line switch that controls what is output
        :raises CLAException: if a problem is encountered
        """
        section_name = model_path_tokens[0]
        valid_section_folder_keys = self._aliases.get_model_section_top_level_folder_names(section_name)

        if model_path_tokens[0] == 'top':
            self._print_model_top_level_sample()
        elif len(model_path_tokens) == 1:
            self._print_model_section_sample(section_name, valid_section_folder_keys, control_option)
        else:
            self._print_model_folder_sample(model_path_tokens, valid_section_folder_keys, control_option)

    def _print_model_top_level_sample(self):
        """
        Prints a model sample with all the the valid section names.
        The -recursive flag is disregarded for this case.
        """
        _method_name = '_print_model_top_level_sample'

        for section in KNOWN_TOPLEVEL_MODEL_SECTIONS:
            print
            _print_indent(section + ":", 0)
            _print_indent("# see " + section + ":", 1)

    def _print_model_section_sample(self, section_name, valid_section_folder_keys, control_option):
        """
        Prints a model sample for a section of a model, when just the section_name[:] is provided
        :param section_name: the name of the model section
        :param valid_section_folder_keys: list of the valid top folders in the specified section
        :param control_option: A command-line switch that controls what is output to STDOUT
        """
        _method_name = '_print_model_section_sample'

        print
        _print_indent(section_name + ":", 0)

        if model_help_utils.show_attributes(control_option):
            attributes_location = self._aliases.get_model_section_attribute_location(section_name)
            if attributes_location is not None:
                self._print_attributes_sample(attributes_location, 1)

        if model_help_utils.show_folders(control_option):
            model_location = LocationContext()
            valid_section_folder_keys.sort()
            self._print_subfolder_keys_sample(model_location, valid_section_folder_keys, control_option, 1)

    def _print_model_folder_sample(self, model_path_tokens, valid_section_folder_keys, control_option):
        """
        Prints a model sample for a folder in a model, when more than just the section_name[:] is provided.
        :param model_path_tokens: a Python list of path elements built from model path
        :param valid_section_folder_keys: A list of valid folder names for the model section in the path
        :param control_option: A command-line switch that controls what is output to STDOUT
        """
        _method_name = '_print_model_folder_sample'

        section_name = model_path_tokens[0]
        top_folder = model_path_tokens[1]
        if top_folder not in valid_section_folder_keys:
            ex = exception_helper.create_cla_exception('WLSDPLY-10110', section_name + ':', top_folder,
                                                       ', '.join(valid_section_folder_keys))
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        print("")

        # write the parent folders, with indentation and any name folders included

        indent = 0
        model_location = LocationContext()
        for token in model_path_tokens:
            last_location = LocationContext(model_location)

            if indent > 0:
                code, message = self._aliases.is_valid_model_folder_name(model_location, token)
                if code != ValidationCodes.VALID:
                    ex = exception_helper.create_cla_exception("WLSDPLY-05027", message)
                    self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                    raise ex
                model_location.append_location(token)

            if self._aliases.is_artificial_type_folder(model_location):
                name = self._get_member_name(last_location, 0)
                _print_indent(name + ":", indent)
                indent += 1

            _print_indent(token + ":", indent)
            indent += 1

            if self._has_multiple_folders(model_location):
                name = self._get_member_name(model_location, 0)
                _print_indent(name + ":", indent)
                indent += 1

        # list the attributes and folders, as specified

        if model_help_utils.show_attributes(control_option):
            # Print the attributes associated with location context
            self._print_attributes_sample(model_location, indent)

        if model_help_utils.show_folders(control_option):
            self._print_subfolders_sample(model_location, control_option, indent)

        return

    def _print_subfolders_sample(self, model_location, control_option, indent_level):
        """
        Prints a model sample section for the folders in a model location.
        The subfolder keys are derived from the model location using aliases.
        :param model_location: the model location being worked on
        :param control_option: a command-line switch that controls what is output to STDOUT
        :param indent_level: the level to indent by, before printing output
        """
        _method_name = '_print_subfolders_sample'

        valid_subfolder_keys = self._aliases.get_model_subfolder_names(model_location)

        valid_subfolder_keys.sort()
        self._print_subfolder_keys_sample(model_location, valid_subfolder_keys, control_option, indent_level)

    def _print_subfolder_keys_sample(self, model_location, subfolder_keys, control_option, indent_level):
        """
        Prints a model sample for the specified subfolder keys at the specified location.
        :param model_location: the model location being worked on
        :param subfolder_keys: the keys of the sub-folders at the location
        :param control_option: a command-line switch that controls what is output to STDOUT
        :param indent_level: the level to indent by, before printing output
        """
        _method_name = '_print_subfolder_keys_sample'

        artificial_index = 0
        parent_location = LocationContext(model_location)

        for key in subfolder_keys:
            model_location.append_location(key)

            # folder may not be valid for WLS version
            if self._aliases.get_wlst_mbean_type(model_location) is None:
                model_location.pop_location()
                continue

            name_token = self._aliases.get_name_token(model_location)
            if name_token is not None:
                model_location.add_name_token(name_token, '%s-0' % key)

            if control_option != ControlOptions.RECURSIVE:
                print("")

            key_level = indent_level
            if self._aliases.is_artificial_type_folder(model_location):
                name = self._get_member_name(parent_location, artificial_index)
                artificial_index += 1
                _print_indent(name + ":", indent_level)
                key_level += 1

            _print_indent(key + ":", key_level)

            child_level = key_level
            if self._has_multiple_folders(model_location):
                name = self._get_member_name(model_location, 0)
                child_level += 1
                _print_indent(name + ":", child_level)

            if control_option == ControlOptions.RECURSIVE:
                # Call this method recursively
                self._print_subfolders_sample(model_location, control_option, child_level + 1)
            else:
                _print_indent("# see " + model_location.get_folder_path(), child_level + 1)

            model_location.pop_location()

    def _print_attributes_sample(self, model_location, indent_level):
        """
        Prints a model sample for the attributes in a model location
        :param model_location: An object containing data about the model location being worked on
        :param indent_level: The level to indent by, before printing output
        """
        _method_name = '_print_attributes_sample'

        attr_infos = self._aliases.get_model_attribute_names_and_types(model_location)

        if attr_infos:
            attr_list = attr_infos.keys()
            attr_list.sort()

            maxlen = 0
            for name in attr_list:
                if len(name) > maxlen:
                    maxlen = len(name)

            format_string = '%-' + str(maxlen + 1) + 's # %s'
            for attr_name in attr_list:
                line = format_string % (attr_name + ":", attr_infos[attr_name])
                _print_indent(line, indent_level)
        else:
            _print_indent("# no attributes", indent_level)

    def _has_multiple_folders(self, location):
        """
        Determine if the specified location has multiple named children.
        :param location: the location to be checked
        :return: True if the location has multiple children
        """
        # check this first to avoid errors on subsequent checks
        if self._aliases.is_artificial_type_folder(location):
            return False

        return self._aliases.supports_multiple_mbean_instances(location)

    def _get_member_name(self, location, index):
        """
        Return a name to be used for member of a model folder with multiple values.
        :param location: the location of the folder
        :param index: the index of the member in the folder
        :return: the member name
        """
        short_name = self._aliases.get_folder_short_name(location)
        if len(short_name) == 0:
            short_name = location.get_current_model_folder()
        return "'" + short_name + "-" + str(index + 1) + "'"


def _print_indent(msg, level=1):
    """
    Print a message at the specified indent level.
    :param msg: the message to be printed
    :param level: the indent level
    """
    result = ''
    i = 0
    while i < level:
        result += '    '
        i += 1
    print '%s%s' % (result, msg)
