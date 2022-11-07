"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import java.lang.Boolean as Boolean
import java.lang.Exception as JException

from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.logging.platform_logger import PlatformLogger

import aliastest.generate.generator_wlst as generator_wlst
import aliastest.generate.utils as generator_utils

CMO_READ_TYPE = generator_utils.CMO_READ_TYPE
FAIL = generator_utils.FAIL
READ_ONLY = generator_utils.READ_ONLY
READ_WRITE = generator_utils.READ_WRITE
UNKNOWN = generator_utils.UNKNOWN


class MBeanMethodHelper(object):
    
    __logger = PlatformLogger('test.aliases.generate.mbean.method')

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
            _get_mbean_type(self.__mbean_instance)
        return self.__mbean_type

    def get_attributes(self):
        _method_name = 'get_attributes'

        if self.__attribute_mbean_helpers is None:
            self.__attribute_mbean_helpers = PyOrderedDict()
            if self.__exists():
                for attribute_name, helper in self.get_all_attributes().iteritems():
                    if helper.is_attribute():
                        self.__logger.finest('MBean {0} has attribute {1} in CMO methods map', self.get_mbean_type(),
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
            return self.__create_attribute_helper(attribute_name)

    def get_child_mbeans(self):
        _method_name = 'get_child_mbeans'

        if self.__child_mbean_helpers is None:
            self.__child_mbean_helpers = PyOrderedDict()
            if self.__exists():
                for attribute_name, helper in self.get_all_attributes().iteritems():
                    if helper.is_mbean():
                        self.__logger.finest('MBean type {0} has child MBean {1} in CMO methods map',
                                             self.get_mbean_type(), attribute_name,
                                             class_name=self.__class_name__, method_name=_method_name)
                        self.__child_mbean_helpers[attribute_name] = helper
            else:
                self.__logger.finer('MBean type {0} is not valid and cannot produce a list of child MBeans',
                                    self.get_mbean_type(), class_name=self.__class_name__, method_name=_method_name)

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
                for attribute_name in self.__get_mbean_info():
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

        if helper is None:
            helper = self.get_attribute(attribute_name)
        if helper is not None:
            self.__logger.finer('Generating information for mbean {0} attribute {1}', self.__mbean_type, attribute_name,
                                class_name=self.__class_name__, method_name=_method_name)
            helper.generate_attribute(dictionary)
        else:
            self.__logger.fine('Mbean type {0} attribute {1} cannot be located', self.__mbean_type, attribute_name,
                               class_name=self.__class_name__, method_name=_method_name)

    def __create_attribute_helper(self, attribute_name):
        return MBeanMethodAttributeHelper(self.__mbean_info, attribute_name, self.__mbean_instance)

    def __exists(self):
        return self.__get_mbean_info() is not None and self.__len__() > 0

    def __get_mbean_info(self):
        _method_name = '__get_mbean_info'

        if self.__mbean_info is None:
            method_list = self.__mbean_instance.getClass().getMethods()
            if method_list is None or len(method_list) == 0:
                self.__mbean_info = dict()
                self.__logger.fine('Unable to locate CMO methods for MBean at location {0}', self.__mbean_path,
                                   class_name=self.__class_name__, method_name=_method_name)
            else:
                self.__mbean_info = self.__massage_methods(method_list)

        return self.__mbean_info

    def __encapsulate_mbean_instance(self, mbean_instance=None, mbean_path=None):
        _method_name = '__encapsulate_mbean_instance'

        if mbean_instance is None:
            mbean_instance = generator_wlst.get_mbean_proxy(mbean_path)
        path = mbean_path
        if path is None:
            path = generator_wlst.current_path()
        self.__logger.finer('Located the MBean instance is {0} at location {1}',
                            Boolean(mbean_instance is not None), path,
                            class_name=self.__class_name__, method_name=_method_name)

        return mbean_instance

    def __massage_methods(self, methods):
        _method_name = '__massage_methods'
        self.__logger.entering(len(methods), class_name=self.__class_name__, method_name=_method_name)

        attribute_map = dict()
        for attribute_name in _get_attribute_names(methods):
            attribute_map[attribute_name] = [method for method in methods if method.getName().endswith(attribute_name)]

        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name, result=len(attribute_map))
        return attribute_map

    def __len__(self):
        if self.__mbean_info is not None and len(self.__mbean_info) > 0:
            return len(self.__mbean_info.keys())
        return 0

    def str(self):
        return self.__str__()

    def __str__(self):
        return '%s, %s, valid=%s location=%s' % (self.__class_name__, self.get_mbean_type(),
                                                 Boolean(self.__exists()), self.__mbean_path)

    def __repr__(self):
        return self.__class_name__ + ' MBean type ' + self.get_mbean_type() + \
               ' valid=' + Boolean(self.__exists()).toString()


class MBeanMethodAttributeHelper(object):

    __tossed_attributes = ['DefaultedMBean', 'Attribute', 'Comments', 'Attributes', 'PersistenceEnabled']
    __logger = PlatformLogger('test.aliases.generate')

    def __init__(self, mbean_info, attribute_name, mbean_instance):
        self.__class_name__ = self.__class__.__name__
        self.__attribute_name = attribute_name
        self.__mbean_instance = mbean_instance
        self.__attribute_info = self.__get_mbean_attribute_info(mbean_info, attribute_name)
        self.__exists = self.__attribute_info is not None
        self.__mbean_type = _get_mbean_type(mbean_instance)
        self.__attribute_value = None
        self.__method_names = None

    def is_attribute_found(self):
        return self.__exists

    def get_name(self):
        return self.__attribute_name

    def get_mbean_type(self):
        return self.__mbean_type

    def has_since(self):
        return self.since_version() is not None

    def since_version(self):
        self.__logger.finest('{0} does not contain since version', self.__class_name__,
                             class_name=self.__class_name__, method_name='since_version')
        return None

    def is_deprecated(self):
        return self.deprecated_version() is not None

    def deprecated_version(self):
        self.__logger.finest('{0} does not contain deprecated version', self.__class_name__,
                             class_name=self.__class_name__, method_name='deprecated_version')
        return None

    def restart_required(self):
        self.__logger.finest('{0} does not contain restart value', self.__class_name__,
                             class_name=self.__class_name__, method_name='restart_required')
        return None

    def get_read_method(self):
        method = None
        if self.__exists:
            method = self.__get_method_for_name('get' + self.__attribute_name)
            if method is None:
                method = self.__get_method_for_name('is' + self.__attribute_name)
        return method

    def getter_name(self):
        getter = self.get_read_method()
        if getter is not None:
            return getter.getName()
        return None

    def is_readable(self):
        return self.get_read_method() is not None

    def is_writable(self):
        return self.__get_method_for_name('set' + self.__attribute_name) is not None

    def is_readonly(self):
        return self.__exists and not self.is_writable()

    def is_mbean(self):
        if self.__exists:
            attribute_type = self.attribute_type()
            return attribute_type is not None and (attribute_type.startswith('weblogic') or
                                                   attribute_type.startswith('[Lweblogic')) and self.is_readonly()
        return False

    def is_attribute(self):
        return self.is_mbean() is False and self.get_name() not in self.__tossed_attributes

    def is_reference(self):
        self.__logger.finest('{0} cannot determine reference', self.__class_name__,
                             class_name=self.__class_name__, method_name='is_reference')
        return None

    def is_valid_reference(self):
        self.__logger.finest('{0} cannot determine reference', self.__class_name__,
                             class_name=self.__class_name__, method_name='is_valid_reference')
        return None

    def is_reference_only(self):
        self.__logger.finest('{0} cannot determine reference', self.__class_name__,
                             class_name=self.__class_name__, method_name='is_reference_only')
        return None

    def attribute_type(self):
        _method_name = 'attribute_type'

        attr_type = UNKNOWN
        if self.__exists:
            getter = self.get_read_method()
            if getter is not None:
                check_type = getter.getReturnType()
                if check_type is not None:
                    try:
                        type_getter = getattr(check_type, 'getTypeName', str(check_type))
                        attr_type = type_getter()
                    except (Exception, JException):
                        attr_type = str(check_type)
        self.__logger.finest('Attribute type for MBean {0} attribute {1} is {2}',
                             self.get_mbean_type(), self.get_name(), attr_type,
                             class_name=self.__class_name__, method_name=_method_name)

        return attr_type

    def derived_default_value(self):
        return None

    def default_value(self):
        return self.attribute_value()

    def attribute_value(self):
        if self.is_valid_getter():
            return self.__attribute_value
        return FAIL

    def is_encrypted(self):
        return self.__exists and str(self.get_read_method().getReturnType()) == '[B'

    def is_valid_getter(self):
        success = False
        if self.__exists and self.__mbean_instance is not None:
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
            return self.__get_method_for_name('create' + self.__attribute_name)
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

        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name, result=dictionary)

    def generate_mbean(self, dictionary):
        _method_name = 'generate_mbean'

        if self.__exists:
            self.__logger.finest('Nothing to generate by Methods helper for MBean {0} attribute {1}',
                                 self.get_mbean_type(), self.get_name(),
                                 class_name=self.__class_name__, method_name=_method_name, result=dictionary)

    def __get_method_for_name(self, method_name):
        list_index = self._get_index_of_method_in_list(method_name)
        if list_index >= 0:
            return self.__attribute_info[list_index]
        return None

    def __get_attribute_method_names(self):
        if self.__exists:
            if self.__method_names is None:
                self.__method_names = [method.getName() for method in self.__attribute_info]
        return self.__method_names

    def _get_index_of_method_in_list(self, method_name):
        if self.__exists:
            try:
                return self.__get_attribute_method_names().index(method_name)
            except ValueError:
                pass
        return -1

    def __get_mbean_attribute_info(self, mbean_info, attribute_name):
        _method_name = '__get_mbean_attribute_info'

        attribute_info = None
        if mbean_info is not None and attribute_name is not None and attribute_name in mbean_info:
            attribute_info = [method for method in mbean_info[attribute_name]
                              if method.getName().endswith(attribute_name)]
        if attribute_info is not None and len(attribute_info) > 0:
            self.__logger.finest('Attribute {0} exists in MBean methods', attribute_name,
                                 class_name=self.__class_name__, method_name=_method_name)
        else:
            self.__logger.fine('Unable to locate attribute {0} in MBean methods', attribute_name,
                               class_name=self.__class_name__, method_name=_method_name)

        return attribute_info

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
        return self.__class_name__ + ' MBean type ' + str(self.get_mbean_type()) + \
            atype + 'attribute ' + self.get_name()


def _get_mbean_type(mbean_instance):
    if mbean_instance is not None and mbean_instance.getClass() is not None and \
            mbean_instance.getClass().getInterfaces() and len(mbean_instance.getClass().getInterfaces()) > 0:
        return generator_utils.get_interface_name(mbean_instance.getClass().getInterfaces()[0]).split('MBean')[0]
    return 'Unknown'


def _get_attribute_names(methods):
    mbean_info_names = list()
    if methods is not None and len(methods) > 0:
        mbean_info_names = [method.getName()[3:] for method in methods
                            if method.getName().startswith('get')]
        is_names = [attribute for attribute in [method.getName()[2:] for method in methods
                                                if method.getName().startswith('is')]
                    if attribute not in mbean_info_names]
        if len(is_names) > 0:
            mbean_info_names.extend(is_names)
    return mbean_info_names

