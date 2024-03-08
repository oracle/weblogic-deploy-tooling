"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import re
from java.io import File
from java.io import FileOutputStream
from javax.xml.parsers import DocumentBuilderFactory
from javax.xml.transform import OutputKeys
from javax.xml.transform import TransformerFactory
from javax.xml.transform.dom import DOMSource
from javax.xml.transform.stream import StreamResult
from oracle.weblogic.deploy.util import WLSDeployArchive

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import LIBRARY
from wlsdeploy.aliases.model_constants import PARTITION
from wlsdeploy.aliases.model_constants import PLAN_DIR
from wlsdeploy.aliases.model_constants import PLAN_PATH
from wlsdeploy.aliases.model_constants import RESOURCES
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP_TEMPLATE
from wlsdeploy.aliases.model_constants import SOURCE_PATH
from wlsdeploy.aliases.model_constants import TARGETS
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy.applications_version_helper import ApplicationsVersionHelper
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.tool.util import appmodule_helper
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

    # FIXME - keep me in this class
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

    # FIXME - currently only used by online, seems relevant to both
    # FIXME - very similar to offline deployer __extract_app_or_lib_from_archive()
    def _extract_source_path_from_archive(self, source_path, model_type, model_name,
                                          upload_remote_directory=None):
        """
        Extract contents from the archive set for the specified source path.
        The contents may be a single file, or a directory with exploded content.
        :param source_path: the path to be extracted (previously checked to be under wlsdeploy)
        :param model_type: the model type (Application, etc.), used for logging
        :param model_name: the element name (my-app, etc.), used for logging
        :param upload_remote_directory: the source directory where we upload the deployments
        """
        _method_name = '_extract_source_path_from_archive'

        # model may have trailing slash on exploded source path
        if source_path.endswith('/') or source_path.endswith('\\'):
            source_path = source_path[:-1]

        # source path may be a single file (jar, war, etc.)
        if self.archive_helper.contains_file(source_path):
            if self.model_context.is_remote():
                self.archive_helper.extract_file(source_path, upload_remote_directory, False)
            elif self.model_context.is_ssh():
                self.archive_helper.extract_file(source_path, upload_remote_directory, False)
                self.upload_deployment_to_remote_server(source_path, upload_remote_directory)
            else:
                self.archive_helper.extract_file(source_path)

        # source path may be exploded directory in archive
        elif self.archive_helper.contains_path(source_path):
            # exploded format cannot be used for remote upload
            if self.model_context.is_remote():
                ex = exception_helper.create_deploy_exception('WLSDPLY-09341', model_name, source_path)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            if self.model_context.is_ssh():
                self.archive_helper.extract_directory(source_path, location=upload_remote_directory)
                self.upload_deployment_to_remote_server(source_path, upload_remote_directory)
            else:
                self.archive_helper.extract_directory(source_path)

        else:
            ex = exception_helper.create_deploy_exception('WLSDPLY-09330', model_type, model_name, source_path)
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

    def _fix_plan_file(self, plan_dir, plan_path):
        if string_utils.is_empty(plan_path):
            return

        plan_file_name = plan_path
        if self.path_helper.is_relative_local_path(plan_file_name) and not string_utils.is_empty(plan_dir):
            plan_file_name = self.path_helper.local_join(plan_dir, plan_file_name)

        if self.path_helper.is_relative_local_path(plan_file_name):
            if self.model_context.is_remote() or self.model_context.is_ssh():
                plan_file_name = self.path_helper.local_join(self.upload_temporary_dir, plan_file_name)
            else:
                plan_file_name = self.path_helper.local_join(self.model_context.get_domain_home(), plan_file_name)

        dbf = DocumentBuilderFactory.newInstance()
        db = dbf.newDocumentBuilder()
        document = db.parse(File(plan_file_name))
        document.normalizeDocument()
        elements = document.getElementsByTagName("config-root")

        if elements is not None and elements.getLength() > 0:
            element = elements.item(0)
            element.setNodeValue(plan_dir)
            element.setTextContent(plan_dir)
            ostream = FileOutputStream(plan_file_name)
            transformer_factory = TransformerFactory.newInstance()
            transformer = transformer_factory.newTransformer()
            transformer.setOutputProperty(OutputKeys.INDENT, "yes")
            transformer.setOutputProperty(OutputKeys.STANDALONE, "no")
            source = DOMSource(document)
            result = StreamResult(ostream)

            transformer.transform(source, result)

    def _validate_source_path_matches_deployment_type(self, model_name, model_type, model_source_path):
        _method_name = '_validate_source_path_matches_deployment_type'
        self.logger.entering(model_name, model_type, model_source_path,
                             class_name=self._class_name, method_name=_method_name)

        if not string_utils.is_empty(model_source_path):
            if model_type == LIBRARY:
                is_structured_app = False
                if not model_source_path.startswith(self.SHARED_LIBRARY_PATH_INTO_ARCHIVE):
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09342', model_name,
                                                                  self.SHARED_LIBRARY_PATH_INTO_ARCHIVE, model_source_path)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex
            elif model_type == APPLICATION:
                if model_source_path.startswith(self.APPLICATION_PATH_INTO_ARCHIVE):
                    is_structured_app = False
                elif model_source_path.startswith(self.STRUCTURED_APPLICATION_PATH_INTO_ARCHIVE):
                    is_structured_app = True
                else:
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09343', model_name,
                                                                  self.APPLICATION_PATH_INTO_ARCHIVE,
                                                                  self.STRUCTURED_APPLICATION_PATH_INTO_ARCHIVE,
                                                                  model_source_path)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex
            else:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09344', model_name, model_type)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
        else:
            is_structured_app = False

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=is_structured_app)
        return is_structured_app

    def _get_combined_model_plan_path(self, deployment_dict):
        """
        Combine the PlanDir and PlanPath attributes from the model dictionary
        to create a single path.
        :param deployment_dict: a model deployment dictionary
        :return: a full path for deployment plan
        """
        plan_dir = dictionary_utils.get_element(deployment_dict, PLAN_DIR)
        plan_path = dictionary_utils.get_element(deployment_dict, PLAN_PATH)
        full_path = None
        if not string_utils.is_empty(plan_path):
            if deployer_utils.is_path_into_archive(plan_path):
                full_path = plan_path
            elif deployer_utils.is_path_into_archive(plan_dir):
                full_path = self.path_helper.local_join(plan_dir, plan_path)
        return full_path

    def _validate_plan_file_to_extract(self, model_name, model_type, is_structured_app, model_plan_dir, model_plan_path):
        """
        Get the plan file to extract from the archive, if required.

        :param model_name:        the model name of the deployment
        :param model_type:        the model type of the deployment (i.e., APPLICATION or LIBRARY)
        :param is_structured_app: whether the application is a structured application
        :param model_plan_dir:    the model value of the deployment's PlanDir with any path tokens replaced
        :param model_plan_path:   the model value of the deployment's PlanPath with any path tokens replaced
        :return:                  The archive path of the plan file to extract.  Structured apps will always have
                                  a value of None since the plan will be under the directory extracted
        """
        _method_name = '_validate_plan_file_to_extract'
        self.logger.entering(model_name, model_type, is_structured_app, model_plan_dir, model_plan_path,
                             class_name=self._class_name, method_name=_method_name)

        plan_file_to_extract = None
        if not string_utils.is_empty(model_plan_path):
            if deployer_utils.is_path_into_archive(model_plan_path):
                plan_file_to_extract = model_plan_path
            elif deployer_utils.is_path_into_archive(model_plan_dir):
                plan_file_to_extract = self.path_helper.local_join(model_plan_dir, model_plan_path)

        if not string_utils.is_empty(plan_file_to_extract):
            if model_type == LIBRARY:
                if not plan_file_to_extract.startswith(self.SHARED_LIBRARY_PATH_INTO_ARCHIVE):
                    ex = exception_helper.create_deploy_exception('WLSDPLY-09345', LIBRARY, model_name,
                                                                  plan_file_to_extract,
                                                                  self.SHARED_LIBRARY_PATH_INTO_ARCHIVE)
                    self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex
            elif model_type == APPLICATION:
                if is_structured_app:
                    if not plan_file_to_extract.startswith(self.STRUCTURED_APPLICATION_PATH_INTO_ARCHIVE):
                        ex = exception_helper.create_deploy_exception('WLSDPLY-09345', APPLICATION,
                                                                      model_name, plan_file_to_extract,
                                                                      self.STRUCTURED_APPLICATION_PATH_INTO_ARCHIVE)
                        self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                        raise ex
                    else:
                        #
                        # Never extract the structured app plan file separately.  It must live under the structured
                        # app directory and will automatically be extracted when we extract the structured app
                        # directory.
                        #
                        plan_file_to_extract = None
                else:
                    if not plan_file_to_extract.startswith(self.APPLICATION_PATH_INTO_ARCHIVE):
                        ex = exception_helper.create_deploy_exception('WLSDPLY-09345', APPLICATION,
                                                                      model_name, plan_file_to_extract,
                                                                      self.APPLICATION_PATH_INTO_ARCHIVE)
                        self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                        raise ex
            else:
                ex = exception_helper.create_deploy_exception('WLSDPLY-09344', model_name, model_type)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=plan_file_to_extract)
        return plan_file_to_extract

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

    # FIXME - currently only used by online, seems relevant to both
    def _get_config_targets(self):
        self.wlst_helper.cd(TARGETS)
        config_targets = self.wlst_helper.lsc()
        self.wlst_helper.cd('..')
        return config_targets

    # FIXME - currently only used by online, seems relevant to both
    def _get_mt_names_from_location(self, app_location):
        dummy_location = LocationContext()
        token_name = self.aliases.get_name_token(dummy_location)
        dummy_location.add_name_token(token_name, self.model_context.get_domain_name())

        dummy_location.append_location(RESOURCE_GROUP_TEMPLATE)
        token_name = self.aliases.get_name_token(dummy_location)
        resource_group_template_name = app_location.get_name_for_token(token_name)
        dummy_location.pop_location()

        dummy_location.append_location(RESOURCE_GROUP)
        token_name = self.aliases.get_name_token(dummy_location)
        resource_group_name = app_location.get_name_for_token(token_name)
        dummy_location.pop_location()

        dummy_location.append_location(PARTITION)
        token_name = self.aliases.get_name_token(dummy_location)
        partition_name = app_location.get_name_for_token(token_name)
        dummy_location.pop_location()
        return resource_group_template_name, resource_group_name, partition_name

    # FIXME - keep this method in class
    # online deployer uses model_context.replace_token_string() directly
    def _replace_tokens_in_path(self, deployment_dict, path_attribute_name):
        """
        Get the path-related attribute out of the deployment's dictionary and replace any path tokens in it.
        No need to worry about a delimiter-separated string here since all the deployment attributes are not lists.

        :param deployment_dict:     the app or lib dictionary
        :param path_attribute_name: the name of the attribute to get
        :return:                    the dictionary value with any path tokens replaced
        """
        _method_name = '_replace_tokens_in_path'
        self.logger.entering(deployment_dict, path_attribute_name, class_name=self._class_name, method_name=_method_name)

        result = \
            self.model_context.replace_token_string(dictionary_utils.get_element(deployment_dict, path_attribute_name))

        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

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
            path = RESOURCES + '/' + PARTITION + '/' + part_name
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

    # def __online_deploy_apps_and_libs(self, base_location, is_restart_required=False):
    #     """
    #     Deploy shared libraries and applications in online mode.
    #
    #     This method tries to validate that the binaries have actually changed prior to deploy them.
    #     It also handles shared libraries that have changed by undeploying all of their referencing
    #     applications first, deploy the new shared library, and then redeploying the newest version
    #     of the referencing applications.
    #     :param base_location: the location where the apps/libraries are located
    #     :param is_restart_required: if online deployment, whether the previous changes require a server restart
    #     :raises: DeployException: if an error occurs
    #     """
    #     _method_name = '__online_deploy_apps_and_libs'
    #
    #     # Don't log the parent dictionary since it will be large
    #     self.logger.entering(self._parent_name, self._parent_type,
    #                          class_name=self._class_name, method_name=_method_name)
    #
    #     # Make copies of the model dictionary since we are going
    #     # to modify it as we build the deployment strategy.
    #     model_shared_libraries = copy.deepcopy(dictionary_utils.get_dictionary_element(self._parent_dict, LIBRARY))
    #     model_applications = copy.deepcopy(dictionary_utils.get_dictionary_element(self._parent_dict, APPLICATION))
    #
    #     if len(model_shared_libraries) == 0 and len(model_applications) == 0:
    #         # Nothing to do...
    #         return
    #
    #     existing_app_refs = self.__get_existing_apps(self._base_location)
    #     existing_lib_refs = self.__get_library_references(self._base_location)
    #
    #     # stop the app if the referenced shared library is newer or if the source path changes
    #     stop_app_list = list()
    #
    #     # applications to be stopped and undeployed
    #     stop_and_undeploy_app_list = list()
    #
    #     # libraries to be undeployed
    #     update_library_list = list()
    #
    #     lib_location = LocationContext(base_location).append_location(LIBRARY)
    #     # Go through the model libraries and find existing libraries that are referenced
    #     # by applications and compute a processing strategy for each library.
    #     self.__build_library_deploy_strategy(lib_location, model_shared_libraries, existing_lib_refs,
    #                                          stop_app_list, update_library_list)
    #
    #
    #     # Go through the model applications and compute the processing strategy for each application.
    #     app_location = LocationContext(base_location).append_location(APPLICATION)
    #     self.__build_app_deploy_strategy(app_location, model_applications, existing_app_refs,
    #                                      stop_and_undeploy_app_list)
    #
    #     # deployed_app_list is list of apps that has been deployed and started again
    #     deployed_app_list = []
    #
    #     #  For in-place update of shared libraries (i.e. impl/spec versions are not updated in the MANIFEST.MF for
    #     #   update), trying to do so will result in error just like the console.
    #     #
    #     # we will not automatically detect the referencing app and try to figure out the dependency graph and orders
    #     # for undeploying apps.
    #     #
    #     #   1.  It needs to be fully undeploy shared library referenced apps
    #     #   2.  But if the user only provides a sparse model for library update,  the sparse model will not have the
    #     #   original app and it will not be deployed again
    #     #   3.  There maybe transitive references by shared library and it will be difficult to handle processing order
    #     #    the full dependency graph
    #     #   4.  Console will result in error and ask user to undeploy the app first, so we are not trying to add new
    #     #   functionalities in wls.
    #     #
    #
    #     # user provide new versioned app, it must be stopped and undeployed first
    #     for app in stop_and_undeploy_app_list:
    #         self.__stop_app(app)
    #         self.__undeploy_app(app)
    #         self._delete_deployment_on_server(model_applications[app])
    #
    #     # library is updated, it must be undeployed first
    #     for lib in update_library_list:
    #         self.__undeploy_app(lib, library_module='true')
    #         self._delete_deployment_on_server(model_shared_libraries[lib])
    #
    #     self.__deploy_model_libraries(model_shared_libraries, lib_location)
    #     self.__deploy_model_applications(model_applications, app_location, deployed_app_list)
    #
    #     self.__start_all_apps(deployed_app_list, base_location, is_restart_required)
    #     self.logger.exiting(class_name=self._class_name, method_name=_method_name)

    # became __get_existing_library_references in online deployer
    # def __get_library_references(self, base_location):
    #     """
    #     Getting shared library referenced
    #     :param base_location: location context
    #     :return: dictonary of the library referenced details.
    #     """
    #     _method_name = '__get_library_references'
    #     self.logger.entering(str_helper.to_string(base_location),
    #                          class_name=self._class_name, method_name=_method_name)
    #
    #     # In 12.1.3 and older release this internal library is accidentally exposed in libraryruntimes mbean
    #
    #     internal_skip_list = ['bea_wls_async_response']
    #
    #     location = LocationContext(base_location).append_location(LIBRARY)
    #     token_name = self.aliases.get_name_token(location)
    #
    #     existing_libraries = OrderedDict()
    #     self.wlst_helper.domain_runtime()
    #     server_runtime_path = '/ServerRuntimes/'
    #     server_runtimes = self.wlst_helper.get_existing_object_list(server_runtime_path)
    #
    #     for server_runtime in server_runtimes:
    #         library_runtime_path = server_runtime_path + server_runtime + '/LibraryRuntimes/'
    #
    #         self.wlst_helper.domain_runtime()
    #         libs = self.wlst_helper.get_existing_object_list(library_runtime_path)
    #
    #         for lib in libs:
    #             if lib in internal_skip_list:
    #                 continue
    #             self.__get_library_reference_attributes(existing_libraries, lib, library_runtime_path, location,
    #                                                     token_name)
    #     return existing_libraries

    # moved to online deployer
    # def __is_builtin_library_or_app(self, path):
    #     oracle_home = self.model_context.get_oracle_home()
    #     return not deployer_utils.is_path_into_archive(path) and path.startswith(oracle_home)

    # moved to online deployer
    # def __handle_builtin_libraries(self, targets_not_changed, model_libs, lib,
    #                                existing_lib_targets_set, model_targets_set):
    #     if targets_not_changed or existing_lib_targets_set.issuperset(model_targets_set):
    #         self.__remove_lib_from_deployment(model_libs, lib)
    #     else:
    #         # adjust the targets to only the new ones
    #         # no need to check hash for weblogic distributed libraries
    #         adjusted_set = model_targets_set.difference(existing_lib_targets_set)
    #         adjusted_targets = ','.join(adjusted_set)
    #         model_libs[lib][TARGET] = adjusted_targets

    # moved to online deployer
    # def __stop_app(self, application_name, partition_name=None):
    #     _method_name = '__stop_app'
    #
    #     self.logger.info('WLSDPLY-09312', application_name, class_name=self._class_name, method_name=_method_name)
    #     progress = self.wlst_helper.stop_application(
    #         application_name, partition=partition_name,
    #         timeout=self.model_context.get_model_config().get_stop_app_timeout())
    #     while progress.isRunning():
    #         continue
    #     if progress.isFailed():
    #         ex = exception_helper.create_deploy_exception('WLSDPLY-09327', application_name, progress.getMessage())
    #         self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
    #         raise ex

    # moved to online deployer
    # def __start_app(self, application_name, partition_name=None):
    #     _method_name = '__start_app'
    #
    #     self.logger.info('WLSDPLY-09313', application_name, class_name=self._class_name, method_name=_method_name)
    #     self.wlst_helper.start_application(application_name, partition=partition_name,
    #                                        timeout=self.model_context.get_model_config().get_start_app_timeout())

    # moved to online deployer
    # def __undeploy_app(self, application_name, library_module='false', partition_name=None,
    #                    resource_group_template=None, targets=None):
    #     _method_name = '__undeploy_app'
    #
    #     type_name = APPLICATION
    #     if library_module == 'true':
    #         type_name = LIBRARY
    #
    #     if targets is not None:
    #         self.logger.info('WLSDPLY-09335', type_name, application_name, targets, class_name=self._class_name,
    #                          method_name=_method_name)
    #     else:
    #         self.logger.info('WLSDPLY-09314', type_name, application_name, class_name=self._class_name,
    #                          method_name=_method_name)
    #
    #     self.wlst_helper.undeploy_application(application_name, libraryModule=library_module, partition=partition_name,
    #                                           resourceGroupTemplate=resource_group_template,
    #                                           timeout=self.model_context.get_model_config().get_undeploy_timeout(),
    #                                           targets=targets)

    # moved to online deployer
    # def _delete_deployment_on_server(self, app_or_lib):
    #     """
    #     Remove deployed files on server after undeploy.
    #     :param source_path: source path in the model
    #     """
    #     # remove if ssh or local
    #     # For remote then the undeploy should already been removed the source
    #     #
    #     # Check for None and source path, a simple partial model may not have all the information
    #     # e.g. appDeployments:
    #     #        "!myear":
    #     #
    #     if app_or_lib is not None and SOURCE_PATH in app_or_lib:
    #         source_path = app_or_lib[SOURCE_PATH]
    #         if self.path_helper.is_relative_path(source_path):
    #             if self.model_context.is_ssh():
    #                 self.model_context.get_ssh_context().remove_file_or_directory(self.path_helper.remote_join(
    #                     self.model_context.get_domain_home(), source_path))
    #             else:
    #                 if not self.model_context.is_remote():
    #                     FileUtils.deleteDirectory(File(self.path_helper.local_join(
    #                         self.model_context.get_domain_home(), source_path)))

    # moved to online deployer
    # def __start_all_apps(self, deployed_app_list, base_location, is_restart_required=False):
    #     _method_name = '__start_all_apps'
    #     self.logger.entering(deployed_app_list, str_helper.to_string(base_location), is_restart_required,
    #                          class_name=self._class_name, method_name=_method_name)
    #
    #     temp_app_dict = OrderedDict()
    #     location = LocationContext(base_location).append_location(APPLICATION)
    #     token_name = self.aliases.get_name_token(location)
    #
    #     self.wlst_helper.server_config()
    #     for app in deployed_app_list:
    #         location.add_name_token(token_name, app)
    #         wlst_attribute_path = self.aliases.get_wlst_attributes_path(location)
    #         self.wlst_helper.cd(wlst_attribute_path)
    #         deployment_order = self.wlst_helper.get(DEPLOYMENT_ORDER)
    #
    #         if temp_app_dict.has_key(app) is False:
    #             temp_app_dict[app] = OrderedDict()
    #         temp_app_dict[app][DEPLOYMENT_ORDER] = deployment_order
    #
    #     start_order = self.__get_deployment_ordering(temp_app_dict)
    #     for app in start_order:
    #         if is_restart_required:
    #             self.logger.notification('WLSDPLY-09800', app, class_name=self._class_name, method_name=_method_name)
    #         else:
    #             self.__start_app(app)
    #
    #     self.logger.exiting(class_name=self._class_name, method_name=_method_name)

# no refs to this?
# def _add_ref_apps_to_stoplist(stop_and_undeploy_applist, lib_refs, lib_name):
#     """
#     Add the referencing apps for the specified shared library to the stop list.
#     :param stop_and_undeploy_applist: the stop list
#     :param lib_refs: the library references
#     :param lib_name: the library name
#     """
#     if lib_refs[lib_name].has_key('referencingApp'):
#         apps = lib_refs[lib_name]['referencingApp'].keys()
#         for app in apps:
#             if app not in stop_and_undeploy_applist:
#                 stop_and_undeploy_applist.append(app)

