"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from oracle.weblogic.deploy.util import WLSDeployArchive

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.create.custom_folder_helper import CustomFolderHelper
from wlsdeploy.tool.util.attribute_setter import AttributeSetter
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model_helper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util.model import Model
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.weblogic_helper import WebLogicHelper
from wlsdeploy.tool.deploy import deployer_utils


class Creator(object):
    """
    The base class used by the DomainCreator.
    """
    __class_name = 'Creator'

    def __init__(self, model, model_context, aliases, exception_type=ExceptionType.CREATE,
                 logger=PlatformLogger('wlsdeploy.create')):

        self.logger = logger
        self.aliases = aliases
        self._exception_type = exception_type
        self.wlst_helper = WlstHelper(exception_type)
        self.model = Model(model)
        self.model_context = model_context
        self.wls_helper = WebLogicHelper(self.logger)
        self.attribute_setter = AttributeSetter(self.model_context, self.aliases, exception_type)
        self.custom_folder_helper = CustomFolderHelper(self.aliases, self.logger, self.model_context, exception_type)

        # Must be initialized by the subclass since only it has
        # the knowledge required to compute the domain name.
        self.archive_helper = None
        self.files_to_extract_from_archive = list()

    def _create_named_mbeans(self, type_name, model_nodes, base_location, log_created=False, delete_now=True):
        """
        Create the specified type of MBeans that support multiple instances in the specified location.
        :param type_name: the model folder type
        :param model_nodes: the model dictionary of the specified model folder type
        :param base_location: the base location object to use to create the MBeans
        :param log_created: whether or not to log created at INFO level, by default it is logged at the FINE level
        :raises: CreateException: if an error occurs
        """
        _method_name = '_create_named_mbeans'

        self.logger.entering(type_name, str_helper.to_string(base_location), log_created,
                             class_name=self.__class_name, method_name=_method_name)
        if model_nodes is None or len(model_nodes) == 0 or not self._is_type_valid(base_location, type_name):
            return

        location = LocationContext(base_location).append_location(type_name)
        self._process_flattened_folder(location)

        token_name = self.aliases.get_name_token(location)
        create_path = self.aliases.get_wlst_create_path(location)
        list_path = self.aliases.get_wlst_list_path(location)
        existing_folder_names = self._get_existing_folders(list_path)
        for model_name in model_nodes.keys():
            name = self.wlst_helper.get_quoted_name_for_wlst(model_name)
            if model_helper.is_delete_name(name):
                if delete_now:
                    deployer_utils.delete_named_element(location, name, existing_folder_names, self.aliases)
                continue

            if token_name is not None:
                location.add_name_token(token_name, name)

            wlst_type, wlst_name = self.aliases.get_wlst_mbean_type_and_name(location)
            if wlst_name not in existing_folder_names:
                if log_created:
                    self.logger.info('WLSDPLY-12100', type_name, name,
                                     class_name=self.__class_name, method_name=_method_name)
                else:
                    self.logger.fine('WLSDPLY-12100', type_name, name,
                                     class_name=self.__class_name, method_name=_method_name)
                self.wlst_helper.create_and_cd(self.aliases, wlst_type, wlst_name, location, create_path)
            else:
                if log_created:
                    self.logger.info('WLSDPLY-12101', type_name, name,
                                     class_name=self.__class_name, method_name=_method_name)
                else:
                    self.logger.fine('WLSDPLY-12101', type_name, name,
                                     class_name=self.__class_name, method_name=_method_name)

                attribute_path = self.aliases.get_wlst_attributes_path(location)
                self.wlst_helper.cd(attribute_path)

            child_nodes = dictionary_utils.get_dictionary_element(model_nodes, name)
            self._process_child_nodes(location, child_nodes)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _create_mbean(self, type_name, model_nodes, base_location, log_created=False):
        """
        Create the specified type of MBean that support a single instance in the specified location.
        :param type_name: the model folder type
        :param model_nodes: the model dictionary of the specified model folder type
        :param base_location: the base location object to use to create the MBean
        :param log_created: whether or not to log created at INFO level, by default it is logged at the FINE level
        :raises: CreateException: if an error occurs
        """
        _method_name = '_create_mbean'
        self.logger.entering(type_name, str_helper.to_string(base_location), log_created,
                             class_name=self.__class_name, method_name=_method_name)

        if model_nodes is None or len(model_nodes) == 0:
           self.logger.fine('WLSDPLY-12568', type_name, class_name=self.__class_name, method_name=_method_name)

        if not self._is_type_valid(base_location, type_name):
            return

        location = LocationContext(base_location).append_location(type_name)
        result, message = self.aliases.is_version_valid_location(location)
        if result == ValidationCodes.VERSION_INVALID:
            self.logger.warning('WLSDPLY-12123', message,
                                class_name=self.__class_name, method_name=_method_name)
            return

        create_path = self.aliases.get_wlst_create_path(location)
        existing_folder_names = self._get_existing_folders(create_path)

        mbean_type, mbean_name = self.aliases.get_wlst_mbean_type_and_name(location)

        token_name = self.aliases.get_name_token(location)
        if token_name is not None:
            if self.aliases.requires_unpredictable_single_name_handling(location):
                existing_subfolder_names = deployer_utils.get_existing_object_list(location, self.aliases)
                if len(existing_subfolder_names) > 0:
                    mbean_name = existing_subfolder_names[0]

            location.add_name_token(token_name, mbean_name)

        self._process_flattened_folder(location)
        if mbean_type not in existing_folder_names:
            if log_created:
                self.logger.info('WLSDPLY-12102', type_name, class_name=self.__class_name, method_name=_method_name)
            else:
                self.logger.fine('WLSDPLY-12102', type_name, class_name=self.__class_name, method_name=_method_name)

            self.wlst_helper.create_and_cd(self.aliases, mbean_type, mbean_name, location, create_path)
        else:
            if log_created:
                self.logger.info('WLSDPLY-20013', type_name, class_name=self.__class_name, method_name=_method_name)
            else:
                self.logger.fine('WLSDPLY-12102', type_name, class_name=self.__class_name, method_name=_method_name)

            attribute_path = self.aliases.get_wlst_attributes_path(location)
            self.wlst_helper.cd(attribute_path)

        self._process_child_nodes(location, model_nodes)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _create_named_subtype_mbeans(self, type_name, model_nodes, base_location, log_created=False):
        """
        Create the specified type of MBeans that support multiple instances, and require an artificial subtype
        layer after each name.
        :param type_name: the model folder type
        :param model_nodes: the model dictionary of the specified model folder type
        :param base_location: the base location object to use to create the MBeans
        :param log_created: whether or not to log created at INFO level, by default it is logged at the FINE level
        :raises: CreateException: if an error occurs
        """
        # There is no default behavior for this method. Subclasses (currently only SecurityProviderCreator)
        # will implement specialized behavior.
        pass

    def _create_subfolders(self, location, model_nodes):
        """
        Create the child MBean folders at the specified location.
        :param location: the location
        :param model_nodes: the model dictionary
        :raises: CreateException: if an error occurs
        """
        _method_name = '_create_subfolders'

        self.logger.entering(location.get_folder_path(), class_name=self.__class_name, method_name=_method_name)
        model_subfolder_names = self.aliases.get_model_subfolder_names(location)
        for key in model_nodes:
            if key in model_subfolder_names:
                subfolder_nodes = model_nodes[key]
                # don't check for empty subfolder nodes here, some create methods allow them

                sub_location = LocationContext(location).append_location(key)

                if self.aliases.requires_artificial_type_subfolder_handling(sub_location):
                    self.logger.finest('WLSDPLY-12116', key, str_helper.to_string(sub_location), subfolder_nodes,
                                       class_name=self.__class_name, method_name=_method_name)
                    self._create_named_subtype_mbeans(key, subfolder_nodes, location, True)
                elif self.aliases.supports_multiple_mbean_instances(sub_location):
                    self.logger.finest('WLSDPLY-12109', key, str_helper.to_string(sub_location), subfolder_nodes,
                                       class_name=self.__class_name, method_name=_method_name)
                    self._create_named_mbeans(key, subfolder_nodes, location)
                elif self.aliases.is_artificial_type_folder(sub_location):
                    # these should have been handled inside create_named_subtype_mbeans
                    ex = exception_helper.create_create_exception('WLSDPLY-12120', str_helper.to_string(sub_location),
                                                                  key, str_helper.to_string(location))
                    self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                    raise ex
                else:
                    self.logger.finest('WLSDPLY-12110', key, str_helper.to_string(sub_location), subfolder_nodes,
                                       class_name=self.__class_name, method_name=_method_name)
                    self._create_mbean(key, subfolder_nodes, location)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _process_child_nodes(self, location, model_nodes):
        """
        Process the model nodes at the specified location.
        The default behavior is to process attributes, then sub-folders.
        Sub-classes may override to reverse this order, or for other special processing.
        :param location: the location where the nodes should be applied
        :param model_nodes: the model dictionary of the nodes to be applied
        :raises: CreateException: if an error occurs
        """
        _method_name = '_process_child_nodes'

        self.logger.finest('WLSDPLY-12111', self.aliases.get_model_folder_path(location),
                           self.wlst_helper.get_pwd(), class_name=self.__class_name, method_name=_method_name)
        self._set_attributes(location, model_nodes)
        self._create_subfolders(location, model_nodes)

    def _set_attributes(self, location, model_nodes):
        """
        Set the attributes for the MBean at the specified location.
        :param location: the location
        :param model_nodes: the model dictionary
        :raises: CreateException: if an error occurs
        """
        _method_name = '_set_attributes'

        model_attribute_names = self.aliases.get_model_attribute_names_and_types(location)
        password_attribute_names = self.aliases.get_model_password_type_attribute_names(location)
        set_method_map = self.aliases.get_model_mbean_set_method_attribute_names_and_types(location)
        uses_path_tokens_attribute_names = self.aliases.get_model_uses_path_tokens_attribute_names(location)
        model_folder_path = self.aliases.get_model_folder_path(location)
        pwd = self.wlst_helper.get_pwd()

        for key, value in model_nodes.iteritems():
            if key in model_attribute_names:
                if key in set_method_map:
                    self.logger.finest('WLSDPLY-12112', key, pwd, model_folder_path,
                                       class_name=self.__class_name, method_name=_method_name)
                    self._set_mbean_attribute(location, key, value, set_method_map)
                elif key in password_attribute_names:
                    self.logger.finest('WLSDPLY-12113', key, pwd, model_folder_path,
                                       class_name=self.__class_name, method_name=_method_name)
                    self._set_attribute(location, key, value, uses_path_tokens_attribute_names, masked=True)
                else:
                    self.logger.finest('WLSDPLY-12113', key, pwd, model_folder_path,
                                       class_name=self.__class_name, method_name=_method_name)
                    self._set_attribute(location, key, value, uses_path_tokens_attribute_names)

    def _set_mbean_attribute(self, location, model_key, model_value, set_method_map):
        """
        Set the attributes for the MBean that require an MBean value to set at the specified location.
        :param location: the location
        :param model_key: the model attribute name
        :param model_value: the model attribute value
        :param set_method_map: the set method map that maps the attribute names requiring MBean
                               values to the attribute setter method name
        :raises: CreateException: if an error occurs
        """
        _method_name = '_set_mbean_attribute'

        set_method_info = dictionary_utils.get_dictionary_element(set_method_map, model_key)
        set_method_name = dictionary_utils.get_element(set_method_info, 'set_method')

        if set_method_name is not None:
            try:
                self.logger.finest('WLSDPLY-12114', model_key, model_value, set_method_name,
                                   class_name=self.__class_name, method_name=_method_name)
                set_method = getattr(self.attribute_setter, set_method_name)
                set_method(location, model_key, model_value, None)
            except AttributeError, ae:
                ex = exception_helper.create_create_exception('WLSDPLY-12104', set_method_name, model_key,
                                                              self.aliases.get_model_folder_path(location),
                                                              error=ae)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
        else:
            ex = exception_helper.create_create_exception('WLSDPLY-12105', model_key,
                                                          self.aliases.get_model_folder_path(location))
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

    def _set_attribute(self, location, model_name, model_value, uses_path_tokens_names, masked=False):
        """
        Set the specified attribute at the specified location to the specified value.
        :param location: the location
        :param model_name: the model attribute name
        :param model_value: the model attribute value
        :param: uses_path_token_names: the list of model attribute names that use file system path tokens
        :param masked: whether or not to mask the attribute value in the log
        :raises: CreateException: if an error occurs
        """
        _method_name = '_set_attribute'
        if (model_name in uses_path_tokens_names) and (model_value is not None):
            self._extract_archive_files(location, model_name, model_value)

        wlst_name, wlst_value = self.aliases.get_wlst_attribute_name_and_value(location, model_name, model_value)

        if wlst_name is None:
            self.logger.info('WLSDPLY-12106', model_name, self.aliases.get_model_folder_path(location),
                             class_name=self.__class_name, method_name=_method_name)
        elif wlst_value is None:
            logged_value = model_value
            if masked:
                logged_value = '<masked>'
            self.logger.info('WLSDPLY-12107', model_name, logged_value,
                             self.aliases.get_model_folder_path(location),
                             class_name=self.__class_name, method_name=_method_name)
        else:
            logged_value = wlst_value
            if masked:
                logged_value = '<masked>'
            self.logger.finest('WLSDPLY-12115', wlst_name, logged_value,
                               class_name=self.__class_name, method_name=_method_name)
            self.wlst_helper.set(wlst_name, wlst_value, masked=masked)

    def _extract_archive_files(self, location, model_name, model_value):
        """
        Extract any archive files associated with the specified model attribute value.
        The attribute has already been determined to use path tokens.
        :param location: the location of the attribute
        :param model_name: the model attribute name
        :param model_value: the model attribute value
        :raises: CreateException: if an error occurs
        """
        _method_name = '_extract_archive_files'

        # model value should be a list, comma-delimited string, or string
        model_paths = model_value
        if isinstance(model_value, basestring):
            model_paths = model_value.split(',')

        for model_path in model_paths:
            model_path = model_path.strip()

            # check for path starting with "wlsdeploy/".
            # skip classpath libraries, they are extracted elsewhere.
            if WLSDeployArchive.isPathIntoArchive(model_path) and not WLSDeployArchive.isClasspathEntry(model_path):
                if self.archive_helper is not None:
                    if self.archive_helper.contains_file(model_path):
                        #
                        # We cannot extract the files until the domain directory exists
                        # so add them to the list so that they can be extracted after
                        # domain creation completes.
                        #
                        self.files_to_extract_from_archive.append(model_path)
                    else:
                        path = self.aliases.get_model_folder_path(location)
                        archive_file_name = self.model_context.get_archive_file_name()
                        ex = exception_helper.create_create_exception('WLSDPLY-12121', model_name, path,
                                                                      model_path, archive_file_name)
                        self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                        raise ex
                else:
                    path = self.aliases.get_model_folder_path(location)
                    ex = exception_helper.create_create_exception('WLSDPLY-12122', model_name, path, model_path)
                    self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                    raise ex

    def _is_type_valid(self, location, type_name):
        """
        Verify that the specified location in valid for the current WLS version.
        A warning is logged if the location is not valid.
        :param location: the location to be checked
        :param type_name: the type location to be checked
        :return: True if the location is valid, False otherwise
        :raises: CreateException: if an error occurs
        """
        _method_name = '_check_location'

        code, message = self.aliases.is_valid_model_folder_name(location, type_name)
        result = False
        if code == ValidationCodes.VALID:
            result = True
        elif code == ValidationCodes.VERSION_INVALID:
            path = self._format_model_path(location, type_name)
            self.logger.warning('WLSDPLY-12108', path, message,
                                class_name=self.__class_name, method_name=_method_name)
        #
        return result

    def _process_flattened_folder(self, location):
        """
        Create the flattened folder at the specified location if one exists.
        :param location: the location
        :raises: CreateException: if an error occurs
        """
        flattened_folder_info = self.aliases.get_wlst_flattened_folder_info(location)
        if flattened_folder_info is not None:
            create_path = self.aliases.get_wlst_flattened_folder_create_path(location)
            mbean_type = flattened_folder_info.get_mbean_type()
            mbean_name = flattened_folder_info.get_mbean_name()
            existing_folders = self._get_existing_folders(create_path)
            if mbean_type not in existing_folders:
                self.wlst_helper.create(mbean_name, mbean_type)

            path_token = flattened_folder_info.get_path_token()
            location.add_name_token(path_token, mbean_name)

    def _get_existing_folders(self, wlst_path):
        """
        Get the list of existing folders at the specified WLST path.
        :param wlst_path: the WLST path
        :return: the list of existing folders, or an empty list if none exist
        """
        return self.wlst_helper.get_existing_object_list(wlst_path)

    def _format_model_path(self, location, name):
        """
        Get the model path of the specified name.
        :param location: the location
        :param name: the name to append to the model folder path
        :return: the path of the specified name
        """
        path = self.aliases.get_model_folder_path(location)
        if not path.endswith('/'):
            path += '/'
        path += name
        return path
