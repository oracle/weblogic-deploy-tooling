"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

from oracle.weblogic.deploy.util import PyWLSTException
from oracle.weblogic.deploy.util import WLSDeployArchive

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.tool.deploy.resources_deployer import ResourcesDeployer

_class_name = 'ModelDeployer'
_logger = PlatformLogger('wlsdeploy.deploy')

class ModelDeployer(Deployer):
    """
    Deploy resources and applications at the domain level using WLST.
    Entry points to support multiple options for partial deployment.
    """
    _class_name = "ModelDeployer"

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
        Deployer.__init__(self, model, model_context, aliases, wlst_mode)
        self.resources_deployer = ResourcesDeployer(model, model_context, aliases, wlst_mode=wlst_mode)
        self.applications_deployer = \
            deployer_utils.get_applications_deployer(model, model_context, aliases, wlst_mode=wlst_mode)

    def deploy_resources(self):
        """
        Deploy the resources in specific order.
        Applications are not included, since they are processed after save/activate for online deployment.
        :raises DeployException: if an error occurs
        """
        _method_name = 'deploy_resources'

        try:
            location = LocationContext()
            self.resources_deployer.deploy(location)
        except PyWLSTException, pwe:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09650', pwe.getLocalizedMessage(), error=pwe)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

    def deploy_app_attributes_online(self):
        deployer_utils.delete_online_deployment_targets(self.model, self.aliases, self.wlst_mode)
        self.applications_deployer.add_application_attributes_online(self.model, LocationContext())

    def deploy_applications(self, is_restart_required=False):
        """
        Deploy the applications from the model.
        :raises DeployException: if an error occurs
        """
        self.applications_deployer.deploy(is_restart_required)

    def deploy_model_offline(self):
        """
        Deploy the topology, resources and applications, in specific order.
        This order is correct for offline. For online deployment, applications should be processed after save/activate.
        :raises DeployException: if an error occurs
        """
        _method_name = 'deploy_model_offline'

        try:
            self.deploy_resources()
            self.deploy_applications()
        except PyWLSTException, pwe:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09650', pwe.getLocalizedMessage(), error=pwe)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

    def distribute_database_wallets_online(self):
        """
        Go through the model and run the WLST distributeApplication command to distribute the already extracted wallet
        to the targets.
        """
        _method_name = 'distribute_database_wallets_online'

        if self.archive_helper is None:
            return

        if not self.wls_helper.is_db_client_data_distribution_supported():
            # Older WLS versions don't support wallet distribution
            return

        if self.model_context.is_remote():
            # Should have already warned during wallets extraction
            return

        try:
            wallet_path_list = self.archive_helper.get_all_database_wallet_paths()
            distribute_list = []
            # Go through the wallet path list and build the actual list avoid duplicate path in different wallets
            for wallet_path in wallet_path_list:
                for path in wallet_path['paths']:
                    # correct deprecated location
                    if path.startswith(WLSDeployArchive.WLSDPLY_ARCHIVE_BINARY_DIR + WLSDeployArchive.ZIP_SEP):
                        path = WLSDeployArchive.CONFIG_DIR_NAME + WLSDeployArchive.ZIP_SEP + path
                    absolute_path = self.path_helper.join(self.model_context.get_domain_home(), path)
                    if absolute_path not in distribute_list:
                        distribute_list.append(absolute_path)

            for distribute_path in distribute_list:
                self.wlst_helper.distribute_application(distribute_path, dbClientData='true', remote='true')

        except PyWLSTException, pwe:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09650', pwe.getLocalizedMessage(), error=pwe)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

    def deploy_model_after_update(self):
        """
        Deploy the resources that must be done after WLST updateDomain.
        :raises DeployException: if an error occurs
        """
        _method_name = 'deploy_model_after_update'

        try:
            location = LocationContext()
            self.resources_deployer.deploy_after_update(location)
        except PyWLSTException, pwe:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09650', pwe.getLocalizedMessage(), error=pwe)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

    def deploy_resources_and_apps_for_create(self):
        """
        Deploy the resources and appDeployments sections after create handles the topology section of the model.
        :raises DeployException: if an error occurs
        """
        self.deploy_model_offline()

    def extract_early_archive_files(self):
        """
        Extract archive files that are needed before model processing.
        These can include database wallets and custom files.
        Files are uploaded if SSH options are used.
        """
        self.extract_all_database_wallets()
        self.extract_all_custom_files()
        self.extract_weblogic_remote_console_extension()

    def extract_weblogic_remote_console_extension(self):
        """
        Extract all the database wallets in the archive(s) to the target domain.
        Use SSH if the domain is on a remote system.
        """
        if self.model_context.is_remote():
            return

        archive_list = self.archive_helper
        if archive_list:
            if not self.model_context.is_ssh():
                archive_list.extract_weblogic_remote_console_extension()
            else:
                found_ext = archive_list.extract_weblogic_remote_console_extension(self.upload_temporary_dir)
                if found_ext:
                    self._upload_extracted_directory(WLSDeployArchive.WRC_EXTENSION_TARGET_DIR_NAME)

    def _add_warnings_for_remote_update_files(self, archive_name, file_paths, destination, method_name):
        if file_paths is not None and len(file_paths) > 0:
            _logger.todo('WLSDPLY-06044', archive_name, ', '.join(file_paths), destination,
                         class_name=_class_name, method_name=method_name)

    def extract_all_database_wallets(self):
        """
        Extract all the database wallets in the archive(s) to the target domain.
        Use SSH if the domain is on a remote system.
        """
        _method_name = 'extract_all_database_wallets'
        archive_list = self.archive_helper

        if archive_list:
            if self.model_context.is_remote():
                wallet_paths = archive_list.get_all_database_wallet_paths()
                for wallet in wallet_paths:
                    remote_dir = self.model_context.get_domain_home()
                    self._add_warnings_for_remote_update_files(wallet['archive'], wallet['paths'], remote_dir, _method_name)
            elif not self.model_context.is_ssh():
                archive_list.extract_all_database_wallets()
            else:
                found_wallets = archive_list.extract_all_database_wallets(self.upload_temporary_dir)
                if found_wallets:
                    self._upload_extracted_directory(WLSDeployArchive.ARCHIVE_DB_WALLETS_DIR)

    def extract_all_custom_files(self):
        """
        Extract all the custom files in the archive(s) to the target domain.
        Use SSH if the domain is on a remote system.
        """
        if self.model_context.is_remote():
            return

        archive_list = self.archive_helper
        if archive_list:
            if not self.model_context.is_ssh():
                archive_list.extract_custom_directory()
            else:
                custom_file_count = archive_list.extract_custom_directory(self.upload_temporary_dir)
                if custom_file_count:
                    self._upload_extracted_directory(WLSDeployArchive.ARCHIVE_CUSTOM_TARGET_DIR)

                    # deprecated location - we didn't extract these to the new location
                    self._upload_extracted_directory(WLSDeployArchive.DEPRECATED_CUSTOM_TARGET_DIR)

    def _upload_extracted_directory(self, archive_path):
        local_dir = self.path_helper.local_join(self.upload_temporary_dir, archive_path)
        if os.path.isdir(local_dir):
            remote_dir = self.path_helper.remote_join(self.model_context.get_domain_home(), archive_path)
            self.model_context.get_ssh_context().create_directories_if_not_exist(remote_dir)

            remote_parent_dir = \
                self.path_helper.get_remote_canonical_path(self.path_helper.remote_join(remote_dir, os.pardir))
            self.model_context.get_ssh_context().upload(local_dir, remote_parent_dir)
