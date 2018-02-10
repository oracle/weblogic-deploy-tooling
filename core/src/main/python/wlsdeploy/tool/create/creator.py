"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.attribute_setter import AttributeSetter
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.weblogic_helper import WebLogicHelper


class Creator(object):
    """
    The base class used by the DomainCreator.
    """
    __class_name = 'Creator'

    def __init__(self, model, model_context, aliases):
        self.logger = PlatformLogger('wlsdeploy.create')
        self.aliases = aliases
        self.alias_helper = AliasHelper(self.aliases, self.logger, ExceptionType.CREATE)
        self.wlst_helper = WlstHelper(self.logger, ExceptionType.CREATE)
        self.model = model
        self.model_context = model_context
        self.wls_helper = WebLogicHelper(self.logger)
        self.attribute_setter = AttributeSetter(self.aliases, self.logger, ExceptionType.CREATE)
        return

    def _create_named_mbeans(self, type_name, model_nodes, base_location, log_created=False):
        """
        Create the specified type of MBeans that support multiple instances in the specified location.
        :param type_name: the model folder type
        :param model_nodes: the model dictionary of the specified model folder type
        :param base_location: the base location object to use to create the MBeans
        :param log_created: whether or not to log created at INFO level, by default it is logged at the FINE level
        :raises: CreateException: if an error occurs
        """
        _method_name = '_create_named_mbeans'

        self.logger.entering(type_name, str(base_location), log_created,
                             class_name=self.__class_name, method_name=_method_name)
        if model_nodes is None or len(model_nodes) == 0 or not self._is_type_valid(base_location, type_name):
            return

        location = LocationContext(base_location).append_location(type_name)
        self._process_flattened_folder(location)

        token_name = self.alias_helper.get_name_token(location)
        create_path = self.alias_helper.get_wlst_create_path(location)
        list_path = self.alias_helper.get_wlst_list_path(location)
        existing_folder_names = self._get_existing_folders(list_path)
        for model_name in model_nodes:
            name = self.wlst_helper.get_quoted_name_for_wlst(model_name)

            if token_name is not None:
                location.add_name_token(token_name, name)

            wlst_type, wlst_name = self.alias_helper.get_wlst_mbean_type_and_name(location)
            if wlst_name not in existing_folder_names:
                if log_created:
                    self.logger.info('WLSDPLY-12100', type_name, name,
                                     class_name=self.__class_name, method_name=_method_name)
                else:
                    self.logger.fine('WLSDPLY-12100', type_name, name,
                                     class_name=self.__class_name, method_name=_method_name)
                self.wlst_helper.create_and_cd(self.alias_helper, wlst_type, wlst_name, location, create_path)
            else:
                if log_created:
                    self.logger.info('WLSDPLY-12101', type_name, name,
                                     class_name=self.__class_name, method_name=_method_name)
                else:
                    self.logger.fine('WLSDPLY-12101', type_name, name,
                                     class_name=self.__class_name, method_name=_method_name)

                attribute_path = self.alias_helper.get_wlst_attributes_path(location)
                self.wlst_helper.cd(attribute_path)

            child_nodes = dictionary_utils.get_dictionary_element(model_nodes, name)
            self.logger.finest('WLSDPLY-12111', self.alias_helper.get_model_folder_path(location),
                               self.wlst_helper.get_pwd(), class_name=self.__class_name, method_name=_method_name)
            self._set_attributes(location, child_nodes)
            self._create_subfolders(location, child_nodes)
            self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

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

        self.logger.entering(type_name, str(base_location), log_created,
                             class_name=self.__class_name, method_name=_method_name)
        if model_nodes is None or len(model_nodes) == 0 or not self._is_type_valid(base_location, type_name):
            return

        location = LocationContext(base_location).append_location(type_name)
        create_path = self.alias_helper.get_wlst_create_path(location)
        existing_folder_names = self._get_existing_folders(create_path)

        mbean_type, mbean_name = self.alias_helper.get_wlst_mbean_type_and_name(location)

        token_name = self.alias_helper.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, mbean_name)

        self._process_flattened_folder(location)
        if mbean_type not in existing_folder_names:
            if log_created:
                self.logger.info('WLSDPLY-12102', type_name, class_name=self.__class_name, method_name=_method_name)
            else:
                self.logger.fine('WLSDPLY-12102', type_name, class_name=self.__class_name, method_name=_method_name)

            self.wlst_helper.create_and_cd(self.alias_helper, mbean_type, mbean_name, location, create_path)
        else:
            if log_created:
                self.logger.info('WLSDPLY-12103', type_name, class_name=self.__class_name, method_name=_method_name)
            else:
                self.logger.fine('WLSDPLY-12102', type_name, class_name=self.__class_name, method_name=_method_name)

            attribute_path = self.alias_helper.get_wlst_attributes_path(location)
            self.wlst_helper.cd(attribute_path)

        self.logger.finest('WLSDPLY-12111', self.alias_helper.get_model_folder_path(location),
                           self.wlst_helper.get_pwd(), class_name=self.__class_name, method_name=_method_name)
        self._set_attributes(location, model_nodes)
        self._create_subfolders(location, model_nodes)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def _set_attributes(self, location, model_nodes):
        """
        Set the attributes for the MBean at the specified location.
        :param location: the location
        :param model_nodes: the model dictionary
        :raises: CreateException: if an error occurs
        """
        _method_name = '_set_attributes'

        model_attribute_names = self.alias_helper.get_model_attribute_names_and_types(location)
        password_attribute_names = self.alias_helper.get_model_password_type_attribute_names(location)
        set_method_map = self.alias_helper.get_model_mbean_set_method_attribute_names_and_types(location)
        model_folder_path = self.alias_helper.get_model_folder_path(location)
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
                    self._set_attribute(location, key, value, masked=True)
                else:
                    self.logger.finest('WLSDPLY-12113', key, pwd, model_folder_path,
                                       class_name=self.__class_name, method_name=_method_name)
                    self._set_attribute(location, key, value)
        return

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
                set_method(location, model_key, model_value)
            except AttributeError, ae:
                ex = exception_helper.create_create_exception('WLSDPLY-12104', set_method_name, model_key,
                                                              self.alias_helper.get_model_folder_path(location),
                                                              error=ae)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
        else:
            ex = exception_helper.create_create_exception('WLSDPLY-12105', model_key,
                                                          self.alias_helper.get_model_folder_path(location))
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def _set_attribute(self, location, model_name, model_value, masked=False):
        """
        Set the specified attribute at the specified location to the specified value.
        :param location: the location
        :param model_name: the model attribute name
        :param model_value: the model attribute value
        :param masked: whetyher or not to mask the attribute value in the log
        :raises: CreateException: if an error occurs
        """
        _method_name = '_set_attribute'
        wlst_name, wlst_value = self.alias_helper.get_wlst_attribute_name_and_value(location, model_name, model_value)

        if wlst_name is None:
            self.logger.info('WLSDPLY-12106', model_name, self.alias_helper.get_model_folder_path(location),
                             class_name=self.__class_name, method_name=_method_name)
        elif wlst_value is None:
            logged_value = model_value
            if masked:
                logged_value = '<masked>'
            self.logger.info('WLSDPLY-12107', model_name, logged_value,
                             self.alias_helper.get_model_folder_path(location),
                             class_name=self.__class_name, method_name=_method_name)
        else:
            logged_value = wlst_value
            if masked:
                logged_value = '<masked>'
            self.logger.finest('WLSDPLY-12115', wlst_name, logged_value,
                               class_name=self.__class_name, method_name=_method_name)
            self.wlst_helper.set(wlst_name, wlst_value, masked=masked)
        return

    def _create_subfolders(self, location, model_nodes):
        """
        Create the child MBean folders at the specified location.
        :param location: the location
        :param model_nodes: the model dictionary
        :raises: CreateException: if an error occurs
        """
        _method_name = '_create_subfolders'

        self.logger.entering(str(location), class_name=self.__class_name, method_name=_method_name)
        model_subfolder_names = self.alias_helper.get_model_subfolder_names(location)

        for key in model_nodes:
            if key in model_subfolder_names:
                subfolder_nodes = model_nodes[key]
                if len(subfolder_nodes) != 0:
                    sub_location = LocationContext(location).append_location(key)
                    if self.alias_helper.supports_multiple_mbean_instances(sub_location):
                        self.logger.finest('WLSDPLY-12109', key, str(sub_location), subfolder_nodes,
                                           class_name=self.__class_name, method_name=_method_name)
                        self._create_named_mbeans(key, subfolder_nodes, location)
                    else:
                        self.logger.finest('WLSDPLY-12110', key, str(sub_location), subfolder_nodes,
                                           class_name=self.__class_name, method_name=_method_name)
                        self._create_mbean(key, subfolder_nodes, location)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return


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

        code, message = self.alias_helper.is_valid_model_folder_name(location, type_name)
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
        if self.alias_helper.is_flattened_folder(location):
            create_path = self.alias_helper.get_wlst_flattened_folder_create_path(location)
            mbean_type = self.alias_helper.get_wlst_flattened_mbean_type(location)
            mbean_name = self.alias_helper.get_wlst_flattened_mbean_name(location)
            existing_folders = self._get_existing_folders(create_path)
            if mbean_type not in existing_folders:
                self.wlst_helper.create(mbean_name, mbean_type)
        return

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
        path = self.alias_helper.get_model_folder_path(location)
        if not path.endswith('/'):
            path += '/'
        path += name
        return path
