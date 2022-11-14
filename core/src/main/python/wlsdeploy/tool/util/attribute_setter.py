"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from javax.management import ObjectName
from org.python.modules import jarray

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.alias_constants import BOOLEAN
from wlsdeploy.aliases.alias_jvmargs import JVMArguments
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import CAPACITY
from wlsdeploy.aliases.model_constants import CERT_PATH_PROVIDER
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import COHERENCE_CLUSTER_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import CONTEXT_REQUEST_CLASS
from wlsdeploy.aliases.model_constants import DISTRIBUTED_QUEUE
from wlsdeploy.aliases.model_constants import DISTRIBUTED_TOPIC
from wlsdeploy.aliases.model_constants import ENABLED
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
from wlsdeploy.aliases.model_constants import LOG_FILTER
from wlsdeploy.aliases.model_constants import MACHINE
from wlsdeploy.aliases.model_constants import MASKED_PASSWORD
from wlsdeploy.aliases.model_constants import MAX_THREADS_CONSTRAINT
from wlsdeploy.aliases.model_constants import MIGRATABLE_TARGET
from wlsdeploy.aliases.model_constants import MIN_THREADS_CONSTRAINT
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.aliases.model_constants import PARTITION
from wlsdeploy.aliases.model_constants import PARTITION_WORK_MANAGER
from wlsdeploy.aliases.model_constants import PERSISTENT_STORE
from wlsdeploy.aliases.model_constants import QUEUE
from wlsdeploy.aliases.model_constants import QUOTA
from wlsdeploy.aliases.model_constants import REALM
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP_TEMPLATE
from wlsdeploy.aliases.model_constants import RESOURCE_MANAGEMENT
from wlsdeploy.aliases.model_constants import RESOURCE_MANAGER
from wlsdeploy.aliases.model_constants import RESPONSE_TIME_REQUEST_CLASS
from wlsdeploy.aliases.model_constants import REST_NOTIFICATION
from wlsdeploy.aliases.model_constants import SAF_AGENT
from wlsdeploy.aliases.model_constants import SAF_ERROR_HANDLING
from wlsdeploy.aliases.model_constants import SAF_IMPORTED_DESTINATION
from wlsdeploy.aliases.model_constants import SAF_QUEUE
from wlsdeploy.aliases.model_constants import SAF_REMOTE_CONTEXT
from wlsdeploy.aliases.model_constants import SAF_TOPIC
from wlsdeploy.aliases.model_constants import SCRIPT_ACTION
from wlsdeploy.aliases.model_constants import SECURITY_CONFIGURATION
from wlsdeploy.aliases.model_constants import SELF_TUNING
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_TEMPLATE
from wlsdeploy.aliases.model_constants import SMTP_NOTIFICATION
from wlsdeploy.aliases.model_constants import SNMP_NOTIFICATION
from wlsdeploy.aliases.model_constants import TEMPLATE
from wlsdeploy.aliases.model_constants import THREAD_DUMP_ACTION
from wlsdeploy.aliases.model_constants import TOPIC
from wlsdeploy.aliases.model_constants import UNIFORM_DISTRIBUTED_QUEUE
from wlsdeploy.aliases.model_constants import UNIFORM_DISTRIBUTED_TOPIC
from wlsdeploy.aliases.model_constants import VIRTUAL_TARGET
from wlsdeploy.aliases.model_constants import WATCH_NOTIFICATION
from wlsdeploy.aliases.model_constants import WS_RELIABLE_DELIVERY_POLICY
from wlsdeploy.aliases.model_constants import XML_ENTITY_CACHE
from wlsdeploy.aliases.model_constants import XML_REGISTRY
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util import model_helper
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.weblogic_helper import WebLogicHelper


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
    __logger = PlatformLogger('wlsdeploy.tool.util')

    def __init__(self, model_context, aliases, exception_type, wlst_mode=WlstModes.OFFLINE):
        self.__model_context = model_context
        self.__exception_type = exception_type
        self.__wlst_mode = wlst_mode
        self.__aliases = aliases
        self.__wlst_helper = WlstHelper(exception_type)
        self.__weblogic_helper = WebLogicHelper(self.__logger)

    #
    # public set_ methods for special attribute types, signature (self, location, key, value, wlst_value, ...)
    #

    def set_target_jms_mbeans(self, location, key, value, wlst_value):
        """
        Set the target MBeans for targets that can include JMS resources (e.g., JMSServer).
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if target is not found
        """
        self.set_target_mbeans(location, key, value, wlst_value, include_jms=True)

    def set_target_mbeans(self, location, key, value, wlst_value, include_jms=False):
        """
        Set the target attribute. For online, use a list of MBeans. For offline, use a comma-separated list of names,
        or set to None for an empty list.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :param include_jms: whether or not to include JMS resources
        :raises BundleAwareException of the specified type: if target is not found
        """
        if self.__wlst_mode == WlstModes.ONLINE:
            targets_value = self.__build_target_mbean_list(value, wlst_value, location, key, include_jms=include_jms)
            self.set_attribute(location, key, targets_value, wlst_merge_value=wlst_value, use_raw_value=True)
        else:
            items = self.__merge_existing_items(value, wlst_value, location, key)
            if not items:
                mbean = self.__wlst_helper.get_mbean(None)
                mbean.setTargets(None)
            else:
                targets_value = MODEL_LIST_DELIMITER.join(items)
                self.set_attribute(location, key, targets_value, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_jms_error_destination_mbean(self, location, key, value, wlst_value):
        """
        Set the JMS Error Destination MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if destination is not found
        """
        mbean = self.__find_jms_destination_mbean(location, value)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_jms_bridge_destination_mbean(self, location, key, value, wlst_value):
        """
        Set the JMS Bridge Destination MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if destination is not found
        """
        mbean = self.__find_in_resource_group_or_domain(location, JMS_BRIDGE_DESTINATION, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_persistent_store_mbean(self, location, key, value, wlst_value):
        """
        Set the Persistent Store MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if store is not found
        """
        mbean = self.__find_persistent_store(location, value)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_data_source_mbean(self, location, key, value, wlst_value):
        """
        Set the DataSource MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if DataSource is not found
        """
        if not value:
            mbean = self.__wlst_helper.get_mbean(None)
            wlst_attr = self.__aliases.get_wlst_attribute_name(location, key)
            method = getattr(mbean, 'set' + wlst_attr)
            method(None)
        else:
            mbean = self.__find_in_resource_group_or_domain(location, JDBC_SYSTEM_RESOURCE, value, required=True)
            self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_saf_remote_context_mbean(self, location, key, value, wlst_value):
        """
        Set the SAF RemoteContext MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if SAF RemoteContext is not found
        """
        resource_location = self.__get_parent_location(location, JMS_RESOURCE)
        mbean = self.__find_in_location(resource_location, SAF_REMOTE_CONTEXT, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_saf_error_destination_mbean(self, location, key, value, wlst_value):
        """
        Set the SAF Error Destination MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if destination is not found
        """
        mbean = self.__find_saf_destination_mbean(location, value)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_saf_error_handling_mbean(self, location, key, value, wlst_value):
        """
        Set the SAF Error Handling MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if destination is not found
        """
        resource_location = self.__get_parent_location(location, JMS_RESOURCE)
        mbean = self.__find_in_location(resource_location, SAF_ERROR_HANDLING, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_self_tuning_mbean(self, location, key, value, wlst_value):
        """
        Set the SelfTuning MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if MBean is not found
        """
        tuning_location = self.__get_parent_location(location, SELF_TUNING)
        mbean = self.__find_in_location(tuning_location, key, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_server_mbeans(self, location, key, value, wlst_value):
        """
        Set the Server MBeans.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if a server is not found
        """
        mbeans = self.__build_server_mbean_list(value, wlst_value, location, key)
        self.set_attribute(location, key, mbeans, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_server_mbean(self, location, key, value, wlst_value):
        """
        Set the Server MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if the server is not found
        """
        mbean = self.__find_in_location(LocationContext(), SERVER, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_server_template_mbean(self, location, key, value, wlst_value):
        """
        Set the Server Template MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if the server template is not found
        """
        mbean = self.__find_in_location(LocationContext(), SERVER_TEMPLATE, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_cluster_mbean(self, location, key, value, wlst_value):
        """
        Set the Cluster MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if the cluster is not found
        """
        mbean = self.__find_in_location(LocationContext(), CLUSTER, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_server_cluster_mbean(self, location, key, value, wlst_value):
        """
        assign the Cluster MBean to a server.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if the cluster is not found
        """

        entity_type, entity_name = self.__aliases.get_model_type_and_name(location)

        self.__wlst_helper.assign(entity_type, entity_name, key, value)

    def set_coherence_cluster_mbean(self, location, key, value, wlst_value):
        """
        Set the Log Filter MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if store is not found
        """
        mbean = self.__find_in_location(LocationContext(), COHERENCE_CLUSTER_SYSTEM_RESOURCE, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_machine_mbean(self, location, key, value, wlst_value):
        """
        Set the Machine MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if the machine is not found
        """
        mbean = self.__find_in_location(LocationContext(), MACHINE, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_jms_template_mbean(self, location, key, value, wlst_value):
        """
        Set the JMS Template MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if the JMS Template is not found
        """
        resource_location = self.__get_parent_location(location, JMS_RESOURCE)
        mbean = self.__find_in_location(resource_location, TEMPLATE, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_wldf_action_mbeans(self, location, key, value, wlst_value):
        """
        Set the WLDF Action/Notification MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if the WLDF Action/Notification is not found
        """
        watch_location = self.__get_parent_location(location, WATCH_NOTIFICATION)
        action_names = self.__merge_existing_items(value, wlst_value, location, key)

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
            self.set_attribute(location, key, action_mbeans, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_log_filter_mbean(self, location, key, value, wlst_value):
        """
        Set the Log Filter MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if store is not found
        """
        mbean = self.__find_in_location(LocationContext(), LOG_FILTER, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_jms_server_mbean(self, location, key, value, wlst_value):
        """
        For those entities, such as WLSReliableDeliveryPolicy, that take a single JMS Server mbean.
        :param location: location to look for jms server
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if jms server mbean is not found.
        """
        mbean = self.__find_in_location(LocationContext(), JMS_SERVER, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_jms_quota_mbean(self, location, key, value, wlst_value):
        """
        For those entities, queues, template, topics, that take a single Quota mbean.
        :param location: location to look for Quota mbean
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if quota mbean is not found.
        """
        resource_location = self.__get_parent_location(location, JMS_RESOURCE)
        mbean = self.__find_in_location(resource_location, QUOTA, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_reliable_delivery_policy_mbean(self, location, key, value, wlst_value):
        """
        Sets the ws soap reliable delivery policy mbean used by mbeans like Server and Server Template.
        :param location: location to look for reliable delivery policy
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if reliable delivery policy mbean is not found.
        """
        mbean = self.__find_in_location(LocationContext(), WS_RELIABLE_DELIVERY_POLICY, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_xml_entity_cache_mbean(self, location, key, value, wlst_value):
        """
        Sets the XML cache mbean used by topology entities such as Server.
        :param location: location to look for reliable delivery policy
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if xml entity cache mbean is not found.
        """
        mbean = self.__find_in_location(LocationContext(), XML_ENTITY_CACHE, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_xml_registry_mbean(self, location, key, value, wlst_value):
        """
        Sets the XML registry mbean used by topology entities such as Server.
        :param location: location to look for reliable delivery policy
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if xml registry mbean is not found.
        """
        mbean = self.__find_in_location(LocationContext(), XML_REGISTRY, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_mt_target_mbeans(self, location, key, value, wlst_value):
        """
        Set the virtual target MBeans.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if target is not found
        """
        targets_value = self.__build_virtual_target_mbean_list(value, wlst_value, location, key)
        self.set_attribute(location, key, targets_value, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_security_realm_mbean(self, location, key, value, wlst_value):
        """
        Set the security realm MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if target is not found
        """
        security_location = self.__get_domain_location(location).append_location(SECURITY_CONFIGURATION)
        mbean = self.__find_in_location(security_location, REALM, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_certificate_registry_mbean(self, location, key, value, wlst_value):
        """
        Set the certificate registry MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if target is not found
        """
        realm_location = self.__get_parent_location(location, REALM)
        mbean = self.__find_in_location(realm_location, CERT_PATH_PROVIDER, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_resource_group_template_mbean(self, location, key, value, wlst_value):
        """
        Set the resource group template MBean.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if target is not found
        """
        domain_location = self.__get_domain_location(location)
        mbean = self.__find_in_location(domain_location, RESOURCE_GROUP_TEMPLATE, value, required=True)
        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_partition_work_manager_mbean(self, location, key, value, wlst_value):
        """
        Set the partition work manager MBean. Search in the same partition, then at the domain level.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if target is not found
        """
        method_name = 'set_partition_work_manager_mbean'
        partition_location = self.__get_parent_location(location, PARTITION)
        mbean = self.__find_in_location(partition_location, PARTITION_WORK_MANAGER, value)
        if mbean is None:
            domain_location = self.__get_domain_location(location)
            mbean = self.__find_in_location(domain_location, PARTITION_WORK_MANAGER, value)

        if mbean is None:
            _type, partition_name = self.__aliases.get_model_type_and_name(location)
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19206', value, partition_name)
            self.__logger.throwing(class_name=self._class_name, method_name=method_name, error=ex)
            raise ex

        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_resource_manager_mbean(self, location, key, value, wlst_value):
        """
        Set the resource manager MBean. Search in the same partition, then at the domain level.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if target is not found
        """
        method_name = 'set_resource_manager_mbean'
        partition_location = self.__get_parent_location(location, PARTITION)
        mbean = self.__find_in_location(partition_location, RESOURCE_MANAGER, value)
        if mbean is None:
            management_location = self.__get_domain_location(location).append_location(RESOURCE_MANAGEMENT)
            mbean = self.__find_in_location(management_location, RESOURCE_MANAGER, value)

        if mbean is None:
            _type, manager_name = self.__aliases.get_model_type_and_name(location)
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19207', value, manager_name)
            self.__logger.throwing(class_name=self._class_name, method_name=method_name, error=ex)
            raise ex

        self.set_attribute(location, key, mbean, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_jvm_args(self, location, key, value, wlst_value):
        """
        Set the server start args string. The new arguments are merged and re-sorted with existing arguments.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if an error occurs
        """
        if value is None or len(value) == 0:
            result = value
        elif wlst_value is None or len(wlst_value) == 0:
            new_args = JVMArguments(self.__logger, value)
            result = new_args.get_arguments_string()
        else:
            new_args = JVMArguments(self.__logger, value)
            merged_args = JVMArguments(self.__logger, wlst_value)
            merged_args.merge_jvm_arguments(new_args)
            result = merged_args.get_arguments_string()

        self.set_attribute(location, key, result, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_boolean(self, location, key, value, wlst_value):
        """
        Set the specified attribute with a Jython boolean primitive value.
        By default in WDT, boolean attributes are converted to string values for assignment.
        Some attributes can only be assigned consistently using a boolean primitive, using this attribute setter.
        :param location: the location
        :param key: the attribute name
        :param value: the string value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if an error occurs
        """
        result = alias_utils.convert_to_type(BOOLEAN, value)
        result = result == 'true'
        self.set_attribute(location, key, result, wlst_merge_value=wlst_value, use_raw_value=True)

    def set_with_ssl_enabled(self, location, key, value, wlst_value):
        """
        Set the specified attribute with SSL enabled in the current location.
        Restore SSL enabled status value after setting value.
        Currently, only Server/SSL/ListenPort offline has this requirement.
        :param location: the location
        :param key: the attribute name
        :param value: the new attribute value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if an error occurs
        """
        wlst_enabled_attribute = self.__aliases.get_wlst_attribute_name(location, ENABLED)
        was_enabled = self.__wlst_helper.get(wlst_enabled_attribute)
        self.set_attribute(location, ENABLED, True)
        self.set_attribute(location, key, value, wlst_merge_value=wlst_value)
        self.set_attribute(location, ENABLED, was_enabled)

    def set_encrypted(self, location, key, value, wlst_value):
        """
        Set the specified attribute with a pre-encrypted value in the current location.
        This is required when WLST does not encrypt a plain-text value during set() as it normally does.
        This can happen when offline WLST does not include an attribute in a hard-coded list of encrypted values.
        Currently, only OracleIdentityCloudIntegrator/ClientSecretEncrypted offline has this issue.
        :param location: the location
        :param key: the attribute name
        :param value: the new attribute value
        :param wlst_value: the existing value of the attribute from WLST
        :raises BundleAwareException of the specified type: if an error occurs
        """
        encrypted_value = \
            self.__weblogic_helper.encrypt(str_helper.to_string(value), self.__model_context.get_domain_home())
        self.set_attribute(location, key, encrypted_value, wlst_merge_value=wlst_value)

    #
    # public set_attribute convenience methods
    #

    def set_attribute(self, location, model_key, model_value, wlst_merge_value=None, use_raw_value=False):
        """
        Convenience method for setting the attribute.
        :param location: location
        :param model_key: attribute name
        :param model_value: attribute value
        :param wlst_merge_value: value from WLST to merge
        :param use_raw_value: whether or not to the use the model value, default is to use the WLST value
        :raises BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'set_attribute'

        if use_raw_value:
            wlst_param = self.__aliases.get_wlst_attribute_name(location, model_key)
            wlst_value = model_value
        else:
            wlst_param, wlst_value = \
                self.__aliases.get_wlst_attribute_name_and_value(location, model_key, model_value,
                                                                 existing_wlst_value=wlst_merge_value)

        if wlst_param is None:
            self.__logger.info('WLSDPLY-20011', model_key, class_name=self._class_name, method_name=_method_name)
        elif wlst_value is None:
            self.__logger.info('WLSDPLY-20012', model_key, str_helper.to_string(model_value),
                               class_name=self._class_name, method_name=_method_name)
        else:
            if self.__logger.is_finer_enabled():
                print_model_value = model_value
                print_wlst_value = wlst_value
                if self.__aliases.is_model_password_attribute(location, model_key):
                    print_model_value = MASKED_PASSWORD
                    print_wlst_value = MASKED_PASSWORD
                self.__logger.finer('WLSDPLY-19211', wlst_param, print_model_value, print_wlst_value,
                                    location.get_folder_path(), class_name=self._class_name, method_name=_method_name)

            self.__wlst_helper.set(wlst_param, wlst_value)

    def set_attribute_with_cmo(self, location, key, value, wlst_value=None, masked=False):
        _method_name = 'set_attribute_with_cmo'

        wlst_attr_name, wlst_attr_value = \
            self.__aliases.get_wlst_attribute_name_and_value(location, key, value, existing_wlst_value=wlst_value)

        if wlst_attr_name is None:
            self.__logger.info('WLSDPLY-20011', key, class_name=self._class_name, method_name=_method_name)
        elif wlst_attr_value is None:
            log_value = str_helper.to_string(value)
            if masked:
                log_value = '<masked>'
            self.__logger.info('WLSDPLY-20012', key, log_value, class_name=self._class_name, method_name=_method_name)
        else:
            attrib_path = self.__aliases.get_wlst_attributes_path(location)
            self.__wlst_helper.cd(attrib_path)
            self.__wlst_helper.set_with_cmo(wlst_attr_name, wlst_attr_value, masked=masked)

    #
    # internal lookup methods
    #

    def __build_target_mbean_list(self, target_value, wlst_value, location, key, include_jms=False):
        """
        Construct the target MBean list.
        :param target_value: the target value
        :param wlst_value: the existing value from WLST
        :param location: location of the attribute
        :param key: the attribute name
        :param include_jms: whether or not to include JMS targets, the default is False
        :return: the Java array of MBeans ObjectNames
        :raises BundleAwareException of the specified type: if an error occurs
        """
        target_names = self.__merge_existing_items(target_value, wlst_value, location, key)

        name_list = []
        for target_name in target_names:
            target_mbean = self.__find_target(target_name, location, include_jms=include_jms)
            name_list.append(target_mbean.getObjectName())

        return jarray.array(name_list, ObjectName)

    def __build_server_mbean_list(self, value, wlst_value, location, key):
        """
        Construct the server MBean list.
        :param value: the value
        :param wlst_value: the existing value from WLST
        :param location: location of the attribute
        :param key: the attribute name
        :return: the Java array of MBeans ObjectNames
        :raises BundleAwareException of the specified type: if an error occurs
        """
        server_names = self.__merge_existing_items(value, wlst_value, location, key)

        name_list = []
        for server_name in server_names:
            mbean = self.__find_in_location(LocationContext(), SERVER, server_name, required=True)
            name_list.append(mbean.getObjectName())

        return jarray.array(name_list, ObjectName)

    def __build_virtual_target_mbean_list(self, target_value, wlst_value, location, key):
        """
        Construct the virtual target MBean list.
        :param target_value: the target value
        :param wlst_value: the existing value from WLST
        :param location: location of the attribute
        :param key: the attribute name
        :return: for offline, a list of MBeans; for online, a jarray of MBean ObjectNames
        :raises BundleAwareException of the specified type: if an error occurs
        """
        target_names = self.__merge_existing_items(target_value, wlst_value, location, key)

        if self.__wlst_mode == WlstModes.ONLINE:
            name_list = []
            for target_name in target_names:
                target_mbean = self.__find_in_location(LocationContext(), VIRTUAL_TARGET, target_name, required=True)
                name_list.append(target_mbean.getObjectName())
            return jarray.array(name_list, ObjectName)
        else:
            mbean_list = []
            for target_name in target_names:
                target_mbean = self.__find_in_location(LocationContext(), VIRTUAL_TARGET, target_name, required=True)
                mbean_list.append(target_mbean)
            return mbean_list

    def __find_target(self, target_name, location, include_jms=False):
        """
        Find a target by name.
        :param target_name: the target name
        :param include_jms: whether or not to include JMS in the search, the default is False
        :return: the MBean for the target
        :raises BundleAwareException of the specified type: if an error occurs
        """
        method_name = '__find_target'
        domain_location = self.__get_domain_location(location)
        for type_name in self.__target_type_names:
            mbean = self.__find_in_location(domain_location, type_name, target_name)
            if mbean is not None:
                return mbean

        if include_jms:
            mbean = self.__find_in_resource_group_or_domain(location, JMS_SERVER, target_name)
            if mbean is not None:
                return mbean
            mbean = self.__find_in_resource_group_or_domain(location, SAF_AGENT, target_name)
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

        _resource_type, resource_name = self.__aliases.get_model_type_and_name(resource_location)
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

        token_name = self.__aliases.get_name_token(destination_location)
        for set_name in existing_sets:
            if token_name is not None:
                destination_location.add_name_token(token_name, set_name)
            for type_name in self.__saf_destination_type_names:
                mbean = self.__find_in_location(destination_location, type_name, destination_name)
                if mbean is not None:
                    return mbean

        _resource_type, resource_name = self.__aliases.get_model_type_and_name(resource_location)
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
        If the specified location is in a resource group, search only that resource group.
        :param location: the WLST location of the attribute
        :param name: the name of the element to find
        :param required: indicates exception should be thrown if not found
        :return: the mbean for the destination
        :raises BundleAwareException of the specified type: if element is not found, and required is True
        """
        method_name = '__find_in_resource_group_or_domain'

        in_resource_group = RESOURCE_GROUP in location.get_model_folders()
        if in_resource_group:
            resource_group_location = self.__get_parent_location(location, RESOURCE_GROUP)
            mbean = self.__find_in_location(resource_group_location, element_type, name)
            if mbean is None:
                template_id = self.__wlst_helper.get("ResourceGroupTemplate")
                domain_location = self.__get_domain_location(location)
                mbean = self.__find_in_location(domain_location, RESOURCE_GROUP_TEMPLATE, template_id)
        else:
            location = self.__get_domain_location(location)
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
        if self.__aliases.get_wlst_mbean_type(location) is not None:
            existing_names = self.__get_existing_object_list(location)
            if name in existing_names:
                location_type, location_name = self.__aliases.get_model_type_and_name(location)
                self.__logger.fine('WLSDPLY-19204', element_type, name, location_type, location_name,
                                   class_name=self._class_name, method_name=method_name)
                token = self.__aliases.get_name_token(location)
                location.add_name_token(token, name)
                path = self.__aliases.get_wlst_attributes_path(location)
                return self.__wlst_helper.get_mbean_for_wlst_path(path)

        if required:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19210', element_type, name,
                                                   self.__aliases.get_model_folder_path(location))
            self.__logger.throwing(class_name=self._class_name, method_name=method_name, error=ex)
            raise ex

        return None

    def __get_domain_location(self, location):
        """
        Returns a copy of the specified location with all folders removed, but tokens intact.
        :param location: the location to be examined
        :return: the domain location
        """
        _method_name = '__get_domain_location'
        self.__logger.entering(str_helper.to_string(location), class_name=self._class_name, method_name=_method_name)

        location = LocationContext(location)
        while len(location.get_model_folders()) > 0:
            location.pop_location()
        return location

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
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19205', folder_name,
                                                   str_helper.to_string(location))
            self.__logger.throwing(class_name=self._class_name, method_name=method_name, error=ex)
            raise ex
        return location

    def __get_existing_object_list(self, location):
        """
        Convenience method to get the existing object list by location's list path
        :param location: the location
        :return: the list of existing names
        :raises BundleAwareException of the specified type: if an error occurs
        """
        _method_name = '__get_existing_object_list'

        self.__logger.entering(str_helper.to_string(location), class_name=self._class_name, method_name=_method_name)
        list_path = self.__aliases.get_wlst_list_path(location)
        existing_names = self.__wlst_helper.get_existing_object_list(list_path)
        self.__logger.exiting(class_name=self._class_name, method_name=_method_name, result=existing_names)
        return existing_names

    #
    # methods for merging existing values
    #

    def __merge_existing_items(self, items, existing_value, location, key):
        """
        Merge the specified items with the items represented by existing value, and return the result.
        :param items: the attribute value (may be a string or list)
        :param existing_value: the value representing the existing items (may be a string or list)
        :param location: the location of the attribute, for logging
        :param key: the name of the attribute, for logging
        :return: the merged list of items
        :raises BundleAwareException of the specified type: if the WLDF Action/Notification is not found
        """
        _method_name = '__merge_existing_items'
        self.__logger.entering(str_helper.to_string(items), str_helper.to_string(existing_value),
                               class_name=self._class_name, method_name=_method_name)

        result = alias_utils.create_list(existing_value, 'WLSDPLY-08001')
        items_iterator = alias_utils.create_list(items, 'WLSDPLY-08000')

        for item in items_iterator:
            if model_helper.is_delete_name(item):
                item_name = model_helper.get_delete_item_name(item)
                if item_name in result:
                    result.remove(item_name)
                else:
                    location_path = self.__aliases.get_model_folder_path(location)
                    self.__logger.warning('WLSDPLY-08022', item_name, key, location_path,
                                          class_name=self._class_name, method_name=_method_name)

            elif item not in result:
                result.append(item)

        return result
