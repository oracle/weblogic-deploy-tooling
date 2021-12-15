"""
Copyright (c) 2020, 2021, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import unittest

from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.aliases.model_constants import KUBERNETES
from wlsdeploy.tool.extract import wko_schema_helper


class KubernetesSchemaTest(unittest.TestCase):
    _model_dir = '../../unit-tests/wko'
    _model_path = _model_dir + '/model.yaml'

    def setUp(self):
        self.schema_map = wko_schema_helper.get_domain_resource_schema()

        if not os.path.exists(self._model_dir):
            os.makedirs(self._model_dir)
        file_path = self._model_dir + "/model.yaml"
        self.out_file = open(file_path, "w")

    def tearDown(self):
        self.out_file.close()

    def testKubernetesSchema(self):
        # create a model with every element.
        # verify that there are no unknown types or structures.
        self._write_line(KUBERNETES + ":")
        self._write_folder(self.schema_map, False, "", "  ")

    def _write_folder(self, folder, is_multiple, path, indent):
        # for a multiple (object list) type, the first field is prefixed with a hyphen
        plain_indent = indent
        hyphen_indent = indent[:-2] + "- "
        this_indent = plain_indent
        if is_multiple:
            this_indent = hyphen_indent

        properties = wko_schema_helper.get_properties(folder)
        property_names = list(properties.keys())
        property_names.sort()

        sub_folders = PyOrderedDict()
        multi_sub_folders = []
        for property_name in property_names:
            property_map = properties[property_name]
            property_type = wko_schema_helper.get_type(property_map)

            if wko_schema_helper.is_simple_map(property_map):
                additional_type = wko_schema_helper.get_map_element_type(property_map)
                if additional_type not in wko_schema_helper.SIMPLE_TYPES:
                    self.fail('Unknown map type ' + additional_type + ' for ' + path + ' ' + property_name)
                self._write_line(this_indent + property_name + ":")
                this_indent = plain_indent
                nest_indent = this_indent + "  "
                self._write_line(nest_indent + "'key-1': " + _get_sample_value(additional_type))
                self._write_line(nest_indent + "'key-2': " + _get_sample_value(additional_type))

            elif wko_schema_helper.is_single_object(property_map):
                # single object instance
                sub_folders[property_name] = property_map

            elif wko_schema_helper.is_object_array(property_map):
                array_items = wko_schema_helper.get_array_item_info(property_map)
                sub_folders[property_name] = array_items
                multi_sub_folders.append(property_name)

            elif wko_schema_helper.is_simple_array(property_map):
                array_type = wko_schema_helper.get_array_element_type(property_map)
                self._write_line(this_indent + property_name + ":")
                this_indent = plain_indent
                each_indent = this_indent + "- "
                self._write_line(each_indent + _get_sample_value(array_type))
                self._write_line(each_indent + _get_sample_value(array_type))

            elif wko_schema_helper.is_simple_type(property_map):
                value = _get_sample_value(property_type)
                enum_values = wko_schema_helper.get_enum_values(property_map)
                if enum_values:
                    value = "'" + enum_values[0] + "'  # " + ', '.join(enum_values)
                self._write_line(this_indent + str(property_name) + ": " + value)
                this_indent = plain_indent

            else:
                self.fail('Unknown property type ' + str(property_type) + ' for ' + str(path) + ' '
                          + str(property_name))

        # process sub-folders after attributes for clarity
        for property_name in sub_folders:
            next_path = wko_schema_helper.append_path(path, property_name)
            if wko_schema_helper.is_unsupported_folder(next_path):
                self._write_line(indent + "# " + property_name + ": (unsupported folder)")
            else:
                self._write_line(this_indent + property_name + ":")
                this_indent = plain_indent
                subfolder = sub_folders[property_name]
                is_multiple = property_name in multi_sub_folders
                child_indent = this_indent + "  "
                self._write_folder(subfolder, is_multiple, next_path, child_indent)

    def _write_line(self, text):
        self.out_file.write(text + "\n")


def _get_sample_value(simple_type):
    if simple_type == 'boolean':
        return 'true'
    elif simple_type == 'number':
        return '123'
    else:
        return "'text'"


if __name__ == '__main__':
    unittest.main()
