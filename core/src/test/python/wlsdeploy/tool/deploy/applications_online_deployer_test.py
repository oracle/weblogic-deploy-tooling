"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import shutil

from sets import Set

from java.io import File
from java.io import IOException
from java.lang import IllegalArgumentException
from oracle.weblogic.deploy.deploy import DeployException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict

from base_test import BaseTestCase
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ABSOLUTE_PLAN_PATH
from wlsdeploy.aliases.model_constants import ABSOLUTE_SOURCE_PATH
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import LIBRARY
from wlsdeploy.aliases.model_constants import PLAN_PATH
from wlsdeploy.aliases.model_constants import PLAN_DIR
from wlsdeploy.aliases.model_constants import SOURCE_PATH
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.deploy import applications_online_deployer
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy.applications_online_deployer import OnlineApplicationsDeployer
from wlsdeploy.util.model import Model
from wlsdeploy.util.model_context import ModelContext


class ApplicationsOnlineDeployerTest(BaseTestCase):
    """Exercise strategy diagnostics using real file hashing and simulated WLST inventory."""

    def setUp(self):
        BaseTestCase.setUp(self)
        self.test_dir = str(FileUtils.createTempDirectory(File(self.TEST_OUTPUT_DIR), 'strategy-').getAbsolutePath())
        self.source = os.path.join(self.test_dir, 'source.jar')
        self.changed_source = os.path.join(self.test_dir, 'changed.jar')
        self.missing = os.path.join(self.test_dir, 'missing.jar')
        for path, content in [(self.source, 'original'), (self.changed_source, 'updated')]:
            stream = open(path, 'w')
            try:
                stream.write(content)
            finally:
                stream.close()

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        BaseTestCase.tearDown(self)

    def _new_deployer(self, deployments=None):
        # Parsed model attribute dictionaries return None for absent optional attributes.
        for entries in (deployments or {}).values():
            for name, attributes in entries.items():
                ordered_attributes = OrderedDict()
                ordered_attributes.update(attributes)
                entries[name] = ordered_attributes
        model = Model({'appDeployments': deployments or {}})
        context = ModelContext('applications_online_deployer_test', {'-domain_home': self.test_dir})
        context.get_domain_typedef = lambda: _UnfilteredDomain()
        aliases = Aliases(model_context=context, wlst_mode=WlstModes.ONLINE, wls_version='14.1.2.0')
        deployer = OnlineApplicationsDeployer(model, context, aliases)
        deployer.wlst_helper = _Inventory()
        deployer._get_config_targets = lambda: ['cluster1']
        deployer._OnlineApplicationsDeployer__deploy_db_client_data = lambda: None
        return deployer

    def _assert_failure(self, action, message_id, *details):
        try:
            action()
            self.fail('Expected a handled deployment failure')
        except DeployException, ex:
            self.assertEqual(message_id, ex.getMessageID())
            for detail in details:
                self.assert_(detail in ex.getLocalizedMessage())
            return ex

    def test_missing_file_is_a_deploy_exception(self):
        deployer = self._new_deployer()
        ex = self._assert_failure(lambda: deployer._OnlineApplicationsDeployer__get_file_hash(self.missing),
                                  'WLSDPLY-09309', self.missing)
        self.assert_(isinstance(ex.getCause(), IllegalArgumentException))

    def test_resource_hash_errors_use_the_hash_message(self):
        ex = self._assert_failure(lambda: deployer_utils.get_file_hash(self.missing),
                                  'WLSDPLY-09309', self.missing)
        self.assert_(isinstance(ex.getCause(), IllegalArgumentException))
        original_file_utils = deployer_utils.FileUtils
        try:
            deployer_utils.FileUtils = _UnreadableFileUtils
            ex = self._assert_failure(lambda: deployer_utils.get_file_hash(self.source),
                                      'WLSDPLY-09309', self.source, 'test read failure')
            self.assert_(isinstance(ex.getCause(), IOException))
        finally:
            deployer_utils.FileUtils = original_file_utils

    def test_resource_disappearing_after_existence_check_fails_without_extraction(self):
        deployer = self._new_deployer()
        archive = _RecordingArchive(self.source)
        deployer.archive_helper = archive
        original_file_utils = deployer_utils.FileUtils
        try:
            deployer_utils.FileUtils = _DisappearingFileUtils
            self._assert_failure(lambda: deployer._Deployer__process_archive_entry(
                LocationContext(), SOURCE_PATH, 'source.jar', self.test_dir),
                'WLSDPLY-09309', self.source)
            self.assertEqual([], archive.extracted)
        finally:
            deployer_utils.FileUtils = original_file_utils

    def test_resource_hash_comparison_preserves_extraction_decisions(self):
        for entry, archive_source, expected in [('source.jar', self.source, []),
                                                ('source.jar', self.changed_source, ['source.jar']),
                                                ('missing.jar', self.source, ['missing.jar'])]:
            deployer = self._new_deployer()
            archive = _RecordingArchive(archive_source)
            deployer.archive_helper = archive
            deployer._Deployer__process_archive_entry(LocationContext(), SOURCE_PATH, entry, self.test_dir)
            self.assertEqual(expected, archive.extracted)

    def test_unreadable_file_preserves_io_cause_and_deployment_context(self):
        deployer = self._new_deployer()
        original_file_utils = applications_online_deployer.FileUtils
        try:
            applications_online_deployer.FileUtils = _UnreadableFileUtils
            ex = self._assert_failure(lambda: deployer._OnlineApplicationsDeployer__get_deployment_hash(
                self.source, APPLICATION, 'sample-app', PLAN_PATH),
                'WLSDPLY-09359', APPLICATION, 'sample-app', PLAN_PATH, self.source, 'test read failure')
            self.assert_(isinstance(ex.getCause().getCause(), IOException))
        finally:
            applications_online_deployer.FileUtils = original_file_utils

    def test_missing_library_blocks_application_delete_with_context(self):
        deployer = self._new_deployer({APPLICATION: {'!sample-app': {}}})
        deployer.wlst_helper.libraries['shared#1.0@1.0'] = {SOURCE_PATH: self.missing}
        actions = self._record_execution(deployer)
        ex = self._assert_failure(deployer.deploy, 'WLSDPLY-09359', LIBRARY, 'shared#1.0@1.0',
                                  '/Libraries/shared#1.0@1.0', SOURCE_PATH, self.missing)
        self.assertEqual('WLSDPLY-09309', ex.getCause().getMessageID())
        self.assert_(isinstance(ex.getCause().getCause(), IllegalArgumentException))
        self.assertEqual([], actions)

    def test_missing_existing_application_source_and_plan(self):
        for attribute in [SOURCE_PATH, PLAN_PATH]:
            deployer = self._new_deployer({APPLICATION: {'!sample-app#1.0': {}}})
            attributes = {SOURCE_PATH: self.source}
            attributes[attribute] = self.missing
            deployer.wlst_helper.applications['sample-app#1.0'] = attributes
            actions = self._record_execution(deployer)
            self._assert_failure(deployer.deploy, 'WLSDPLY-09359', APPLICATION, 'sample-app#1.0',
                                 '/AppDeployments/sample-app#1.0', attribute, self.missing)
            self.assertEqual([], actions)

    def test_missing_model_library_source(self):
        deployer = self._new_deployer()
        model_libs = {'shared': {SOURCE_PATH: self.missing, 'Target': 'cluster1'}}
        updates = []
        self._assert_failure(lambda: deployer._update_library_build_strategy_based_on_hashes(
            Set(['cluster1']), self.source, 'shared', model_libs['shared'], model_libs,
            self.missing, Set(['cluster1']), updates, 'shared#1.0@1.0'),
            'WLSDPLY-09360', LIBRARY, 'shared', SOURCE_PATH, self.missing)
        self.assertEqual([], updates)

    def test_missing_model_application_source_and_plan(self):
        for attribute in [SOURCE_PATH, PLAN_PATH]:
            deployer = self._new_deployer()
            app = {SOURCE_PATH: self.source, 'Target': 'cluster1'}
            app[attribute] = self.missing
            stops = []
            compare = deployer._OnlineApplicationsDeployer__update_app_build_strategy_based_on_hashes
            self._assert_failure(lambda: compare(
                'sample-app', app, Set(['cluster1']), {'sample-app': app}, app[SOURCE_PATH],
                None, self.source, stops, 'sample-app#1.0'),
                'WLSDPLY-09360', APPLICATION, 'sample-app', attribute, self.missing)
            self.assertEqual([], stops)

    def test_sparse_models_report_inherited_source_as_existing(self):
        for deployment_type, name in [(APPLICATION, 'sample-app#1.0'), (LIBRARY, 'shared#1.0@1.0')]:
            deployer = self._new_deployer()
            attributes = {SOURCE_PATH: None, 'Target': 'cluster2'}
            updates = []
            self._assert_failure(lambda: self._compare_sparse_source(
                deployer, deployment_type, name, self.missing, attributes, updates),
                'WLSDPLY-09359', deployment_type, name, SOURCE_PATH, self.missing)
            self.assertEqual([], updates)

    def test_sparse_models_preserve_inherited_source_and_new_targets(self):
        for deployment_type, name in [(APPLICATION, 'sample-app#1.0'), (LIBRARY, 'shared#1.0@1.0')]:
            deployer = self._new_deployer()
            attributes = {SOURCE_PATH: None, 'Target': 'cluster1,cluster2'}
            updates = []
            self._compare_sparse_source(deployer, deployment_type, name, self.source, attributes, updates)
            self.assertEqual([], updates)
            self.assertEqual('cluster2', attributes['Target'])
            self.assertEqual(self.source, attributes[SOURCE_PATH])

    def _compare_sparse_source(self, deployer, deployment_type, name, source, attributes, updates):
        if deployment_type == APPLICATION:
            compare = deployer._OnlineApplicationsDeployer__update_app_build_strategy_based_on_hashes
            compare('sample-app', attributes, Set(['cluster1']), {'sample-app': attributes}, source,
                    None, source, updates, name)
        else:
            deployer._update_library_build_strategy_based_on_hashes(
                Set(['cluster1']), source, 'shared', attributes, {'shared': attributes}, source,
                Set(attributes['Target'].split(',')), updates, name)

    def test_mbean_absolute_paths_take_precedence(self):
        for attribute, absolute_attribute in [(SOURCE_PATH, ABSOLUTE_SOURCE_PATH), (PLAN_PATH, ABSOLUTE_PLAN_PATH)]:
            deployer = self._new_deployer({APPLICATION: {'!sample-app#1.0': {}}})
            attributes = {SOURCE_PATH: self.source, attribute: self.source, absolute_attribute: self.missing}
            deployer.wlst_helper.applications['sample-app#1.0'] = attributes
            self._assert_failure(deployer.deploy, 'WLSDPLY-09359', 'sample-app#1.0', attribute, self.missing)

    def test_mbean_relative_source_and_plan_paths(self):
        deployer = self._new_deployer()
        deployer.wlst_helper.applications['sample-app#1.0'] = {
            SOURCE_PATH: 'source.jar', PLAN_PATH: 'changed.jar', PLAN_DIR: self.test_dir}
        references = deployer._OnlineApplicationsDeployer__get_existing_apps()
        self.assertEqual(FileUtils.computeHash(self.source), references['sample-app#1.0']['hash'])
        self.assertEqual(FileUtils.computeHash(self.changed_source), references['sample-app#1.0']['planHash'])
        deployer.wlst_helper.applications['sample-app#1.0'][PLAN_DIR] = 'plans'
        self._assert_failure(deployer._OnlineApplicationsDeployer__get_existing_apps,
                             'WLSDPLY-09359', PLAN_PATH, os.path.join(self.test_dir, 'plans', 'changed.jar'))

    def test_existing_files_missing_at_comparison_still_fail(self):
        deployer = self._new_deployer()
        app = {SOURCE_PATH: self.source, 'Target': 'cluster1'}
        for attribute in [SOURCE_PATH, PLAN_PATH]:
            existing_source = self.source
            existing_plan = None
            if attribute == SOURCE_PATH:
                existing_source = self.missing
            else:
                existing_plan = self.missing
            stops = []
            compare = deployer._OnlineApplicationsDeployer__update_app_build_strategy_based_on_hashes
            self._assert_failure(lambda: compare(
                'sample-app', app, Set(['cluster1']), {'sample-app': app}, self.source,
                existing_plan, existing_source, stops, 'sample-app#1.0'),
                'WLSDPLY-09359', APPLICATION, 'sample-app#1.0', attribute, self.missing)
            self.assertEqual([], stops)

    def test_existing_library_missing_at_comparison_still_fails(self):
        deployer = self._new_deployer()
        library = {SOURCE_PATH: self.source, 'Target': 'cluster1'}
        updates = []
        self._assert_failure(lambda: deployer._update_library_build_strategy_based_on_hashes(
            Set(['cluster1']), self.missing, 'shared', library, {'shared': library},
            self.source, Set(['cluster1']), updates, 'shared#1.0@1.0'),
            'WLSDPLY-09359', LIBRARY, 'shared#1.0@1.0', SOURCE_PATH, self.missing)
        self.assertEqual([], updates)

    def test_referenced_library_inventory_retains_referencing_application(self):
        deployer = self._new_deployer()
        deployer.wlst_helper.libraries['shared#1.0@1.0'] = {SOURCE_PATH: self.source}
        deployer.wlst_helper.referenced = True
        references = deployer._OnlineApplicationsDeployer__get_existing_library_references()
        library = references['shared#1.0@1.0']
        self.assertEqual(FileUtils.computeHash(self.source), library['hash'])
        self.assertEqual(['cluster1'], library['target'])
        self.assert_('sample-app' in library['referencingApp'])

    def test_hash_results_for_file_directory_and_absent_plan(self):
        deployer = self._new_deployer()
        hashes = deployer._OnlineApplicationsDeployer__get_app_and_plan_hash(
            'sample-app', self.source, None, self.test_dir)
        self.assertEqual((FileUtils.computeHash(self.source), None), hashes)
        hashes = deployer._OnlineApplicationsDeployer__get_app_and_plan_hash(
            'sample-app', self.test_dir, None, self.test_dir)
        self.assertEqual((None, None), hashes)

    def test_library_comparisons_preserve_content_and_target_decisions(self):
        for source, targets, expected_targets, expected_updates in [
                (self.source, ['cluster1'], None, []),
                (self.source, ['cluster1', 'cluster2'], Set(['cluster2']), []),
                (self.changed_source, ['cluster2'], Set(['cluster1', 'cluster2']), ['shared#1.0@1.0'])]:
            deployer = self._new_deployer()
            lib = {SOURCE_PATH: source, 'Target': ','.join(targets)}
            libraries = {'shared': lib}
            updates = []
            deployer._update_library_build_strategy_based_on_hashes(
                Set(['cluster1']), self.source, 'shared', lib, libraries,
                source, Set(targets), updates, 'shared#1.0@1.0')
            self.assertEqual(expected_updates, updates)
            if expected_targets is None:
                self.assertEqual({}, libraries)
            else:
                self.assertEqual(expected_targets, Set(libraries['shared']['Target'].split(',')))

    def test_application_comparisons_preserve_content_plan_and_target_decisions(self):
        for source, plan, targets, expected_stops, expected_targets in [
                (self.changed_source, None, 'cluster1', ['sample-app#1.0'], 'cluster1'),
                (self.source, self.changed_source, 'cluster1', ['sample-app#1.0'], 'cluster1'),
                (self.source, None, 'cluster1,cluster2', [], 'cluster2')]:
            deployer = self._new_deployer()
            app = {SOURCE_PATH: source, PLAN_PATH: plan, 'Target': targets}
            stops = []
            compare = deployer._OnlineApplicationsDeployer__update_app_build_strategy_based_on_hashes
            compare('sample-app', app, Set(['cluster1']), {'sample-app': app}, source,
                    None, self.source, stops, 'sample-app#1.0')
            self.assertEqual(expected_stops, stops)
            self.assertEqual(expected_targets, app['Target'])

    def test_versioned_delete_uses_exact_name_and_preserves_execution_order(self):
        deployer = self._new_deployer({APPLICATION: {'!sample-app#1.0': {'Target': 'cluster2'}},
                                      LIBRARY: {'!shared#1.0@1.0': {}}})
        deployer.wlst_helper.applications['sample-app#1.0'] = {SOURCE_PATH: self.source}
        deployer.wlst_helper.libraries['shared#1.0@1.0'] = {SOURCE_PATH: self.source}
        actions = self._record_execution(deployer)
        deployer.deploy()
        self.assertEqual([('stop', 'sample-app#1.0'), ('undeploy', 'sample-app#1.0', APPLICATION),
                          ('undeploy', 'shared#1.0@1.0', LIBRARY)], actions)
        self.assertEqual(False, deployer._does_deployment_to_delete_exist(
            '!sample-app', ['sample-app#1.0'], APPLICATION))
        self.assertEqual(False, deployer._does_deployment_to_delete_exist(
            '!absent', ['sample-app#1.0'], APPLICATION))

    def test_remote_and_ssh_library_inventory_does_not_hash_local_paths(self):
        for mode in ['remote', 'ssh']:
            deployer = self._new_deployer()
            deployer.model_context.is_remote = lambda: mode == 'remote'
            deployer.model_context.is_ssh = lambda: mode == 'ssh'
            deployer.wlst_helper.libraries['shared#1.0@1.0'] = {SOURCE_PATH: self.missing}
            references = deployer._OnlineApplicationsDeployer__get_existing_library_references()
            self.assert_(references['shared#1.0@1.0']['hash'] is None)

    def test_remote_application_inventory_does_not_hash_local_paths(self):
        deployer = self._new_deployer()
        deployer.model_context.is_remote = lambda: True
        hashes = deployer._OnlineApplicationsDeployer__get_app_and_plan_hash(
            'sample-app', self.missing, self.missing, self.test_dir)
        self.assertEqual((None, None), hashes)

    def test_ssh_application_hashes_downloaded_files(self):
        deployer = self._new_deployer()
        deployer.model_context.is_ssh = lambda: True
        downloads = []

        def download(context, path, root, kind):
            downloads.append((path, kind))
            return self.source

        original_download = deployer.path_helper.download_file_from_remote_server
        try:
            deployer.path_helper.download_file_from_remote_server = download
            hashes = deployer._OnlineApplicationsDeployer__get_app_and_plan_hash(
                'sample-app', '/remote/app.jar', '/remote/plan.xml', self.test_dir)
            self.assertEqual((FileUtils.computeHash(self.source), FileUtils.computeHash(self.source)), hashes)
            self.assertEqual([('/remote/app.jar', 'apps'), ('/remote/plan.xml', 'plans')], downloads)
        finally:
            deployer.path_helper.download_file_from_remote_server = original_download

    def test_ssh_download_failures_include_remote_path_and_deployment(self):
        for attribute, file_type, remote_path in [(SOURCE_PATH, 'apps', '/remote/app.jar'),
                                                 (PLAN_PATH, 'plans', '/remote/plan.xml')]:
            deployer = self._new_deployer()
            deployer.model_context.is_ssh = lambda: True
            failure = exception_helper.create_ssh_exception(
                'WLSDPLY-32015', remote_path, self.test_dir, 'test download failure')

            def download(context, path, root, kind):
                if kind == file_type:
                    raise failure
                return self.source

            original_download = deployer.path_helper.download_file_from_remote_server
            try:
                deployer.path_helper.download_file_from_remote_server = download
                ex = self._assert_failure(lambda: deployer._OnlineApplicationsDeployer__get_app_and_plan_hash(
                    'sample-app#1.0', '/remote/app.jar', '/remote/plan.xml', self.test_dir),
                    'WLSDPLY-09361', APPLICATION, 'sample-app#1.0', '/AppDeployments/sample-app#1.0',
                    attribute, remote_path, os.path.join(self.test_dir, file_type), 'test download failure')
                self.assertEqual(failure, ex.getCause())
            finally:
                deployer.path_helper.download_file_from_remote_server = original_download

    def test_ssh_hash_failures_include_remote_and_downloaded_paths(self):
        for attribute, file_type, remote_path in [(SOURCE_PATH, 'apps', '/remote/app.jar'),
                                                 (PLAN_PATH, 'plans', '/remote/plan.xml')]:
            deployer = self._new_deployer()
            deployer.model_context.is_ssh = lambda: True

            def download(context, path, root, kind):
                if kind == file_type:
                    return self.missing
                return self.source

            original_download = deployer.path_helper.download_file_from_remote_server
            try:
                deployer.path_helper.download_file_from_remote_server = download
                ex = self._assert_failure(lambda: deployer._OnlineApplicationsDeployer__get_app_and_plan_hash(
                    'sample-app#1.0', '/remote/app.jar', '/remote/plan.xml', self.test_dir),
                    'WLSDPLY-09361', APPLICATION, 'sample-app#1.0', attribute, remote_path, self.missing)
                self.assertEqual('WLSDPLY-09309', ex.getCause().getMessageID())
                self.assert_(isinstance(ex.getCause().getCause(), IllegalArgumentException))
            finally:
                deployer.path_helper.download_file_from_remote_server = original_download

    def test_ssh_local_file_errors_include_deployment_context(self):
        for failure in [IOException('test local file failure'), IOError('test local file failure'),
                        OSError('test local file failure')]:
            deployer = self._new_deployer()
            deployer.model_context.is_ssh = lambda: True

            def download(context, path, root, kind):
                raise failure

            original_download = deployer.path_helper.download_file_from_remote_server
            try:
                deployer.path_helper.download_file_from_remote_server = download
                ex = self._assert_failure(lambda: deployer._OnlineApplicationsDeployer__get_app_and_plan_hash(
                    'sample-app', '/remote/app.jar', None, self.test_dir),
                    'WLSDPLY-09361', APPLICATION, 'sample-app', SOURCE_PATH, '/remote/app.jar',
                    os.path.join(self.test_dir, 'apps'), 'test local file failure')
                self.assert_(ex.getCause() is not None)
            finally:
                deployer.path_helper.download_file_from_remote_server = original_download

    def _record_execution(self, deployer):
        actions = []
        deployer._OnlineApplicationsDeployer__stop_app = lambda name: actions.append(('stop', name))
        deployer._OnlineApplicationsDeployer__undeploy_app = \
            lambda name, kind: actions.append(('undeploy', name, kind))
        deployer._OnlineApplicationsDeployer__delete_deployment_on_server = lambda name, model: None
        deployer._OnlineApplicationsDeployer__deploy_model_libraries = lambda model, location: None
        deployer._OnlineApplicationsDeployer__deploy_model_applications = lambda model, location: []
        deployer._OnlineApplicationsDeployer__start_all_apps = lambda apps, location, restart: None
        return actions


class _UnfilteredDomain(object):

    def is_filtered(self, location, name):
        return False


class _UnreadableFileUtils(object):

    def computeHash(path):
        raise IOException('test read failure')

    computeHash = staticmethod(computeHash)


class _DisappearingFileUtils(object):

    def computeHash(path):
        os.remove(path)
        return FileUtils.computeHash(path)

    computeHash = staticmethod(computeHash)


class _RecordingArchive(object):

    def __init__(self, source):
        self.source = source
        self.extracted = []

    def contains_file(self, path):
        return True

    def get_file_hash(self, path):
        return FileUtils.computeHash(self.source)

    def extract_file(self, path, location=None, strip_leading_path=True):
        self.extracted.append(path)


class _Inventory(object):
    """Read-only WLST responses; unexpected reads fail the test."""

    def __init__(self):
        self.applications = {}
        self.libraries = {}
        self.referenced = False
        self.path = None

    def server_config(self):
        pass

    def domain_runtime(self):
        pass

    def cd(self, path):
        self.path = path

    def get(self, path):
        if path == '/AppRuntimeStateRuntime/AppRuntimeStateRuntime/ApplicationIds':
            return self.applications.keys()
        raise AssertionError('Unexpected get: ' + path)

    def get_existing_object_list(self, path):
        if path.rstrip('/') == '/AppDeployments':
            return self.applications.keys()
        if path == '/ServerRuntimes/':
            return ['AdminServer']
        if path == '/ServerRuntimes/AdminServer/LibraryRuntimes/':
            return self.libraries.keys()
        if path.endswith('/ReferencingRuntimes/'):
            return ['sample-app']
        raise AssertionError('Unexpected list: ' + path)

    def lsa(self, name=None):
        if self.path.endswith('/ReferencingRuntimes/') and name == 'sample-app':
            return {'Type': 'ApplicationRuntime', 'ApplicationName': name}
        if self.path.startswith('/ServerRuntimes/AdminServer/LibraryRuntimes/'):
            return {'Referenced': self.referenced}
        if self.path.startswith('/Libraries/'):
            return self.libraries[self.path[len('/Libraries/'):]]
        if self.path.startswith('/AppDeployments/'):
            return self.applications[self.path[len('/AppDeployments/'):]]
        raise AssertionError('Unexpected attributes: ' + self.path)
