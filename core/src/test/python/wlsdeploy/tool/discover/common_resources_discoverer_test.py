"""
Copyright (c) 2026, Oracle and/or its affiliates. All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from base_test import BaseTestCase
from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.discover.common_resources_discoverer import CommonResourcesDiscoverer
from wlsdeploy.util.model_context import ModelContext


class _DomainTypedef(object):
    def is_filtered(self, location, name):
        return False


class _ModelContext(ModelContext):
    def get_domain_typedef(self):
        return _DomainTypedef()


class _WlstHelper(object):
    def __init__(self, exception_type):
        pass

    def get_existing_object_list(self, path):
        if path == '/JDBCSystemResource/(jdbc/comta/DefaultDS)/JdbcResource':
            return ['jdbc/comta/DefaultDS']
        if path == '/JDBCSystemResource/JDBC_IW/JdbcResource':
            return ['JDBC_IW']
        raise ValueError('Unexpected JDBC list path: ' + path)


class _ResourcesDiscoverer(CommonResourcesDiscoverer):
    def _find_names_in_folder(self, location):
        return ['jdbc/comta/DefaultDS', 'JDBC_IW']

    def _populate_model_parameters(self, dictionary, location):
        if location.get_current_model_folder() == model_constants.JDBC_SYSTEM_RESOURCE:
            self.resource_locations.append(LocationContext(location))
            dictionary[model_constants.TARGET] = 'AdminServer'

    def wlst_cd(self, path, location):
        self.navigation_paths.append(path)
        if self.fail_first_resource and location.get_name_for_token('DATASOURCE') == 'jdbc/comta/DefaultDS':
            return None
        return True

    def _discover_subfolders(self, dictionary, location):
        dictionary[model_constants.JDBC_DRIVER_PARAMS] = {'DriverName': 'test.Driver'}
        # Child discovery can leave tokens that must not reach the next datasource.
        location.add_name_token('PROPERTIES', 'NO_NAME_0')

    def _collect_jdbc_driver_wallet(self, datasource, driver_params):
        self.wallet_resources.append(datasource)


class CommonResourcesDiscovererTest(BaseTestCase):
    def _discover(self, fail_first_resource):
        context = _ModelContext('test', {})
        resources = _ResourcesDiscoverer.__new__(_ResourcesDiscoverer)
        resources._model_context = context
        resources._aliases = Aliases(context, wls_version='12.1.3.0.0', exception_type=ExceptionType.DISCOVER)
        resources._base_location = LocationContext().add_name_token('DOMAIN', 'DemoDomain')
        resources.fail_first_resource = fail_first_resource
        resources.resource_locations = []
        resources.navigation_paths = []
        resources.wallet_resources = []
        original_helper = deployer_utils.WlstHelper
        deployer_utils.WlstHelper = _WlstHelper
        try:
            folder, result = resources.get_datasources()
        finally:
            deployer_utils.WlstHelper = original_helper

        self.assertEqual(model_constants.JDBC_SYSTEM_RESOURCE, folder)
        self.assertEqual(2, len(resources.resource_locations))
        second_location = resources.resource_locations[1]
        self.assertEqual([model_constants.JDBC_SYSTEM_RESOURCE], second_location.get_model_folders())
        self.assertEqual({'DOMAIN': 'DemoDomain', 'DATASOURCE': 'JDBC_IW'}, second_location.get_name_tokens())
        self.assertEqual('/JDBCSystemResource/JDBC_IW/JdbcResource/JDBC_IW', resources.navigation_paths[1])
        self.assertEqual({'DriverName': 'test.Driver'}, result['JDBC_IW']['JdbcResource']['JDBCDriverParams'])
        self.assertEqual([], resources._base_location.get_model_folders())
        self.assertEqual({'DOMAIN': 'DemoDomain'}, resources._base_location.get_name_tokens())
        return resources, result

    def test_failed_resource_does_not_prevent_next_resource_discovery(self):
        resources, result = self._discover(True)
        self.assertEqual(False, model_constants.JDBC_RESOURCE in result['jdbc/comta/DefaultDS'])
        self.assertEqual(['JDBC_IW'], resources.wallet_resources)

    def test_successful_resource_does_not_leave_tokens_for_next_resource(self):
        resources, result = self._discover(False)
        self.assertEqual(True, model_constants.JDBC_RESOURCE in result['jdbc/comta/DefaultDS'])
        self.assertEqual(['jdbc/comta/DefaultDS', 'JDBC_IW'], resources.wallet_resources)


if __name__ == '__main__':
    import unittest
    unittest.main()
