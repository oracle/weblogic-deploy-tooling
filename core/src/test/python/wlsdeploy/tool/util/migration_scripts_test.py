"""
Copyright (c) 2026, Oracle and/or its affiliates. All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import shutil

from java.io import File
from oracle.weblogic.deploy.util import WLSDeployArchive

from base_test import BaseTestCase
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import POST_SCRIPT
from wlsdeploy.aliases.model_constants import PRE_SCRIPT
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.create.creator import Creator
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.tool.discover.topology_discoverer import TopologyDiscoverer
from wlsdeploy.tool.util.archive_helper import ArchiveList
from wlsdeploy.tool.util.topology_helper import TopologyHelper
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext


class _Context(ModelContext):
    skip_archive = False
    remote = False
    ssh = False

    def is_skip_archive(self):
        return self.skip_archive

    def is_remote(self):
        return self.remote

    def is_ssh(self):
        return self.ssh


class _WlstHelper(object):
    def set(self, name, value, masked=False):
        self.value = value


class MigrationScriptsTest(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.root = os.path.join(self.TEST_OUTPUT_DIR, 'migration-scripts')
        if os.path.exists(self.root):
            shutil.rmtree(self.root)
        os.makedirs(os.path.join(self.root, 'source', 'bin', 'service_migration', 'nested'))
        self.source_domain = os.path.join(self.root, 'source')
        self.target_domain = os.path.join(self.root, 'target')
        os.mkdir(self.target_domain)
        self.source = os.path.join(self.source_domain, 'bin', 'service_migration', 'nested', 'pre.sh')
        self._write(self.source, '#!/bin/sh\necho migration\n')
        self.archive_name = os.path.join(self.root, 'archive.zip')
        self.archive = WLSDeployArchive(self.archive_name)
        arguments = {CommandLineArgUtil.DOMAIN_HOME_SWITCH: self.source_domain,
                     CommandLineArgUtil.ARCHIVE_FILE_SWITCH: self.archive_name,
                     CommandLineArgUtil.ARCHIVE_FILE: self.archive}
        self.context = _Context('test', arguments)
        self.aliases = Aliases(self.context, wls_version='12.2.1.4', exception_type=ExceptionType.DISCOVER)
        self.logger = PlatformLogger('wlsdeploy.test')
        self.helper = TopologyHelper(self.aliases, ExceptionType.CREATE, self.logger)

    def tearDown(self):
        self.archive.close()
        BaseTestCase.tearDown(self)

    def _write(self, path, text):
        stream = open(path, 'w')
        try:
            stream.write(text)
        finally:
            stream.close()

    def _locations(self):
        return [LocationContext().append_location('MigratableTarget').add_name_token('MIGRATABLE', 'mt'),
                LocationContext().append_location('Server').add_name_token('SERVER', 'ms1')
                    .append_location('JTAMigratableTarget').add_name_token('JTAMIGRATABLETARGET', 'ms1'),
                LocationContext().append_location('ServerTemplate').add_name_token('SERVERTEMPLATE', 'template')
                    .append_location('JTAMigratableTarget').add_name_token('JTAMIGRATABLETARGET', 'template')]

    def _discoverer(self):
        discoverer = TopologyDiscoverer.__new__(TopologyDiscoverer)
        discoverer._model_context = self.context
        discoverer._aliases = self.aliases
        discoverer.path_helper = self.path_helper
        discoverer.download_temporary_dir = self.root
        return discoverer

    def _deployer(self, mode):
        deployer = Deployer.__new__(Deployer)
        deployer.model_context = self.context
        deployer.aliases = self.aliases
        deployer.logger = self.logger
        deployer.path_helper = self.path_helper
        deployer.topology_helper = self.helper
        deployer.wlst_mode = mode
        deployer.archive_helper = ArchiveList(self.archive_name, self.context, ExceptionType.DEPLOY)
        return deployer

    def test_discover_relative_and_absolute_paths(self):
        discoverer = self._discoverer()
        for location in self._locations():
            for attribute in [PRE_SCRIPT, POST_SCRIPT]:
                for source in ['nested/pre.sh', self.source, '@@DOMAIN_HOME@@/bin/service_migration/nested/pre.sh']:
                    path = discoverer._add_migration_script_to_archive(attribute, source, location)
                    self.assertEqual(True, self.archive.containsFile(path))
                    self.assertEqual(True, path.startswith(WLSDeployArchive.ARCHIVE_SCRIPTS_DIR + '/'))

    def test_missing_empty_and_skipped_scripts_retain_value(self):
        discoverer = self._discoverer()
        location = self._locations()[0]
        for value in [None, '', 'missing.sh']:
            self.assertEqual(value, discoverer._add_migration_script_to_archive(PRE_SCRIPT, value, location))
        self.context.skip_archive = True
        self.assertEqual('nested/pre.sh', discoverer._add_migration_script_to_archive(
            PRE_SCRIPT, 'nested/pre.sh', location))

    def test_remote_discovery_resolves_service_migration_directory(self):
        self.context.remote = True
        discoverer = self._discoverer()
        entries = []
        discoverer.add_to_remote_map = lambda source, target, entry_type: entries.append((source, target, entry_type))
        path = discoverer._add_migration_script_to_archive(PRE_SCRIPT, 'nested/pre.sh', self._locations()[1])
        self.assertEqual([(self.source, path, 'SCRIPT')], entries)

    def test_ssh_discovery_archives_downloaded_script(self):
        self.context.ssh = True
        discoverer = self._discoverer()
        downloads = []
        def download(source, directory, name):
            downloads.append(source)
            return self.source
        discoverer.download_deployment_from_remote_server = download
        path = discoverer._add_migration_script_to_archive(POST_SCRIPT, 'nested/pre.sh', self._locations()[2])
        self.assertEqual([self.source], downloads)
        self.assertEqual(True, self.archive.containsFile(path))

    def test_create_defers_extraction_and_sets_filename(self):
        path = self.archive.addScript(self.source)
        for location in self._locations():
            for attribute in [PRE_SCRIPT, POST_SCRIPT]:
                creator = Creator({}, self.context, self.aliases)
                creator.archive_helper = ArchiveList(self.archive_name, self.context, ExceptionType.CREATE)
                creator.wlst_helper = _WlstHelper()
                creator._set_attribute(location, attribute, path, [attribute])
                self.assertEqual('pre.sh', creator.wlst_helper.value)
                self.assertEqual([(path, 'bin/service_migration/pre.sh', True)],
                                 creator.files_to_extract_from_archive)
                creator._extract_deferred_archive_files(self.target_domain)
                self._assert_extracted('pre.sh')

    def test_offline_and_online_update_and_duplicate_filenames(self):
        first = self.archive.addScript(self.source)
        other = os.path.join(self.root, 'pre.sh')
        self._write(other, '#!/bin/sh\necho other\n')
        second = self.archive.addScript(other)
        self.assertEqual(False, first == second)
        self.context._domain_home = self.target_domain
        for mode in [WlstModes.OFFLINE, WlstModes.ONLINE]:
            deployer = self._deployer(mode)
            for location in self._locations():
                for attribute in [PRE_SCRIPT, POST_SCRIPT]:
                    for path in [first, second]:
                        filename = path.split('/')[-1]
                        self.assertEqual(filename, deployer._extract_from_archive_if_needed(location, attribute, path))
                        self._assert_extracted(filename)
                        # Existing content must also be replaced on update.
                        self._write(os.path.join(self.target_domain, 'bin', 'service_migration', filename), 'old')
                        deployer._extract_from_archive_if_needed(location, attribute, path)
                        self._assert_extracted(filename)

    def test_ssh_update_uploads_to_migration_directory(self):
        path = self.archive.addScript(self.source)
        self.context._domain_home = self.target_domain
        self.context.ssh = True
        self.path_helper.set_remote_path_module(False)
        deployer = self._deployer(WlstModes.ONLINE)
        deployer.upload_temporary_dir = self.root
        uploads = []
        deployer.upload_specific_file_to_remote_server = lambda source, target: uploads.append((source, target))
        self.assertEqual('pre.sh', deployer._extract_from_archive_if_needed(self._locations()[0], PRE_SCRIPT, path))
        self.assertEqual([(os.path.join(self.root, path),
                           os.path.join(self.target_domain, 'bin', 'service_migration', 'pre.sh'))], uploads)
        if File.separator != '\\':
            self.assertEqual(True, File(uploads[0][0]).canExecute())

    def test_other_scripts_and_external_paths_keep_existing_behavior(self):
        path = self.archive.addScript(self.source)
        self.assertEqual(path, self.helper.get_archive_extract_path(path, self._locations()[0], 'CreateTableDDLFile'))
        for location in self._locations():
            self.assertEqual('nested/pre.sh', self.helper.get_archive_extract_path('nested/pre.sh', location, PRE_SCRIPT))
            self.assertEqual(self.source, self.helper.get_archive_extract_path(self.source, location, POST_SCRIPT))

    def _assert_extracted(self, filename):
        file_path = os.path.join(self.target_domain, 'bin', 'service_migration', filename)
        self.assertEqual(True, os.path.isfile(file_path))
        stream = open(file_path)
        try:
            self.assertEqual(True, stream.read().startswith('#!/bin/sh'))
        finally:
            stream.close()
        if File.separator != '\\':
            self.assertEqual(True, File(file_path).canExecute())
