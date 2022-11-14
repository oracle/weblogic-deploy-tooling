"""
Copyright (c) 2020, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.targets import model_crd_helper
from wlsdeploy.tool.util.targets import schema_helper
from wlsdeploy.tool.modelhelp import model_help_utils
from wlsdeploy.tool.modelhelp.model_help_utils import ControlOptions
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.exit_code import ExitCode


class ModelKubernetesPrinter(object):
    """
    Class for printing kubernetes sections as model samples.
    """
    _class_name = "ModelKubernetesPrinter"
    _logger = PlatformLogger('wlsdeploy.modelhelp')

    def __init__(self, model_context):
        self._crd_helper = model_crd_helper.get_helper(model_context)

    def print_model_sample(self, model_path_tokens, control_option):
        """
        Prints out a model sample for the given model path tokens.
        :param model_path_tokens: a list of folder tokens indicating a model location
        :param control_option: a command-line switch that controls what is output
        :raises CLAException: if a problem is encountered
        """
        section_name = model_path_tokens[0]

        if len(model_path_tokens) == 1:
            self._print_model_section_sample(section_name, control_option)
        else:
            self._print_model_folder_sample(section_name, model_path_tokens, control_option)

    def _print_model_section_sample(self, section_name, control_option):
        """
        Prints a model sample for a section of a model, when just the section_name[:] is provided
        :param section_name: the name of the model section
        :param control_option: A command-line switch that controls what is output to STDOUT
        """
        print("")
        path = section_name + ":"
        _print_indent(path, 0)

        # examine model folders directly under kubernetes

        for crd_folder in self._crd_helper.get_crd_folders():
            folder_path = path
            show_children = True
            indent = 1

            if crd_folder.has_model_key():
                if control_option != ControlOptions.RECURSIVE:
                    print("")

                model_key = crd_folder.get_model_key()
                _print_indent(model_key + ':', indent)
                show_children = control_option == ControlOptions.RECURSIVE
                folder_path = path + '/' + model_key
                indent = indent + 1

            if show_children:
                schema = crd_folder.get_schema()
                in_array = crd_folder.is_array()

                if model_help_utils.show_attributes(control_option):
                    in_array = self._print_attributes_sample(schema, indent, in_array)

                if model_help_utils.show_folders(control_option):
                    self._print_subfolders_sample(schema, control_option, indent, folder_path, in_array)
            else:
                _print_indent("# see " + folder_path, indent)

    def _print_model_folder_sample(self, section_name, model_path_tokens, control_option):
        """
        Prints a model sample for a folder in a model, when more than just the section_name[:] is provided.
        :param section_name: the name of the model section
        :param model_path_tokens: a Python list of path elements built from model path
        :param control_option: A command-line switch that controls what is output to STDOUT
        """
        _method_name = '_print_model_folder_sample'

        print("")

        # write the parent folders leading up to the specified folder.
        # include any name folders.

        indent = 0
        _print_indent(section_name + ":", indent)
        indent += 1

        in_object_array = False
        model_path = section_name + ":"
        token_index = 1

        # resolve model folders directly under kubernetes

        crd_folder = self._crd_helper.get_keyless_crd_folder()
        if not crd_folder:
            first_token = model_path_tokens[token_index]
            crd_folder = self._crd_helper.get_crd_folder(first_token)
            if not crd_folder:
                ex = exception_helper.create_cla_exception(
                    ExitCode.ARG_VALIDATION_ERROR, "WLSDPLY-10111", model_path, first_token,
                    ', '.join(self._crd_helper.get_crd_folder_keys()))
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            model_key = crd_folder.get_model_key()
            _print_indent(model_key + ":", indent, in_object_array)
            model_path += '/' + model_key
            token_index += 1
            indent += 1

        schema = crd_folder.get_schema()

        # process elements inside kubernetes sub-folders

        current_folder = schema
        for token in model_path_tokens[token_index:]:
            properties = _get_properties(current_folder)

            valid_subfolder_keys = _get_folder_names(properties)
            if token not in valid_subfolder_keys:
                ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                           "WLSDPLY-10111", model_path, token,
                                                           ', '.join(valid_subfolder_keys))
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            current_folder = properties[token]

            _print_indent(token + ":", indent, in_object_array)
            indent += 1

            # apply to the next folder in the path
            in_object_array = schema_helper.is_object_array(current_folder)
            model_path = model_path + "/" + token

        # list the attributes and folders, as specified

        if model_help_utils.show_attributes(control_option):
            # Print the attributes associated with schema folder
            in_object_array = self._print_attributes_sample(current_folder, indent, in_object_array)

        if model_help_utils.show_folders(control_option):
            self._print_subfolders_sample(current_folder, control_option, indent, model_path, in_object_array)

    def _print_subfolders_sample(self, schema_folder, control_option, indent_level, path, in_object_array):
        """
        Prints a model sample section for the folders in a model location.
        :param schema_folder: the schema folder being printed
        :param control_option: a command-line switch that controls what is output to STDOUT
        :param indent_level: the level to indent by, before printing output
        :param path: indicates path to request for child folder help
        :param in_object_array: if True, a hyphen is printed before the first attribute
        """
        folder_info = _get_properties(schema_folder)
        folder_map = dict()
        object_array_keys = []

        for key in folder_info:
            property_map = folder_info[key]

            if property_map is not None:
                if schema_helper.is_single_object(property_map):
                    folder_map[key] = property_map

                elif schema_helper.is_object_array(property_map):
                    folder_map[key] = schema_helper.get_array_item_info(property_map)
                    object_array_keys.append(key)

        folder_keys = list(folder_map.keys())
        folder_keys.sort()

        for key in folder_keys:
            folder_info = folder_map[key]

            if control_option != ControlOptions.RECURSIVE:
                print("")

            _print_indent(key + ":", indent_level, in_object_array)
            in_object_array = False

            child_level = indent_level + 1

            next_path = path + "/" + key
            if control_option == ControlOptions.RECURSIVE:
                # Call this method recursively
                child_in_object_array = key in object_array_keys
                self._print_subfolders_sample(folder_info, control_option, child_level, path,
                                              child_in_object_array)
            else:
                _print_indent("# see " + next_path, child_level)

        return in_object_array

    def _print_attributes_sample(self, schema_folder, indent_level, in_object_array):
        """
        Prints a model sample for the attributes in a model location
        :param schema_folder: the schema folder to be printed
        :param indent_level: the level of indentation for this folder
        :param in_object_array: if True, a hyphen is printed before the first attribute
        :return: value of in_object_array, or False if an attribute was printed with a hyphen
        """
        attribute_map = dict()
        properties = _get_properties(schema_folder)

        for key in properties:
            property_map = properties[key]
            if property_map is not None:
                if schema_helper.is_simple_map(property_map):
                    # map of key / value pairs
                    attribute_map[key] = 'properties'

                elif schema_helper.is_simple_array(property_map):
                    # array of simple type
                    attribute_map[key] = 'list of ' + schema_helper.get_array_element_type(property_map)

                elif not schema_helper.is_object_type(property_map):
                    type_text = schema_helper.get_type(property_map)
                    enum_values = schema_helper.get_enum_values(property_map)
                    if enum_values:
                        type_text += ' (' + ', '.join(enum_values) + ')'
                    attribute_map[key] = type_text

        if attribute_map:
            attr_list = attribute_map.keys()
            attr_list.sort()

            maxlen = 0
            for name in attr_list:
                if len(name) > maxlen:
                    maxlen = len(name)

            format_string = '%-' + str_helper.to_string(maxlen + 1) + 's # %s'
            for attr_name in attr_list:
                line = format_string % (attr_name + ":", attribute_map[attr_name])
                _print_indent(line, indent_level, in_object_array)
                in_object_array = False
        else:
            _print_indent("# no attributes", indent_level)

        return in_object_array


def _get_properties(schema_folder):
    # in array elements, the properties are under "items"
    if schema_helper.is_object_array(schema_folder):
        item_info = schema_helper.get_array_item_info(schema_folder)
        return schema_helper.get_properties(item_info)
    else:
        return schema_helper.get_properties(schema_folder)


def _get_folder_names(schema_properties):
    """
    Return the object keys (single or array) described by the schema properties.
    :param schema_properties: the properties to be examined
    :return: a list of folder names
    """
    folder_names = []
    for key in schema_properties:
        property_map = schema_properties[key]
        if property_map is not None:
            if schema_helper.is_object_type(property_map):
                folder_names.append(key)
    return folder_names


def _print_indent(msg, level=1, first_in_list_object=False):
    """
    Print a message at the specified indent level.
    :param msg: the message to be printed
    :param level: the indent level
    :param first_in_list_object: True if this is the first property of an object in a list
    """
    result = ''
    i = 0
    while i < level:
        result += '    '
        i += 1

    if first_in_list_object:
        result = result[:-2] + "- "

    print('%s%s' % (result, msg))
