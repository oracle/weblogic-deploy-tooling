"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import re
import shutil

from java.io import File
from java.io import FileOutputStream
from java.io import IOException
from javax.xml.parsers import DocumentBuilderFactory
from javax.xml.transform import OutputKeys
from javax.xml.transform import TransformerFactory
from javax.xml.transform.dom import DOMSource
from javax.xml.transform.stream import StreamResult
from oracle.weblogic.deploy.util import WLSDeployArchive

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import PARTITION
from wlsdeploy.aliases.model_constants import PLAN_DIR
from wlsdeploy.aliases.model_constants import PLAN_PATH
from wlsdeploy.aliases.model_constants import RESOURCES
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP_TEMPLATE
from wlsdeploy.aliases.model_constants import SOURCE_PATH
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy.applications_version_helper import ApplicationsVersionHelper
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.tool.util import appmodule_helper
from wlsdeploy.tool.util import structured_apps_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model_helper
from wlsdeploy.util import string_utils
from wlsdeploy.util import unicode_helper as str_helper
from wlsdeploy.util import variables


class ApplicationsDeployer(Deployer):
    """
    This class handles application and shared library deployment operations.  For applications/libraries that are
    in the archive file, WDT owns making sure that the application/library is deployed properly, which includes
    making sure that the files are provided to the remote server where applicable.  For applications/libraries that
    are not in the archive file, WDT simply deploys the application without worrying about how the file(s) get to
    the remote file system for the SSH use case.

    For applications, there are two distinct types of applications:
        - regular applications which consist of an archive file or exploded archive directory
        - application installation directories (which WDT calls "structured applications")

    The main difference is how the files in the archive are handled in that a structured application
    should extract the entire directory--not just the files pointed to in the model (e.g., SourcePath, PlanPath,
    PlanDir)

    Application and shared libraries may have a deployment plan.

    For offline deployment, everything is simple and always local.  For online deployment, there are 3 use cases:
        - normal: WDT and the AdminServer share the same file system so both archive and non-archive paths work
        - remote: WDT is using a different file system from the Admin Server.  All model paths, both into the
                  archive and not into the archive are always local and handled using the deployer's upload option.
        - ssh:    WDT is using a different file system from the Admin Server.  For archive paths, WDT extracts the
                  archive file contents and uploads them to the remote server prior to deploying them.  For any
                  non-archive path, we assume the file already exists on the remote server.  If the path is an absolute
                  path, we just use it.  If it is a relative path, we assume it is relative to the domain home directory.
    """

    APPLICATION_PATH_INTO_ARCHIVE = WLSDeployArchive.getPathForType(WLSDeployArchive.ArchiveEntryType.APPLICATION)
    SHARED_LIBRARY_PATH_INTO_ARCHIVE = WLSDeployArchive.getPathForType(WLSDeployArchive.ArchiveEntryType.SHARED_LIBRARY)
    STRUCTURED_APPLICATION_PATH_INTO_ARCHIVE = \
        WLSDeployArchive.getPathForType(WLSDeployArchive.ArchiveEntryType.STRUCTURED_APPLICATION)

    # these attributes are extracted internally, superclass should not extract
    EXTRACT_ATTRIBUTES = [SOURCE_PATH, PLAN_DIR, PLAN_PATH]

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE, base_location=LocationContext()):
        Deployer.__init__(self, model, model_context, aliases, wlst_mode)
        self._class_name = 'ApplicationsDeployer'
        self._base_location = base_location
        self._parent_dict, self._parent_name, self._parent_type = self.__get_parent_by_location(self._base_location)
        self.version_helper = ApplicationsVersionHelper(model_context, self.archive_helper)

    # Override
    def _extract_from_archive_if_needed(self, location, key, value):
        """
        Overriding this method so deployer superclass will not
        automatically extract these paths when processing attributes.
        """
        if key in self.EXTRACT_ATTRIBUTES:
            return value

        return Deployer._extract_from_archive_if_needed(self, location, key, value)

    ###########################################################################
    #                      Subclass utility methods                           #
    ###########################################################################

    def _does_deployment_to_delete_exist(self, deployment_name, existing_deployment_names, deployment_type='app'):
        """
        Verify that the specified app or library is in the existing list.  Since this app/library
        has been specified in the model as one to be deleted, this method will only consider
        it a match if the names match exactly.  That is, if the model specifies !myapp, this method
        will try to find myapp in the list of existing apps, skipping over version-qualified names
        like myapp#1.0 or myapp#1.0@1.1.3.
        :param deployment_name: the app or library name to be checked, with '!' still prepended
        :param existing_deployment_names: the list of existing apps from WLST
        :param deployment_type: the type for logging, 'app' for app, library otherwise
        :return: True if the item is in the list, False otherwise
        """
        _method_name = '_does_deployment_to_delete_exist'
        self.logger.entering(deployment_name, existing_deployment_names, deployment_type,
                             class_name=self._class_name, method_name=_method_name)

        found_deployment = True
        depl_name = model_helper.get_delete_item_name(deployment_name)
        if not depl_name in existing_deployment_names:
            found_deployment = False
            tokens = re.split(r'[#@]', depl_name)
            re_expr = '^' + tokens[0] + '[#@]*'
            r = re.compile(re_expr)
            matched_list = filter(r.match, existing_deployment_names)

            if deployment_type == 'app':
                err_key_list = 'WLSDPLY-09332'
                err_key = 'WLSDPLY-09334'
            else:
                err_key_list = 'WLSDPLY-09331'
                err_key = 'WLSDPLY-09333'

            if len(matched_list) > 0:
                self.logger.warning(err_key_list, depl_name, matched_list,
                                    class_name=self._class_name, method_name=_method_name)
            else:
                self.logger.warning(err_key, depl_name, class_name=self._class_name, method_name=_method_name)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=found_deployment)
        return found_deployment

    def _fixup_structured_app_plan_file_config_root(self, structured_app_name, structured_app_dict):
        _method_name = '_fixup_structured_app_plan_file_config_root'
        self.logger.entering(structured_app_name, structured_app_dict,
                             class_name=self._class_name, method_name=_method_name)

        # The plan file must exist for structured applications but we should only edit
        # it if we plan to move it--which means only if it is in the archive...
        plan_file_name = self._get_combined_model_plan_path(structured_app_dict)
        if deployer_utils.is_path_into_archive(plan_file_name):
            # We need to know where the file lives on the local file system so that it can be edited.
            if self.model_context.is_remote() or self.model_context.is_ssh():
                plan_file_name = self.path_helper.local_join(self.upload_temporary_dir, plan_file_name)
            else:
                plan_file_name = self.path_helper.local_join(self.model_context.get_domain_home(), plan_file_name)

            # The config-root of the deployment plan must be set to the location where the plan_dir will eventually live.
            future_plan_file_name = self._get_combined_model_plan_path(structured_app_dict)
            future_plan_file_name = self.path_helper.join(self.model_context.get_domain_home(), future_plan_file_name)
            plan_dir, __ = self.path_helper.split(future_plan_file_name)
            # Since the plan is processed by Java code, go ahead and replace any Windows separators with forward slashes.
            plan_dir = plan_dir.replace('\\', '/')

            if File(plan_file_name).isFile():
                dbf = DocumentBuilderFactory.newInstance()
                db = dbf.newDocumentBuilder()
                document = db.parse(File(plan_file_name))
                document.normalizeDocument()
                elements = document.getElementsByTagName("config-root")

                if elements is not None and elements.getLength() > 0:
                    element = elements.item(0)
                    element.setNodeValue(plan_dir)
                    element.setTextContent(plan_dir)
                    output_stream = None
                    try:
                        output_stream = FileOutputStream(plan_file_name)
                        transformer_factory = TransformerFactory.newInstance()
                        transformer = transformer_factory.newTransformer()
                        transformer.setOutputProperty(OutputKeys.INDENT, "yes")
                        transformer.setOutputProperty(OutputKeys.STANDALONE, "no")
                        source = DOMSource(document)
                        result = StreamResult(output_stream)

                        transformer.transform(source, result)
                    finally:
                        if output_stream is not None:
                            try:
                                output_stream.close()
                            except IOException:
                                # best effort only...
                                pass
            else:
                self.logger.warning('WLSDPLY-09352', structured_app_name, plan_file_name,
                                    class_name=self._class_name, method_name=_method_name)
        else:
            self.logger.fine('WLSDPLY-09353', structured_app_name, plan_file_name,
                             class_name=self._class_name, method_name=_method_name)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def _is_structured_app(self, app_name, app_dict):
        """
        Is the application represented by the dictionary a structured application?  It is the caller's responsibility
        to only call this method for applications and not shared libraries!

        :param app_name: the application name
        :param app_dict: the model dictionary representing the application
        :return: True, structured_app_dir if the application is a structured application; False, None otherwise
        """
        _method_name = 'is_structured_app'
        self.logger.entering(app_name, app_dict, class_name=self._class_name, method_name=_method_name)

        result = False
        structured_app_dir = None
        if app_dict:
            model_source_path = dictionary_utils.get_element(app_dict, SOURCE_PATH)
            combined_plan_path = self._get_combined_model_plan_path(app_dict)

            result, structured_app_dir = self.__is_archived_structured_app(model_source_path, combined_plan_path)

            if not result:
                result, structured_app_dir = \
                    self.__is_external_structured_app(app_name, model_source_path, combined_plan_path)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=[result, structured_app_dir])
        return result, structured_app_dir

    def _get_combined_model_plan_path(self, deployment_dict):
        """
        Combine the PlanDir and PlanPath attributes from the model dictionary
        to create a single path.
        :param deployment_dict: a model deployment dictionary
        :return: a full path for deployment plan
        """
        _method_name = '_get_combined_model_plan_path'
        self.logger.entering(deployment_dict, class_name=self._class_name, method_name=_method_name)

        plan_dir = dictionary_utils.get_element(deployment_dict, PLAN_DIR)
        plan_path = dictionary_utils.get_element(deployment_dict, PLAN_PATH)

        full_path = None
        if not string_utils.is_empty(plan_path):
            if string_utils.is_empty(plan_dir):
                full_path = plan_path
            elif deployer_utils.is_path_into_archive(plan_path):
                full_path = plan_path
            elif deployer_utils.is_path_into_archive(plan_dir):
                full_path = self.path_helper.local_join(plan_dir, plan_path)
            else:
                # not an archive location...
                # for the SSH use case with the plan not in the archive,
                # we assume that the path is already present on the remote machine
                if self.model_context.is_ssh():
                    full_path = self.path_helper.remote_join(plan_dir, plan_path)
                else:
                    full_path = self.path_helper.local_join(plan_dir, plan_path)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=full_path)
        return full_path

    def _get_structured_app_archive_path(self, model_name, source_path_to_extract, plan_file_to_extract):
        _method_name = '_get_structured_app_archive_path'
        self.logger.entering(model_name, source_path_to_extract, plan_file_to_extract,
                             class_name=self._class_name, method_name=_method_name)

        #
        # We have already validated that the source path starts with wlsdeploy/structuredApplications
        # so just return the path to the structured application top-level directory.
        #
        start_index = len(self.STRUCTURED_APPLICATION_PATH_INTO_ARCHIVE) + 1
        first_remaining_slash_index = source_path_to_extract[start_index:].find('/')
        if first_remaining_slash_index == -1:
            result = source_path_to_extract
        else:
            end_index = start_index + first_remaining_slash_index
            if len(source_path_to_extract) > end_index:
                result = source_path_to_extract[0:end_index]
            else:
                ex = exception_helper.create_deploy_exception(
                    'WLSDPLY-09436', model_name, source_path_to_extract,
                    self.STRUCTURED_APPLICATION_PATH_INTO_ARCHIVE)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

        if plan_file_to_extract is not None and not plan_file_to_extract.startswith(result):
            ex = exception_helper.create_deploy_exception('WLSDPLY-09437', model_name,
                                                          result, plan_file_to_extract)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def _replace_path_tokens_for_deployment(self, deployment_type, deployment_name, deployment_dict):
        _method_name = '_replace_path_tokens_for_deployment'
        self.logger.entering(deployment_type, deployment_name, deployment_dict,
                             class_name=self._class_name, method_name=_method_name)

        self.model_context.replace_tokens(deployment_type, deployment_name, SOURCE_PATH, deployment_dict)
        self.model_context.replace_tokens(deployment_type, deployment_name, PLAN_DIR, deployment_dict)
        self.model_context.replace_tokens(deployment_type, deployment_name, PLAN_PATH, deployment_dict)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def _substitute_appmodule_token(self, path, module_type):
        # we need to substitute any token in the app module xml file
        if not string_utils.is_empty(path) and self.version_helper.is_module_type_app_module(module_type):
            abspath = path
            if self.path_helper.is_relative_local_path(path):
                abspath = self.path_helper.local_join(self.model_context.get_domain_home(), path)

            original_variables = {}
            variable_file = self.model_context.get_variable_file()
            if variable_file is not None and os.path.exists(variable_file):
                original_variables = variables.load_variables(variable_file)

            fh = open(abspath, 'r')
            text = fh.read()
            fh.close()
            newtext = variables.substitute_value(text, original_variables, self.model_context)
            # only jdbc and jms for now
            if module_type == 'jdbc':
                newtext = appmodule_helper.process_jdbc_appmodule_xml(newtext, self.model_context)
            elif module_type == 'jms':
                newtext = appmodule_helper.process_jms_appmodule_xml(newtext, self.model_context)

            newfh = open(abspath, 'w')
            newfh.write(newtext)
            newfh.close()

    def _extract_deployment_from_archive(self, deployment_name, deployment_type, deployment_dict):
        _method_name = '_extract_deployment_from_archive'
        self.logger.entering(deployment_name, deployment_type, deployment_dict,
                             class_name=self._class_name, method_name=_method_name)

        source_path = dictionary_utils.get_element(deployment_dict, SOURCE_PATH)
        combined_path_path = self._get_combined_model_plan_path(deployment_dict)
        if deployer_utils.is_path_into_archive(source_path) or deployer_utils.is_path_into_archive(combined_path_path):
            if self.archive_helper is None:
                ex = exception_helper.create_deploy_exception(
                    'WLSDPLY-09303', deployment_type, deployment_name)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            is_structured_app = False
            structured_app_dir = None
            if deployment_type == APPLICATION:
                is_structured_app, structured_app_dir = self._is_structured_app(deployment_name, deployment_dict)

            if is_structured_app:
                # is_structured_app() only returns true if both the app and the plan have similar paths.
                # Since the caller already verified the app or plan was in the archive, it is safe to assume
                # both are in the archive.
                if self.archive_helper.contains_path(structured_app_dir):
                    self._extract_directory_from_archive(structured_app_dir, deployment_name, deployment_type)
            else:
                model_source_path = dictionary_utils.get_element(deployment_dict, SOURCE_PATH)
                plan_file_to_extract = self._get_combined_model_plan_path(deployment_dict)

                if not string_utils.is_empty(model_source_path) and \
                        (model_source_path.endswith('/') or model_source_path.endswith('\\')):
                    # model may have trailing slash on exploded source path
                    source_path_to_extract = model_source_path[:-1]
                else:
                    source_path_to_extract = model_source_path

                # The caller only verified that either the app or the plan was in the archive; therefore,
                # we have to validate each one before trying to extract.
                if self.archive_helper.is_path_into_archive(source_path_to_extract):
                    # source path may be a single file (jar, war, etc.) or an exploded directory
                    if self.archive_helper.contains_file(source_path_to_extract):
                        self._extract_file_from_archive(source_path_to_extract, deployment_name, deployment_type)
                    elif self.archive_helper.contains_path(source_path_to_extract):
                        self._extract_directory_from_archive(source_path_to_extract, deployment_name, deployment_type)
                    else:
                        ex = exception_helper.create_deploy_exception(
                            'WLSDPLY-09330', deployment_type, deployment_name, source_path_to_extract)
                        self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                        raise ex

                if self.archive_helper.is_path_into_archive(plan_file_to_extract):
                    self._extract_file_from_archive(plan_file_to_extract, deployment_name, deployment_type)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    def _extract_directory_from_archive(self, directory_path, _deployment_name, _deployment_type):
        """
        Extract the specified directory path from the archive.
        The default behavior is to extract to the local file system.
        Subclasses can this method for other cases (ssh and remote).
        :param directory_path: the path to extract
        :param _deployment_name: the deployment name (myApp), can be used for logging
        :param _deployment_type: the deployment type (Application, etc.), can be used for logging
        """
        # When extracting a directory, delete the old directory if it already exists so that the
        # extracted directory is exactly what is in the archive file.
        existing_directory_path = \
            self.path_helper.local_join(self.model_context.get_domain_home(), directory_path)
        if os.path.isdir(existing_directory_path):
            shutil.rmtree(existing_directory_path)
        self.archive_helper.extract_directory(directory_path)

    def _extract_file_from_archive(self, file_path, _deployment_name, _deployment_type):
        """
        Extract the specified file path from the archive.
        The default behavior is to extract to the local file system.
        Subclasses can this method for other cases (ssh and remote).
        :param file_path: the path to extract
        :param _deployment_name: the deployment name (myApp), can be used for logging
        :param _deployment_type: the deployment type (Application, etc.), can be used for logging
        """
        self.archive_helper.extract_file(file_path)

    ###########################################################################
    #                      Private utility methods                            #
    ###########################################################################

    def __get_parent_by_location(self, location):
        _method_name = '_get_parent_by_location'

        self.logger.entering(str_helper.to_string(location), class_name=self._class_name, method_name=_method_name)
        location_folders = location.get_model_folders()
        if len(location_folders) == 0:
            parent_dict = self.model.get_model_app_deployments()
            self.logger.exiting(class_name=self._class_name, method_name=_method_name,
                                result=[self.model_context.get_domain_name(), 'Domain'])
            return parent_dict, self.model_context.get_domain_name(), 'Domain'

        top_folder = location_folders[0]
        resources = self.model.get_model_resources()
        if top_folder == RESOURCE_GROUP:
            result_dict, result_name = \
                self.__get_parent_dict_and_name_for_resource_group(location, resources, RESOURCES)
            result_type = RESOURCE_GROUP

        elif top_folder == RESOURCE_GROUP_TEMPLATE:
            if RESOURCE_GROUP_TEMPLATE not in resources:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09305', RESOURCE_GROUP_TEMPLATE, RESOURCES)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            rgt_token = self.aliases.get_name_token(location)
            rgt_name = location.get_name_for_token(rgt_token)
            if rgt_name is None:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09306', rgt_token, RESOURCE_GROUP_TEMPLATE)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            elif rgt_name not in resources[RESOURCE_GROUP_TEMPLATE]:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09307', rgt_name,
                                                              RESOURCE_GROUP_TEMPLATE, RESOURCES)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            result_dict = resources[RESOURCE_GROUP_TEMPLATE][rgt_name]
            result_name = rgt_name
            result_type = RESOURCE_GROUP_TEMPLATE

        elif top_folder == PARTITION:
            if PARTITION not in resources:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09305', PARTITION, RESOURCES)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            part_location = LocationContext().append_location(PARTITION)
            part_token = self.aliases.get_name_token(part_location)
            part_name = location.get_name_for_token(part_token)
            if part_name is None:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09306', part_token, PARTITION)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            elif part_name not in resources[PARTITION]:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09307', part_name, PARTITION, RESOURCES)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            part_dict = resources[PARTITION][part_name]
            path = '%s/%s/%s' % (RESOURCES, PARTITION, part_name)
            result_dict, result_name = self.__get_parent_dict_and_name_for_resource_group(location, part_dict, path)
            result_type = RESOURCE_GROUP

        else:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09308', top_folder)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name,
                            result=[result_name, result_type])
        return result_dict, result_name, result_type

    def __get_parent_dict_and_name_for_resource_group(self, location, parent_dict, parent_path):
        _method_name = '__get_parent_dict_and_name_for_resource_group'
        self.logger.entering(str_helper.to_string(location), parent_path,
                             class_name=self._class_name, method_name=_method_name)

        if RESOURCE_GROUP not in parent_dict:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09305', RESOURCE_GROUP, parent_path)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        rg_token = self.aliases.get_name_token(location)
        rg_name = location.get_name_for_token(rg_token)
        if rg_name is None:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09306', rg_token, RESOURCE_GROUP)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        elif rg_name not in parent_dict[RESOURCE_GROUP]:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09307', rg_name, RESOURCE_GROUP, parent_path)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        return parent_dict[RESOURCE_GROUP][rg_name], rg_name

    def __is_archived_structured_app(self, model_source_path, combined_plan_path):
        _method_name = '__is_archived_structured_app'
        self.logger.entering(model_source_path, combined_plan_path,
                             class_name=self._class_name, method_name=_method_name)

        result = False
        structured_app_dir = None
        if not string_utils.is_empty(model_source_path) and not string_utils.is_empty(combined_plan_path):
            source_path_to_compare = model_source_path.replace('\\', '/')
            plan_path_to_compare = combined_plan_path.replace('\\', '/')

            if self.archive_helper:
                if source_path_to_compare.startswith(self.STRUCTURED_APPLICATION_PATH_INTO_ARCHIVE) and \
                        plan_path_to_compare.startswith(self.STRUCTURED_APPLICATION_PATH_INTO_ARCHIVE):
                    leading_slash_index = len(self.STRUCTURED_APPLICATION_PATH_INTO_ARCHIVE)
                    trailing_slash_index = source_path_to_compare.find('/', leading_slash_index + 1)
                    if trailing_slash_index > 0:
                        structured_app_dir = model_source_path[0:trailing_slash_index]
                        result = plan_path_to_compare.startswith(structured_app_dir + '/')

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=[result, structured_app_dir])
        return result, structured_app_dir

    def __is_external_structured_app(self, app_name, model_source_path, combined_plan_path):
        _method_name = '__is_external_structured_app'
        self.logger.entering(app_name, model_source_path, combined_plan_path,
                             class_name=self._class_name, method_name=_method_name)

        structured_app_dir = None
        if not string_utils.is_empty(model_source_path) and not string_utils.is_empty(combined_plan_path) \
                and not WLSDeployArchive.isPathIntoArchive(model_source_path):
            structured_app_dir = \
                structured_apps_helper.get_structured_app_install_root(app_name, model_source_path, combined_plan_path,
                                                                       ExceptionType.DEPLOY)
        result = not string_utils.is_empty(structured_app_dir)

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=[result, structured_app_dir])
        return result, structured_app_dir
