"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.extract import wko_schema_helper
from wlsdeploy.tool.modelhelp import model_help_utils
from wlsdeploy.tool.modelhelp.model_help_utils import ControlOptions


class ModelKubernetesPrinter(object):
    """
    Class for printing kubernetes sections as model samples.
    """
    _class_name = "ModelKubernetesPrinter"
    _logger = PlatformLogger('wlsdeploy.modelhelp')

    def __init__(self):
        self._schema = wko_schema_helper.get_domain_resource_schema()

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
        _method_name = '_print_model_section_sample'

        print
        path = section_name + ":"
        _print_indent(path, 0)

        if model_help_utils.show_attributes(control_option):
            self._print_attributes_sample(self._schema, 1)

        if model_help_utils.show_folders(control_option):
            self._print_subfolders_sample(self._schema, control_option, 1, path)

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

        model_path = section_name + ":"
        current_folder = self._schema
        for token in model_path_tokens[1:]:
            properties = _get_properties(current_folder)

            valid_subfolder_keys = _get_folder_names(properties)
            if token not in valid_subfolder_keys:
                ex = exception_helper.create_cla_exception("WLSDPLY-10111", model_path, token,
                                                           ', '.join(valid_subfolder_keys))
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            current_folder = properties[token]

            _print_indent(token + ":", indent)
            indent += 1

            if wko_schema_helper.is_multiple_folder(current_folder):
                name = token + '-1'
                _print_indent(name + ":", indent)
                indent += 1

            model_path = model_path + "/" + token

        # list the attributes and folders, as specified

        if model_help_utils.show_attributes(control_option):
            # Print the attributes associated with schema folder
            self._print_attributes_sample(current_folder, indent)

        if model_help_utils.show_folders(control_option):
            self._print_subfolders_sample(current_folder, control_option, indent, model_path)

    def _print_subfolders_sample(self, schema_folder, control_option, indent_level, path):
        """
        Prints a model sample section for the folders in a model location.
        :param schema_folder: the schema folder being printed
        :param control_option: a command-line switch that controls what is output to STDOUT
        :param indent_level: the level to indent by, before printing output
        """
        _method_name = '_print_subfolders_sample'

        folder_info = _get_properties(schema_folder)
        folder_map = dict()
        multi_folders = []

        for key in folder_info:
            property_map = folder_info[key]

            if property_map is not None:
                if wko_schema_helper.is_single_folder(property_map):
                    folder_map[key] = property_map

                elif wko_schema_helper.is_multiple_folder(property_map):
                    folder_map[key] = wko_schema_helper.get_array_item_info(property_map)
                    multi_folders.append(key)

        folder_keys = list(folder_map.keys())
        folder_keys.sort()

        for key in folder_keys:
            folder_info = folder_map[key]

            if control_option != ControlOptions.RECURSIVE:
                print("")

            key_level = indent_level
            _print_indent(key + ":", key_level)

            child_level = key_level
            if key in multi_folders:
                name = key + "-1"
                child_level += 1
                _print_indent(name + ":", child_level)

            if control_option == ControlOptions.RECURSIVE:
                # Call this method recursively
                self._print_subfolders_sample(folder_info, control_option, child_level + 1, path)
            else:
                next_path = path + "/" + key
                _print_indent("# see " + next_path, child_level + 1)

    def _print_attributes_sample(self, schema_folder, indent_level):
        """
        Prints a model sample for the attributes in a model location
        :param schema_folder: the schema folder to be printed
        :param indent_level: the level of indentation for this folder
        """
        _method_name = '_print_attributes_sample'

        attribute_map = dict()
        properties = _get_properties(schema_folder)

        for key in properties:
            property_map = properties[key]
            if property_map is not None:
                if wko_schema_helper.is_simple_map(property_map):
                    # map of key / value pairs
                    attribute_map[key] = 'properties'

                elif wko_schema_helper.is_simple_array(property_map):
                    # array of simple type
                    attribute_map[key] = 'list of ' + wko_schema_helper.get_array_element_type(property_map)

                elif not wko_schema_helper.is_folder(property_map):
                    type_text = wko_schema_helper.get_type(property_map)
                    enum_values = wko_schema_helper.get_enum_values(property_map)
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

            format_string = '%-' + str(maxlen + 1) + 's # %s'
            for attr_name in attr_list:
                line = format_string % (attr_name + ":", attribute_map[attr_name])
                _print_indent(line, indent_level)
        else:
            _print_indent("# no attributes", indent_level)


def _get_properties(schema_folder):
    # in array elements, the properties are under "items"
    if wko_schema_helper.is_multiple_folder(schema_folder):
        return schema_folder['items']['properties']
    else:
        return schema_folder['properties']


def _get_folder_names(schema_properties):
    """
    Return the folder names (single and multiple) described by the schema properties.
    :param schema_properties: the properties to be examined
    :return: a list of folder names
    """
    folder_names = []
    for key in schema_properties:
        property_map = schema_properties[key]
        if property_map is not None:
            if wko_schema_helper.is_single_folder(property_map) or wko_schema_helper.is_multiple_folder(property_map):
                folder_names.append(key)
    return folder_names


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
