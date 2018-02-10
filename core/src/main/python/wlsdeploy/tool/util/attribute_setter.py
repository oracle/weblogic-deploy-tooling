"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from java.util import List

import javax.management.ObjectName as ObjectName

from oracle.weblogic.deploy.util import TypeUtils

import org.python.modules.jarray as jarray

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper

from wlsdeploy.aliases.model_constants import CAPACITY
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import CONTEXT_REQUEST_CLASS
from wlsdeploy.aliases.model_constants import DISTRIBUTED_QUEUE
from wlsdeploy.aliases.model_constants import DISTRIBUTED_TOPIC
from wlsdeploy.aliases.model_constants import FAIR_SHARE_REQUEST_CLASS
from wlsdeploy.aliases.model_constants import FILE_STORE
from wlsdeploy.aliases.model_constants import HEAP_DUMP_ACTION
from wlsdeploy.aliases.model_constants import IMAGE_NOTIFICATION
from wlsdeploy.aliases.model_constants import JDBC_STORE
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import JMS_BRIDGE_DESTINATION
from wlsdeploy.aliases.model_constants import JMS_NOTIFICATION
from wlsdeploy.aliases.model_constants import JMS_RESOURCE
from wlsdeploy.aliases.model_constants import JMS_SERVER
from wlsdeploy.aliases.model_constants import JMX_NOTIFICATION
from wlsdeploy.aliases.model_constants import LOG_ACTION
from wlsdeploy.aliases.model_constants import MACHINE
from wlsdeploy.aliases.model_constants import MAX_THREADS_CONSTRAINT
from wlsdeploy.aliases.model_constants import MIGRATABLE_TARGET
from wlsdeploy.aliases.model_constants import MIN_THREADS_CONSTRAINT
from wlsdeploy.aliases.model_constants import PERSISTENT_STORE
from wlsdeploy.aliases.model_constants import QUEUE
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP
from wlsdeploy.aliases.model_constants import RESPONSE_TIME_REQUEST_CLASS
from wlsdeploy.aliases.model_constants import REST_NOTIFICATION
from wlsdeploy.aliases.model_constants import SAF_IMPORTED_DESTINATION
from wlsdeploy.aliases.model_constants import SAF_QUEUE
from wlsdeploy.aliases.model_constants import SAF_TOPIC
from wlsdeploy.aliases.model_constants import SAF_REMOTE_CONTEXT
from wlsdeploy.aliases.model_constants import SCRIPT_ACTION
from wlsdeploy.aliases.model_constants import SELF_TUNING
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SMTP_NOTIFICATION
from wlsdeploy.aliases.model_constants import SNMP_NOTIFICATION
from wlsdeploy.aliases.model_constants import TEMPLATE
from wlsdeploy.aliases.model_constants import THREAD_DUMP_ACTION
from wlsdeploy.aliases.model_constants import TOPIC
from wlsdeploy.aliases.model_constants import UNIFORM_DISTRIBUTED_QUEUE
from wlsdeploy.aliases.model_constants import UNIFORM_DISTRIBUTED_TOPIC
from wlsdeploy.aliases.model_constants import WATCH_NOTIFICATION


class AttributeSetter(object):
    """
    Contains the "set" methods used to set WLST values that require mbeans or other special processing.
    The public set_ methods in this class correspond directly to the set_method names in the alias files.
    The signature for each set_ method is (location, key, value), where key and value are from the model.
    """

    # used for target search
    __target_type_names = [
        CLUSTER,
        SERVER,
        MIGRATABLE_TARGET,
    ]

    # used for destination search
    __destination_type_names = [
        QUEUE,
        TOPIC,
        DISTRIBUTED_QUEUE,
        DISTRIBUTED_TOPIC,
        UNIFORM_DISTRIBUTED_QUEUE,
        UNIFORM_DISTRIBUTED_TOPIC
    ]

    # used for SAF destination search
    __saf_destination_type_names = [
        SAF_QUEUE,
        SAF_TOPIC
    ]

    # used for persistent store search
    __persistent_store_type_names = [
        FILE_STORE,
        JDBC_STORE
    ]

    # used for self-tuning deployment and attribute processing.
    # these names are applicable as self-tuning sub-folder names, and work manager attribute names.
    # work manager is intentionally excluded and treated separately.
    __self_tuning_type_names = [
        CAPACITY,
        CONTEXT_REQUEST_CLASS,
        FAIR_SHARE_REQUEST_CLASS,
        MAX_THREADS_CONSTRAINT,
        MIN_THREADS_CONSTRAINT,
        RESPONSE_TIME_REQUEST_CLASS
    ]

    # used for WLDF watch notification search
    __watch_action_types = [
        HEAP_DUMP_ACTION,
        IMAGE_NOTIFICATION,
        JMS_NOTIFICATION,
        JMX_NOTIFICATION,
        LOG_ACTION,
        REST_NOTIFICATION,
        SCRIPT_ACTION,
        SMTP_NOTIFICATION,
        SNMP_NOTIFICATION,
        THREAD_DUMP_ACTION
    ]

    _class_name = "AttributeSetter"

    def __init__(self, aliases, logger, exception_type, wlst_mode=WlstModes.OFFLINE):
        self.__logger = logger
        self.__exception_type = exception_type
        self.__wlst_mode = wlst_mode
        self.__alias_helper = AliasHelper(aliases, self.__logger, exception_type)
        self.__wlst_helper = WlstHelper(self.__logger, exception_type)
        return

    #
    # public set_ methods for special attribute types, signature (self, location, key, value, ...)
    #

    def set_target_jms_mbeans(self, location, key, value):
        """
        Set the target MBeans for targets that can include JMS resources (e.g., JMSServer).
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :raises BundleAwareException of the specified type: if target is not found
        """
        self.set_target_mbeans(location, key, value, include_jms=True)
        return

    def set_target_mbeans(self, location, key, value, include_jms=False):
        """
        Set the target MBeans.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param include_jms: whether or not to include JMS resources
        :raises BundleAwareException of the specified type: if target is not found
        """
        targets_value = self.__build_target_mbean_list(value, include_jms=include_jms)
        self.__set_attribute(location, key, targets_value, use_raw_value=True)
        return

    def set_jms_error_destination_mbean(self, location, key, value):
        """
        Set the JMS Error Destination MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :raises BundleAwareException of the specified type: if destination is not found
        """
        mbean = self.__find_jms_destination_mbean(location, value)
        self.__set_attribute(location, key, mbean, use_raw_value=True)
        return

    def set_jms_bridge_destination_mbean(self, location, key, value):
        """
        Set the JMS Bridge Destination MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :raises BundleAwareException of the specified type: if destination is not found
        """
        mbean = self.__find_in_resource_group_or_domain(location, JMS_BRIDGE_DESTINATION, value, required=True)
        self.__set_attribute(location, key, mbean, use_raw_value=True)
        return

    def set_persistent_store_mbean(self, location, key, value):
        """
        Set the Persistent Store MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :raises BundleAwareException of the specified type: if store is not found
        """
        mbean = self.__find_persistent_store(location, value)
        self.__set_attribute(location, key, mbean, use_raw_value=True)
        return

    def set_data_source_mbean(self, location, key, value):
        """
        Set the DataSource MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :raises BundleAwareException of the specified type: if DataSource is not found
        """
        mbean = self.__find_in_resource_group_or_domain(location, JDBC_SYSTEM_RESOURCE, value, required=True)
        self.__set_attribute(location, key, mbean, use_raw_value=True)
        return

    def set_saf_remote_context_mbean(self, location, key, value):
        """
        Set the SAF RemoteContext MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :raises BundleAwareException of the specified type: if SAF RemoteContext is not found
        """
        resource_location = self.__get_parent_location(location, JMS_RESOURCE)
        mbean = self.__find_in_location(resource_location, SAF_REMOTE_CONTEXT, value)
        self.__set_attribute(location, key, mbean, use_raw_value=True)
        return

    def set_saf_error_destination_mbean(self, location, key, value):
        """
        Set the SAF Error Destination MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :raises BundleAwareException of the specified type: if destination is not found
        """
        mbean = self.__find_saf_destination_mbean(location, value)
        self.__set_attribute(location, key, mbean, use_raw_value=True)
        return

    def set_self_tuning_mbean(self, location, key, value):
        """
        Set the SelfTuning MBeans.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :raises BundleAwareException of the specified type: if MBean is not found
        """
        tuning_location = self.__get_parent_location(location, SELF_TUNING)
        mbean = self.__find_in_location(tuning_location, key, value, required=True)
        self.__set_attribute(location, key, mbean, use_raw_value=True)
        return

    def set_server_mbeans(self, location, key, value):
        """
        Set the Servers MBeans.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :raises BundleAwareException of the specified type: if a server is not found
        """
        mbeans = self.__build_server_mbean_list(value)
        self.__set_attribute(location, key, mbeans, use_raw_value=True)
        return

    def set_server_mbean(self, location, key, value):
        """
        Set the Server MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :raises BundleAwareException of the specified type: if the server is not found
        """
        mbean = self.__find_in_location(LocationContext(), SERVER, value, required=True)
        self.__set_attribute(location, key, mbean, use_raw_value=True)
        return

    def set_cluster_mbean(self, location, key, value):
        """
        Set the Cluster MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :raises BundleAwareException of the specified type: if the cluster is not found
        """
        mbean = self.__find_in_location(LocationContext(), CLUSTER, value, required=True)
        self.__set_attribute(location, key, mbean, use_raw_value=True)
        return

    def set_machine_mbean(self, location, key, value):
        """
        Set the Machine MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :raises BundleAwareException of the specified type: if the machine is not found
        """
        mbean = self.__find_in_location(LocationContext(), MACHINE, value, required=True)
        self.__set_attribute(location, key, mbean, use_raw_value=True)
        return

    def set_jms_template_mbean(self, location, key, value):
        """
        Set the JMS Template MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :raises BundleAwareException of the specified type: if the JMS Template is not found
        """
        resource_location = self.__get_parent_location(location, JMS_RESOURCE)
        mbean = self.__find_in_location(resource_location, TEMPLATE, value, required=True)
        self.__set_attribute(location, key, mbean, use_raw_value=True)
        return

    def set_wldf_action_mbeans(self, location, key, value):
        """
        Set the WLDF Action/Notification MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :raises BundleAwareException of the specified type: if the WLDF Action/Notification is not found
        """
        watch_location = self.__get_parent_location(location, WATCH_NOTIFICATION)
        action_names = TypeUtils.convertToType(List, value)  # type: list of str

        action_mbeans = []
        for action_name in action_names:
            action_mbean = self.__find_wldf_action(watch_location, action_name)
            action_mbeans.append(action_mbean)

        if self.__wlst_mode == WlstModes.ONLINE:
            # for online, call the current location's add method for each action mbean
            location_mbean = self.__wlst_helper.cd(self.__wlst_helper.get_pwd())
            for action_mbean in action_mbeans:
                location_mbean.addNotification(action_mbean)
        else:
            self.__set_attribute(location, key, action_mbeans, use_raw_value=True)
        return

    #
    # internal lookup methods
    #

    def __build_target_mbean_list(self, target_value, include_jms=False):
        """
        Construct the target MBean list.
        :param target_value: the target value
        :param include_jms: whether or not to include JMS targets, the default is False
        :return: the Java array of MBeans ObjectNames
        :raises BundleAwareException of the specified type: if an error occurs
        """
        target_names = TypeUtils.convertToType(List, target_value)  # type: list of str

        name_list = []
        for target_name in target_names:
            target_mbean = self.__find_target(target_name, include_jms=include_jms)
            name_list.append(target_mbean.getObjectName())

        return jarray.array(name_list, ObjectName)

    def __build_server_mbean_list(self, value):
        """
        Construct the server MBean list.
        :param value: the value
        :return: the Java array of MBeans ObjectNames
        :raises BundleAwareException of the specified type: if an error occurs
        """
        server_names = TypeUtils.convertToType(List, value)  # type: list of str

        name_list = []
        for server_name in server_names:
            mbean = self.__find_in_location(LocationContext(), SERVER, server_name, required=True)
            name_list.append(mbean.getObjectName())

        return jarray.array(name_list, ObjectName)

    def __find_target(self, target_name, include_jms=False):
        """
        Find a target by name.
        :param target_name: the target name
        :param include_jms: whether or not to include JMS in the search, the default is False
        :return: the MBean for the target
        :raises BundleAwareException of the specified type: if an error occurs
        """
        method_name = '__find_target'
        location = LocationContext()
        for type_name in self.__target_type_names:
            mbean = self.__find_in_location(location, type_name, target_name)
            if mbean is not None:
                return mbean

        if include_jms:
            mbean = self.__find_in_resource_group_or_domain(location, JMS_SERVER, target_name)
            if mbean is not None:
                return mbean

        ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19200', target_name)
        self.__logger.throwing(class_name=self._class_name, method_name=method_name, error=ex)
        raise ex

    def __find_jms_destination_mbean(self, location, destination_name):
        """
        Find the destination with the specified name and return its WLST mbean.
        :param location: the WLST location of the attribute
        :param destination_name: the name of the destination to find
        :return: the mbean for the destination
        :raises BundleAwareException of the specified type: if destination is not found
        """
        method_name = '__find_jms_destination_mbean'

        resource_location = self.__get_parent_location(location, JMS_RESOURCE)
        for type_name in self.__destination_type_names:
            mbean = self.__find_in_location(resource_location, type_name, destination_name)
            if mbean is not None:
                return mbean

        resource_type, resource_name = self.__alias_helper.get_model_type_and_name(resource_location)
        ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19201', destination_name, resource_name)
        self.__logger.throwing(class_name=self._class_name, method_name=method_name, error=ex)
        raise ex

    def __find_persistent_store(self, location, store_name):
        """
        Find the persistent store with the specified name and return its WLST mbean.
        :param location: the WLST location of the attribute
        :param store_name: the name of the store to find
        :return: the mbean for the store
        :raises BundleAwareException of the specified type: if store is not found
        """
        method_name = '__find_persistent_store'
        for type_name in self.__persistent_store_type_names:
            mbean = self.__find_in_resource_group_or_domain(location, type_name, store_name)
            if mbean is not None:
                return mbean

        ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19202', PERSISTENT_STORE, store_name)
        self.__logger.throwing(class_name=self._class_name, method_name=method_name, error=ex)
        raise ex

    def __find_saf_destination_mbean(self, location, destination_name):
        """
        Find the SAF destination with the specified name and return its WLST mbean.
        :param location: the WLST location of the attribute
        :param destination_name: the name of the SAF destination to find
        :return: the mbean for the SAF destination
        :raises BundleAwareException of the specified type: if SAF destination is not found
        """
        method_name = '__find_saf_destination_mbean'
        resource_location = self.__get_parent_location(location, JMS_RESOURCE)
        destination_location = LocationContext(resource_location).append_location(SAF_IMPORTED_DESTINATION)
        existing_sets = self.__get_existing_object_list(destination_location)

        token_name = self.__alias_helper.get_name_token(destination_location)
        for set_name in existing_sets:
            if token_name is not None:
                destination_location.add_name_token(token_name, set_name)
            for type_name in self.__saf_destination_type_names:
                mbean = self.__find_in_location(destination_location, type_name, destination_name)
                if mbean is not None:
                    return mbean

        resource_type, resource_name = self.__alias_helper.get_model_type_and_name(resource_location)
        ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19203', destination_name, resource_name)
        self.__logger.throwing(class_name=self._class_name, method_name=method_name, error=ex)
        raise ex

    def __find_wldf_action(self, watch_location, action_name):
        """
        Find the WLDF action with the specified name and return its WLST mbean.
        :param watch_location: the WLST location of the watch notification
        :param action_name: the name of the action to find
        :return: the mbean for the action
        :raises BundleAwareException of the specified type: if action is not found
        """
        method_name = '__find_wldf_action'
        for type_name in self.__watch_action_types:
            mbean = self.__find_in_location(watch_location, type_name, action_name)
            if mbean is not None:
                return mbean

        ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19202', WATCH_NOTIFICATION, action_name)
        self.__logger.throwing(class_name=self._class_name, method_name=method_name, error=ex)
        raise ex

    def __find_in_resource_group_or_domain(self, location, element_type, name, required=False):
        """
        Find the element with the specified name and type and return its WLST mbean.
        :param location: the WLST location of the attribute
        :param name: the name of the element to find
        :param required: indicates exception should be thrown if not found
        :return: the mbean for the destination
        :raises BundleAwareException of the specified type: if element is not found, and required is True
        """
        method_name = '__find_in_resource_group_or_domain'

        in_resource_group = RESOURCE_GROUP in location.get_model_folders()
        if in_resource_group:
            mbean = None
            # pseudo-code for searching resource group and template
            #
            #     resource_group_location = self.__get_parent_location(location, RESOURCE_GROUP)
            #     mbean = self._get_in_location(location, element_type, name)
            #     if mbean is None:
            #         template_id = get attribute from WLST
            #         template_location = find_template(template_id)
            #         mbean = self._get_in_location(location, element_type, name)
        else:
            location = LocationContext()
            mbean = self.__find_in_location(location, element_type, name)

        if required and (mbean is None):
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19202', element_type, name)
            self.__logger.throwing(class_name=self._class_name, method_name=method_name, error=ex)
            raise ex
        return mbean

    def __find_in_location(self, location, element_type, name, required=False):
        """
        Find the element with the specified name and type and return its WLST mbean.
        :param location: the WLST location of the attribute
        :param element_type: the thype of the element to be found
        :param name: the name of the element to find
        :param required: indicates exception should be thrown if not found
        :return: the mbean for the destination
        :raises BundleAwareException of the specified type: if element is not found, and required is True
        """
        method_name = '__find_in_location'

        location = LocationContext(location).append_location(element_type)
        if self.__alias_helper.get_wlst_mbean_type(location) is not None:
            existing_names = self.__get_existing_object_list(location)
            if name in existing_names:
                location_type, location_name = self.__alias_helper.get_model_type_and_name(location)
                self.__logger.fine('WLSDPLY-19204', element_type, name, location_type, location_name,
                                   class_name=self._class_name, method_name=method_name)
                token = self.__alias_helper.get_name_token(location)
                location.add_name_token(token, name)
                path = self.__alias_helper.get_wlst_attributes_path(location)
                return self.__wlst_helper.get_mbean_for_wlst_path(path)

        if required:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19202', element_type, name)
            self.__logger.throwing(class_name=self._class_name, method_name=method_name, error=ex)
            raise ex

        return None

    def __get_parent_location(self, location, folder_name):
        """
        Searches the specified location for the specified folder name, and returns the corresponding location.
        :param location: the location to be examined
        :param folder_name: the folder name to find
        :return: the parent location
        :raises BundleAwareException of the specified type: if the folder is not found in the location folders list
        """
        method_name = '__get_parent_location'

        try:
            location = LocationContext(location)
            resource_index = location.get_model_folders().index(folder_name)
            while len(location.get_model_folders()) > resource_index + 1:
                location.pop_location()
        except:
            # index throws a ValueError if the item is not in the list...
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19205', folder_name, str(location))
            self.__logger.throwing(class_name=self._class_name, method_name=method_name, error=ex)
            raise ex
        return location

    def __set_attribute(self, location, model_key, model_value, use_raw_value=False):
        """
        Convenience method for setting the attribute.
        :param location: location
        :param model_key: attribute name
        :param model_value: attribute value
        :param use_raw_value: whether or not to the use the model value, default is to use the WLST value
        :raises BundleAwareException of the specified type: if an error occurs
        """
        _method_name = '__set_attribute'

        if use_raw_value:
            wlst_param = self.__alias_helper.get_wlst_attribute_name(location, model_key)
            wlst_value = model_value
        else:
            wlst_param, wlst_value = \
                self.__alias_helper.get_wlst_attribute_name_and_value(location, model_key, model_value)

        if wlst_param is None:
            self.__logger.info('WLSDPLY-19206', model_key, class_name=self._class_name, method_name=_method_name)
        elif wlst_value is None:
            self.__logger.info('WLSDPLY-19207', model_key, str(model_value),
                               class_name=self._class_name, method_name=_method_name)
        else:
            self.__wlst_helper.set(wlst_param, wlst_value)
        return

    def __get_existing_object_list(self, location):
        """
        Convenience method to get the existing object list by location's list path
        :param location: the location
        :return: the list of existing names
        :raises BundleAwareException of the specified type: if an error occurs
        """
        _method_name = '__get_existing_object_list'

        self.__logger.entering(str(location), class_name=self._class_name, method_name=_method_name)
        list_path = self.__alias_helper.get_wlst_list_path(location)
        existing_names = self.__wlst_helper.get_existing_object_list(list_path)
        self.__logger.exiting(class_name=self._class_name, method_name=_method_name, result=existing_names)
        return existing_names
