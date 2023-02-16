"""
Copyright (c) 2020, 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import unittest

from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.tool.util.targets import model_crd_helper
from wlsdeploy.tool.util.targets import schema_helper
import wlsdeploy.util.unicode_helper as str_helper


class CrdSchemaTest(unittest.TestCase):
    _model_dir = '../../unit-tests/crd-models'

    def testWkoSchema(self):
        self._testSchemas(model_crd_helper.WKO_PRODUCT_KEY, model_crd_helper.WKO_VERSION_3)

    def testWko4Schemas(self):
        self._testSchemas(model_crd_helper.WKO_PRODUCT_KEY, model_crd_helper.WKO_VERSION_4)

    def testVerrazzanoSchemas(self):
        self._testSchemas(model_crd_helper.VERRAZZANO_PRODUCT_KEY, model_crd_helper.VERRAZZANO_VERSION_1)

    def _testSchemas(self, product_key, product_version):
        # create a model with every element.
        # verify that there are no unknown types or structures.
        try:
            if not os.path.exists(self._model_dir):
                os.makedirs(self._model_dir)
            file_path = self._model_dir + "/" + product_key + "-" + product_version + ".yaml"
            self.out_file = open(file_path, "w")

            this_crd_helper = model_crd_helper.get_product_helper(product_key, product_version)
            self._write_line(this_crd_helper.get_model_section() + ":  # " + product_version)

            crd_folders = this_crd_helper.get_crd_folders()
            for crd_folder in crd_folders:
                indent = "  "
                if crd_folder.has_model_key():
                    self._write_line(indent + crd_folder.get_model_key() + ":")
                    indent = indent + "  "
                self._write_folder(crd_folder.get_schema(), crd_folder.is_array(), "", indent)

            self.out_file.close()
        except Exception, e:
            self.fail(str_helper.to_string(e))

    def _write_folder(self, folder, in_array, path, indent):
        # for an object in an array, the first field is prefixed with a hyphen
        this_indent = plain_indent = indent
        if in_array:
            this_indent = indent[:-2] + "- "

        properties = schema_helper.get_properties(folder)
        property_names = list(properties.keys())
        property_names.sort()

        sub_folders = PyOrderedDict()
        object_array_keys = []
        for property_name in property_names:
            property_map = properties[property_name]
            property_type = schema_helper.get_type(property_map)

            if schema_helper.is_simple_map(property_map):
                additional_type = schema_helper.get_map_element_type(property_map)
                if additional_type not in schema_helper.SIMPLE_TYPES:
                    self.fail('Unknown map type ' + additional_type + ' for ' + path + ' ' + property_name)
                self._write_line(this_indent + property_name + ":")
                this_indent = plain_indent
                nest_indent = this_indent + "  "
                self._write_line(nest_indent + "'key-1': " + _get_sample_value(additional_type))
                self._write_line(nest_indent + "'key-2': " + _get_sample_value(additional_type))

            elif schema_helper.is_single_object(property_map):
                # single object instance
                sub_folders[property_name] = property_map

            elif schema_helper.is_object_array(property_map):
                array_items = schema_helper.get_array_item_info(property_map)
                sub_folders[property_name] = array_items
                object_array_keys.append(property_name)

            elif schema_helper.is_simple_array(property_map):
                array_type = schema_helper.get_array_element_type(property_map)
                self._write_line(this_indent + property_name + ":")
                this_indent = plain_indent
                each_indent = this_indent + "- "
                self._write_line(each_indent + _get_sample_value(array_type))
                self._write_line(each_indent + _get_sample_value(array_type))

            elif schema_helper.is_simple_type(property_map):
                value = _get_sample_value(property_type)
                enum_values = schema_helper.get_enum_values(property_map)
                if enum_values:
                    value = "'" + enum_values[0] + "'  # " + ', '.join(enum_values)
                self._write_line(this_indent + str_helper.to_string(property_name) + ": " + value)
                this_indent = plain_indent

            else:
                self.fail('Unknown property type ' + str_helper.to_string(property_type)
                          + ' for ' + str_helper.to_string(path) + ' ' + str_helper.to_string(property_name))

        # process sub-folders after attributes for clarity
        for property_name in sub_folders:
            next_path = schema_helper.append_path(path, property_name)
            if schema_helper.is_unsupported_folder(next_path):
                self._write_line(indent + "# " + property_name + ": (unsupported folder)")
            else:
                self._write_line(this_indent + property_name + ":")
                this_indent = plain_indent
                subfolder = sub_folders[property_name]
                in_array = property_name in object_array_keys
                child_indent = this_indent + "  "

                # if this folder has multiple options (oneOf), print each with comments
                subfolder_options = [subfolder]
                one_of_options = schema_helper.get_one_of_options(subfolder)
                if one_of_options:
                    subfolder_options = one_of_options

                for index, subfolder_option in enumerate(subfolder_options):
                    if one_of_options:
                        self._write_line('')
                        self._write_line(child_indent + "# option " + str_helper.to_string(index + 1))

                    # comment out options after the first
                    subfolder_indent = child_indent
                    if index > 0:
                        subfolder_indent = subfolder_indent + "# "

                    self._write_folder(subfolder_option, in_array, next_path, subfolder_indent)

    def _write_line(self, text):
        self.out_file.write(text + "\n")


def _get_sample_value(simple_type):
    if simple_type == 'boolean':
        return 'true'
    elif simple_type == 'integer':
        return '345'
    elif simple_type == 'number':
        return '123'
    else:
        return "'text'"


if __name__ == '__main__':
    unittest.main()
