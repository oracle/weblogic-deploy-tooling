"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
from java.io import File

from base_test import BaseTestCase
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.model_constants import SECURITY
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.tool.util import default_authenticator_helper
from wlsdeploy.tool.util import ldif_entry
from wlsdeploy.tool.util.default_authenticator_helper import DefaultAuthenticatorHelper
from wlsdeploy.tool.util.default_authenticator_helper import LDIFT_UNIQUE_MEMBER
from wlsdeploy.tool.util.default_authenticator_helper import LDIFT_WLS_MEMBER_OF
from wlsdeploy.tool.util.ldif_entry import LDIFEntry
from wlsdeploy.tool.util.targets import file_template_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.yaml.yaml_translator import YamlToPython


class DefaultAuthenticatorHelperTest(BaseTestCase):

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self.MODELS_DIR = os.path.join(self.TEST_CLASSES_DIR, 'ldift')
        self.OUTPUT_DIR = os.path.join(self.TEST_OUTPUT_DIR, 'ldift')
        self.SECURITY_RESOURCES_DIR = '../../../src/main/resources/oracle/weblogic/deploy/security'

    def setUp(self):
        BaseTestCase.setUp(self)
        self._establish_directory(self.OUTPUT_DIR)
        self._model_context = ModelContext("test", {})
        self._aliases = Aliases(self._model_context, wlst_mode=WlstModes.OFFLINE, wls_version=self.ALIAS_WLS_VERSION)

    def test_create_init_file(self):
        """
        Test that an existing LDIFT file is read and updated.
        """
        helper = DefaultAuthenticatorHelper(self._model_context, self._aliases, ExceptionType.DEPLOY)

        model_file = os.path.join(self.MODELS_DIR, 'security-model.yaml')
        reader = YamlToPython(model_file, True)
        model_dict = reader.parse()
        topology_dict = dictionary_utils.get_dictionary_element(model_dict, TOPOLOGY)
        security_dict = dictionary_utils.get_dictionary_element(topology_dict, SECURITY)

        ldift_name = 'DefaultAuthenticatorInit.ldift'
        source_ldift = File(self.MODELS_DIR, ldift_name)
        template_hash = helper._build_default_template_hash(security_dict, source_ldift)

        template_file_name = ldift_name + file_template_helper.MUSTACHE_SUFFIX
        template_path = os.path.join(self.SECURITY_RESOURCES_DIR, template_file_name)
        target_ldift = File(self.OUTPUT_DIR, ldift_name)
        file_template_helper.create_file_from_file(template_path, template_hash, target_ldift,
                                                   self._aliases.get_exception_type())

        # read the resulting file and check its contents
        entries = ldif_entry.read_entries(target_ldift)

        # are the expected entries present?
        names = ['Administrators', 'Monitors', 'OracleSystemUser', 'AppMonitors', 'DoorMonitors', 'john']
        entry_count = len(names)
        self.assertEqual(entry_count, len(entries),
                         "Result LDIFT should have %d entries, not %d" % (entry_count, len(entries)))

        for i in range(len(names)):
            entry = entries[i]  # type: LDIFEntry
            value = entry.get_single_value('cn')
            self.assertEqual(names[i], value, "Entry %d should have name %s, not %s" % (i, names[i], value))

        # did an existing group and the new group get assigned to Administrators?
        administrators = entries[0]  # type: LDIFEntry
        self._check_unqualified_values('Administrators', administrators, LDIFT_UNIQUE_MEMBER,
                                       ['Monitors', 'AppMonitors'])

        # did existing Monitors group get an updated description?
        monitors = entries[1]  # type: LDIFEntry
        expected = "Updated monitors group"
        value = monitors.get_single_value(default_authenticator_helper.LDIFT_DESCRIPTION)
        self.assertEqual(expected, value,
                         'Monitors description should be "%s", not "%s"' % (expected, value))

        # did existing OracleSystemUser get an updated description?
        system_user = entries[2]  # type: LDIFEntry
        expected = "An updated Oracle system user"
        value = system_user.get_single_value(default_authenticator_helper.LDIFT_DESCRIPTION)
        self.assertEqual(expected, value,
                         'OracleSystemUser description should be "%s", not "%s"' % (expected, value))

        # did existing OracleSystemUser get a mail attribute?
        expected = "osu@mycompany.com"
        value = system_user.get_single_value("mail")
        self.assertEqual(expected, value,
                         'OracleSystemUser mail attribute should be "%s", not "%s"' % (expected, value))

        # did existing OracleSystemUser get a duplicated assignment to OracleSystemGroup?
        self._check_unqualified_values('OracleSystemUser', system_user, LDIFT_WLS_MEMBER_OF,
                                       ['OracleSystemGroup', 'AppMonitors'])

        # did a new group get assigned to new group AppMonitors?
        app_monitors_group = entries[3]  # type: LDIFEntry
        self._check_unqualified_values('AppMonitors', app_monitors_group, LDIFT_UNIQUE_MEMBER,
                                       ['DoorMonitors'])

        # did new user john get assigned to Monitors and AppMonitors?
        user_john = entries[5]  # type: LDIFEntry
        self._check_unqualified_values('User john', user_john, LDIFT_WLS_MEMBER_OF,
                                       ['Monitors', 'AppMonitors'])

    def _check_unqualified_values(self, label, entry, key, expected_names):
        names = entry.get_unqualified_names(key)
        expected = len(expected_names)
        self.assertEqual(expected, len(names),
                         label + " should have %d %s values, not %d" % (expected, key, len(names)))

        for name in expected_names:
            self.assertEqual(True, name in names,
                             label + ' should have %s value %s' % (key, name))
