"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import java.util.logging.Level as Level
import java.lang.Boolean as Boolean

from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.logging.platform_logger import PlatformLogger

import aliastest.generate.generator_wlst as generator_wlst
import aliastest.generate.utils as generator_utils

CMO_READ_TYPE = generator_utils.CMO_READ_TYPE
CMO_TYPE = generator_utils.CMO_TYPE
DEPRECATED = generator_utils.DEPRECATED
FAIL = generator_utils.FAIL
READ_ONLY = generator_utils.READ_ONLY
READ_WRITE = generator_utils.READ_WRITE
RESTART = generator_utils.RESTART
SINCE_VERSION = generator_utils.SINCE_VERSION
UNKNOWN = generator_utils.UNKNOWN


class MBIHelper(object):

    __logger = PlatformLogger('test.aliases.generate.mbean.mbi')

    def __init__(self, mbean_instance, mbean_path, mbean_type=None):
        self.__class_name__ = self.__class__.__name__
        self.__mbean_path = mbean_path
        self.__mbean_instance = self.__encapsulate_mbean_instance(mbean_instance=mbean_instance, mbean_path=mbean_path)
        self.__mbean_type = mbean_type
        self.__mbean_info = None
        self.__all_helpers = None
        self.__child_mbean_helpers = None
        self.__attribute_mbean_helpers = None

    def get_mbean_type(self):
        if self.__mbean_type is None:
            _get_mbean_type(self.__get_mbean_info())
        return self.__mbean_type

    def get_attributes(self):
        _method_name = 'get_attributes'

        if self.__attribute_mbean_helpers is None:
            self.__attribute_mbean_helpers = PyOrderedDict()
            if self.__exists():
                for attribute_name, helper in self.get_all_attributes().iteritems():
                    if helper.is_attribute():
                        self.__logger.finest('MBean {0} has attribute {1} in MBI map', self.get_mbean_type(),
                                             attribute_name, class_name=self.__class_name__, method_name=_method_name)
                        self.__attribute_mbean_helpers[attribute_name] = helper
            else:
                self.__logger.finer('MBean type {0} is not valid and cannot produce a list of attributes',
                                    self.get_mbean_type(), class_name=self.__class_name__, method_name=_method_name)

        return self.__attribute_mbean_helpers

    def get_attribute(self, attribute_name):
        if attribute_name in self.get_attributes():
            return self.get_attributes()[attribute_name]
        else:
            # this helper returns false on helper.is_attribute_found()
            return self.__create_attribute_helper(attribute_name)

    def get_child_mbeans(self):
        _method_name = 'get_child_mbeans'

        if self.__child_mbean_helpers is None:
            self.__child_mbean_helpers = PyOrderedDict()
            if self.__exists():
                for attribute_name, helper in self.get_all_attributes().iteritems():
                    if helper.is_mbean():
                        self.__logger.finer('MBean type {0} has child MBean {1} in MBI map', self.get_mbean_type(),
                                            attribute_name, class_name=self.__class_name__, method_name=_method_name)
                        self.__child_mbean_helpers[attribute_name] = helper
            else:
                self.__logger.fine('MBean type {0} is not valid and cannot produce a list of child MBeans',
                                   self.get_mbean_type(), class_name=self.__class_name__, method_name=_method_name)

        return self.__child_mbean_helpers

    def get_child_mbean(self, attribute):
        if attribute in self.get_child_mbeans():
            return self.get_child_mbeans()[attribute]
        else:
            # this helper returns false on helper.is_attribute_found()
            return self.__create_attribute_helper(attribute)

    def get_all_attributes(self):
        _method_name = 'get_attributes'

        if self.__all_helpers is None:
            self.__all_helpers = PyOrderedDict()
            if self.__exists():
                for attribute_name in self.__get_attribute_names():
                    self.__all_helpers[attribute_name] = self.__create_attribute_helper(attribute_name)
            else:
                self.__logger.fine('MBean type {0} is not valid and cannot produce a list of attributes',
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
        return MBIAttributeHelper(self.__mbean_info, attribute_name, self.__mbean_instance)

    def __exists(self):
        return self.__get_mbean_info() is not None and self.__len__() > 0

    def __encapsulate_mbean_instance(self, mbean_instance=None, mbean_path=None):
        _method_name = '__encapsulate_mbean_instance'

        if mbean_instance is None:
            mbean_instance = generator_wlst.get_mbean_proxy(mbean_path)
        local_path = mbean_path
        if local_path is None:
            local_path = generator_wlst.current_path()
        self.__logger.finer('Located the MBean instance is {0} at location {1}', Boolean(mbean_instance is not None),
                            local_path, class_name=self.__class_name__, method_name=_method_name)

        return mbean_instance

    def __get_attribute_names(self):
        return [attribute.getName() for attribute in self.__mbean_info.getAttributes()]

    def __get_mbean_info(self):
        _method_name = '__get_mbean_info'
        self.__logger.entering(class_name=self.__class_name__, method_name=_method_name)

        if self.__mbean_info is None:
            self.__mbean_info = dict()
            mbi_info = generator_wlst.get_mbi_info()
            if mbi_info is None:
                self.__logger.fine('Unable to locate the MBI information at this location {0}', self.__mbean_path,
                                   class_name=self.__class_name__, method_name=_method_name)
            else:
                self.__mbean_info = mbi_info
                self.__mbean_type = _get_mbean_type(self.__mbean_info)
                self.__logger.finest('MBI info for MBean {0}={1}', self.__mbean_type, self.__mbean_info,
                                     class_name=self.__class_name__, method_name=_method_name)

        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name, result=self.__mbean_info)
        return self.__mbean_info

    def str(self):
        return self.__str__()

    def __str__(self):
        return '%s, %s, valid=%s location=%s' % (self.__class_name__, str(self.get_mbean_type()),
                                                 Boolean(self.__exists()), self.__mbean_path)

    def __repr__(self):
        return self.__class_name__ + ' MBean type ' + self.get_mbean_type() + \
               ' valid=' + Boolean(self.__exists()).toString()

    def __len__(self):
        if self.__mbean_info is not None and type(self.__mbean_info) is not dict:
            return len(self.__mbean_info.getAttributes())
        return 0


class MBIAttributeHelper(object):

    __logger = PlatformLogger('test.aliases.generate')

    def __init__(self, mbean_info, attribute_name, mbean_instance):
        self.__class_name__ = self.__class__.__name__
        self.__attribute_name = attribute_name
        self.__mbean_instance = mbean_instance
        self.__attribute_info = self.__get_mbean_attribute_info(mbean_info, attribute_name)
        self.__exists = _info_is_not_empty(self.__attribute_info)
        self.__mbean_type = _get_mbean_type(mbean_info)
        self.__attribute_value = None
        self.__invokable_getter = None
        self.__info_field_keys = None
        self.__method_list = None

    def is_attribute_found(self):
        return self.__exists

    def get_name(self):
        if self.__exists:
            return self.__attribute_info.getName()
        return None

    def get_mbean_type(self):
        return self.__mbean_type

    def has_since(self):
        return self.since_version() is not None

    def since_version(self):
        if self.__exists and 'since' in self.__get_descriptor_field_keys():
            version_string = self.__get_descriptor_value('since')
            if _check_version(version_string):
                return version_string
        return None

    def is_deprecated(self):
        return self.deprecated_version() is not None

    def deprecated_version(self):
        if self.__exists and 'deprecated' in self.__get_descriptor_field_keys():
            version_string = self.__get_descriptor_value('deprecated')
            if _check_version(version_string):
                return version_string
        return None

    def restart_required(self):
        return self.__exists and self.__get_descriptor_value('com.bea.dynamic') is False

    def get_read_method(self):
        if self.is_attribute():
            method = \
                [method for method in generator_utils.get_mbean_methods(self.__mbean_instance)
                    if method.getName() == 'get' + self.__attribute_name or method.getName() ==
                 'is' + self.__attribute_name]
            if len(method) == 1:
                return method[0]
        return None

    def getter_name(self):
        getter = self.get_read_method()
        if getter is not None:
            return getter.getName()
        return None

    def is_readable(self):
        return self.__exists and self.__attribute_info.isReadable()

    def is_writable(self):
        return self.__exists and self.__attribute_info.isWritable()

    def is_readonly(self):
        return not self.is_writable()

    def is_mbean(self):
        if self.__exists:
            return self.__get_descriptor_value('com.bea.relationship') == 'containment'
        return None

    def is_attribute(self):
        if self.__exists:
            return self.__get_descriptor_value('descriptorType') == 'Attribute' and \
                not self.is_mbean()
        return None

    def is_reference(self):
        return self.__exists and self.__get_descriptor_value('com.bea.relationship') == 'reference'

    def is_valid_reference(self):
        return self.is_reference() and self.is_writable()

    def is_reference_only(self):
        return self.is_reference() and self.__get_descriptor_value('com.bea.transient') is True

    def attribute_type(self):
        _method_name = 'attribute_type'

        attr_type = UNKNOWN
        if self.__exists:
            check_type = self.__attribute_info.getType()
            if check_type is not None:
                attr_type = check_type
        self.__logger.fine('Attribute type for MBean {0} attribute {1} is {2}',
                           self.get_mbean_type(), self.get_name(), attr_type,
                           class_name=self.__class_name__, method_name=_method_name)

        return attr_type

    def derived_default_value(self):
        return self.__get_descriptor_value('restDerivedDefault')

    def default_value(self):
        _method_name = 'default_value'
        self.__logger.entering(class_name=self.__class_name__, method_name=_method_name)

        default = None
        if self.__exists:
            values = self.__get_descriptor_field_keys()
            if 'defaultValueNull' in values:
                if self.__get_descriptor_value('defaultValueNull') is True:
                    default = None
                elif 'defaultValue' in values:
                    default = self.__get_descriptor_value('defaultValue')
                    if default is None:
                        default = self.attribute_value()
                        if default is None:
                            self.__logger.fine(
                                'MBean {0} attribute {1} does not allow Null values and returned Null value for result',
                                self.get_mbean_type(), self.get_name(),
                                class_name=self.__class_name__, method_name=_method_name)
                            default = 'NotNull'
            elif 'defaultValue' in values:
                default = self.__get_descriptor_value('defaultValue')
            else:
                default = self.attribute_value()
                self.__logger.fine('MBean {0} attribute {1} does not have defaultValue or defaultValueNull'
                                   ' in descriptor. Using the attribute value {2} : descriptor keys={3}',
                                   self.get_mbean_type(), self.get_name(), default, self.__get_descriptor_field_keys(),
                                   class_name=self.__class_name__, method_name=_method_name)

        self.__logger.exiting(result=default, class_name=self.__class_name__, method_name=_method_name)
        return default

    def attribute_value(self):
        if self.is_valid_getter():
            return self.__attribute_value
        return FAIL

    def is_encrypted(self):
        return self.__get_descriptor_value('com.bea.encrypted') is True

    def is_valid_getter(self):
        if self.__exists and self.__invokable_getter is None:
            self.__invokable_getter = False
            if self.__mbean_instance is not None:
                self.__invokable_getter, self.__attribute_value = \
                   generator_utils.get_from_bean_proxy(self.__mbean_instance, self.__mbean_type,
                                                       self.getter_name(), self.get_name())
        return self.__invokable_getter

    def generate_attribute(self, dictionary):
        _method_name = 'generate_attribute'
        self.__logger.entering(class_name=self.__class_name__, method_name=_method_name)

        if self.__exists:
            if CMO_TYPE in dictionary:
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
            return self.__attribute_info.getDescriptor().getFieldValue(field_name)
        return None

    def __get_mbean_attribute_info(self, mbean_info, attribute_name):
        _method_name = '__get_mbean_attribute_info'

        attribute_info = None
        if _info_is_not_empty(mbean_info) and attribute_name is not None:
            attribute_info = mbean_info.getAttribute(attribute_name)
        if attribute_info is not None:
            self.__logger.finest('Attribute {0} exists in MBI bean info', attribute_name,
                                 class_name=self.__class_name__, method_name=_method_name)
        else:
            self.__logger.fine('Unable to locate attribute {0} in MBI bean info', attribute_name,
                               class_name=self.__class_name__, method_name=_method_name)

        return attribute_info

    def __get_descriptor_field_keys(self):
        _method_name = '__get_descriptor_field_keys'

        if self.__exists and self.__info_field_keys is None:
            self.__info_field_keys = self.__attribute_info.getDescriptor().getFieldNames()
            self.__logger.finer('MBean {0} attribute {1} descriptor fields are {2}',
                                self.get_mbean_type(), self.get_name(), self.__info_field_keys,
                                class_name=self.__class_name__, method_name=_method_name)

        return self.__info_field_keys

    def str(self):
        return self.__str__()

    def __str__(self):
        atype = 'No '
        if self.is_attribute_found():
            if self.is_mbean():
                atype = 'Child MBean '
            elif self.is_reference():
                atype = 'Reference '
            else:
                atype = ' '
        return self.__class__.__name__ + ' MBean type ' + str(self.get_mbean_type()) + \
            atype + 'attribute ' + self.get_name()


def _check_version(version_string):
    return version_string is not None and version_string != 'null' and len(version_string) > 1


def _get_mbean_type(mbean_info):
    if _info_is_not_empty(mbean_info):
        return mbean_info.getMBeanDescriptor().getFieldValue('name').split('MBean')[0]
    return 'Not found'


def _info_is_not_empty(mbean_info):
    return mbean_info is not None and type(mbean_info) is not dict
