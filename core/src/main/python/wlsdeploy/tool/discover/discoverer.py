"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import javaos as os

from oracle.weblogic.deploy.aliases import AliasException
from oracle.weblogic.deploy.discover import DiscoverException
from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict
from oracle.weblogic.deploy.util import PyWLSTException
from oracle.weblogic.deploy.util import StringUtils

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util import path_utils
from wlsdeploy.util import wlst_helper
from wlsdeploy.util.weblogic_helper import WebLogicHelper

_DISCOVER_LOGGER_NAME = 'wlsdeploy.discover'

_class_name = 'Discoverer'
_logger = PlatformLogger(_DISCOVER_LOGGER_NAME)


class Discoverer(object):
    """
    Discoverer contains the private methods used to facilitate discovery of the domain information by its subclasses.
    """

    def __init__(self, model_context, base_location, wlst_mode, aliases=None):
        """

        :param model_context: context about the model for this instance of discover domain
        :param base_location: to look for common weblogic resources. By default this is the global path or '/'
        """
        self._model_context = model_context
        self._base_location = base_location
        self._wlst_mode = wlst_mode
        if aliases:
            self._aliases = aliases
        else:
            self._aliases = Aliases(self._model_context, wlst_mode=self._wlst_mode)
        self._alias_helper = AliasHelper(self._aliases, _logger, ExceptionType.DISCOVER)
        self._att_handler_map = OrderedDict()
        self._weblogic_helper = WebLogicHelper(_logger)
        self._wls_version = self._weblogic_helper.get_actual_weblogic_version()
        self._wlst_helper = WlstHelper(_logger, ExceptionType.DISCOVER)

    # methods for use only by the subclasses

    def _populate_model_parameters(self, dictionary, location):
        """
        Populate the model dictionary with the attribute values discovered at the current location. Perform
        any special processing for a specific attribute before storing into the model dictionary.
        :param dictionary: where to store the discovered attributes
        :param location: context containing current location information
        :return: dictionary of model attribute name and wlst value
        """
        _method_name = '_populate_model_parameters'
        wlst_path = self._alias_helper.get_wlst_attributes_path(location)
        _logger.finer('WLSDPLY-06100', wlst_path, class_name=_class_name, method_name=_method_name)

        if not self.wlst_cd(wlst_path, location):
            return

        wlst_params = self._get_attributes_for_current_location(location)
        _logger.finest('WLSDPLY-06102', self._wlst_helper.get_pwd(), wlst_params, class_name=_class_name,
                       method_name=_method_name)
        wlst_get_params = self._get_required_attributes(location)
        _logger.finest('WLSDPLY-06103', str(location), wlst_get_params,
                       class_name=_class_name, method_name=_method_name)
        attr_dict = OrderedDict()
        if wlst_params:
            for wlst_param in wlst_params:
                if wlst_param in wlst_get_params:
                    _logger.finest('WLSDPLY-06104', wlst_param, class_name=_class_name, method_name=_method_name)
                    try:
                        wlst_value = wlst_helper.get(wlst_param)
                    except PyWLSTException, pe:
                        _logger.warning('WLSDPLY-06127', wlst_param, wlst_path,
                                        pe.getLocalizedMessage(), class_name=_class_name, method_name=_method_name)
                        continue
                else:
                    _logger.finer('WLSDPLY-06131', wlst_param, class_name=_class_name, method_name=_method_name)
                    wlst_value = wlst_params[wlst_param]

                # if type(wlst_value) == str and len(wlst_value) == 0:
                #     wlst_value = None

                _logger.finer('WLSDPLY-06105', wlst_param, wlst_value, wlst_path, class_name=_class_name,
                              method_name=_method_name)
                try:
                    model_param, model_value = self._aliases.get_model_attribute_name_and_value(location,
                                                                                                wlst_param,
                                                                                                wlst_value)
                except AliasException, de:
                    _logger.info('WLSDPLY-06106', wlst_param, wlst_path, de.getLocalizedMessage(),
                                 class_name=_class_name, method_name=_method_name)
                    continue

                attr_dict[model_param] = wlst_value
                model_value = self._check_attribute(model_param, model_value, location)
                if model_value is not None:
                    _logger.finer('WLSDPLY-06107', model_param, model_value, class_name=_class_name,
                                  method_name=_method_name)
                    dictionary[model_param] = model_value
                elif model_param is None:
                    _logger.finest('WLSDPLY-06108', model_param, class_name=_class_name, method_name=_method_name)
        return attr_dict

    def _get_attributes_for_current_location(self, location):
        """
        Change to the mbean folder with the provided name using the current location and return
        the attributes at that location.
        :param location: context with the current location information
        :return: list of attributes
        """
        if self._wlst_mode == WlstModes.OFFLINE:
            return self._get_attributes_for_current_location_offline(location)
        else:
            return self._get_attributes_for_current_location_online(location)

    def _get_attributes_for_current_location_offline(self, location):
        _method_name = '_get_attributes_for_current_location_offline'
        attributes = []
        path = self._alias_helper.get_wlst_attributes_path(location)
        try:
            attributes = wlst_helper.lsa(path)
        except PyWLSTException, pe:
            name = location.get_model_folders()[-1]
            _logger.fine('WLSDPLY-06109', name, str(location), pe.getLocalizedMessage(), class_name=_class_name,
                         method_name=_method_name)
        return attributes

    def _get_attributes_for_current_location_online(self, location):
        _method_name = '_get_attributes_for_current_location_online'
        lsa_attributes = dict()
        path = self._alias_helper.get_wlst_attributes_path(location)
        try:
            lsa_attributes = wlst_helper.lsa(path)
            mbi_attributes = _get_mbi_attribute_list(path)
            if mbi_attributes:
                for lsa_attribute_name in lsa_attributes:
                    if lsa_attribute_name in lsa_attributes and lsa_attribute_name not in mbi_attributes:
                        _logger.finer('WLSDPLY-06142', lsa_attribute_name)
                        del lsa_attributes[lsa_attribute_name]
                for mbi_attribute_name in mbi_attributes:
                    if mbi_attribute_name not in lsa_attributes and mbi_attribute_name in mbi_attributes:
                        # don't count on the item in the get required list in caller, just get the value
                        # and add it to our lsa list
                        _logger.finer('WLSDPLY-06141', mbi_attribute_name, class_name=_class_name,
                                      method_name=_method_name)
                        lsa_attributes[mbi_attribute_name] = wlst_helper.get(mbi_attribute_name)
        except PyWLSTException, pe:
            name = location.get_model_folders()[-1]
            _logger.fine('WLSDPLY-06109', name, str(location), pe.getLocalizedMessage(), class_name=_class_name,
                         method_name=_method_name)
        return lsa_attributes

    def _is_defined_attribute(self, location, wlst_name):
        attribute = False
        try:
            if self._aliases.get_model_attribute_name(location, wlst_name):
                attribute = True
        except AliasException:
            pass
        return attribute

    def _get_required_attributes(self, location):
        """
        Use get for all online attributes, and use the attribute names in the
        :param location: current location context
        :return: list of attributes that require wlst.get
        """
        _method_name = '_get_required_attributes'
        attributes = []
        try:
            attributes = self._alias_helper.get_wlst_get_required_attribute_names(location)
        except DiscoverException, de:
            name = location.get_model_folders()[-1]
            _logger.warning('WLSDPLY-06109', name, location.get_folder_path(), de.getLocalizedMessage(),
                            class_name=_class_name, method_name=_method_name)
        return attributes

    def _mbean_names_exist(self, location):
        """
        Check to see if there are any configured MBeans for the current location
        :param location: context with the current location
        :return: True if MBeans of the type at the location exist
        """
        path = self._alias_helper.get_wlst_list_path(location)
        mbean_name_map = None
        try:
            mbean_name_map = wlst_helper.lsc(path)
        except DiscoverException, de:
            _logger.warning('WLSDPLY-06130', path, de.getLocalizedMessage())
        if mbean_name_map:
            return True
        return False

    def _check_attribute(self, model_name, model_value, location):
        """
        Check to see if the attribute has special handling indicated by the discover handler map. If the
        attribute needs special processing, all the handler specified by the map.
        :param model_name: model name for the attribute to check
        :param model_value: value converted to model format
        :param location: context containing current location information
        :return: new value if modified by the handler or the original value if not a special attribute
        """
        if model_value == 'null ':
            new_value = None
        else:
            new_value = model_value
        if model_name in self._att_handler_map:
            type_method = self._att_handler_map[model_name]
            if type_method is not None:
                new_value = type_method(model_name, model_value, location)
        return new_value

    def _find_names_in_folder(self, location):
        """
        Find the names for the top folder in the current location.
        :param location: context containing the current location information
        :return: list of names for the folder or None if the folder does not exist in the domain
        """
        _method_name = '_find_names_in_folder'
        names = None
        mbean_type = self._alias_helper.get_wlst_mbean_type(location)
        if mbean_type is None:
            _logger.fine('WLSDPLY-06110', location.get_model_folders()[-1], location.get_folder_path(),
                         class_name=_class_name, method_name=_method_name)
        else:
            folder_path = self._alias_helper.get_wlst_list_path(location)
            _logger.finest('WLSDPLY-06111', folder_path, class_name=_class_name, method_name=_method_name)
            if wlst_helper.path_exists(folder_path):
                self.wlst_cd(folder_path, location)
                names = self._wlst_helper.lsc()
                _logger.finest('WLSDPLY-06146', names, location, class_name=_class_name, method_name=_method_name)
        return names

    def _find_singleton_name_in_folder(self, location):
        """
        The top folder is a singleton. Find the single name for the folder.
        :param location: context containing current location informationget_mbean_folders
        :return: The single name for the folder, or None if the top folder does not exist in the domain
        """
        _method_name = '_find_singleton_name_in_top_folder'
        name = None
        names = self._find_names_in_folder(location)
        if names is not None:
            names_len = len(names)
            if names_len > 1:
                ex = exception_helper.create_discover_exception('WLSDPLY-06112', location.get_model_folders(),
                                                                self._alias_helper.get_model_folder_path(location),
                                                                len(names))
                _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            if names_len > 0:
                name = names[0]
        return name

    def _find_subfolders(self, location):
        if self._wlst_mode == WlstModes.OFFLINE:
            return self._find_subfolders_offline(location)
        else:
            return self._find_subfolders_online(location)

    def _find_subfolders_offline(self, location):
        """
        Find the subfolders of the current location.
        :param location: context containing current location information
        :return: list of subfolders
        """
        wlst_path = self._alias_helper.get_wlst_subfolders_path(location)
        wlst_subfolders = []
        if self.wlst_cd(wlst_path, location):
            wlst_subfolders = self._wlst_helper.lsc()
            if wlst_subfolders:
                new_subfolders = []
                for wlst_subfolder in wlst_subfolders:
                    model_subfolder_name = self._get_model_name(location, wlst_subfolder)
                    if model_subfolder_name:
                        new_subfolders.append(wlst_subfolder)
                wlst_subfolders = new_subfolders
        return wlst_subfolders

    def _find_subfolders_online(self, location):
        wlst_path = self._alias_helper.get_wlst_subfolders_path(location)
        wlst_subfolders = []
        if self.wlst_cd(wlst_path, location):
            wlst_subfolders = _massage_online_folders(self._wlst_helper.lsc())
            if wlst_subfolders:
                new_subfolders = []
                for wlst_subfolder in wlst_subfolders:
                    model_subfolder_name = self._get_model_name(location, wlst_subfolder)
                    if model_subfolder_name:
                        new_subfolders.append(wlst_subfolder)
                wlst_subfolders = new_subfolders
        return wlst_subfolders

    def _discover_subfolder_singleton(self, model_subfolder_name, location):
        """
        Discover the subfolder from the wlst subfolder name. populate the attributes in the folder.
        Return the subfolder model name and  the dictionary populated from the subfolder.
        The location is appended and then removed from the provided location context prior to return.
        :param model_subfolder_name: subfolder name in wlst format
        :param location: containing the current location information
        :return: model subfolder name: subfolder result dictionary:
        """
        _method_name = '_discover_subfolder_singleton'
        _logger.entering(model_subfolder_name, str(location), class_name=_class_name, method_name=_method_name)
        subfolder_result = OrderedDict()
        # For all server subfolder names there should only be one path
        if self._mbean_names_exist(location):
            subfolder_path = self._alias_helper.get_wlst_attributes_path(location)
            if self.wlst_cd(subfolder_path, location):
                self._populate_model_parameters(subfolder_result, location)
                self._discover_subfolders(subfolder_result, location)
        _logger.finest('WLSDPLY-06111', str(location), class_name=_class_name, method_name=_method_name)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return subfolder_result

    def _discover_subfolder_with_single_name(self, model_subfolder_name, location, name_token):
        """
        Discover a subfolder that is a singleton but has an unpredictable naming strategy. Find the name for
        the singleton folder and then discover the folder contents.
        :param location: context containing current location information
        :param name_token: represents the single folder name token in the aliases
        :return: dictionary containing discovered folder attributes
        """
        _method_name = '_discover_subfolder_with_single_name'
        _logger.entering(name_token, class_name=_class_name, method_name=_method_name)
        name = self._find_singleton_name_in_folder(location)
        result = OrderedDict()
        if name:
            location.add_name_token(name_token, name)
            result = self._discover_subfolder_singleton(model_subfolder_name, location)
            location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return result

    def _discover_artificial_folder(self, model_subfolder_name, location, name_token):
        """
        Discover the subfolder that has an artificial connection; the subfolder contains multiple different types
        under one MBean. The model must contain the subfolder type, the artificial type that specifies which it is,
        and the name of the subfolder. This folder is only one layer deep. No need to continue to discover
        additional subfolders
        :param model_subfolder_name: type of the model subfolder
        :param location: context containing the current location information
        :param name_token: for use in the location to contain the folder name
        :return: dictionary containing the discovered folder attributes
        """
        _method_name = '_discover_artifical_folder'
        _logger.entering(model_subfolder_name, str(location), name_token, class_name=_class_name,
                         method_name=_method_name)
        subfolder_result = OrderedDict()
        names = self._find_names_in_folder(location)
        if names is not None:
            for name in names:
                massaged = self._inspect_artificial_folder_name(name, location)
                location.add_name_token(name_token, massaged)
                artificial = self._get_artificial_type(location)
                if artificial is None:
                    _logger.warning('WLSDPLY-06123', self._alias_helper.get_model_folder_path(location),
                                    class_name=_class_name, method_name=_method_name)
                else:
                    _logger.finer('WLSDPLY-06120', artificial, massaged, model_subfolder_name, class_name=_class_name,
                                  method_name=_method_name)
                    location.append_location(artificial)
                    subfolder_result[massaged] = OrderedDict()
                    subfolder_result[massaged][artificial] = OrderedDict()
                    self._populate_model_parameters(subfolder_result[massaged][artificial], location)
                    location.pop_location()
                location.remove_name_token(name_token)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=subfolder_result)
        return subfolder_result

    def _discover_subfolder_with_names(self, model_subfolder_name, location, name_token):
        """
        Discover the subfolders from the wlst subfolder name. The subfolder may contain 0 to n instances, each
        with a unique name. Create an entry for each name in the subfolder. Populate the attributes of the subfolder.
        Return the subfolder model name and the populated dictionary.
        :param model_subfolder_name: model name of the wlst subfolder
        :param location: context of the current location
        :param name_token: aliases token for the type of model folder name
        :return: model subfolder name: dictionary results:
        """
        _method_name = '_discover_subfolder_with_names'
        _logger.entering(model_subfolder_name, str(location), name_token, class_name=_class_name,
                         method_name=_method_name)
        subfolder_result = OrderedDict()
        names = self._find_names_in_folder(location)
        if names is not None:
            for name in names:
                _logger.finer('WLSDPLY-06113', name, self._alias_helper.get_model_folder_path(location),
                              class_name=_class_name, method_name=_method_name)
                subfolder_result[name] = OrderedDict()
                location.add_name_token(name_token, name)
                subfolder_path = self._alias_helper.get_wlst_attributes_path(location)
                if self.wlst_cd(subfolder_path, location):
                    self._populate_model_parameters(subfolder_result[name], location)
                    self._discover_subfolders(subfolder_result[name], location)
                location.remove_name_token(name_token)
        _logger.finest('WLSDPLY-06114', str(location), class_name=_class_name, method_name=_method_name)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return subfolder_result

    def _discover_subfolder(self, model_subfolder_name, location, result=None):
        """
        Discover the subfolder indicated by the model subfolder name. Append the model subfolder to the
        current location context, and pop that location before return
        :param model_subfolder_name: Name of the model subfolder
        :param location: context containing the current subfolder information
        :return: discovered dictionary
        """
        _method_name = '_discover_subfolder'
        _logger.entering(model_subfolder_name, location.get_folder_path(), class_name=_class_name,
                         method_name=_method_name)
        location.append_location(model_subfolder_name)
        _logger.finer('WLSDPLY-06115', model_subfolder_name, self._alias_helper.get_model_folder_path(location),
                      class_name=_class_name, method_name=_method_name)
        # handle null model_subfolder name which should never happen in discover. throw exception about version
        if result is None:
            result = OrderedDict()
        name_token = self._alias_helper.get_name_token(location)
        _logger.finest('WLSDPLY-06116', model_subfolder_name, self._alias_helper.get_model_folder_path(location),
                       name_token, class_name=_class_name, method_name=_method_name)
        if name_token is not None:
            if self._alias_helper.requires_unpredictable_single_name_handling(location):
                subfolder_result = self._discover_subfolder_with_single_name(model_subfolder_name, location,
                                                                             name_token)
            elif self._alias_helper.requires_artificial_type_subfolder_handling(location):
                subfolder_result = self._discover_artificial_folder(model_subfolder_name, location, name_token)
            else:
                subfolder_result = self._discover_subfolder_with_names(model_subfolder_name, location,
                                                                       name_token)
        else:
            subfolder_result = self._discover_subfolder_singleton(model_subfolder_name, location)
        add_to_model_if_not_empty(result, model_subfolder_name, subfolder_result)
        location.pop_location()
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return result

    def _discover_subfolders(self, result, location):
        """
        Discover the rest of the mbean hierarchy at the current location.
        :param result: dictionary where to store the discovered subfolders
        :param location: context containing current location information
        :return: populated dictionary
        """
        _method_name = '_discover_subfolders'
        _logger.entering(str(location), method_name=_method_name, class_name=_class_name)
        wlst_subfolders = self._find_subfolders(location)
        if wlst_subfolders is not None:
            for wlst_subfolder in wlst_subfolders:
                model_subfolder_name = self._get_model_name(location, wlst_subfolder)
                # will return a None if subfolder not in current wls version
                if model_subfolder_name is not None:
                    result = self._discover_subfolder(model_subfolder_name, location, result)
        _logger.finest('WLSDPLY-06114', str(location), class_name=_class_name, method_name=_method_name)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return result

    def _discover_single_folder(self, location):
        """
        Discover the attributes in the single folder at current location and allow the
        caller to continue the discover for any of its child folders. This is for required
        for certain folders that need to be handled differently.
        :param location: containing the current location information
        :return: folder result dictionary:
        """
        _method_name = '_discover_single_folder'
        _logger.entering(str(location), class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        subfolder_path = self._alias_helper.get_wlst_attributes_path(location)
        if self.wlst_cd(subfolder_path, location):
            self._populate_model_parameters(result, location)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return result

    def _get_model_name(self, location, wlst_name):
        """
        Get the model folder name for the provided wlst mbean name. Throw an exception if the model name is
        not found in the aliases.
        :param location: context containing the current location information
        :param wlst_name: for which to locate the mbean name
        :return: model name for the folder
        :raises:DiscoverException:The mbean name is not in the alias folders
        """
        _method_name = '_get_model_name'
        _logger.finer('WLSDPLY-06117', wlst_name, self._alias_helper.get_model_folder_path(location),
                      class_name=_class_name, method_name=_method_name)
        model_name = None
        # The below call will throw an exception if the folder does not exist; need to have that
        # exception thrown. The get_model_subfolder_name does not throw an exception if the alias
        # does not exist. We do not want an exception if the folder is just not available for the version
        mbean_type = self._alias_helper.get_wlst_mbean_type(location)
        if mbean_type:
            model_name = self._alias_helper.get_model_subfolder_name(location, wlst_name)
            _logger.finest('WLSDPLY-06118', model_name, wlst_name, class_name=_class_name, method_name=_method_name)
            if model_name is None:
                _logger.fine('WLSDPLY-06119', wlst_name, self._get_wlst_mode_string(), self._wls_version,
                             class_name=_class_name, method_name=_method_name)
        return model_name

    def _topfolder_exists(self, model_top_folder_name):
        """
        Check to see if the folder represented by the top folder name exists at the current location.
        There is not a way to check for wlst_type for top folders. The top folder name and the wlst name
        must be the same.
        :param model_top_folder_name: to check for at top directory
        :return: True if the folder exists at the current location in the domain
        """
        result = self._wlst_helper.lsc('/', log_throwing=False)
        return model_top_folder_name in result

    def _subfolder_exists(self, model_folder_name, location):
        """
        Check to see if the folder represented by the model folder name exists at the current loction
        :param model_folder_name: to check for at location
        :param location: context containing the current location information
        :return: True if the folder exists at the current location in the domain
        """
        temp_location = LocationContext(location)
        subfolders = self._find_subfolders(temp_location)
        temp_location.append_location(model_folder_name)
        wlst_mbean_type = self._alias_helper.get_wlst_mbean_type(temp_location)
        if subfolders:
            return wlst_mbean_type in subfolders
        return False

    def _add_att_handler(self, attribute_key, method):
        self._att_handler_map[attribute_key] = method

    def _convert_path(self, file_name):
        file_name_resolved = self._model_context.replace_token_string(file_name)
        if path_utils.is_relative_path(file_name_resolved):
            return convert_to_absolute_path(self._model_context.get_domain_home(), file_name_resolved)
        return file_name_resolved

    def _is_oracle_home_file(self, file_name):
        """
        Determine if the absolute file name starts with an oracle home. Disregard if the application is
        located in the domain home.

        :param file_name: to check for oracle home or weblogic home
        :return: true if in oracle home location
        """
        py_str = str(file_name)
        return (not py_str.startswith(self._model_context.get_domain_home())) and \
            (py_str.startswith(self._model_context.get_oracle_home()) or
             py_str.startswith(self._model_context.get_wl_home()))

    def _get_wlst_mode_string(self):
        """
         Helper method to return the string representation for the online/offline mode of discovery.
         :return: String representation of mode
        """
        return WlstModes.from_value(self._wlst_mode)

    def _get_artificial_type(self, location):
        """
        Return the short model name for the MBean interface found for the location object
        :param location:context containing current location object information
        :return: short artificial name for the model
        """
        _method_name = '_get_artificial_type'
        _logger.entering(str(location), class_name=_class_name, method_name=_method_name)
        mbean_name = None
        subfolder_path = self._alias_helper.get_wlst_attributes_path(location)
        if subfolder_path:
            location_object = self.wlst_cd(subfolder_path, location)
            if location_object is None:
                _logger.fine('WLSDPLY-06121', self._alias_helper.get_wlst_attributes_path(location),
                             class_name=_class_name, method_name=_method_name)
            else:
                interfaces = location_object.getClass().getInterfaces()
                if not interfaces:
                    _logger.info('WLSDPLY-06124', str(location), str(location_object))
                else:
                    mbean_name = self._find_mbean_interface(location, interfaces)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=mbean_name)
        return mbean_name

    def _find_mbean_interface(self, location, interfaces):
        _method_name = '_find_mbean_interface'
        mbean_name = None
        for interface in interfaces:
            interface_name = str(interface)
            if 'MBean' in interface_name:
                _logger.finer('WLSDPLY-06126', interface_name, self._alias_helper.get_model_folder_path(location),
                              class_name=_class_name, method_name=_method_name)
                try:
                    mbean_name = self._alias_helper.get_model_subfolder_name(location, interface_name)
                except DiscoverException, ae:
                    _logger.fine('WLSDPLY-06122', interface_name, ae.getLocalizedMessage(), class_name=_class_name,
                                 method_name=_method_name)
                if mbean_name is None:
                    _logger.fine('WLSDPLY-06125', interface_name, str(location), class_name=_class_name,
                                 method_name=_method_name)
                break
        return mbean_name

    def _get_wlst_attributes(self, location):
        wlst_attributes = []
        model_attributes = self._alias_helper.get_model_attribute_names(location)
        if model_attributes:
            for model_attribute in model_attributes:
                try:
                    wlst_attribute = self._aliases.get_wlst_attribute_name(location, model_attribute)
                    if wlst_attribute:
                        wlst_attributes.append(wlst_attribute)
                except AliasException:
                    continue
        return wlst_attributes

    def wlst_cd(self, path, location):
        """
        Change to the directory specified in the path. If the wlst.cd() fails, assume something is wrong with the
        construction of the path tokens: Log a message, and return a indication to the caller that it should
        not continue on in this path.
        :param path: where to change directory
        :param location: context containing the current location information used to determine the path
        :return: the mbean instance if the wlst.cd() was successful, or None
        """
        _method_name = 'wlst_cd'
        result = None
        try:
            result = wlst_helper.cd(path)
        except PyWLSTException, pe:
            _logger.warning('WLSDPLY-06140', path, str(location), pe.getLocalizedMessage(), class_name=_class_name,
                            method_name=_method_name)
        return result

    def _inspect_artificial_folder_name(self, folder_name, location):
        """
        Perform any special handling for the folder or folder names.
        :param location: current context of location
        :return: Original name or processed name value
        """
        return self._inspect_security_folder_name(folder_name, location)

    def _inspect_security_folder_name(self, folder_name, location):
        # This is clunky - Some security providers in 11g offline have the name "Provider", and cannot be discovered.
        # If found, log and throw an exception here, and the SecurityConfiguration will be omitted from the model.

        if (not self._weblogic_helper.is_version_in_12c()) and self._wlst_mode == WlstModes.OFFLINE and \
                self._alias_helper.is_security_provider_type(location) and 'Provider' == folder_name:
            raise exception_helper.create_discover_exception('WLSDPLY-06201', folder_name, location.get_folder_path())

        _logger.fine('version {0} mode {1} type? {2} provider {3}', not self._weblogic_helper.is_version_in_12c(),
                     self._wlst_mode == WlstModes.OFFLINE, self._alias_helper.is_security_provider_type(location),
                     'Provider' == folder_name)
        return folder_name


def add_to_model_if_not_empty(dictionary, entry_name, entry_value):
    """
    Helper method for discover to add a non-empty value to the dictionary with the provided entry-name
    :param dictionary: to add the value
    :param entry_name: key to the value
    :param entry_value: to add to dictionary
    :return: True if the value was not empty and added to the dictionary
    """
    if entry_value and len(entry_value):
        dictionary[entry_name] = entry_value
        return True
    return False


def convert_to_absolute_path(relative_to, file_name):
    """
    Transform the path by joining the relative_to before the file_name and converting the resulting path name to
    an absolute path name.
    :param relative_to: prefix of the path
    :param file_name: name of the file
    :return: absolute path of the relative_to and file_name
    """
    if not StringUtils.isEmpty(relative_to) and not StringUtils.isEmpty(file_name):
        file_name = os.path.join(relative_to, file_name)
    return file_name


def _get_mbi_attribute_list(path):
    attribute_list = []
    for mbean_attribute_info in wlst_helper.get_mbi(path).getAttributes():
        if _is_attribute(mbean_attribute_info):
            attribute_list.append(mbean_attribute_info.getName())
    return attribute_list


def _is_attribute(attributes_info):
    return _is_attribute_type(attributes_info) or _is_valid_reference(attributes_info)


def _is_valid_reference(attribute_info):
    # check again after all done to see whether need to use get deprecated
    return _is_reference(attribute_info) and (
        attribute_info.isWritable() or not _is_deprecated(attribute_info))


def _is_reference(mbean_attribute_info):
    return mbean_attribute_info.getDescriptor().getFieldValue('com.bea.relationship') == 'reference'


def _is_deprecated(mbean_attribute_info):
    deprecated_version = mbean_attribute_info.getDescriptor().getFieldValue('deprecated')
    return deprecated_version is not None and deprecated_version != 'null' and len(deprecated_version) > 1


def _is_containment(mbean_attribute_info):
    return mbean_attribute_info.getDescriptor().getFieldValue('com.bea.relationship') == 'containment'


def _is_attribute_type(attribute_info):
    _method_name = '_is_attribute_type'
    if not attribute_info.isWritable() and _is_deprecated(attribute_info):
        _logger.finer('WLSDPLY-06143', attribute_info.getName(), wlst_helper.get_pwd(),
                      class_name=_class_name, method_name=_method_name)
    return attribute_info.getDescriptor().getFieldValue(
        'descriptorType') == 'Attribute' and attribute_info.getDescriptor().getFieldValue(
        'com.bea.relationship') is None and (attribute_info.isWritable() or not _is_deprecated(attribute_info))


def _massage_online_folders(lsc_folders):
    _method_name = '_massage_online_folders'
    location = wlst_helper.get_pwd()
    folder_list = []
    mbi_folder_list = []
    for mbean_attribute_info in wlst_helper.get_mbi(location).getAttributes():
        if _is_containment(mbean_attribute_info):
            mbi_folder_list.append(mbean_attribute_info.getName())
    for lsc_folder in lsc_folders:
        if lsc_folder in mbi_folder_list:
            folder_list.append(lsc_folder)
        else:
            _logger.finer('WLSDPLY-06144', lsc_folder, location, class_name=_class_name, method_name=_method_name)
    if len(folder_list) != len(mbi_folder_list):
        _logger.fine('WLSDPLY-06145', folder_list, location, mbi_folder_list, class_name=_class_name,
                     method_name=_method_name)
    return folder_list


def get_discover_logger_name():
    """
    Return the common logger used for all discover logging.
    :return: logger name
    """
    return _DISCOVER_LOGGER_NAME
