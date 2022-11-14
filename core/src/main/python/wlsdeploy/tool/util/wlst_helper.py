"""
Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import types

from java.io import PrintStream
from java.lang import System
from java.lang import Throwable

import com.oracle.cie.domain.script.jython.WLSTException as offlineWLSTException
import oracle.weblogic.deploy.util.StringUtils as StringUtils
import weblogic.management.mbeanservers.edit.ValidationException as ValidationException

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.string_output_stream import StringOutputStream
import wlsdeploy.util.unicode_helper as str_helper

wlst_functions = None


class WlstHelper(object):
    """
    The helper class to execute all WLST commands. The class uses the globals
    loaded by WLST and stored in the wlst_functions global variable.
    """
    __class_name = 'WlstHelper'
    __logger = PlatformLogger('wlsdeploy.wlst')

    def __init__(self, exception_type):
        self.__exception_type = exception_type
        return

    def assign(self, source_type, source_name, target_type, target_name):
        """
        Assign target entity to source entity

        :param source_type: source entity type
        :param source_name: entity name
        :param target_type: target type
        :param target_name: target name
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'assign'
        self.__logger.entering(source_type, source_name, target_type, target_name,
                               class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('assign')(source_type, source_name, target_type, target_name)
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            raise exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00002', source_type, source_name,
                                                    target_type, target_name, self.__get_exception_mode(e),
                                                    _format_exception(e), error=e)
        self.__logger.finest('WLSDPLY-00003', source_type, source_name, target_type, target_name,
                             class_name=self.__class_name, method_name=_method_name)
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def cd(self, path):
        """
        Change location to the provided path.

        :param path: wlst directory to which to change location
        :return: cmo object reference of the new location
        :raises: Exception for the specified tool type: if a WLST error occurs
        """

        _method_name = 'cd'
        self.__logger.finest('WLSDPLY-00001', path, class_name=self.__class_name, method_name=_method_name)

        try:
            result = self.__load_global('cd')(path)
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00002', path,
                                                   self.__get_exception_mode(e), _format_exception(e), error=e)
            raise ex
        self.__logger.finest('WLSDPLY-00003', path, result, class_name=self.__class_name, method_name=_method_name)
        return result

    def get(self, attribute):
        """
        Return the value for the attribute at the current location

        :param attribute: name of the wlst attribute
        :return: value set for the attribute
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'get'
        self.__logger.finest('WLSDPLY-00004', attribute, class_name=self.__class_name, method_name=_method_name)

        try:
            result = self.__load_global('get')(attribute)
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00005', attribute,
                                                    self.__get_exception_mode(e), _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.finest('WLSDPLY-00006', attribute, class_name=self.__class_name, method_name=_method_name)
        return result

    def is_set(self, attribute):
        """
        Determine if the specified attribute has been set.
        In online WLST, attributes may return values that did not originate in config.xml (not set).
        For offline WLST, return True always.
        :param attribute: name of the WLST attribute
        :return: True if the value has been set or in offline mode, False otherwise
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'is_set'
        self.__logger.finest('WLSDPLY-00124', attribute, class_name=self.__class_name, method_name=_method_name)

        if not self.__check_online_connection():
            return True

        mbean_path = self.get_pwd()

        try:
            mbean = self.get_mbean_for_wlst_path(mbean_path)
            if 'isSet' not in dir(mbean):
                return True

            result = mbean.isSet(attribute)
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00125', attribute,
                                                    self.__get_exception_mode(e), _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        except Throwable, e:
            # isSet() throws a Java error for /ResourceManagement attribute in 14.1.1.
            # in this case, return False to prevent further processing of this attribute.
            self.__logger.info('WLSDPLY-00129', attribute, mbean_path, e, class_name=self.__class_name,
                               method_name=_method_name)
            return False

        self.__logger.finest('WLSDPLY-00126', attribute, class_name=self.__class_name, method_name=_method_name)
        return result

    def set_if_needed(self, wlst_name, wlst_value, masked=False):
        """
        Set the WLST attribute to the specified value if the name and value are not None.
        :param wlst_name: the WLST attribute name
        :param wlst_value: the WLST attribute value
        :param masked: whether or not to mask the value in the logs, default value is False
        :raises: Exception for the specified tool type: if an error occurs
        """
        if wlst_name is not None and wlst_value is not None:
            self.set(wlst_name, wlst_value, masked)

    def set(self, attribute, value, masked=False):
        """
        Set the configuration for the indicated attribute to the provided value.

        :param attribute: attribute name at the current location
        :param value: to configure the attribute
        :param masked: if the value is encrypted mask the value in log streams
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'set'
        log_value = value
        if masked:
            log_value = '<masked>'
        self.__logger.finest('WLSDPLY-00007', attribute, log_value, self.get_pwd(),
                             class_name=self.__class_name, method_name=_method_name)
        try:
            self.__load_global('set')(attribute, value)
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            path = self.get_pwd()
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-0100', attribute, path,
                                                   log_value, _format_exception(e), error=e)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        self.__logger.finest('WLSDPLY-00009', class_name=self.__class_name, method_name=_method_name)

    def set_with_cmo(self, wlst_name, wlst_value, masked=False):
        """
        Set the specified attribute using the corresponding cmo set method (e.g., cmo.setListenPort()).
        :param wlst_name: the WLST attribute name
        :param wlst_value: the WLST value
        :param masked: whether or not to mask the wlst_value from the log files.
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'set_with_cmo'
        value = wlst_value
        if masked:
            value = '<masked>'

        self.__logger.finest('WLSDPLY-00010', wlst_name, value, class_name=self.__class_name, method_name=_method_name)

        set_method_name = 'set' + wlst_name
        self.__logger.finest('WLSDPLY-00011', set_method_name, class_name=self.__class_name, method_name=_method_name)

        current_cmo = self.get_cmo()
        if current_cmo is None:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00012', set_method_name,
                                                    value, self._get_wlst_mode())
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe

        try:
            set_method = getattr(current_cmo, set_method_name)
            set_method(wlst_value)
        except AttributeError, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00013', set_method_name,
                                                    self.__get_exception_mode(e), _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00014', set_method_name, value,
                                                    self.__get_exception_mode(e), _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.finest('WLSDPLY-00015', wlst_name, value, class_name=self.__class_name, method_name=_method_name)

    def _get_wlst_mode(self):
        """
        Get the text to describe the current WLST mode.
        :return: online, if connected, offline if not
        """
        if self.__check_online_connection():
            result = 'online'
        else:
            result = 'offline'
        return result

    def get_cmo(self):
        """
        update the Current Management Object (cmo) to current mbean in self.__load_global('
        :return: updated cmo
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'get_cmo'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        load_cmo = self.__load_global('cmo')
        if self.is_connected():
            if load_cmo is None:
                pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00070')
                self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
                raise pwe
        else:
            load_update_cmo = self.__load_global('updateCmo')
            try:
                load_update_cmo()
            except offlineWLSTException, e:
                pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00036', self.get_pwd(),
                                                        self.__get_exception_mode(e), _format_exception(e), error=e)
                self.__logger.throwing(class_name=self.__class_name, method_name='get_cmo', error=pwe)
                raise pwe
            self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=load_cmo)
        return load_cmo

    def is_connected(self):
        """
        Determine if wlst is currently connected to the admin server - from the WlstContext
        :return: Return True if currently connected
        """
        return self.__load_global('connected') == 'true'

    def is_restart_required(self):
        """
        Return if the update changes require restart of the domain or servers.
        :return: true if the changes require restart
        """
        return self.__load_global('isRestartRequired')()

    def cancel_edit(self):
        """
        Cancel current edit session and discard all unsaved changes
        """
        self.__load_global('cancelEdit')('y')

    def create(self, name, folder, base_provider_type=None):
        """
        Create the mbean folder with the provided name at the current location.

        :param name: to create under the folder
        :param folder: name of the mbean folder
        :param base_provider_type: the name of the security provider base type
        :return: the MBean object returned by the underlying WLST create() method
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'create'
        self.__logger.entering(name, folder, base_provider_type, class_name=self.__class_name, method_name=_method_name)

        load_create = self.__load_global('create')
        try:
            if base_provider_type is None:
                result = load_create(name, folder)
            else:
                if not self.__check_online_connection():
                    result = self.__load_global('WLS').create(name, folder, base_provider_type)
                else:
                    result = load_create(name, folder, base_provider_type)
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00017', name, folder,
                                                    base_provider_type, self.__get_exception_mode(e),
                                                    _format_exception(e), self.get_pwd(), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.finest('WLSDPLY-00018', name, folder, base_provider_type, result,
                             class_name=self.__class_name, method_name=_method_name)
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return result

    def create_and_cd(self, aliases, type_name, name, location, create_path=None):
        """
        Create a new MBean instance and change directories to its attributes location.
        :param aliases: the alias helper object
        :param type_name: the WLST type
        :param name: the name for the new object
        :param location: the location
        :param create_path: the WLST path from which to create the new MBean
        :return: the result from cd()
        :raises: Exception for the specified tool type: if an error occurs
        """
        _method_name = 'create_and_cd'
        self.__logger.entering(name, location.get_folder_path(), create_path,
                               class_name=self.__class_name, method_name=_method_name)
        if create_path is not None:
            self.cd(create_path)
        self.create(name, type_name)
        result = self.cd(aliases.get_wlst_attributes_path(location))
        self.__logger.exiting(result=result, class_name=self.__class_name, method_name=_method_name)
        return result

    def delete(self, name, folder):
        """
        Delete an MBean of the specified name and type at the current location.
        :param name: the MBean name
        :param folder: the MBean type
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'delete'
        self.__logger.entering(name, folder, class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('delete')(name, folder)
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00020', name, folder,
                                                    self.__get_exception_mode(e), _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.finest('WLSDPLY-00021', name, folder, class_name=self.__class_name, method_name=_method_name)
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def get_database_defaults(self):
        """
        sets the database defaults indicated by RCU.
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'get_database_defaults'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('getDatabaseDefaults')()
        except offlineWLSTException, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00022',
                                                    e.getLocalizedMessage(), error=e)
            self.__logger.throwing(pwe, class_name=self.__class_name, method_name=_method_name)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def modify_bootstrap_credentials(self, jps_configfile, username, password):
        """
        modify the boot strap credentials in a JRF domain
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'modifyBootStrapCredentials'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('modifyBootStrapCredential')(jps_configfile, username, password)
        except offlineWLSTException, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00101',
                                                    e.getLocalizedMessage(), error=e)
            self.__logger.throwing(pwe, class_name=self.__class_name, method_name=_method_name)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def set_server_groups(self, server, server_groups, timeout):
        """
        Targets the list of server groups to the managed server.

        WARNING: The online version of setServerGroups() does change out of the edit MBean
        tree when complete.  However, since we don't know the mode at this level, leave
        it up to the caller to determine if moving back to the edit() tree is needed.

        :param server: the name of the managed server
        :param server_groups: the list of template-defined server groups to target to the server
        :param timeout: the timeout for the setServerGroups command
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'set_server_groups'
        self.__logger.entering(server_groups, server, timeout, class_name=self.__class_name, method_name=_method_name)

        try:
            # In the WDT context, we never need online setServerGroups to acquire its own edit lock.
            # As such, always pass true for skipEdit.
            #
            self.__load_global('setServerGroups')(serverName=server, serverGroups=server_groups, timeout=timeout, skipEdit=True)
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00023', server_groups, server,
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def set_server_group_dynamic_cluster(self, cluster, server_group):
        """
        Target the server group to the cluster. This function is used in 12c versions
        12.2.1.1 to 12.2.1.3.

        :param cluster: the name of the dynamic cluster
        :param server_group: the server group to target to the dynamic cluster
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'set_server_group_dynamic_cluster'
        self.__logger.entering(server_group, cluster, class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('setAssociatedClusterDynamicServerGroup')(cluster, server_group)
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00123', server_group, cluster,
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def set_option_if_needed(self, option_name, option_value):
        """
        Set the WLST domain option to the provided value if the name and value are not None.

        :param option_name: attribute name at the current location
        :param option_value: to configure the attribute
        :raises: Exception for the specified tool type: if an error occurs
        """
        if option_name is not None and option_value is not None:
            self.set_option(option_name, option_value)

    def set_option(self, option, value):
        """
        Set the configuration for the indicated option to the provided value.

        :param option: domain option to set
        :param value: to which to set the option
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'set_option'
        self.__logger.entering(option, value, class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('setOption')(option, value)
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00024', option,
                                                    self.__get_exception_mode(e), _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def lsa(self, path=None, log_throwing=True):
        """
        Return a map of WebLogic attributes found at the wlst path or the current path.

        In online mode, clean up the return values to strip off trailing spaces and
        convert the string 'null' into None.
        :param path: for which to return a map of attributes. If None, the current path is searched
        :param log_throwing: whether or not to log the throwing message if the path location is not found
        :return: map of WebLogic attributes
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'lsa'
        result = self.__ls(_method_name, 'a', path, log_throwing)
        make_dict = dict()
        if result and len(result) > 0:
            for entry in result.entrySet():
                key = entry.getKey()
                value = entry.getValue()
                if value and type(value) in [str, unicode]:
                    new_value = value.rstrip()
                    if new_value == 'null' or new_value == 'none':
                        make_dict[key] = None
                    else:
                        make_dict[key] = new_value
                else:
                    make_dict[key] = value
        return make_dict

    def lsc(self, path=None, log_throwing=True):
        """
        Return a map of WebLogic folders found at the wlst path or the current path.
        :param path: for which to return a map of folders. If None, the current path is searched
        :param log_throwing: whether or not to log the throwing message if the path location is not found
        :return: list of WebLogic folders
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'lsc'
        return self.__ls(_method_name, 'c', path, log_throwing)

    def path_exists(self, path):
        """
        Determine if the provided path exists in the domain. This can be a path relative to the
        current location or a fully qualified path.
        :param path: path to validate.
        :return: True if path exists; false otherwise
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'path_exists'
        self.__logger.finest('WLSDPLY-00025', path, class_name=self.__class_name, method_name=_method_name)

        exists = True
        try:
            self.__load_global('ls')(path)
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            self.__logger.finest('WLSDPLY-00026', path, e.getLocalizedMessage(),
                                 class_name=self.__class_name, method_name=_method_name)
            exists = False
        self.__logger.finest('WLSDPLY-00027', path, exists, class_name=self.__class_name, method_name=_method_name)
        return exists

    def get_singleton_name(self, path=None):
        """
        Return the name at the current location or at the provided path. This location represents
        the name of an MBean that is a singleton. None will be returned if a location is provided and
        it does not exist.
        :param path: location to retrieve the singleton name, or the current location if no path is provided
        :return: name of the MBean
        :raises Exception for the specified tool type: if there is either no name or more than one name found at the
                      location or if a WLST error occurs
        """
        _method_name = 'get_singleton_name'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        mbean_name = None
        if path is None or self.path_exists(path):
            print_path = path
            if path is None:
                print_path = self.get_pwd()
            name_list = self.lsc(path)
            nbr_names = 0
            if name_list is not None:
                nbr_names = len(name_list)
            if not nbr_names == 1:
                pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00031',
                                                        print_path, nbr_names, name_list)
                self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
                raise pwe
            mbean_name = name_list[0]
            self.__logger.finest('WLSDPLY-00032', print_path, mbean_name,
                                 class_name=self.__class_name, method_name=_method_name)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=mbean_name)
        return mbean_name

    def get_mbean(self, wlst_path):
        """
        Return the current CMO or the proxy instance for the MBean of the current folder.
        There are certain directories in offline that will not deliver a cmo, but will
        give an MBean proxy for a cd to a fully qualified path
        :param wlst_path: path of the named MBean
        :return: CMO or MBean proxy for the current location
        ":raises Exception for the specified tool type: If cmo is not present or WLST error occurs.
        """
        _method_name = 'get_mbean'
        self.__logger.entering(wlst_path, class_name=self.__class_name, method_name=_method_name)
        current_dir = self.get_pwd()
        mbean_path = wlst_path
        if mbean_path is None:
            mbean_path = current_dir
        self.__logger.finest('WLSDPLY-00097', mbean_path, class_name=self.__class_name, method_name=_method_name)
        self.cd(current_dir)
        cmo = self.get_cmo()
        if cmo is None:
            cmo = self.get_mbean_for_wlst_path(mbean_path)
        if cmo is None:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00096', mbean_path)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        if wlst_path is None:
            self.cd(current_dir)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=cmo)
        return cmo

    def get_mbean_for_wlst_path(self, path):
        """
        Return the mbean object for the provided path.
        :param path: to return mbean object
        :return: mbean object
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'get_mbean_for_wlst_path'
        self.__logger.finest(path, class_name=self.__class_name, method_name=_method_name)

        current_dir = self.get_pwd()
        the_object = self.cd(path)
        self.cd(current_dir)

        self.__logger.finest(self.__class_name, _method_name, the_object)
        return the_object

    def read_template(self, template):
        """
        Read the server template into the WebLogic domain for domain creation.
        :param template: name of the template to load for domain creation
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'read_template'
        self.__logger.entering(template, class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('readTemplate')(template)
        except offlineWLSTException, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00037', template,
                                                    e.getLocalizedMessage(), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def add_template(self, template):
        """
        Extend the domain with the server template.
        :param template: name of the template to load for domain extension
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'add_template'
        self.__logger.entering(template, class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('addTemplate')(template)
        except offlineWLSTException, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00038', template,
                                                    e.getLocalizedMessage(), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def close_template(self):
        """
        Close the template that is currently loaded for domain creation.
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'close_template'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        try:
            self.__load_global('closeTemplate')()
        except offlineWLSTException, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00039',
                                                    e.getLocalizedMessage(), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def select_template(self, template):
        """
        Select an existing domain template or application template for create a domain. This is
        available only in WebLogic 12c versions
        :param template: to be selected and loaded into the current session
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'select_template'
        self.__logger.entering(template, class_name=self.__class_name, method_name=_method_name)
        try:
            self.__load_global('selectTemplate')(template)
        except offlineWLSTException, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00040', template,
                                                    e.getLocalizedMessage(), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def select_custom_template(self, template):
        """
        Select an existing custom domain template or application template for create a domain. This is
        available only in WebLogic 12c versions
        :param template: to be selected and loaded into the current session
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'select_custom_template'
        self.__logger.entering(template, class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('selectCustomTemplate')(template)
        except offlineWLSTException, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00095', template,
                                                    e.getLocalizedMessage(), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def load_templates(self):
        """
        Load all the selected templates.
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'load_templates'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        try:
            self.__load_global('loadTemplates')()
        except offlineWLSTException, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00041',
                                                    e.getLocalizedMessage(), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def set_topology_profile(self, profile):
        """
        Set the desired topology profile defined in the domain extension template.
        :param profile: the profile to use
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'set-topology_profile'

        self.__logger.entering(profile, class_name=self.__class_name, method_name=_method_name)
        try:
            self.__load_global('setTopologyProfile')(profile)
        except offlineWLSTException, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00128', profile,
                                                    e.getLocalizedMessage(), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def read_domain(self, domain_home):
        """
        Read the domain indicated by the domain_home name in offline mode.
        :param domain_home: domain to read and load into the current offline session
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'read_domain'
        self.__logger.entering(domain_home, class_name=self.__class_name, method_name=_method_name)
        try:
            self.__load_global('readDomain')(domain_home)
        except offlineWLSTException, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00042', domain_home,
                                                    e.getLocalizedMessage(), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def write_domain(self, domain_home):
        """
        Persist the newly created domain configuration to the provided location. This will automatically
        overwrite an existing domain at this location.
        :param domain_home: path location to write the domain and its configuration
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'write_domain'
        self.__logger.entering(domain_home, class_name=self.__class_name, method_name=_method_name)
        try:
            self.__load_global('setOption')('OverwriteDomain', 'true')
        except offlineWLSTException, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00043', domain_home,
                                                    e.getLocalizedMessage(), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe

        try:
            self.__load_global('writeDomain')(domain_home)
        except offlineWLSTException, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00044', domain_home,
                                                    e.getLocalizedMessage(), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def update_domain(self):
        """
        Update the existing domain configuration with the edits made during the offline session.
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'update_domain'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        try:
            self.__load_global('updateDomain')()
        except offlineWLSTException, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00045',
                                                    e.getLocalizedMessage(), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def close_domain(self):
        """
        Close the domain currently loaded into the offline wlst session.
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'close_domain'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        try:
            self.__load_global('closeDomain')()
        except offlineWLSTException, e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00046',
                                                    e.getLocalizedMessage(), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def connect(self, username, password, url, timeout):
        """
        Connect WLST to a WebLogic Server instance at the provided url with the provided credentials.
        :param username: WebLogic user name
        :param password: WebLogic password
        :param url: WebLogic Server URL
        :param timeout: Connect timeout
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'connect'
        self.__logger.entering(username, url, timeout, class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('connect')(username=username, password=password, url=url, timeout=timeout)
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00047', username, url, timeout,
                                                    self.__get_exception_mode(e), _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def disconnect(self):
        """
        Disconnects WLST from the current connected WebLogic Server instance.
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'disconnect'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('disconnect')()
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00048',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def edit(self):
        """
        Edit the current WebLogic Server configuration.
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'edit'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('edit')()
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00049',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def start_edit(self, acquire_timeout=0, release_timeout=-1, exclusive='false'):
        """
        Start an edit session with the WebLogic Server for the currently connected user.
        :param acquire_timeout: Time (in milliseconds) that WLST waits until it gets a lock, in the event that another user has a lock.
        :param release_timeout: Timeout (in milliseconds) that WLST waits to release the edit lock (-1 means edit session never expires).
        :param exclusive: Whether to request an exclusive lock or not
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        """
        """
        _method_name = 'start_edit'
        self.__logger.entering(acquire_timeout, release_timeout, exclusive, class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('startEdit')(waitTimeInMillis=acquire_timeout, timeOutInMillis=release_timeout, exclusive=exclusive)
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00050',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def stop_edit(self):
        """
        Stop the current edit session and discard all unsaved changes.
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'stop_edit'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('stopEdit')('y')
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00051',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def undo(self):
        """
        Revert all unsaved or unactivated edits.
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'undo'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('undo')('true', 'y')
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00069',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def save(self):
        """
        Save the outstanding WebLogic Server configuration changes for the current edit session.
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'save'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('save')()
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00052',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def activate(self, timeout):
        """
        Activate changes saved during the current edit session but not yet deployed.
        :param timeout: Timeout for the activate command
        :return ActivationTaskMBean: with the state of the changes, and the server status for the activated changes
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'activate'
        self.__logger.entering(timeout, class_name=self.__class_name, method_name=_method_name)
        try:
            activate_status = self.__load_global('activate')(timeout)
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00053',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return activate_status

    def get_existing_object_list(self, wlst_objects_path):
        """
        Get the existing directory list at the provided WLST path.
        :param wlst_objects_path:
        :return: the list of directory objects
        """
        _method_name = 'get_existing_object_list'
        self.__logger.finest('WLSDPLY-00054', wlst_objects_path, class_name=self.__class_name, method_name=_method_name)
        current_dir = self.get_pwd()
        exception_class = exception_helper.get_exception_class(self.__exception_type)
        try:
            result = self.lsc(wlst_objects_path, log_throwing=False)
        except exception_class:
            # if the ls() failed, directory does not exist
            result = []
        self.cd(current_dir)
        self.__logger.finest('WLSDPLY-00055', wlst_objects_path, result,
                             class_name=self.__class_name, method_name=_method_name)
        return result

    def subfolder_exists(self, wlst_mbean_type, wlst_objects_path=None):
        """
        Determine if the child exists in the current mbean.
        :param wlst_objects_path: if not None, the wlst mbean attributes path. Current path if none
        :param wlst_mbean_type: wlst child mbean to search for
        :return: True if the child folder exists under the wlst mbean
        """
        _method_name = 'subfolder_exists'
        child_folder_list = self.get_existing_object_list(wlst_objects_path)
        if child_folder_list is not None and wlst_mbean_type in child_folder_list:
            self.__logger.finest('WLSDPLY-00074', wlst_mbean_type, wlst_objects_path, class_name=self.__class_name,
                                 _method_name=_method_name)
            exists = True
        else:
            self.__logger.finest('WLSDPLY-00075', wlst_mbean_type, wlst_objects_path, class_name=self.__class_name,
                                 method_name=_method_name)
            exists = False
        return exists

    def start_application(self, application_name, *args, **kwargs):
        """
        Start the application in the connected domain.
        :param application_name: the application name
        :param args: the positional arguments to the WLST function
        :param kwargs: the keyword arguments to the WLST function
        :return: progress object (depends on whether it is blocked)
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'start_application'
        self.__logger.entering(application_name, args, kwargs, class_name=self.__class_name, method_name=_method_name)

        try:
            result = self.__load_global('startApplication')(application_name, *args, **kwargs)
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00056', application_name,
                                                    args, kwargs, _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def stop_application(self, application_name, *args, **kwargs):
        """
        Stop the application in the connected domain.
        :param application_name: the application name
        :param args: the positional arguments to the WLST function
        :param kwargs: the keyword arguments to the WLST function
        :return: progress object (depends on whether it is blocked)
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'stop_application'
        self.__logger.entering(application_name, args, kwargs, class_name=self.__class_name, method_name=_method_name)

        try:
            result = self.__load_global('stopApplication')(application_name, *args, **kwargs)
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00057', application_name,
                                                    args, kwargs, _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def deploy_application(self, application_name, *args, **kwargs):
        """
        Deploy the application in the connected domain.
        :param application_name: the application name
        :param args: the positional arguments to the WLST function
        :param kwargs: the keyword arguments to the WLST function
        :return: progress object (depends on whether it is blocked)
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'deploy_application'
        self.__logger.entering(application_name, args, kwargs, class_name=self.__class_name, method_name=_method_name)
        deploy_error = None
        sostream = None

        try:
            self.enable_stdout()
            sostream = StringOutputStream()
            System.setOut(PrintStream(sostream))
            result = self.__load_global('deploy')(application_name, *args, **kwargs)
            self.silence()
        except self.__load_global('WLSTException'), e:
            if sostream:
                deploy_error = sostream.get_string()
            self.silence()
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00058', application_name,
                                                    args, kwargs, _format_exception(e), deploy_error, error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def undeploy_application(self, application_name, *args, **kwargs):
        """
        Undeploy the application in the connected domain.
        :param application_name: the application name
        :param args: the positional arguments to the WLST function
        :param kwargs: the keyword arguments to the WLST function
        :return: progress object (depends on whether it is blocked)
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'undeploy_application'
        self.__logger.entering(application_name, args, kwargs, class_name=self.__class_name, method_name=_method_name)
        undeploy_error = None
        sostream = None
        try:
            self.enable_stdout()
            sostream = StringOutputStream()
            System.setOut(PrintStream(sostream))
            result = self.__load_global('undeploy')(application_name, *args, **kwargs)
            self.silence()
        except self.__load_global('WLSTException'), e:
            if sostream:
              undeploy_error = sostream.get_string()
            self.silence()
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00059', application_name,
                                                    args, kwargs, _format_exception(e), undeploy_error, error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def redeploy_application(self, application_name, *args, **kwargs):
        """
        Redeploy the application in the connected domain.
        :param application_name: the application name
        :param args: the positional arguments to the WLST function
        :param kwargs: the keyword arguments to the WLST function
        :return: progress object (depends on whether it is blocked)
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'redeploy_application'
        self.__logger.entering(application_name, args, kwargs, class_name=self.__class_name, method_name=_method_name)
        redeploy_error = None
        sostream = None

        try:
            self.enable_stdout()
            sostream = StringOutputStream()
            System.setOut(PrintStream(sostream))
            result = self.__load_global('redeploy')(application_name, *args, **kwargs)
            self.silence()
        except self.__load_global('WLSTException'), e:
            if sostream:
                redeploy_error = sostream.get_string()
            self.silence()
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00060', application_name,
                                                    args, kwargs, _format_exception(e), redeploy_error, error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def apply_jrf_with_context(self, jrf_targets, model_context):
        """
        Apply JRF server groups to targeted servers.
        :param jrf_targets: list of Server or cluster to target server groups
        :param model_context: context with current tool parameters
        :raises Exception for the specified tool type: If a WLST error occurs
        """
        for jrf_target in jrf_targets:
            self.apply_jrf(jrf_target, model_context.get_domain_home())

    def apply_jrf(self, jrf_target, domain_home=None):
        """
        For installs that need to connect extension template server groups to servers
        The applyJRF always updates the domain before returning
        :param jrf_target: entity (cluster, server) to target JRF applications and service
        :param domain_home: the domain home directory
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'apply_jrf'
        self.__logger.entering(jrf_target, domain_home, class_name=self.__class_name, method_name=_method_name)
        self.__logger.fine('WLSDPLY-00073', jrf_target, domain_home,
                           class_name=self.__class_name, method_name=_method_name)

        try:
            # It does not matter what value you pass to applyJRF, it will always update the domain.
            # You must arrange your updates around this fact.
            self.__load_global('applyJRF')(jrf_target, domain_home, shouldUpdateDomain=False)
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            raise exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00071', jrf_target, domain_home,
                                                    _format_exception(e), error=e)
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def get_config_manager(self):
        """
        Return the online configuration manager
        :return: configuration manager
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'get_config_manager'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        try:
            result = self.__load_global('getConfigManager')()
        except (offlineWLSTException, self.__load_global('WLSTException')), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00086', 'getConfigManager()',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_current_editor(self, cmgr):
        """
        Return current editor
        :param cmgr: configuration manager
        :return: current editor of the domain
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'get_current_editor'
        self.__logger.entering(cmgr, class_name=self.__class_name, method_name=_method_name)

        try:
            result = cmgr.getCurrentEditor()
        except (offlineWLSTException, self.__load_global('WLSTException')), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00086', 'cmgr.getCurrentEditor()',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def is_editor(self, cmgr):
        """
        Determine if an edit is in progress and if this context is the current editor.
        :param cmgr: current configuration manager
        :return: True if context is current editor
        :raises Exception for the specified tool type: If a WLST error occurs
        """
        _method_name = 'is_editor'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        try:
            result = cmgr.isEditor()
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00094',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name,
                              result=StringUtils.stringForBoolean(result))
        return result

    def have_unactivated_changes(self, cmgr):
        """
        Return True if there is any unactivated changes in the domain
        :param cmgr: configuration manager
        :return: True if there is any unactivated changes in the domain
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'have_unactivated_changes'
        self.__logger.entering(cmgr, class_name=self.__class_name, method_name=_method_name)
        try:
            result = cmgr.haveUnactivatedChanges()
        except (offlineWLSTException, self.__load_global('WLSTException')), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00086',
                                                    'cmgr.haveUnactivatedChanges()', _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_active_activation_tasks(self, cmgr):
        """
        Return list of active activation tasks
        :param cmgr: configuration manager
        :return: list of active activation tasks
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'get_active_activation_tasks'
        self.__logger.entering(cmgr, class_name=self.__class_name, method_name=_method_name)
        try:
            result = cmgr.getActiveActivationTasks()
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00062',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def cm_save(self, cmgr):
        """
        Use the Configuration Manager to save the unsaved changes in online mode.
        :param cmgr: Current Configuration Manager
        :raises Exception for the specified tool type: If unable to perform the online save
        """
        _method_name = 'cm_save'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        try:
            cmgr.save()
        except (self.__load_global('WLSTException'), ValidationException), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00090',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def cm_activate(self, cmgr):
        """
        Use the configuration manager to activate the saved changes
        :param cmgr: current configuration manager
        :throws Exception for the specified tool type: if in the wrong state to activate the changes
        """
        _method_name = 'cm_activate'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        timeout = 300000L
        try:
            cmgr.activate(timeout)
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00091',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def cm_start_edit(self, cmgr):
        """
        Use the configuration manager to start an edit session
        :param cmgr: current configuration manager
        :raises Exception for the specified tool type: If in wrong state to start an edit session
        """
        _method_name = 'cm_edit'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        try:
            cmgr.startEdit(0, -1, False)
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00093',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def get_unsaved_changes(self, cmgr):
        """
        Return the current edit session unsaved changes
        :param cmgr: current configuration manager
        :return: unsaved changes as Change[]
        :raises Exception for the specified tool type: If a WLST error occurs
        """
        _method_name = 'get_changes'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        try:
            changes = cmgr.getChanges()
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00092',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=len(changes))
        return changes

    def have_unsaved_changes(self, cmgr):
        """
        Return true if the current edit session contains unsaved changes
        :param cmgr: Current Configuration Manager of the connected
        :raises Exception for the specified tool type: If a WLST error occurs
        """
        _method_name = 'have_unsaved_changes'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        changes = self.get_unsaved_changes(cmgr)
        unsaved = changes is not None and len(changes) > 0
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name,
                              result=StringUtils.stringForBoolean(unsaved))
        return unsaved

    def server_config(self):
        """
        Change to the serverConfig MBean tree.
        :raises Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'server_config'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('serverConfig')()
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00065',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def domain_runtime(self):
        """
        Change to the domainRuntime MBean tree.
        :raises Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'domain_runtime'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('domainRuntime')()
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00066',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def custom(self):
        """
        Change to the custom MBean tree.
        :raises Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'custom'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        try:
            self.__load_global('custom')()
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00067',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def get_mbi(self, path=None):
        """
        Get the MBeanInfo for the current or specified MBean location.
        :param path: optionally specify path to check
        :return: javax.management.modelmbean.ModelMBeanInfo instance for the current location
        """
        _method_name = 'get_mbi'
        self.__logger.entering(path, class_name=self.__class_name, method_name=_method_name)

        current_path = None
        if path is not None:
            current_path = self.get_pwd()
            self.cd(path)

        result = self.__load_global('getMBI')()

        if current_path is not None:
            self.cd(current_path)

        self.__logger.exiting(result=str_helper.to_string(result),
                              class_name=self.__class_name, method_name=_method_name)
        return result

    def set_shared_secret_store_with_password(self, wallet_path, password):
        """
        Set opss store password
        :param wallet_path: opss extracted wallet
        :param password:  opss store extraction time password
        """
        _method_name = 'set_shared_secret_store_with_password'
        self.__logger.entering(wallet_path, class_name=self.__class_name, method_name=_method_name)
        self.__load_global('setSharedSecretStoreWithPassword')(wallet_path, password)
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def get_pwd(self):
        """
        Return the current WebLogic path. The domain name is stripped from this path.
        :return: path of current location.
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = 'get_pwd'
        self.__logger.finest('WLSDPLY-00033', class_name=self.__class_name, method_name=_method_name)

        try:
            path = self.__load_global('pwd')()[1:]
        except (self.__load_global('WLSTException'), offlineWLSTException), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00034',
                                                    self.__get_exception_mode(e), _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe

        second_slash = path.find('/')
        if second_slash != -1:
            path = path[second_slash:]
        else:
            path = '/'
        self.__logger.finest('WLSDPLY-00035', path, class_name=self.__class_name, method_name=_method_name)
        return path

    def get_object_name_name(self, object_name):
        """
        Get the object name from the ObjectName instance using javax.management.ObjectName methods.
        :param object_name: ObjectName instance
        :return: ObjectName name value
        """
        _method_name = 'get_object_name_name'
        self.__logger.entering(object_name, class_name=self.__class_name, method_name=_method_name)
        name = object_name.getKeyProperty('Name')
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=name)
        return name

    def get_object_name_type(self, object_name):
        """
        Get the type of the object from the ObjectName instance using javax.management.ObjectName methods.
        :param object_name: ObjectName instance
        :return: ObjectName Type value
        """
        _method_name = 'get_object_name_name'
        self.__logger.entering(object_name, class_name=self.__class_name, method_name=_method_name)
        name_type = object_name.getKeyProperty('Type')
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=name_type)
        return name_type

    def silence(self):
        """
        Silence the STDOUT chatter from WLST.
        :raises Exception for the specified tool type: If WLST error occurs
        """
        _method_name = 'silence'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        """
        Silence the chatter that wlst generates by default.
        """
        local_wls = self.__load_global('WLS')
        local_wls_on = self.__load_global('WLS_ON')
        local_wls.setLogToStdOut(False)
        local_wls.setShowLSResult(False)
        local_wls_on.setlogToStandardOut(False)
        local_wls_on.setHideDumpStack('true')
        local_wls.getCommandExceptionHandler().setMode(True)
        local_wls.getCommandExceptionHandler().setSilent(True)
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def enable_stdout(self):
        """
        Performs the wlst commands to enable stdout.
        :raises Exception for the specified tool type: If a WLST error occurs
        """
        local_wls = self.__load_global('WLS')
        local_wls_on = self.__load_global('WLS_ON')
        local_wls.setLogToStdOut(True)
        local_wls.setShowLSResult(True)
        local_wls_on.setlogToStandardOut(True)

    def get_quoted_name_for_wlst(self, name):
        """
        Return a wlst required string for a name value in format ('<name>')
        :param name: to represent in the formatted string
        :return: formatted string
        """
        _method_name = 'get_quoted_name_for_wlst'
        result = name
        if name is not None and '/' in name:
            result = '(' + name + ')'
        self.__logger.finest('WLSDPLY-0098', class_name=self.__class_name, method_name=_method_name)
        return result

    def get_server_runtimes(self):
        """
        Return the ServerRuntimeMBeans instances for the domain
        :return: list of server runtimes
        """
        return self.get_domain_runtime_service().getServerRuntimes()

    def get_domain_runtime_service(self):
        """
        Return the DomainRuntimeServiceMBean instance.
        :return: DomainRuntimeServiceMBean for the domain
        """
        _method_name = 'get_domain_runtime_service'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        try:
            drs = self.__load_global('domainRuntimeService')
        except self.__load_global('WLSTException'), e:
            pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00127',
                                                    _format_exception(e), error=e)
            self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
            raise pwe
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=drs)
        return drs

    def __ls(self, method_name, ls_type, path=None, log_throwing=True):
        """
        Private helper method shared by various API methods
        :param method_name: calling method name
        :param ls_type: the WLST return type requested
        :param path: if not None the path (default is the current path)
        :param log_throwing: whether or not to log the throwing message if the path location is not found
        :return: the result of the WLST ls(returnMap='true') call
        :raises: Exception for the specified tool type: if a WLST error occurs
        """
        _method_name = method_name
        self.__logger.finest('WLSDPLY-00028', method_name, ls_type, path,
                             class_name=self.__class_name, method_name=_method_name)

        load_ls = self.__load_global('ls')
        if path is not None:
            # ls(path, returnMap='true') is busted in earlier versions of WLST so go ahead and
            # change directories to the specified path to workaround this
            current_path = self.get_pwd()
            self.cd(path)
            try:
                result = load_ls(ls_type, returnMap='true', returnType=ls_type)
            except (self.__load_global('WLSTException'), offlineWLSTException), e:
                pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00029', path, ls_type,
                                                        self.__get_exception_mode(e), _format_exception(e), error=e)
                if log_throwing:
                    self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
                self.cd(current_path)
                raise pwe
            self.cd(current_path)
        else:
            current_path = self.get_pwd()
            try:
                result = load_ls(ls_type, returnMap='true', returnType=ls_type)
            except (self.__load_global('WLSTException'), offlineWLSTException), e:
                pwe = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00029', current_path, ls_type,
                                                        self.__get_exception_mode(e), _format_exception(e), error=e)
                self.__logger.throwing(class_name=self.__class_name, method_name=_method_name, error=pwe)
                raise pwe
        self.__logger.finest('WLSDPLY-00030', method_name, ls_type, current_path, result,
                             class_name=self.__class_name, method_name=_method_name)
        return result

    def __check_online_connection(self):
        return self.__load_global('WLS_ON').isConnected()

    def __load_global(self, global_name):
        """
        The WLST globals were stored on entry into the tool instance. Look for the provided name in the
        globals and return the corresponding function or variable.
        :param global_name: Name to look up in the globals
        :return: the function or variable associated with the name from the globals
        :raises: Exception for the specified tool type: If the global name is not found in the globals
        """
        member = None
        if wlst_functions is not None and global_name in wlst_functions:
            member = wlst_functions[global_name]

        if member is None:
            raise exception_helper.create_exception(self.__exception_type, 'WLSDPLY-00087', global_name)
        return member

    def __get_exception_mode(self, e):
        """
        Return a text value dependent on online or offline mode. The wlst exception messages differ between offline
        and online, and this can provide clarity to our exception. This value is not internationalized.
        :param e: The exception instance. The class of this instance determines whether the exception was thrown
                    in offline or online mode
        :return: The text value online, offline or unknown
        """
        if isinstance(e, self.__load_global('WLSTException')):
            return 'online'
        if isinstance(e, offlineWLSTException):
            return 'offline'
        return 'unknown'


def _format_exception(e):
    """
    Format the exception
    :param e: the exception
    :return: the formatted exception message
    """
    if isinstance(e, offlineWLSTException):
        message = e.getLocalizedMessage()
        #
        # Try to find a message that is not empty
        #
        if message is None:
            cause = e.getCause()
            while message is None and cause is not None:
                message = cause.getLocalizedMessage()
                cause = cause.getCause()
        return message
    return str_helper.to_string(e)
