"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

from oracle.weblogic.deploy.util import PyWLSTException

from wlsdeploy.exception import exception_helper
from wlsdeploy.util import wlst_extended
from wlsdeploy.util import wlst_helper


class WlstHelper(object):
    """
    This class simply wraps the wlst_helper methods to catch exceptions and convert them into
    BundleAwareException of the specified types.
    """
    __class_name = 'WlstHelper'

    def __init__(self, logger, exception_type):
        self.__logger = logger
        self.__exception_type = exception_type
        return

    def assign(self, source_type, source_name, target_type, target_name):
        """
        Assign target entity to source entity
        :param source_type: source entity type
        :param source_name: entity name
        :param target_type: target type
        :param target_name: target name
        :raises: BundleAwareException of the specified type: if an error occurs
        """

        _method_name = 'assign'

        try:
            wlst_helper.assign(source_type, source_name, target_type, target_name)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19143',
                                                   target_type, target_name, source_type, source_name,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

    def apply_jrf(self, jrf_target, model_context, should_update=False):
        """
        For those installs that require populating the JRF server group information to the managed servers
        :param jrf_target: The entity to which to target the JRF applications and services
        :param model_context: The context containing the tool session information needed for the applyJRF
        :param should_update: If True the applyJRF will update the domain after apply
        :raises: Exception specific to tool type
        """
        _method_name = 'apply_jrf'

      
        try:
            wlst_extended.session_start(model_context.is_wlst_online(), jrf_target, 
                                        model_context.get_admin_user(),
                                        model_context.get_admin_password(),
                                        model_context.get_admin_url(),
                                        model_context.get_domain_home())
            wlst_extended.apply_jrf(jrf_target, domain_home=model_context.get_domain_home(),
                                    should_update=should_update)
            wlst_extended.session_end(model_context.is_wlst_online(), jrf_target)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19146',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

    def apply_jrf_control_updates(self, jrf_targets, model_context):
        """
        For those installs that require populating the JRF server group information to the managed servers. Control
        the session updates within the global context. Save the updates in the current context.
        :param jrf_targets: The list of entities to which to target the JRF applications and services
        :param model_context: The context containing the tool session information needed for the applyJRF
        :raises: Exception specific to tool type
        """
        _method_name = 'apply_jrf_control_updates'


        try:
            wlst_extended.apply_jrf_global_updates(model_context.is_wlst_online(),
                                                   jrf_targets,
                                                   admin_user=model_context.get_admin_user(),
                                                   admin_pass=model_context.get_admin_password(),
                                                   admin_url=model_context.get_admin_url(),
                                                   domain_home=model_context.get_domain_home())
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19146',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex


        return

    def cd(self, wlst_path):
        """
        Change WLST directories to the specified path
        :param wlst_path: the WLST path
        :return: the return value from the cd()
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'cd'

        try:
            result = wlst_helper.cd(wlst_path)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19100',
                                                   wlst_path, pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def get(self, attribute_name):
        """
        Return the value for the attribute at the current location

        :param attribute_name: name of the wlst attribute
        :return: value set for the attribute
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get'

        try:
            result = wlst_helper.get(attribute_name)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19101', attribute_name,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def set(self, attribute_name, attribute_value, masked=False):
        """
        Set the configuration for the indicated attribute to the provided value.

        :param attribute_name: attribute name at the current location
        :param attribute_value: to configure the attribute
        :param masked: whether the attribute value should be masked from the log file, default is False
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'set'

        try:
            wlst_helper.set(attribute_name, attribute_value)
        except PyWLSTException, pwe:
            log_value = attribute_value
            if masked:
                log_value = '<masked>'
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19102', attribute_name, log_value,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def set_with_cmo(self, attribute_name, attribute_value, masked=False):
        """
        Set the specified attribute using the corresponding cmo set method (e.g., cmo.setListenPort()).
        :param attribute_name: the WLST attribute name
        :param attribute_value: the WLST value
        :param masked: whether or not to mask the attribute_value from the log files.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'set_with_cmo'

        try:
            wlst_helper.set_with_cmo(attribute_name, attribute_value, masked=masked)
        except PyWLSTException, pwe:
            log_value = attribute_value
            if masked:
                log_value = '<masked>'
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19136', attribute_name, log_value,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def create(self, wlst_name, wlst_type, base_provider_type=None):
        """
        Create the mbean folder with the provided name at the current location.
        :param wlst_name: the MBean name
        :param wlst_type: the MBean type
        :param base_provider_type: the base security provider type, if required
        :return: the MBean object returned by the underlying WLST create() method
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'create'

        try:
            mbean = wlst_helper.create(wlst_name, wlst_type, base_provider_type)
        except PyWLSTException, pwe:
            if base_provider_type is None:
                ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19103', wlst_type, wlst_name,
                                                       pwe.getLocalizedMessage(), error=pwe)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            else:
                ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19134', base_provider_type,
                                                       wlst_type, wlst_name, pwe.getLocalizedMessage(), error=pwe)
            raise ex
        return mbean

    def delete(self, wlst_name, wlst_type):
        """
        Delete an MBean of the specified name and type at the current location.
        :param wlst_name: the MBean name
        :param wlst_type: the MBean type
        :raises: PyWLSTException: if a WLST error occurs
        """
        _method_name = 'delete'

        try:
            wlst_helper.delete(wlst_name, wlst_type)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19135', wlst_type, wlst_name,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def create_and_cd(self, alias_helper, type_name, name, location, create_path=None):
        """
        Create a new MBean instance and change directories to its attributes location.
        :param alias_helper: the alias helper object
        :param type_name: the WLST type
        :param name: the name for the new object
        :param location: the location
        :param create_path: the WLST path from which to create the new MBean
        :return: the result from cd()
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'create_and_cd'

        try:
            if create_path is not None:
                wlst_helper.cd(create_path)
            wlst_helper.create(name, type_name)
            result = wlst_helper.cd(alias_helper.get_wlst_attributes_path(location))
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19104', type_name, name,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def lsc(self, path=None, log_throwing=True):
        """
        Get the list of child folders from WLST.
        :param path: the WLST path, by default it uses the current location
        :param log_throwing: whether to log throwing if the path does not exist, the default is True
        :return: the list of folder names
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'lsc'

        try:
            result = wlst_helper.lsc(path=path, log_throwing=log_throwing)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19105',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def lsa(self, path=None, log_throwing=True):
        """
        Get the map of attributes and their values from WLST.
        :param path: the WLST path, by default it uses the current location
        :param log_throwing: whether to log throwing if the path does not exist, the default is True
        :return: the map of attributes and their values
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'lsa'

        try:
            result = wlst_helper.lsa(path=path, log_throwing=log_throwing)
        except PyWLSTException, pwe:
            if path is None:
                path = self.get_pwd()
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19106', path,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def get_pwd(self):
        """
        Get the current WLST directory path.
        :return: the WLST path
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_pwd'

        try:
            result = wlst_helper.get_pwd()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19107',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def get_existing_object_list(self, wlst_path=None):
        """
        Get the existing directory list at the provided WLST path.
        :param wlst_path: the WLST path, by default it uses the current location
        :return: the list of folder names
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_existing_object_list'

        try:
            result = wlst_helper.get_existing_object_list(wlst_path)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19108',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def subfolder_exists(self, wlst_mbean_type, wlst_path=None):
        """
        Determine if the child exists in the current mbean.
        :param wlst_path: This will be the MBean attributes path, or current path in WLST session if Noe
        :param wlst_mbean_type: WLST child MBean to search for
        :return: True if the child folder exists for the MBean
        """
        _method_name = 'subfolder_exists'

        # Exception not currently thrown.
        try:
            result = wlst_helper.subfolder_exists(wlst_path, wlst_mbean_type)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19108',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def set_option_if_needed(self, option_name, option_value):
        """
        Set the WLST domain option to the provided value if the name and value are not None.

        :param option_name: attribute name at the current location
        :param option_value: to configure the attribute
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'set_option_if_needed'

        try:
            wlst_helper.set_option(option_name, option_value)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19109', option_name, option_value,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def set_server_groups(self, server_name, server_groups_to_target):
        """
        Target the server groups to the specified server.

        :param server_name: the server name
        :param server_groups_to_target: the list of server groups to target
        :param current_edit: if True and online, perform the set in the current edit session
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'set_server_groups'

        try:
            wlst_helper.set_server_groups(server_name, server_groups_to_target)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19110', server_name,
                                                   server_groups_to_target, pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        return

    def get_database_defaults(self):
        """
        Assign the database defaults based on the service table data source.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_database_defaults'

        try:
            wlst_helper.get_database_defaults()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19111',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def get_quoted_name_for_wlst(self, model_value):
        """
        Get the quoted MBean name to use in WLST.
        This method checks for slashes in the name and quotes the name accordingly.
        :param model_value: the model value
        :return: the quoted value to pass to WLST
        """
        return wlst_helper.get_quoted_name_for_wlst(model_value)

    def read_domain(self, domain_home):
        """
        Read the domain from the specified location.
        :param domain_home: the domain directory to read
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'read_domain'

        try:
            wlst_helper.read_domain(domain_home)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19112', domain_home,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def update_domain(self):
        """
        Update the domain.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'update_domain'

        try:
            wlst_helper.update_domain()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19113',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def write_domain(self, domain_home):
        """
        Write the domain to the specified location.
        :param domain_home: the domain directory to which to write
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'write_domain'

        try:
            wlst_helper.write_domain(domain_home)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19114', domain_home,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def close_domain(self):
        """
        Close the domain.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'close_domain'

        try:
            wlst_helper.close_domain()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19115',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def read_template(self, template_name):
        """
        Read the domain template from the specified location.
        :param template_name: the domain template to read
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'read_template'

        try:
            wlst_helper.read_template(template_name)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19116', template_name,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def select_template(self, template_name):
        """
        Select the domain template from the specified location.
        :param template_name: the domain template to select
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'select_template'

        try:
            wlst_helper.select_template(template_name)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19117', template_name,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def add_template(self, template_name):
        """
        Add the domain extension template from the specified location.
        :param template_name: the domain extension template to add
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'add_template'

        try:
            wlst_helper.add_template(template_name)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19118', template_name,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def load_templates(self):
        """
        Load the selected domain templates into the domain.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'load_templates'

        try:
            wlst_helper.load_templates()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19119',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def close_template(self):
        """
        Close the domain template.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'close_template'

        try:
            wlst_helper.close_template()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19120',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def connect(self, admin_user, admin_pwd, admin_url):
        """
        Connects to the domain at the specified URL with the specified credentials.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'connect'

        try:
            wlst_helper.connect(admin_user, admin_pwd, admin_url)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19127', admin_url, admin_user,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def edit(self):
        """
        Edit the current Weblogic Server configuration.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'edit'

        try:
            wlst_helper.edit()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19128',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def start_edit(self):
        """
        Start an edit session with the Weblogic Server for the currently connected user.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'start_edit'

        try:
            wlst_helper.start_edit()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19129',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def stop_edit(self):
        """
        Stop the current edit session and discard all unsaved changes.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'stop_edit'

        try:
            wlst_helper.stop_edit()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19130',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def undo(self):
        """
        Revert all unsaved or unactivated edits.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'undo'

        try:
            wlst_helper.undo()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19142',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def save(self):
        """
        Save the outstanding Weblogic Server configuration changes for the current edit session.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'save'

        try:
            wlst_helper.save()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19131',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def activate(self):
        """
        Activate changes saved during the current edit session but not yet deployed.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'activate'

        try:
            wlst_helper.activate()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19132',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def disconnect(self):
        """
        Disconnects WLST from the current connected WebLogic Server instance.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'disconnect'

        try:
            wlst_helper.disconnect()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19133',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def silence(self):
        """
        Performs the wlst commands to suppress stdout and stderr chatter.
        """
        _method_name = 'silence'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)
        wlst_helper.silence()
        return

    def set_if_needed(self, wlst_name, wlst_value, model_type, model_name, masked=False):
        """
        Set the WLST attribute to the specified value if the name and value are not None.
        :param wlst_name: the WLST attribute name
        :param wlst_value: the WLST attribute value
        :param model_type: the model type
        :param model_name: the model MBean name
        :param masked: whether or not to mask the value in the logs, default value is False
        :raises: CreateException: if an error occurs
        """
        _method_name = 'set_if_needed'

        if wlst_name is not None and wlst_value is not None:
            try:
                wlst_helper.set(wlst_name, wlst_value)
            except PyWLSTException, pwe:
                value = wlst_value
                if masked:
                    value = '<masked>'
                ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19121', model_type, model_name,
                                                       wlst_name, value, pwe.getLocalizedMessage(), error=pwe)
                self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
        return

    def get_mbean_for_wlst_path(self, wlst_path):
        """
        Get the MBean for the specified location.
        :param wlst_path: the WLST path
        :return: the MBean or None
        :raises: CreateException: if an error occurs
        """
        _method_name = 'get_mbean_for_wlst_path'

        try:
            wlst_value = wlst_helper.get_mbean_for_wlst_path(wlst_path)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19122',
                                                   wlst_path, pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return wlst_value

    def get_config_manager(self):
        """
        Returns the online configuration manager
        :return: online configuration manager
        :raises: BundleAwareException: if an error occurs
        """
        _method_name = 'get_config_manager'

        try:
            wlst_value = wlst_helper.get_config_manager()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19123',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return wlst_value

    def get_active_activation_tasks(self, config_manager):
        """
        Return list of active activation tasks.
        :param config_manager: configuration manager
        :return: list of active activation tasks
        :raises: BundleAwareException: if an error occurs
        """
        _method_name = 'get_active_activation_tasks'

        try:
            active_tasks = wlst_helper.get_active_activation_tasks(config_manager)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19124',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return active_tasks

    def get_current_editor(self, config_manager):
        """
        Return current editor
        :param config_manager: configuration manager
        :return: current editor of the domain
        :raises: BundleAwareException: if an error occurs
        """
        _method_name = 'get_current_editor'

        try:
            editor = wlst_helper.get_current_editor(config_manager)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19125',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return editor

    def have_unactivated_changes(self, config_manager):
        """
        Return True if there is any unactivated changes in the domain
        :param config_manager: configuration manager
        :return: True if there are any unactivated changes in the domain
        :raises: BundleAwareException: if an error occurs
        """
        _method_name = 'have_unactivated_changes'

        try:
            have_changes = wlst_helper.have_unactivated_changes(config_manager)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19126',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return have_changes

    def start_application(self, application_name, *args, **kwargs):
        """
        Start the application in the connected domain.
        :param application_name: the application name
        :param args: the positional arguments to the WLST function
        :param kwargs: the keywork arguments to the WLST function
        :return: progress object (depends on whether it is blocked)
        :raises: BundleAwareException: if an error occurs
        """
        _method_name = 'start_application'

        try:
            result = wlst_helper.start_application(application_name, *args, **kwargs)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19139', application_name,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def stop_application(self, application_name, *args, **kwargs):
        """
        Stop the application in the connected domain.
        :param application_name: the application name
        :param args: the positional arguments to the WLST function
        :param kwargs: the keywork arguments to the WLST function
        :return: progress object (depends on whether it is blocked)
        :raises: BundleAwareException: if an error occurs
        """
        _method_name = 'stop_application'

        try:
            result = wlst_helper.stop_application(application_name, *args, **kwargs)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19140', application_name,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def deploy_application(self, application_name, *args, **kwargs):
        """
        Deploy the application in the connected domain.
        :param application_name: the application name
        :param args: the positional arguments to the WLST function
        :param kwargs: the keywork arguments to the WLST function
        :return: progress object (depends on whether it is blocked)
        :raises: BundleAwareException: if an error occurs
        """
        _method_name = 'deploy_application'

        try:
            result = wlst_helper.deploy_application(application_name, *args, **kwargs)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19137', application_name,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def redeploy_application(self, application_name, *args, **kwargs):
        """
        Redeploy the application in the connected domain.
        :param application_name: the application name
        :param args: the positional arguments to the WLST function
        :param kwargs: the keywork arguments to the WLST function
        :return: progress object (depends on whether it is blocked)
        :raises: BundleAwareException: if an error occurs
        """
        _method_name = 'redeploy_application'

        try:
            result = wlst_helper.redeploy_application(application_name, args, kwargs)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19138', application_name,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def undeploy_application(self, application_name, *args, **kwargs):
        """
        Undeploy the application in the connected domain.
        :param application_name: the application name
        :param args: the positional arguments to the WLST function
        :param kwargs: the keywork arguments to the WLST function
        :return: progress object (depends on whether it is blocked)
        :raises: BundleAwareException: if an error occurs
        """
        _method_name = 'undeploy_application'

        try:
            result = wlst_helper.redeploy_application(application_name, args, kwargs)
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19141', application_name,
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def server_config(self):
        """
        Change to the serverConfig MBean tree.
        :raises: BundleAwareException: if an error occurs
        """
        _method_name = 'server_config'

        try:
            wlst_helper.server_config()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19137',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def domain_runtime(self):
        """
        Change to the domainRuntime MBean tree.
        :raises: BundleAwareException: if an error occurs
        """
        _method_name = 'domain_runtime'

        try:
            wlst_helper.domain_runtime()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19137',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def is_connected(self):
        """
        Determine if the wlst session is currently connected to the admin server.
        :return: True if connected
        """
        return wlst_helper.is_connected()

    def custom(self):
        """
        Change to the custom MBean tree.
        :raises: BundleAwareException: if an error occurs
        """
        _method_name = 'domain_runtime'

        try:
            wlst_helper.custom()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19137',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return

    def save_and_close(self, model_context):
        """
        Call this if necessary to save changes and disconnect from the domain in the middle of the session.
        This works in both offline and online.
        :param model_context: Contains information about the session, including the WlstMode
        """
        _method_name = 'save_and_close'
        try:
            if model_context.is_wlst_online():
                wlst_helper.save_and_close_online()
            else:
                wlst_helper.save_and_close_offline()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19145', pwe.getLocalizedMessage(),
                                                   error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

    def save_and_activate(self, model_context):
        """
        Call this if necessary to save and activate changes in the middle of the session.
        This works in both offline and online.
        :param model_context: Contains information about the session, including the WlstMode
        """
        _method_name = 'save_and_activate'
        try:
            if model_context.is_wlst_online():
                wlst_helper.save_and_activate_online()
            else:
                wlst_helper.save_and_activate_offline()
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19147', pwe.getLocalizedMessage(),
                                                   error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

    def reopen(self, model_context):
        """
        Establish connection with the domain and start editing in both online and offline wlst mode.
        :param model_context: contains the information needed for the reopen, including the WlstMode
        """
        _method_name = 'reopen'
        try:
            if model_context.is_wlst_online():
                wlst_helper.reopen_online(model_context.get_admin_user(), model_context.get_admin_password(),
                                          model_context.get_admin_url())
            else:
                wlst_helper.reopen_offline(model_context.get_domain_home())
        except PyWLSTException, pwe:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19144',
                                                   pwe.getLocalizedMessage(), error=pwe)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
