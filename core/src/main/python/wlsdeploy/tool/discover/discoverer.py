"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import array

from java.io import IOException
from java.net import MalformedURLException
from java.net import URI
from java.net import URISyntaxException
from oracle.weblogic.deploy.aliases import AliasException
from oracle.weblogic.deploy.discover import DiscoverException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict

from wlsdeploy.aliases import alias_constants
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import MASKED_PASSWORD
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.discover.custom_folder_helper import CustomFolderHelper
from wlsdeploy.tool.encrypt import encryption_utils
from wlsdeploy.tool.util.mbean_utils import MBeanUtils
from wlsdeploy.tool.util.mbean_utils import get_interface_name
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util import path_helper
from wlsdeploy.util import string_utils
import wlsdeploy.util.unicode_helper as str_helper


_DISCOVER_LOGGER_NAME = 'wlsdeploy.discover'

_class_name = 'Discoverer'
_logger = PlatformLogger(_DISCOVER_LOGGER_NAME)

remote_dict = OrderedDict()
REMOTE_TYPE = 'Type'
REMOTE_ARCHIVE_PATH = 'ArchivePath'

_ssh_download_dir = None

class Discoverer(object):
    """
    Discoverer contains the private methods used to facilitate discovery of the domain information by its subclasses.
    """

    def __init__(self, model_context, base_location, wlst_mode, aliases=None, credential_injector=None):
        """
        :param model_context: context about the model for this instance of discoverDomain
        :param base_location: to look for common WebLogic resources. By default, this is the global path or '/'
        :param wlst_mode: offline or online
        :param aliases: optional, aliases object to use
        :param credential_injector: optional, injector to collect credentials
        """
        _method_name = '__init__'
        global _ssh_download_dir

        self._model_context = model_context
        self._security_provider_map = None
        self._base_location = base_location
        self._wlst_mode = wlst_mode
        if aliases:
            self._aliases = aliases
        else:
            self._aliases = Aliases(self._model_context, wlst_mode=self._wlst_mode,
                                    exception_type=ExceptionType.DISCOVER)
        self._credential_injector = credential_injector
        self._att_handler_map = OrderedDict()
        self._custom_folder = CustomFolderHelper(self._aliases, _logger, self._model_context, ExceptionType.DISCOVER,
                                                 self._credential_injector)
        self._weblogic_helper = model_context.get_weblogic_helper()
        self._wlst_helper = WlstHelper(ExceptionType.DISCOVER)
        self._mbean_utils = MBeanUtils(self._model_context, self._aliases, ExceptionType.DISCOVER)
        self._wls_version = model_context.get_effective_wls_version()
        self.path_helper = path_helper.get_path_helper()
        self._export_tmp_directory = None
        self._local_tmp_directory = None

        if model_context.is_ssh():
            if _ssh_download_dir is None:
                try:
                    download_dir_file = FileUtils.createTempDirectory('wdt-downloadtemp')
                    download_dir_file.deleteOnExit()
                except IOException, e:
                    ex = exception_helper.create_discover_exception('WLSDPLY-06161',
                                                                    e.getLocalizedMessage(), error=e)
                    _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                    raise ex

                _ssh_download_dir = download_dir_file.getAbsolutePath()
                if self._model_context.is_discover_passwords():
                    remote_ssi_dat = self.path_helper.remote_join(self._model_context.get_domain_home(), 'security',
                                                                  'SerializedSystemIni.dat')
                    self.download_deployment_from_remote_server(remote_ssi_dat, _ssh_download_dir, 'security')

        self.download_temporary_dir = _ssh_download_dir

    def add_to_remote_map(self, local_name, archive_name, file_type):
        # we don't know the remote machine type, so automatically
        # turn into forward slashes.
        local_name = self.path_helper.fixup_path(local_name, self._model_context.get_domain_home())
        remote_dict[local_name] = OrderedDict()
        remote_dict[local_name][REMOTE_TYPE] = file_type
        remote_dict[local_name][REMOTE_ARCHIVE_PATH] = archive_name

        if file_type == 'FILE_STORE' or file_type == 'COHERENCE_PERSISTENCE_DIR':
            _logger.todo('WLSDPLY-06042', file_type, archive_name)
        else:
            _logger.todo('WLSDPLY-06041', file_type, local_name, archive_name)

    def discover_domain_mbean(self, model_top_folder_name):
        """
        Discover the domain specific MBean and its configuration attributes.
        :return: model name for domain MBean:dictionary containing the discovered Domain MBean attributes
        """
        _method_name = 'discover_domain_mbean'
        _logger.entering(model_top_folder_name, class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        location = LocationContext(self._base_location)
        location.append_location(model_top_folder_name)
        name = self._find_singleton_name_in_folder(location)
        if name is not None:
            _logger.info('WLSDPLY-06644', model_top_folder_name, class_name=_class_name, method_name=_method_name)
            location.add_name_token(self._aliases.get_name_token(location), name)
            self._populate_model_parameters(result, location)
            # if any subfolders exist, discover
            self._discover_subfolders(result, location)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return model_top_folder_name, result

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
        _logger.entering(dictionary, str_helper.to_string(location),
                              class_name=_class_name, method_name=_method_name)

        wlst_path = self._aliases.get_wlst_attributes_path(location)
        _logger.finer('WLSDPLY-06100', wlst_path, class_name=_class_name, method_name=_method_name)

        if not self.wlst_cd(wlst_path, location):
            _logger.exiting(class_name=_class_name, method_name=_method_name, result=None)
            return

        wlst_lsa_params = self._get_attributes_for_current_location(location)
        wlst_did_get = list()
        _logger.finest('WLSDPLY-06102', self._wlst_helper.get_pwd(), wlst_lsa_params,
                       class_name=_class_name, method_name=_method_name)
        wlst_get_params = self._get_required_attributes(location)
        _logger.finest('WLSDPLY-06103', str_helper.to_string(location), wlst_get_params,
                       class_name=_class_name, method_name=_method_name)
        if wlst_lsa_params is not None:
            for wlst_lsa_param in wlst_lsa_params:
                if wlst_lsa_param in wlst_get_params:
                    _logger.finest('WLSDPLY-06132', wlst_lsa_param,
                                   class_name=_class_name, method_name=_method_name)
                    success, wlst_value = self._get_attribute_value_with_get(wlst_lsa_param, wlst_path)
                    wlst_did_get.append(wlst_lsa_param)
                    if not success:
                        continue
                else:
                    _logger.finest('WLSDPLY-06131', wlst_lsa_param,
                                   class_name=_class_name, method_name=_method_name)
                    wlst_value = wlst_lsa_params[wlst_lsa_param]

                # if attribute was never set (online only), don't add to the model
                try:
                    if self._omit_from_model(location, wlst_lsa_param):
                        _logger.finest('WLSDPLY-06157', wlst_lsa_param, str_helper.to_string(location),
                                       class_name=_class_name, method_name=_method_name)
                        continue
                except DiscoverException, de:
                    _logger.info("WLSDPLY-06158", wlst_lsa_param, str_helper.to_string(location),
                                 de.getLocalizedMessage(), class_name=_class_name, method_name=_method_name)
                    continue

                self._add_to_dictionary(dictionary, location, wlst_lsa_param, wlst_value, wlst_path)

        # These will come after the lsa params in the ordered dictionary
        # Find the attributes that are not in the LSA wlst map but are in the alias definitions with GET access
        get_attributes = [get_param for get_param in wlst_get_params if not get_param in wlst_did_get]
        for get_attribute in get_attributes:
            _logger.finest('WLSDPLY-06133', get_attribute,
                           class_name=_class_name, method_name=_method_name)
            success, wlst_value = self._get_attribute_value_with_get(get_attribute, wlst_path)
            if success:
                self._add_to_dictionary(dictionary, location, get_attribute, wlst_value, wlst_path)

        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def _omit_from_model(self, location, wlst_lsa_param):
        """
        Determine if the specified attribute should be omitted from the model.
        Avoid calling wlst_helper.is_set() if possible, it slows down the online discovery process.
        :param location: the location of the attribute to be examined
        :param wlst_lsa_param: the name of the attribute to be examined
        :return: True if attribute should be omitted, False otherwise
        """
        # attributes with derived defaults need to call is_set(), since their value is dynamic.
        # don't call is_set() if the -remote command-line argument is used.
        if self._aliases.is_derived_default(location, wlst_lsa_param) or not self._model_context.is_remote():
            # wlst_helper.is_set already checks for offline / online
            return not self._wlst_helper.is_set(wlst_lsa_param)
        return False

    def _get_attribute_value_with_get(self, wlst_get_param, wlst_path):
        _method_name = '_get_attribute_value_with_get'
        _logger.finest('WLSDPLY-06104', wlst_get_param, class_name=_class_name, method_name=_method_name)
        success = False
        wlst_value = None
        try:
            wlst_value = self._wlst_helper.get(wlst_get_param)
            success = True
        except DiscoverException, pe:
            _logger.info('WLSDPLY-06127', wlst_get_param, wlst_path, pe.getLocalizedMessage(),
                            class_name=_class_name, method_name=_method_name)
        return success, wlst_value

    def _add_to_dictionary(self, dictionary, location, wlst_param, wlst_value, wlst_path):
        _method_name = '_add_to_dictionary'

        try:
            wlst_type = self._aliases.get_wlst_attribute_type(location, wlst_param)

            logged_value = wlst_value
            if wlst_value is not None and wlst_type == alias_constants.PASSWORD:
                logged_value = MASKED_PASSWORD

            _logger.finer('WLSDPLY-06105', wlst_param, logged_value, wlst_path,
                          class_name=_class_name, method_name=_method_name)

            model_param, model_value = \
                self._aliases.get_model_attribute_name_and_value(location, wlst_param, wlst_value)

            if wlst_type == alias_constants.PASSWORD:
                if not string_utils.is_empty(model_value):
                    if self._model_context.is_discover_passwords():
                        if isinstance(model_value, array.array):
                            password_encrypted_string = model_value.tostring()
                        elif isinstance(model_value, (str, unicode)):
                            password_encrypted_string = model_value
                        else:
                            ex = exception_helper.create_discover_exception('WLSDPLY-06053', model_param,
                                                                            location.get_folder_path(), type(model_value))
                            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                            raise ex

                        base_dir = self._model_context.get_domain_home()
                        if self._model_context.is_ssh():
                            base_dir = self.download_temporary_dir

                        model_value = self._weblogic_helper.decrypt(password_encrypted_string, base_dir)

                        if self._model_context.is_encrypt_discovered_passwords():
                            model_value = \
                                encryption_utils.encrypt_one_password(self._model_context.get_encryption_passphrase(),
                                                                      model_value)
                    else:
                        model_value = alias_constants.PASSWORD_TOKEN
                else:
                    model_value = None
        except (AliasException, DiscoverException), de:
            _logger.info('WLSDPLY-06106', wlst_param, wlst_path, de.getLocalizedMessage(),
                         class_name=_class_name, method_name=_method_name)
            return

        model_value = self._check_attribute(model_param, model_value, location)
        if model_value is not None:
            _logger.finer('WLSDPLY-06107', model_param, model_value, class_name=_class_name,
                          method_name=_method_name)
            dictionary[model_param] = model_value

            # tokenize the attribute if needed
            if self._credential_injector is not None:
                self._credential_injector.check_and_tokenize(dictionary, model_param, location)

        elif model_param is None:
            _logger.finest('WLSDPLY-06108', model_param, class_name=_class_name, method_name=_method_name)

    def _get_attributes_for_current_location(self, location):
        """
        Change to the mbean folder with the provided name using the current location and return
        the attributes at that location.
        :param location: context with the current location information
        :return: list of attributes
        """
        _method_name = '_get_attributes_for_current_location'
        attributes = []
        path = self._aliases.get_wlst_attributes_path(location)
        try:
            attributes = self._wlst_helper.lsa(path)
        except DiscoverException, de:
            name = location.get_model_folders()[-1]
            _logger.fine('WLSDPLY-06109', name, str_helper.to_string(location), de.getLocalizedMessage(),
                         class_name=_class_name, method_name=_method_name)
        return attributes

    def _is_defined_attribute(self, location, wlst_name):
        attribute = False
        try:
            if self._aliases.get_model_attribute_name(location, wlst_name, exclude_ignored=False):
                attribute = True
        except DiscoverException:
            pass
        return attribute

    def _get_required_attributes(self, location):
        """
        Use get for all online attributes, and use the attribute names in the
        :param location: current location context
        :return: list of attributes that require wlst.get
        """
        _method_name = '_get_required_attributes'
        attributes = list()
        try:
            attributes = self._aliases.get_wlst_get_required_attribute_names(location)
        except DiscoverException, de:
            name = location.get_model_folders()[-1]
            _logger.warning('WLSDPLY-06109', name, location.get_folder_path(), de.getLocalizedMessage(),
                            class_name=_class_name, method_name=_method_name)
        return attributes

    def _get_additional_parameters(self, location):
        _method_name = '_get_additional_parameters'
        other_attributes = list()
        try:
            other_attributes = self._mbean_utils.get_attributes_not_in_lsa_map(location)
        except DiscoverException, de:
            name = 'DomainConfig'
            folders = location.get_model_folders()
            if len(folders) > 0:
                name = location.get_model_folders()[-1]
            _logger.info('WLSDPLY-06150', name, location.get_folder_path(), de.getLocalizedMessage(),
                         class_name=_class_name, method_name=_method_name)
        return other_attributes

    def _mbean_names_exist(self, location):
        """
        Check to see if there are any configured MBeans for the current location
        :param location: context with the current location
        :return: True if MBeans of the type at the location exist
        """
        path = self._aliases.get_wlst_list_path(location)
        mbean_name_map = None
        try:
            mbean_name_map = self._wlst_helper.lsc(path)
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
        if not self._aliases.is_model_location_valid(location):
            _logger.fine('WLSDPLY-06110', location.get_model_folders()[-1], location.get_folder_path(),
                         class_name=_class_name, method_name=_method_name)
        else:
            folder_path = self._aliases.get_wlst_list_path(location)
            _logger.fine('WLSDPLY-06111', folder_path, class_name=_class_name, method_name=_method_name)
            if self._wlst_helper.path_exists(folder_path):
                self.wlst_cd(folder_path, location)
                names = self._wlst_helper.lsc()
                _logger.fine('WLSDPLY-06146', names, location, class_name=_class_name, method_name=_method_name)
            else:
                _logger.fine('Path {0} does not exist', folder_path, class_name=_class_name, method_name=_method_name)
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
                                                                self._aliases.get_model_folder_path(location),
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
        wlst_path = self._aliases.get_wlst_subfolders_path(location)
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
        wlst_path = self._aliases.get_wlst_subfolders_path(location)
        wlst_subfolders = []
        if self.wlst_cd(wlst_path, location):
            wlst_subfolders = self._massage_online_folders(self._wlst_helper.lsc())
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
        _logger.entering(model_subfolder_name, str_helper.to_string(location),
                         class_name=_class_name, method_name=_method_name)

        subfolder_result = OrderedDict()
        # For all server subfolder names there should only be one path
        if self._mbean_names_exist(location):
            subfolder_path = self._aliases.get_wlst_attributes_path(location)
            if self.wlst_cd(subfolder_path, location):
                self._populate_model_parameters(subfolder_result, location)
                self._discover_subfolders(subfolder_result, location)
        _logger.finest('WLSDPLY-06111', str_helper.to_string(location),
                       class_name=_class_name, method_name=_method_name)
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

    def _discover_artificial_folder(self, model_subfolder_type, location, name_token, check_order=False):
        """
        Discover the subfolder that has an artificial connection; the subfolder contains multiple different types
        under one MBean. The model must contain the subfolder type, the artificial type that specifies which it is,
        and the name of the subfolder. This folder is only one layer deep. No need to continue to discover
        additional subfolders
        :param model_subfolder_type: type of the model subfolder
        :param location: context containing the current location information
        :param name_token: for use in the location to contain the folder name
        :param check_order: if true, check the subfolders for order
        :return: dictionary containing the discovered folder attributes
        """
        _method_name = '_discover_artificial_folder'
        _logger.entering(model_subfolder_type, str_helper.to_string(location), name_token,
                         class_name=_class_name, method_name=_method_name)

        subfolder_result = OrderedDict()
        names = self._find_names_in_folder(location)
        required_order = self._aliases.get_subfolders_in_order(location)
        attr_map = dict()
        default_list = list()
        if names is not None:
            for name in names:
                location.add_name_token(name_token, name)
                self._validate_artificial_folder_name(name, location)
                # circumventing problems if the trust identity asserter schema type jar
                # is not in the oracle home. Force it to have the correct name.
                if name == 'Trust Service Identity Asserter':
                    artificial = 'TrustServiceIdentityAsserter'
                else:
                    artificial = self._get_artificial_type(location)
                if artificial is None:
                    if self._aliases.is_custom_folder_allowed(location):
                        _logger.fine('WLSDPLY-06148', model_subfolder_type, name, location.get_folder_path(),
                                     class_name=_class_name, method_name=_method_name)
                        # doesn't matter how many parameters, it is automatically a non-default name
                        default_list.append(name)
                        attr_map[name] = 0
                        subfolder_result.update(
                            self._custom_folder.discover_custom_mbean(location, model_subfolder_type, name))
                    else:
                        _logger.warning('WLSDPLY-06123', self._aliases.get_model_folder_path(location),
                                        class_name=_class_name, method_name=_method_name)
                else:
                    _logger.finer('WLSDPLY-06120', artificial, name, model_subfolder_type, class_name=_class_name,
                                  method_name=_method_name)
                    location.append_location(artificial)
                    subfolder_result[name] = OrderedDict()
                    subfolder_result[name][artificial] = OrderedDict()
                    self._populate_model_parameters(subfolder_result[name][artificial], location)
                    default_list.append(artificial)
                    attr_map[artificial] = len(subfolder_result[name][artificial])
                    location.pop_location()
                location.remove_name_token(name_token)

        # check_order is True only when the realm is the default realm
        if check_order:
            self._collect_security_provider_types(model_subfolder_type, subfolder_result)

        # check to see if the order and number of the subfolder list is same as required order
        is_default = False
        if check_order and len(required_order) == len(default_list):
            is_default = True
            idx = 0
            while idx < len(required_order):
                if  required_order[idx] != default_list[idx] or attr_map[default_list[idx]] > 0:
                    is_default = False
                    break
                idx += 1
        if is_default:
            subfolder_result = None
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=subfolder_result)
        return subfolder_result

    def _collect_security_provider_types(self, provider_type, providers_dict):
        _method_name = '_collect_security_provider_types'
        _logger.entering(provider_type, providers_dict, class_name=_class_name, method_name=_method_name)

        provider_subtype_map = None
        if self._model_context.is_discover_security_provider_data():
            provider_subtype_map = OrderedDict()
            for provider_name, provider_dict in providers_dict.iteritems():
                provider_subtypes = provider_dict.keys()
                if len(provider_subtypes) != 1:
                    _logger.warning('WLSDPLY-06165', provider_type, provider_name, provider_subtypes)
                    continue
                provider_subtype_map[provider_name] = provider_subtypes[0]
            self._add_provider_data_to_cache(provider_type, provider_subtype_map)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=provider_subtype_map)

    def _add_provider_data_to_cache(self, provider_type, provider_subtype_map):
        if self._security_provider_map is None:
            self._security_provider_map = dict()

        self._security_provider_map[provider_type] = provider_subtype_map

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
        _logger.entering(model_subfolder_name, str_helper.to_string(location), name_token,
                         class_name=_class_name, method_name=_method_name)

        subfolder_result = OrderedDict()
        names = self._find_names_in_folder(location)
        if names is not None:
            typedef = self._model_context.get_domain_typedef()
            for name in names:
                if typedef.is_filtered(location, name):
                    _logger.info('WLSDPLY-06159', typedef.get_domain_type(), location.get_current_model_folder(), name,
                                 class_name=_class_name, method_name=_method_name)
                else:
                    _logger.finer('WLSDPLY-06113', name, self._aliases.get_model_folder_path(location),
                                  class_name=_class_name, method_name=_method_name)
                    subfolder_result[name] = OrderedDict()
                    location.add_name_token(name_token, name)
                    subfolder_path = self._aliases.get_wlst_attributes_path(location)
                    if self.wlst_cd(subfolder_path, location):
                        self._populate_model_parameters(subfolder_result[name], location)
                        self._discover_subfolders(subfolder_result[name], location)
                    location.remove_name_token(name_token)
        _logger.finest('WLSDPLY-06114', str_helper.to_string(location),
                       class_name=_class_name, method_name=_method_name)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return subfolder_result

    def _discover_subfolder(self, model_subfolder_name, location, result=None, check_order=False):
        """
        Discover the subfolder indicated by the model subfolder name. Append the model subfolder to the
        current location context, and pop that location before return
        :param model_subfolder_name: Name of the model subfolder
        :param location: context containing the current subfolder information
        :param check_order: does the folder need to be checked for order
        :return: discovered dictionary
        """
        _method_name = '_discover_subfolder'
        _logger.entering(model_subfolder_name, location.get_folder_path(), class_name=_class_name,
                         method_name=_method_name)
        location.append_location(model_subfolder_name)
        deployer_utils.set_flattened_folder_token(location, self._aliases)

        _logger.finer('WLSDPLY-06115', model_subfolder_name, self._aliases.get_model_folder_path(location),
                      class_name=_class_name, method_name=_method_name)
        # handle null model_subfolder name which should never happen in discover. throw exception about version
        if result is None:
            result = OrderedDict()
        name_token = self._aliases.get_name_token(location)
        _logger.finest('WLSDPLY-06116', model_subfolder_name, self._aliases.get_model_folder_path(location),
                       name_token, class_name=_class_name, method_name=_method_name)
        if name_token is not None:
            if self._aliases.requires_unpredictable_single_name_handling(location):
                subfolder_result = self._discover_subfolder_with_single_name(model_subfolder_name, location,
                                                                             name_token)
            elif self._aliases.requires_artificial_type_subfolder_handling(location):
                subfolder_result = self._discover_artificial_folder(
                    model_subfolder_name, location, name_token, check_order)
            else:
                subfolder_result = self._discover_subfolder_with_names(model_subfolder_name, location,
                                                                       name_token)
        else:
            subfolder_result = self._discover_subfolder_singleton(model_subfolder_name, location)
        # this is a really special case. Empty means not-default it is empty
        if self._aliases.requires_artificial_type_subfolder_handling(location):
            if subfolder_result is not None:
                add_to_model(result, model_subfolder_name, subfolder_result)
        else:
            add_to_model_if_not_empty(result, model_subfolder_name, subfolder_result)
        location.pop_location()
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return result

    def _discover_subfolders(self, result, location, check_order=False):
        """
        Discover the rest of the mbean hierarchy at the current location.
        :param result: dictionary where to store the discovered subfolders
        :param location: context containing current location information
        :param check_order: True if artificial folder has an order to check
        :return: populated dictionary
        """
        _method_name = '_discover_subfolders'
        _logger.entering(str_helper.to_string(location), method_name=_method_name, class_name=_class_name)
        wlst_subfolders = self._find_subfolders(location)
        if wlst_subfolders is not None:
            for wlst_subfolder in wlst_subfolders:
                model_subfolder_name = self._get_model_name(location, wlst_subfolder)
                # will return a None if subfolder not in current wls version
                if model_subfolder_name is not None:
                    result = self._discover_subfolder(model_subfolder_name, location, result, check_order)
        _logger.finest('WLSDPLY-06114', str_helper.to_string(location),
                       class_name=_class_name, method_name=_method_name)
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
        _logger.entering(str_helper.to_string(location), class_name=_class_name, method_name=_method_name)
        result = OrderedDict()
        subfolder_path = self._aliases.get_wlst_attributes_path(location)
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
        _logger.finer('WLSDPLY-06117', wlst_name, self._aliases.get_model_folder_path(location),
                      class_name=_class_name, method_name=_method_name)
        model_name = None
        # The below call will throw an exception if the folder does not exist; need to have that
        # exception thrown. The get_model_subfolder_name does not throw an exception if the alias
        # does not exist. We do not want an exception if the folder is just not available for the version
        # Update 05/21/20 - does not make sense to stop discover because of missing alias definition.

        try:
            location_is_valid = self._aliases.is_model_location_valid(location)
        except DiscoverException, ex:
            _logger.warning('WLSDPLY-06156', str_helper.to_string(location),
                            class_name=_class_name, method_name=_method_name)
            location_is_valid = False
        if location_is_valid:
            model_name = self._aliases.get_model_subfolder_name(location, wlst_name)
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
        wlst_mbean_type = self._aliases.get_wlst_mbean_type(temp_location)
        if subfolders:
            return wlst_mbean_type in subfolders
        return False

    def _add_att_handler(self, attribute_key, method):
        self._att_handler_map[attribute_key] = method

    def _convert_path(self, file_name, relative_to_config=False):
        file_name_resolved = self._model_context.replace_token_string(file_name)
        if self.path_helper.is_relative_path(file_name_resolved):
            relative_to_dir = self._model_context.get_domain_home()
            if relative_to_config:
                relative_to_dir = self.path_helper.join(self._model_context.get_domain_home(), 'config')
            return self.path_helper.get_canonical_path(file_name_resolved, relative_to_dir)
        return file_name_resolved

    def _is_file_to_exclude_from_archive(self, file_name):
        """
        Determine if the absolute file name is one that should be excluded from the archive file.

        :param file_name: to check for oracle home or weblogic home
        :return: true if the file should not be added to the archive
        """
        _method_name = '_is_file_to_exclude_from_archive'
        _logger.entering(file_name, class_name=_class_name, method_name=_method_name)

        py_str = self.path_helper.fixup_path(str_helper.to_string(file_name))
        domain_home = self.path_helper.fixup_path(self._model_context.get_domain_home())
        wl_home = self.path_helper.fixup_path(self._model_context.get_effective_wl_home())
        oracle_home = self.path_helper.fixup_path(self._model_context.get_effective_oracle_home())
        _logger.finer('WLSDPLY-06162', py_str, domain_home, oracle_home, wl_home,
                      class_name=_class_name, method_name=_method_name)

        if py_str.startswith(domain_home):
            result = False
        elif not py_str.startswith(wl_home) and not py_str.startswith(oracle_home):
            result = False
        else:
            # We expect entries in the typedef's discoverExcludedLocationsBinariesToArchive
            # list to normally be tokenized but let's check both just in case...
            tokenized_py_str = self._model_context.tokenize_path(py_str)
            typedef = self._model_context.get_domain_typedef()
            result = not typedef.should_archive_excluded_app(tokenized_py_str)
            _logger.finer('WLSDPLY-06163', py_str, tokenized_py_str, result,
                          class_name=_class_name, method_name=_method_name)
            if result and py_str != tokenized_py_str:
                result = not typedef.should_archive_excluded_app(py_str)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
        return result

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
        _logger.entering(str_helper.to_string(location), class_name=_class_name, method_name=_method_name)
        mbean_name = None
        subfolder_path = self._aliases.get_wlst_attributes_path(location)
        if subfolder_path:
            location_object = self.wlst_cd(subfolder_path, location)
            if location_object is None:
                _logger.fine('WLSDPLY-06121', self._aliases.get_wlst_attributes_path(location),
                             class_name=_class_name, method_name=_method_name)
            else:
                interfaces = location_object.getClass().getInterfaces()
                if not interfaces:
                    _logger.info('WLSDPLY-06124', str_helper.to_string(location),
                                 str_helper.to_string(location_object),
                                 class_name=_class_name, method_name=_method_name)
                else:
                    mbean_name = self._find_mbean_interface(location, interfaces)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=mbean_name)
        return mbean_name

    def _find_mbean_interface(self, location, interfaces):
        _method_name = '_find_mbean_interface'
        mbean_name = None
        for interface in interfaces:
            interface_name = get_interface_name(interface)
            if 'MBean' in interface_name:
                _logger.finer('WLSDPLY-06126', interface_name, self._aliases.get_model_folder_path(location),
                              class_name=_class_name, method_name=_method_name)
                try:
                    mbean_name = self._aliases.get_model_subfolder_name(location, interface_name)
                except DiscoverException, ae:
                    _logger.fine('WLSDPLY-06122', interface_name, ae.getLocalizedMessage(), class_name=_class_name,
                                 method_name=_method_name)
                if mbean_name is None:
                    _logger.fine('WLSDPLY-06125', interface_name, str_helper.to_string(location),
                                 class_name=_class_name, method_name=_method_name)
                break
        return mbean_name

    def _get_wlst_attributes(self, location):
        wlst_attributes = []
        model_attributes = self._aliases.get_model_attribute_names(location)
        if model_attributes:
            for model_attribute in model_attributes:
                try:
                    wlst_attribute = self._aliases.get_wlst_attribute_name(location, model_attribute)
                    if wlst_attribute:
                        wlst_attributes.append(wlst_attribute)
                except DiscoverException:
                    continue
        return wlst_attributes

    def wlst_cd(self, path, location):
        """
        Change to the directory specified in the path. If the wlst.cd() fails, assume something is wrong with the
        construction of the path tokens: Log a message, and return an indication to the caller that it should
        not continue on in this path.
        :param path: where to change directory
        :param location: context containing the current location information used to determine the path
        :return: the mbean instance if the wlst.cd() was successful, or None
        """
        _method_name = 'wlst_cd'
        result = None
        try:
            result = self._wlst_helper.cd(path)
        except DiscoverException, pe:
            _logger.warning('WLSDPLY-06140', path, str_helper.to_string(location), pe.getLocalizedMessage(),
                            class_name=_class_name, method_name=_method_name)
        return result

    def _create_tmp_directories(self, error_key):
        """
        Create the temporary directory(ies) required for exporting the data files and reading the data files.
        In the case of SSH, the export directory is remote and the read directory is local.  Otherwise, they are
        the same.
        :return:
        """
        _method_name = '_create_tmp_directories'
        _logger.entering(error_key, class_name=_class_name, method_name=_method_name)
        if self._model_context.is_ssh():
            export_tmp_directory = \
                self._model_context.get_ssh_context().create_temp_directory_for_security_data_export()
            local_tmp_directory = self.download_temporary_dir
        else:
            try:
                export_dir_file = FileUtils.createTempDirectory('wdt_export_temp')
                # comment out this line to see exported files...
                export_dir_file.deleteOnExit()
            except IOException, e:
                ex = exception_helper.create_discover_exception(error_key,e.getLocalizedMessage(), error=e)
                _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            export_tmp_directory = export_dir_file.getAbsolutePath()
            local_tmp_directory = export_tmp_directory

        _logger.exiting(class_name=_class_name, method_name=_method_name,
                        result=[export_tmp_directory, local_tmp_directory])
        return export_tmp_directory, local_tmp_directory

    def _clean_up_tmp_directories(self, error_key):
        _method_name = '_clean_up_tmp_directories'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        # local directory in both SSH and non-SSH case is already set with java.io.File.deleteOnExit() so
        # the only cleanup needed is the temp directory on the SSH host machine, if applicable.
        if self._model_context.is_ssh():
            ssh_helper = self._model_context.get_ssh_context()
            try:
                if ssh_helper.does_directory_exist(self._export_tmp_directory):
                    ssh_helper.remove_file_or_directory(self._export_tmp_directory)
            except DiscoverException, de:
                # Best effort to remove.  If remove fails, log a warning and continue...
                _logger.warning(error_key, self._export_tmp_directory, self._model_context.get_ssh_host(),
                                de.getLocalizedMessage(), class_name=_class_name, method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name)
    def _validate_artificial_folder_name(self, folder_name, location):
        """
        Validate the folder name.
        :param location: current context of location
        """
        self._validate_security_folder_name(folder_name, location)

    def _validate_security_folder_name(self, folder_name, location):
        # This is clunky - Some security providers in 11g offline have the name "Provider", and cannot be discovered.
        # If found, log and throw an exception here, and the SecurityConfiguration will be omitted from the model.
        _method_name = '_validate_security_folder_name'
        if (not self._weblogic_helper.is_version_in_12c()) and self._wlst_mode == WlstModes.OFFLINE and \
                self._aliases.is_security_provider_type(location) and 'Provider' == folder_name:
            ex = exception_helper.create_discover_exception('WLSDPLY-06201', folder_name, location.get_folder_path())
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

    def _get_credential_injector(self):
        """
        The credential injector is a specialized injector that collects credentials during the discovery process.
        It is later used to create the properties file, or Kubernetes secrets.
        :return: the credential injector
        """
        return self._credential_injector

    def _massage_online_folders(self, lsc_folders):
        _method_name = '_massage_online_folders'
        location = self._wlst_helper.get_pwd()
        folder_list = []
        mbi_folder_list = []
        for mbean_attribute_info in self._wlst_helper.get_mbi(location).getAttributes():
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


    def _get_from_url(self, owner_name, file_name):
        """
        Determine if the provided file name is a URL location where the file is hosted. If it is a URL, return
        a URL stream that can be used to retrieve the file from the hosted location.
        :param owner_name: of the file being discovered
        :param file_name: of the file to be tested as a URL
        :return: True if the file is hosted at a URL: URL file handle for the archive file to retrieve the file, or path
                 from file name
        """
        _method_name = '_get_from_url'
        _logger.entering(owner_name, file_name, class_name=_class_name, method_name=_method_name)

        success = True
        url = None
        path = None
        try:
            uri = URI(file_name)
            if 'http' == uri.getScheme() or 'https' == uri.getScheme():
                url = uri.toURL()
            elif 'file' == uri.getScheme() or uri.getScheme() is None:
                path = uri.getPath()
            else:
                success = False
                _logger.warning('WLSDPLY-06160', owner_name, file_name, uri.getScheme(),
                                class_name=_class_name, method_name=_method_name)
        except (URISyntaxException, MalformedURLException), e:
            success = False
            _logger.warning('WLSDPLY-06321', owner_name, file_name, e.getLocalizedMessage,
                            error=e, class_name=_class_name, method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=(success, url, path))
        return success, url, path

    def download_deployment_from_remote_server(self, source_path, local_download_root, file_type):
        return self.path_helper.download_file_from_remote_server(self._model_context, source_path,
                                                                 local_download_root, file_type)


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


def add_to_model(dictionary, entry_name, entry_value):
    """
    Add this to the model even if empty
    :param dictionary: to add the value
    :param entry_name: name of the key
    :param entry_value: dictionary to add
    """
    dictionary[entry_name] = entry_value


def _is_containment(mbean_attribute_info):
    return mbean_attribute_info.getDescriptor().getFieldValue('com.bea.relationship') == 'containment'


def get_discover_logger_name():
    """
    Return the common logger used for all discover logging.
    :return: logger name
    """
    return _DISCOVER_LOGGER_NAME
