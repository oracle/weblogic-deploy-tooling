"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import java.lang.Boolean as Boolean
import weblogic.management.provider.ManagementServiceClient as ManagementServiceClient

from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.logging.platform_logger import PlatformLogger

import aliastest.generate.generator_wlst as generate_wlst
import aliastest.generate.utils as generator_utils

CMO_READ_TYPE = generator_utils.CMO_READ_TYPE
DEPRECATED = generator_utils.DEPRECATED
READ_ONLY = generator_utils.READ_ONLY
READ_WRITE = generator_utils.READ_WRITE
RESTART = generator_utils.RESTART
SINCE_VERSION = generator_utils.SINCE_VERSION
UNKNOWN = generator_utils.UNKNOWN


class MBeanInfoHelper(object):
    """
    Facade to provide the details for a specific WLST MBean and its attributes / child MBeans.
    The information provided in this class is retrieved from the MBeanInfo descriptors for the MBean
    encapsulated in an instance.
    """
    
    __logger = PlatformLogger('test.aliases.generate.mbean.info')

    def __init__(self, mbean_instance, mbean_path, mbean_type=None):
        self.__class_name__ = self.__class__.__name__
        self.__mbean_path = mbean_path
        self.__mbean_instance = self.__encapsulate_mbean_instance(mbean_instance=mbean_instance, mbean_path=mbean_path)
        self.__mbean_type = mbean_type
        self.__mbean_info = None
        self.__mbean_info_names = None
        self.__all_helpers = None
        self.__child_mbean_helpers = None
        self.__attribute_mbean_helpers = None

    def get_mbean_type(self):
        """
        Return the MBean type name specific to the version and WLST mode for the encapsulated MBean.
        :return: MBean type
        """
        if self.__mbean_type is None:
            self.__mbean_type = _get_mbean_type(self.__get_mbean_info())
        return self.__mbean_type

    def get_attributes(self):
        """
        Return a dictionary of (specific) attributes for the encapsulated MBean, along with an attribute helper
        instance.
        :return: 
        """
        _method_name = 'get_attributes'
        if self.__attribute_mbean_helpers is None:
            self.__attribute_mbean_helpers = PyOrderedDict()
            if self.__exists():
                for attribute_name, helper in self.get_all_attributes().iteritems():
                    if helper.is_attribute():
                        self.__logger.finest('MBean {0} has attribute {1} in MBeanInfo map', self.get_mbean_type(),
                                             attribute_name, class_name=self.__class_name__, method_name=_method_name)
                        self.__attribute_mbean_helpers[attribute_name] = helper
        return self.__attribute_mbean_helpers

    def get_attribute(self, attribute_name):
        """
        Get the attribute information for the attribute name.
        :param attribute_name: to find information for
        :return: Attribute information or None if attributes are invalid or attribute does not exist
        """
        if attribute_name in self.get_attributes():
            return self.get_attributes()[attribute_name]
        else:
            return self.__create_attribute_helper(attribute_name)

    def get_child_mbeans(self):
        _method_name = 'get_child_mbeans'
        if self.__child_mbean_helpers is None:
            self.__child_mbean_helpers = PyOrderedDict()
            if self.__exists():
                for attribute_name, helper in self.get_all_attributes().iteritems():
                    if helper.is_mbean():
                        self.__logger.finest('MBean type {0} has child MBean {1} in MBeanInfo map',
                                             self.get_mbean_type(), attribute_name,
                                             class_name=self.__class_name__, method_name=_method_name)
                        self.__child_mbean_helpers[attribute_name] = helper
        return self.__child_mbean_helpers

    def get_child_mbean(self, attribute):
        if attribute in self.get_child_mbeans():
            return self.get_child_mbeans()[attribute]
        else:
            return self.__create_attribute_helper(attribute)

    def get_all_attributes(self):
        _method_name = 'get_attributes'
        if self.__all_helpers is None:
            self.__all_helpers = PyOrderedDict()
            if self.__exists():
                for attribute_name in self.__get_mbean_info_names():
                    self.__all_helpers[attribute_name] = self.__create_attribute_helper(attribute_name)
            else:
                self.__logger.finer('MBean type {0} is not valid and cannot produce a list of attributes',
                                    self.get_mbean_type(), class_name=self.__class_name__, method_name=_method_name)
        return self.__all_helpers

    def get_all_attribute(self, attribute_name):
        if attribute_name in self.get_all_attributes():
            return self.get_all_attributes()[attribute_name]
        else:
            return self.__create_attribute_helper(attribute_name)

    def generate_attribute(self, dictionary, attribute_name, helper=None):
        _method_name = 'generate_attribute'
        self.__logger.entering(attribute_name, class_name=self.__class_name__, method_name=_method_name)
        if helper is None:
            helper = self.get_attribute(attribute_name)
        if helper is not None:
            self.__logger.finer('Generating information for mbean {0} attribute {1}', self.__mbean_type, attribute_name,
                                class_name=self.__class_name__, method_name=_method_name)
            helper.generate_attribute(dictionary)
        else:
            self.__logger.fine('Mbean type {0} attribute {1} cannot be located', self.__mbean_type, attribute_name,
                               class_name=self.__class_name__, method_name=_method_name)
        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name)

    def __create_attribute_helper(self, attribute_name):
        return MBeanInfoAttributeHelper(self.__mbean_info, attribute_name, self.__mbean_instance)

    def __exists(self):
        return self.__get_mbean_info() is not None and self.__len__() > 0

    def __get_mbean_info(self):
        _method_name = '__get_mbean_info'
        if self.__mbean_info is None:
            self.__logger.entering(class_name=self.__class_name__, method_name=_method_name)
            self.__mbean_info = dict()
            mbean_interface = self.__get_mbean_interface()
            if mbean_interface is not None:
                bean_access = ManagementServiceClient.getBeanInfoAccess()
                type_name = generator_utils.get_interface_name(mbean_interface)
                self.__mbean_info = bean_access.getBeanInfoForInterface(type_name, False, '9.0.0.0')
            if _info_is_not_empty(self.__mbean_info) is False:
                self.__logger.info('Unable to locate MBeanInfo for MBean interface {0}', mbean_interface,
                                   class_name=self.__class_name__, method_name=_method_name)
            self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name,
                                  result=str(self.__mbean_info))
        return self.__mbean_info

    def __get_mbean_info_names(self):
        if self.__mbean_info_names is None:
            self.__mbean_info_names = list()
            mbean_info = self.__get_mbean_info()
            if self.__exists():
                self.__mbean_info_names = [attribute.getName()
                                           for attribute in mbean_info.getPropertyDescriptors()]
                self.__mbean_info_names.sort()
        return self.__mbean_info_names

    def __get_mbean_interface(self):
        _method_name = 'get_mbean_interface'
        self.__logger.entering(class_name=self.__class_name__, method_name=_method_name)

        mbean_interface = None
        if self.__mbean_instance is not None:
            interfaces = self.__mbean_instance.getClass().getInterfaces()
            if len(interfaces) > 0:
                if len(interfaces) > 1:
                    self.__logger.fine('There are multiple Mbean interface{0} for mbean instance {1}',
                                       str(interfaces), self.__mbean_instance,
                                       class_name=self.__class_name__, method_name=_method_name)
                mbean_interface = interfaces[0]
            else:
                self.__logger.fine('Unable to find the mbean interface for mbean instance {0}',
                                   str(self.__mbean_instance),
                                   class_name=self.__class_name__, method_name=_method_name)

        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name, result=mbean_interface)
        return mbean_interface

    def __encapsulate_mbean_instance(self, mbean_instance=None, mbean_path=None):
        _method_name = '__encapsulate_mbean_instance'

        if mbean_instance is None:
            mbean_instance = generate_wlst.get_mbean_proxy(mbean_path)
        local_path = mbean_path
        if local_path is None:
            local_path = generate_wlst.current_path()
        self.__logger.finer('Located the MBean instance {0} {1} at location {2}', str(mbean_instance),
                            Boolean(mbean_instance is not None), local_path,
                            class_name=self.__class_name__, method_name=_method_name)

        return mbean_instance

    def __len__(self):
        if self.__mbean_info is not None and type(self.__mbean_info) is not dict:
            return len(self.__mbean_info.getPropertyDescriptors())
        return 0

    def str(self):
        return self.__str__()

    def __str__(self):
        return '%s, %s, valid=%s location=%s' % (self.__class_name__, str(self.get_mbean_type()),
                                                 Boolean(self.__exists()), self.__mbean_path)


class MBeanInfoAttributeHelper(object):

    __logger = PlatformLogger('test.aliases.generate')

    def __init__(self, mbean_info, attribute_name, mbean_instance, mbean_type=None):
        self.__class_name__ = self.__class__.__name__
        self.__attribute_name = attribute_name
        self.__mbean_instance = mbean_instance
        self.__attribute_info, self.__operation_info = self.__get_mbean_attribute_info(mbean_info, attribute_name)
        self.__exists = _info_is_not_empty(self.__attribute_info)
        if mbean_type is None:
            self.__mbean_type = _get_mbean_type(mbean_info)
        else:
            self.__mbean_type = mbean_type
        self.__attribute_value = None
        self.__info_value_keys = None

    def is_attribute_found(self):
        return self.__exists

    def get_name(self):
        return self.__attribute_name

    def get_mbean_type(self):
        return self.__mbean_type

    def has_since(self):
        return self.since_version() is not None

    def since_version(self):
        if self.__exists and 'since' in self.__get_descriptor_values_keys():
            version_string = self.__get_descriptor_value('since')
            if _check_version(version_string):
                return version_string
        return None

    def is_deprecated(self):
        return self.deprecated_version() is not None

    def deprecated_version(self):
        if self.__exists and 'deprecated' in self.__get_descriptor_values_keys():
            version_string = self.__get_descriptor_value('deprecated')
            if _check_version(version_string):
                return version_string
        return None

    def restart_required(self):
        return self.__exists and self.__get_descriptor_value('dynamic') is False

    def get_read_method(self):
        if self.__exists:
            return self.__attribute_info.getReadMethod()
        return None

    def getter_name(self):
        getter = self.get_read_method()
        if getter is not None:
            return getter.getName()
        return None

    def is_readable(self):
        return self.get_read_method() is not None

    def is_writable(self):
        return self.__exists and self.__attribute_info.getWriteMethod() is not None

    def is_readonly(self):
        return not self.is_writable()

    def is_mbean(self):
        return self.__exists \
               and self.__get_descriptor_value('relationship') == 'containment'

    def is_reference(self):
        return self.__exists and self.__get_descriptor_value('relationship') == 'reference'

    def is_valid_reference(self):
        return self.is_reference() and self.is_writable()

    def is_reference_only(self):
        """
        For a handful of references that might have an alias definition as a folder.
        :return: True if this is another view of a folder but only a reference to that folder
        """
        return self.is_reference() and self.__get_descriptor_value('transient') is True

    def is_attribute(self):
        return not self.is_mbean() and (not self.is_reference() or self.is_valid_reference())

    def attribute_type(self):
        _method_name = 'attribute_type'

        attr_type = UNKNOWN
        if self.__exists:
            check_type = str(self.__attribute_info.getPropertyType())
            if check_type is None:
                check_type = self.get_read_method().getReturnType()
            if check_type is not None:
                attr_type = check_type
        self.__logger.fine('Attribute type for MBean {0} attribute {1} is {2}',
                           self.get_mbean_type(), self.get_name(), attr_type,
                           class_name=self.__class_name__, method_name=_method_name)

        return attr_type

    def default_value(self):
        _method_name = 'default_value'
        self.__logger.entering(class_name=self.__class_name__, method_name=_method_name)

        default = None
        derivedDefault = None
        if self.__exists:
            values = self.__get_descriptor_values_keys()
            if 'defaultValueNull' in values:
                if self.__get_descriptor_value('defaultValueNull') is True:
                    default = None
                elif 'default' in values:
                    default = self.__get_descriptor_value('default')
                    if default is None:
                        default = self.attribute_value()
                        if default is None:
                            self.__logger.fine('MBean {0} attribute {1} does not allow Null values and '
                                               'returned Null value for result', self.get_mbean_type(), self.get_name(),
                                               class_name=self.__class_name__, method_name=_method_name)
                            default = 'NotNull'
            elif 'default' in values:
                default = self.__get_descriptor_value('default')
            else:
                default = self.attribute_value()
                self.__logger.fine('MBean {0} attribute {1} does not have default value in descriptor. '
                                   'Using the attribute value {2} : descriptor keys={3}',
                                   self.get_mbean_type(), self.get_name(), default, self.__get_descriptor_values_keys(),
                                   class_name=self.__class_name__, method_name=_method_name)

        self.__logger.exiting(result=default, class_name=self.__class_name__, method_name=_method_name)
        return default

    def derived_default_value(self):
        if self.__attribute_info is None:
            return None
        value = self.__attribute_info.getValue('restDerivedDefault')
        if value is None:
            value = False
        return value

    def attribute_value(self):
        if self.is_valid_getter():
            return self.__attribute_value
        return None

    def is_encrypted(self):
        return self.__get_descriptor_value('encrypted') is True

    def is_valid_getter(self):
        success = False
        if self.__exists and self.getter_name() is not None:
            success, self.__attribute_value = \
                generator_utils.get_from_bean_proxy(self.__mbean_instance, self.__mbean_type,
                                                    self.getter_name(), self.get_name())
        return success

    def creator_method_name(self):
        creator = self.creator_method()
        if creator is not None:
            return creator.getName()
        return None

    def creator_method(self):
        if self.__exists:
            creator = [creator_method for creator_method in self.__operation_info
                       if creator_method.getName().startswith('create')]
            if len(creator) == 1:
                return creator[0]
        return None

    def mbean_instance(self):
        return self.__mbean_instance

    def generate_attribute(self, dictionary):
        _method_name = 'generate_attribute'
        self.__logger.entering(class_name=self.__class_name__, method_name=_method_name)
        if self.__exists:
            if self.is_readonly():
                dictionary[CMO_READ_TYPE] = READ_ONLY
            else:
                dictionary[CMO_READ_TYPE] = READ_WRITE
            if self.is_deprecated() and DEPRECATED not in dictionary:
                dictionary[DEPRECATED] = self.deprecated_version()
            if self.has_since() and SINCE_VERSION not in dictionary:
                dictionary[SINCE_VERSION] = self.since_version()
            if self.restart_required() and RESTART not in dictionary:
                dictionary[RESTART] = Boolean(self.restart_required()).toString()
        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name, result=dictionary)

    def generate_mbean(self, dictionary):
        if self.__exists:
            if self.is_deprecated() and DEPRECATED not in dictionary:
                dictionary[DEPRECATED] = self.deprecated_version()
            if self.has_since() and SINCE_VERSION not in dictionary:
                dictionary[SINCE_VERSION] = self.since_version()

    def __get_descriptor_value(self, field_name):
        if self.__exists:
            return self.__attribute_info.getValue(field_name)
        return None

    def __get_mbean_attribute_info(self, mbean_info, attribute_name):
        _method_name = '__get_mbean_attribute_info'
        attribute_info = None
        operations_info = list()
        if _info_is_not_empty(mbean_info) and attribute_name is not None:
            attribute_list = [descriptor for descriptor in mbean_info.getPropertyDescriptors()
                              if descriptor.getName() == attribute_name]
            if len(attribute_list) == 1:
                attribute_info = attribute_list[0]
                operations_info = [operator for operator in mbean_info.getMethodDescriptors()
                                   if operator.getValue('property') == attribute_name]
        if attribute_info is not None:
            self.__logger.finest('Attribute {0} exists in MBeanInfo', attribute_name,
                                 class_name=self.__class_name__, method_name=_method_name)
        else:
            self.__logger.fine('Unable to locate attribute {0} in MBeanInfo', attribute_name,
                               class_name=self.__class_name__, method_name=_method_name)

        return attribute_info, operations_info

    def __get_descriptor_values_keys(self):
        _method_name = '__get_descriptor_values_keys'
        if self.__exists and self.__info_value_keys is None:
            self.__info_value_keys = generator_utils.list_from_enumerations(self.__attribute_info.attributeNames())
            self.__logger.finer('MBean {0} attribute {1} descriptor values are {2}',
                                self.get_mbean_type(), self.get_name(), self.__info_value_keys,
                                class_name=self.__class_name__, method_name=_method_name)
        return self.__info_value_keys

    def str(self):
        return self.__str__()

    def __str__(self):
        # change to a resource  undle message
        a_type = 'No '
        if self.is_attribute_found():
            if self.is_mbean():
                a_type = 'Child MBean '
            elif self.is_reference():
                a_type = 'Reference '
            else:
                a_type = ' '
        return self.__class_name__ + ' MBean type ' + str(self.get_mbean_type()) + \
            a_type + 'attribute ' + self.get_name()
    

def _check_version(version_string):
    return version_string is not None and version_string != 'null' and len(version_string) > 1


def _get_mbean_type(mbean_info):
    if _info_is_not_empty(mbean_info):
        return mbean_info.getBeanDescriptor().getName().split('MBean')[0]
    return "Unknown"


def _info_is_not_empty(mbean_info):
    return mbean_info is not None and type(mbean_info) is not dict
