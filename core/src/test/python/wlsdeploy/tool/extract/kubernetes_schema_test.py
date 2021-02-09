"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import unittest

from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.aliases.model_constants import KUBERNETES
from wlsdeploy.tool.extract import domain_resource_extractor
from wlsdeploy.tool.extract import wko_schema_helper
from wlsdeploy.util import dictionary_utils


class KubernetesSchemaTest(unittest.TestCase):
    _model_dir = '../../unit-tests/wko'
    _model_path = _model_dir + '/model.yaml'

    def setUp(self):
        self.schema_map = wko_schema_helper.get_domain_resource_schema()

        os.mkdir(self._model_dir)
        file_path = self._model_dir + "/model.yaml"
        self.out_file = open(file_path, "w")

    def tearDown(self):
        self.out_file.close()

    def testKubernetesSchema(self):
        # create a model with every element.
        # verify that there are no unknown types or structures.
        self._write_folder(self.schema_map, "", False, "", "")

    def _write_folder(self, folder, name, is_multiple, path, indent):
        label = name
        if not label:
            label = KUBERNETES

        if wko_schema_helper.is_unsupported_folder(path):
            self._write_line("\n" + indent + "# " + label + ": (unsupported folder)")
            return

        self._write_line("\n" + indent + label + ":")
        indent = indent + "  "

        properties = folder["properties"]
        if not properties:
            self.fail('No properties in schema path ' + path)

        multi_key = None
        if is_multiple:
            mapped_key = domain_resource_extractor.get_mapped_key(path)
            multi_property = dictionary_utils.get_element(properties, mapped_key)
            if multi_property:
                multi_key = mapped_key
                comment = 'maps to ' + multi_key
            else:
                comment = 'unique key for each'

            self._write_line(indent + "'" + name + "-1':  # " + comment)
            indent = indent + "  "

        property_names = list(properties.keys())
        property_names.sort()

        sub_folders = PyOrderedDict()
        multi_sub_folders = []
        for property_name in property_names:
            property_map = properties[property_name]

            property_type = dictionary_utils.get_element(property_map, "type")

            if property_type == "object":
                additional = dictionary_utils.get_dictionary_element(property_map, "additionalProperties")
                additional_type = dictionary_utils.get_element(additional, "type")
                if additional_type:
                    if additional_type not in wko_schema_helper.SIMPLE_TYPES:
                        self.fail('Unknown map type ' + additional_type + ' for ' + path + ' ' + property_name)
                    nest_indent = indent + "  "
                    self._write_line(indent + property_name + ":")
                    self._write_line(nest_indent + "'key-1': " + _get_sample_value(additional_type))
                    self._write_line(nest_indent + "'key-2': " + _get_sample_value(additional_type))
                else:
                    # single object instance
                    sub_folders[property_name] = property_map

            elif property_type == "array":
                array_items = dictionary_utils.get_dictionary_element(property_map, "items")
                array_type = dictionary_utils.get_dictionary_element(array_items, "type")
                if array_type == "object":
                    # multiple object instances
                    sub_folders[property_name] = array_items
                    multi_sub_folders.append(property_name)
                elif array_type in wko_schema_helper.SIMPLE_TYPES:
                    nest_indent = indent + "  "
                    self._write_line(indent + property_name + ": [")
                    self._write_line(nest_indent + _get_sample_value(array_type) + ",")
                    self._write_line(nest_indent + _get_sample_value(array_type))
                    self._write_line(indent + "]")
                else:
                    self.fail('Unknown array type ' + array_type + ' for ' + path + ' ' + property_name)

            elif property_type in wko_schema_helper.SIMPLE_TYPES:
                if property_name != multi_key:
                    value = _get_sample_value(property_type)
                    enum_values = wko_schema_helper.get_enum_values(property_map)
                    if enum_values:
                        value = "'" + enum_values[0] + "'  # " + ', '.join(enum_values)
                    self._write_line(indent + str(property_name) + ": " + value)

            else:
                self.fail('Unknown property type ' + str(property_type) + ' for ' + str(path) + ' '
                          + str(property_name))

        # process sub-folders after attributes for clarity
        for property_name in sub_folders:
            subfolder = sub_folders[property_name]
            is_multiple = property_name in multi_sub_folders
            next_path = wko_schema_helper.append_path(path, property_name)
            self._write_folder(subfolder, property_name, is_multiple, next_path, indent)

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
