"""
Copyright (c) 2023, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re
import unittest

from oracle.weblogic.deploy.aliases import VersionUtils
from oracle.weblogic.deploy.json import JsonStreamTranslator
from oracle.weblogic.deploy.util import FileUtils

from wlsdeploy.aliases.alias_constants import ATTRIBUTES
from wlsdeploy.aliases.alias_constants import CHILD_FOLDERS_TYPE
from wlsdeploy.aliases.alias_constants import DEFAULT_NAME_VALUE
from wlsdeploy.aliases.alias_constants import FOLDERS
from wlsdeploy.aliases.alias_constants import SECRET_SUFFIX
from wlsdeploy.aliases.alias_constants import SINGLE
from wlsdeploy.aliases.alias_constants import VERSION
from wlsdeploy.aliases.alias_constants import WLST_MODE
from wlsdeploy.aliases.alias_constants import WLST_PATHS
from wlsdeploy.aliases.alias_constants import WLST_TYPE
from wlsdeploy.aliases.alias_entries import AliasEntries
from wlsdeploy.aliases.model_constants import OPSS_SECRETS
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import unicode_helper


class AliasFileContentTestCase(unittest.TestCase):
    _resources_dir = '../../test-classes/'
    _token_pattern = re.compile("^%([\\w-]+)%$")
    _base_wlst_path_name = 'WP001'
    _credential_exceptions = [ unicode_helper.to_string(OPSS_SECRETS) ]
    def setUp(self):
        self.alias_entries = AliasEntries(wls_version='12.2.1.3')
        self.online_alias_entries = AliasEntries(wls_version='12.2.1.3', wlst_mode=WlstModes.ONLINE)
        self.category_file_map = self.alias_entries._unit_test_only_get_category_map_files()

    def testAliasFilesContent(self):
        results = []
        category_names = self.category_file_map.keys()
        category_names.sort()
        for category_name in category_names:
            category_file_path = self.category_file_map[category_name]
            category_dict = self._load_category_file(category_file_path)
            results.extend(self._process_folder(category_name, category_dict))
        message = 'Messages:\n'
        for result in results:
            message += '  ' + result + '\n'
        self.assertEqual(len(results), 0, message)

    def _load_category_file(self, category_file_path):
        category_input_stream = FileUtils.getResourceAsStream(category_file_path)
        self.assertNotEquals(category_input_stream, None)
        json_translator = JsonStreamTranslator(category_file_path, category_input_stream)
        return json_translator.parse()

    def _process_folder(self, folder_path, folder_dict, parent_path=""):
        result = []

        result.extend(self._check_folder_type(folder_path, folder_dict, parent_path))
        result.extend(self._check_secret_names(folder_path, folder_dict))

        wlst_paths = dictionary_utils.get_dictionary_element(folder_dict, WLST_PATHS)
        next_parent = dictionary_utils.get_element(wlst_paths, self._base_wlst_path_name)
        if next_parent is None:
            result.append("Folder at path %s does not have %s entry named \"%s\"" %
                          (folder_path, WLST_PATHS, self._base_wlst_path_name))

        # Verify the sub-folders
        subfolders = folder_dict[FOLDERS]
        for subfolder_name, subfolder_value in subfolders.iteritems():
            new_folder_path = folder_path
            if type(subfolder_value) is dict:
                new_folder_path += '/' + subfolder_name
                result.extend(self._process_folder(new_folder_path, subfolder_value, parent_path=next_parent))

        attributes = folder_dict[ATTRIBUTES]
        for attribute_name, attribute_value in attributes.iteritems():
            result.extend(self._process_attribute(folder_path, attribute_name, attribute_value))

        return result

    def _process_attribute(self, folder_path, attribute_name, attribute_value):
        result = []

        if type(attribute_value) is list:
            new_folder_path = folder_path + '/' + ATTRIBUTES

            # check each attribute for overlapping version ranges
            result.extend(self._check_version_ranges(attribute_value, new_folder_path, attribute_name))

        return result

    def _check_folder_type(self, folder_path, folder_dict, parent_path):
        """
        Verify that the folder is correctly configured for the specified child folder type.
        All folder types should have tokens for folder names.
        Single MBean folders should have create_name, and a unique token at the end of each path.
        :param folder_path: the folder path, used for logging
        :param folder_dict: the dictionary for the folder
        :param parent_path: the WLST path of the parent folder
        :return: an array containing any error messages
        """
        result = []

        folders_type = dictionary_utils.get_element(folder_dict, CHILD_FOLDERS_TYPE)
        is_single_folder = folders_type in (SINGLE, None)
        required_last_token = folder_path.split('/')[-1].upper()
        tokens_found = False

        # verify that each wlst_path value has an alternating token pattern, such as:
        # /Folder1/%TOKEN1%/Folder2/%TOKEN2%/Folder3/%TOKEN3%
        wlst_paths = dictionary_utils.get_dictionary_element(folder_dict, WLST_PATHS)
        for key, wlst_path in wlst_paths.iteritems():
            # skip the first empty element, since path starts with /
            elements = wlst_path.split('/')[1:]

            # verify that each even-numbered element in each path is a token.
            last_token = None
            token_required = False
            for element in elements:
                if token_required:
                    matches = self._token_pattern.findall(element)
                    if len(matches) != 1:
                        result.append("Folder at path %s: %s %s has a name that should be a token: %s" %
                                      (folder_path, WLST_PATHS, key, element))
                    else:
                        last_token = matches[0]
                        tokens_found = True
                # toggle the token required flag
                token_required = not token_required

            if not wlst_path.startswith(parent_path):
                result.append("Folder at path %s: %s %s should start with \"%s\"" %
                              (folder_path, WLST_PATHS, key, parent_path))

            # for single folder, the final token in each wlst_path should correspond to the folder name.
            # this will ensure that the final token is unique in the path.
            if is_single_folder and (last_token is not None) and (last_token != required_last_token):
                result.append("Folder at path %s: %s %s last token should reflect folder name: %s" %
                              (folder_path, WLST_PATHS, key, required_last_token))

        # for single folder, if any tokens were found, a create name should be provided.
        if is_single_folder and tokens_found:
            default_name = dictionary_utils.get_element(folder_dict, DEFAULT_NAME_VALUE)
            if default_name is None:
                result.append("Folder at path %s: %s is required for single MBean folder with path tokens" %
                              (folder_path, DEFAULT_NAME_VALUE))

        return result

    def _check_secret_names(self, folder_path, folder_dict):
        result = []
        suffix_maps = {'credential': {}, 'password': {}}

        attributes = folder_dict[ATTRIBUTES]
        for attribute_name, attribute_value in attributes.iteritems():
            for attr_element_dict in attribute_value:
                wlst_type = dictionary_utils.get_element(attr_element_dict, WLST_TYPE)
                secret_suffix = dictionary_utils.get_element(attr_element_dict, SECRET_SUFFIX)
                if wlst_type in suffix_maps.keys():
                    suffix_map = suffix_maps[wlst_type]
                    suffixed_attribute = dictionary_utils.get_element(suffix_map, secret_suffix)
                    if unicode_helper.to_string(attribute_name) in self._credential_exceptions:
                        continue

                    if suffixed_attribute and unicode_helper.to_string(suffixed_attribute) != unicode_helper.to_string(attribute_name):
                        result.append('Multiple %s attributes in path %s with secret_suffix %s: %s and %s' %
                                      (wlst_type, folder_path, secret_suffix, suffixed_attribute, attribute_name))
                    else:
                        suffix_map[secret_suffix] = unicode_helper.to_string(attribute_name)
                elif secret_suffix:
                    result.append('Attribute %s in path %s with type %s should not have secret suffix' %
                                  (attribute_name, folder_path, wlst_type))
        return result

    def _check_version_ranges(self, attribute_value, new_folder_path, attribute_name):
        result = []

        for mode in ['offline', 'online']:
            wlst_modes = [mode, 'both']
            versions = []
            for attr_element_dict in attribute_value:
                if type(attr_element_dict) is dict:
                    wlst_mode = dictionary_utils.get_element(attr_element_dict, WLST_MODE)
                    if wlst_mode in wlst_modes:
                        version = dictionary_utils.get_element(attr_element_dict, VERSION)
                        if not VersionUtils.isRange(version):
                            result.append('Attribute %s at path %s: Version string for mode %s is not a range: %s' %
                                          (attribute_name, new_folder_path, mode, version))
                        versions.append(version)

            for index in range(len(versions) - 1):
                version_1 = versions[index]
                for nextIndex in range(index + 1, len(versions)):
                    version_2 = versions[nextIndex]
                    if VersionUtils.doVersionRangesOverlap(version_1, version_2):
                        result.append('Attribute %s at path %s: Version ranges for %s overlap: %s %s' %
                                      (attribute_name, new_folder_path, mode, version_1, version_2))
        return result
