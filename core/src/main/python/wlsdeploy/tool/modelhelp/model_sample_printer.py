"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import KNOWN_TOPLEVEL_MODEL_SECTIONS
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.tool.modelhelp import model_help_utils
from wlsdeploy.tool.modelhelp.model_help_utils import ControlOptions
from wlsdeploy.exception import exception_helper
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.exit_code import ExitCode

from oracle.weblogic.deploy.util import WLSBeanHelp as WLSBeanHelp

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
        for section in KNOWN_TOPLEVEL_MODEL_SECTIONS:
            print("")
            _print_indent(section + ":", 0)
            _print_indent("# see " + section + ":", 1)

    def _print_model_section_sample(self, section_name, valid_section_folder_keys, control_option):
        """
        Prints a model sample for a section of a model, when just the section_name[:] is provided
        :param section_name: the name of the model section
        :param valid_section_folder_keys: list of the valid top folders in the specified section
        :param control_option: A command-line switch that controls what is output to STDOUT
        """
        print("")
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

        if model_path_tokens[1] not in valid_section_folder_keys:
            # print attribute help if top_folder turns out to be an attribute, throw otherwise
            self._print_section_attribute_bean_help(model_path_tokens, valid_section_folder_keys)
            return

        print("")

        # write the parent folders, with indentation and any name folders included

        indent = 0
        model_location = LocationContext()
        tokens_left = len(model_path_tokens)
        for token in model_path_tokens:
            tokens_left = tokens_left - 1
            last_location = LocationContext(model_location)

            if indent > 0:
                code, message = self._aliases.is_valid_model_folder_name(model_location, token)
                if code != ValidationCodes.VALID:
                    # print attribute help if the token turns out to be an attribute, throws otherwise
                    self._print_folder_attribute_bean_help(control_option, model_location,
                                                           indent, tokens_left, token, message)
                    return
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

        online_bean = self._aliases.get_online_bean_name(model_location)
        bean_help = WLSBeanHelp.get(online_bean, 60)
        if bean_help:
            print("")
            _print_indent(bean_help, 0)

    def _print_subfolders_sample(self, model_location, control_option, indent_level):
        """
        Prints a model sample section for the folders in a model location.
        The subfolder keys are derived from the model location using aliases.
        :param model_location: the model location being worked on
        :param control_option: a command-line switch that controls what is output to STDOUT
        :param indent_level: the level to indent by, before printing output
        """
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

    def _get_att_short_help(self, model_location, attr_name):
        """
        Gets short help for an attribute for appending after the att in a folder listing.
        :param model_location: An object containing data about the model location being worked on
        :param att_name: The attribute
        :return: the short help
        """
        att_default = self._aliases.get_model_attribute_default_value(model_location, attr_name)

        if att_default is None:
            att_default = ''
        else:
            att_default = ' (default=' + str_helper.to_string(att_default) + ')'

        online_bean = self._aliases.get_online_bean_name(model_location)

        # Instead of showing abbreviated help, use a trailing "+" to indicate
        # that more help is avail for the attribute, and a "-" otherwise
        if WLSBeanHelp.get(online_bean, attr_name, 100, ''):
            return att_default + ' +'
        else:
            return att_default + ' -'

    def _print_attributes_sample(self, model_location, indent_level):
        """
        Prints a model sample for the attributes in a model location
        :param model_location: An object containing data about the model location being worked on
        :param indent_level: The level to indent by, before printing output
        """
        attr_infos = self._aliases.get_model_attribute_names_and_types(model_location)

        if attr_infos:
            attr_list = attr_infos.keys()
            attr_list.sort()

            maxlen_attr = 0
            maxlen_type = 0
            for name in attr_list:
                if len(name) > maxlen_attr:
                    maxlen_attr = len(name)
                if len(attr_infos[name]) > maxlen_type:
                    maxlen_type = len(attr_infos[name])

            format_string = '%-' + str_helper.to_string(maxlen_attr + 1) + 's # %-' + \
                            str_helper.to_string(maxlen_type + 1) + 's'
            for attr_name in attr_list:
                att_help = self._get_att_short_help(model_location, attr_name)
                line = format_string % (attr_name + ":", attr_infos[attr_name]) + att_help
                _print_indent(line, indent_level)

        else:
            _print_indent("# no attributes", indent_level)

    def _print_section_attribute_bean_help(self, model_path_tokens, valid_section_folder_keys):
        """
        Print attribute help if path turns out to be an attribute of a section, throw otherwise
        :param model_path_tokens: a Python list of path elements built from model path
        :param valid_section_folder_keys: A list of valid folder names for the model section in the path
        """
        _method_name = '_print_section_attribute_bean_help'

        section_name = model_path_tokens[0]
        attribute = model_path_tokens[1]

        if len(model_path_tokens) == 2:
            attributes_location = self._aliases.get_model_section_attribute_location(section_name)
            if attributes_location is not None:
                if self._print_attribute_bean_help(attributes_location, 0, attribute):
                    return

        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                   'WLSDPLY-10110', section_name + ':', attribute,
                                                   ', '.join(valid_section_folder_keys))
        self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    def _print_folder_attribute_bean_help(self, control_option, model_location, indent, tokens_left, token, message):
        """
        Print attribute help if the token turns out to be an attribute, throw otherwise
        :param control_option: A command-line switch that controls what is output to STDOUT
        :param model_location: An object containing data about the model location being worked on
        :param indent: The level to indent by, before printing output
        :param tokens_left: Equal to 0 if this is the last token in proposed model path.
        :param token: The potential attribute name.
        :param message: Error message if token is not an attribute
        :param valid_section_folder_keys: A list of valid folder names for the model section in the path
        """
        _method_name = '_print_folder_attribute_bean_help'

        if tokens_left == 0 and model_help_utils.show_attributes(control_option) and \
                self._print_attribute_bean_help(model_location, indent, token):
            return

        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                   "WLSDPLY-05027", message)
        self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    def _print_attribute_bean_help(self, model_location, indent_level, the_attribute):
        """
        Checks if the the_attribute is an attribute of model_location, and if so prints its help
        :param model_location: An object containing data about the model location being worked on
        :param indent_level: The level to indent by, before printing output
        :param the_attribute: The attribute to print
        :return: True if the_attribute was an attribute
        """

        the_bean = self._aliases.get_online_bean_name(model_location)
        attr_infos = self._aliases.get_model_attribute_names_and_types(model_location)

        if attr_infos and the_attribute in attr_infos:
            line = '%s # %s' % (the_attribute + ":", attr_infos[the_attribute])
            _print_indent(line, indent_level)

            att_default = self._aliases.get_model_attribute_default_value(model_location, the_attribute)
            if att_default is not None:
                att_default = str_helper.to_string(att_default)

            att_help = WLSBeanHelp.get(the_bean, the_attribute, 60, att_default)

            if att_help:
                print("")
                print(att_help)
                print("")

            return True

        return False

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
        return "'%s-%s'" % (short_name, str_helper.to_string(index + 1))


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
    print('%s%s' % (result, msg))
