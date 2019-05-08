"""
Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import re

import java.lang.Boolean as Boolean

from oracle.weblogic.deploy.exception import BundleAwareException

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util.weblogic_helper import WebLogicHelper


_logger = PlatformLogger('wlsdeploy.mbean.utils')


class MBeanUtils(object):
    """
    Utility class used to provide information about WLST attributes retrieved from the MBean MBeanInfo or Interface
    methods.
    """

    __class_name = 'MBeanUtils'

    def __init__(self, model_context, exception_type):
        self.__model_context = model_context
        self.__exception_type = exception_type
        self.__aliases = Aliases(self.__model_context, wlst_mode=self.__model_context.get_target_wlst_mode())
        self.__alias_helper = AliasHelper(self.__aliases, _logger, exception_type)
        self.__wlst_helper = WlstHelper(_logger, exception_type)
        self.__helper = self.__get_helper()
        self.__ignore_list = self.__alias_helper.get_ignore_attribute_names()

    def get_attributes_not_in_lsa_map(self, location, lsa_map=None):
        """
        Return a list of all attributes from the MBean MBeanInfo or Interface methods that are not contained in the LSA
        attributes for the location in the location context.
        :param location: current location context of the MBean
        :param lsa_map: map returned from WLST ls('a') or None to get the LSA map from the current location context
        :return: Any additional attributes or empty list if none found
        """
        _method_name = 'get_attributes_not_in_lsa_map'
        _logger.entering(location.get_folder_path(), class_name=self.__class_name, method_name=_method_name)
        mbean_attributes = self.__collapse_attributes(location)
        lsa_attributes = self.__get_lsa_attributes(location, lsa_map)
        loose_attributes = [attribute for attribute in mbean_attributes
                            if not self.__helper.is_attribute_in_lsa_map(attribute, lsa_attributes)]
        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=loose_attributes)
        return loose_attributes

    def get_mbean_info_attributes(self, location=None, helper=None):
        if helper is None:
            helper = self.__get_info_helper(location)
        return helper.get_mbean_info_attributes()

    def get_interface_attributes(self, location=None, helper=None):
        if helper is None:
            helper = self.__get_interface_helper(location)
        return helper.get_interface_attributes()

    def __collapse_attributes(self, location):
        _method_name = '__filter_attributes'
        _logger.entering(location.get_folder_path(), class_name=self.__class_name, method_name=_method_name)

        info_helper = self.__get_info_helper(location)
        info_attributes = self.get_mbean_info_attributes(helper=info_helper)

        interface_helper = self.__get_interface_helper(location)
        interface_attributes = self.get_interface_attributes(helper=interface_helper)

        self.__remove_duplicates(interface_attributes, info_attributes)
        self.__slim_list(info_attributes, info_helper)
        self.__slim_list(interface_attributes, interface_helper)
        consolidated = list()
        consolidated.extend(info_attributes)
        consolidated.extend(interface_attributes)
        return consolidated

    def __slim_list(self, attributes, attribute_helper):
        return [attribute for attribute in attributes if not (
            self.__in_ignore(attribute) or
            attribute_helper.is_child_mbean(attribute)
        )]

    def __get_info_helper(self, location):
        return MBeanInfoAttributes(self.__model_context, self.__exception_type, location)

    def __get_interface_helper(self, location):
        return InterfaceAttributes(self.__model_context, self.__exception_type, location)

    def __remove_duplicates(self, check_list, main_list):
        _method_name = '__remove_duplicates'
        _logger.entering(len(check_list), class_name=self.__class_name, method_name=_method_name)
        for attribute in main_list:
            if attribute in check_list:
                check_list.remove(attribute)
        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=len(check_list))

    def __in_ignore(self, attribute_name):
        return attribute_name in self.__ignore_list

    def __get_helper(self):
        if self.__model_context.get_target_wlst_mode() == WlstModes.OFFLINE:
            helper = OfflineMBeanHelper(self.__model_context, self.__exception_type)
        else:
            helper = OnlineMBeanHelper(self.__model_context, self.__exception_type)
        return helper

    def __get_lsa_attributes(self, location, lsa_map):
        _method_name = '__get_lsa_attributes'
        attributes = None
        attribute_path = self.__alias_helper.get_wlst_attributes_path(location)
        if lsa_map is None:
            if location is not None:
                if attribute_path is not None:
                    try:
                        return_map = self.__wlst_helper.lsa(attribute_path)
                        if return_map is not None:
                            attributes = return_map.keys()
                        else:
                            attributes = list()
                    except BundleAwareException:
                        pass
        if attributes is None:
            # throw exception
            _logger.fine('Unable to retrieve the lsa attributes for the MBean at location {0}', attribute_path,
                         class_name=self.__class_name, method_name=_method_name)
            attributes = list()
        return attributes


class MBeanHelper(object):
    """
    Utility methods to assist with retrieving MBean information from the CMO MBean instance and
    the MBeanInfo for the MBean interface.
    """

    __class_name = 'MBeanHelper'

    def __init__(self, model_context, exception_type):
        """
        Create an instance of this class containing the context of the instance of this tool.

        :param model_context: context about the model for this instance of discover domain
        """
        self.__model_context = model_context
        self.__exception_type = exception_type


class OnlineMBeanHelper(MBeanHelper):

    __class_name = 'OnlineMBeanHelper'

    def __init__(self, model_context, exception_type):
        """
        Create an utility helper instance for online.

        :param model_context: current context for the running tool
        """
        MBeanHelper.__init__(self,  model_context, exception_type)

    def is_attribute_in_lsa_map(self, attribute, lsa_attributes):
        _method_name = 'is_attribute_in_lsa_map'
        _logger.entering(attribute, class_name=self.__class_name, method_name=_method_name)

        found = False
        if attribute in lsa_attributes:
            found = True
        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=Boolean(found))
        return found

    def is_lsa_in_attributes(self, lsa_attribute, attribute_list):
        _method_name = 'is_lsa_in_attributes'
        _logger.entering(lsa_attribute, class_name=self.__class_name, method_name=_method_name)
        found = False
        if lsa_attribute in attribute_list:
            found = True
        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=Boolean(found))
        return found


class OfflineMBeanHelper(MBeanHelper):

    __class_name = 'OfflineMBeanUtils'

    def __init__(self, model_context, exception_type):
        """
        Create an utility helper instance for offline.

        :param model_context: current context for the running tool
        """
        MBeanHelper.__init__(self,  model_context, exception_type)

    def is_attribute_in_lsa_map(self, attribute, lsa_attributes):
        _method_name = 'is_attribute_in_lsa_map'
        _logger.entering(attribute, class_name=self.__class_name, method_name=_method_name)
        found = True
        if attribute not in lsa_attributes and not self.__is_found_with_lower_case(attribute, lsa_attributes):
            if not attribute.endswith('ies') or \
                    not self.__is_found_with_lower_case(attribute[:len(attribute) - 3] + 'y', lsa_attributes):
                if not attribute.endswith('es') or \
                        not self.__is_found_with_lower_case(attribute[:len(attribute) - 2], lsa_attributes):
                    if not attribute.endswith('s') or \
                            not self.__is_found_with_lower_case(attribute[:len(attribute) - 1], lsa_attributes):
                        found = False
        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=Boolean(found))
        return found

    def is_lsa_in_attributes(self, lsa_attribute, attribute_list):
        _method_name = 'is_lsa_in_attributes'
        _logger.entering(lsa_attribute, class_name=self.__class_name, method_name=_method_name)
        found = True
        if lsa_attribute not in attribute_list and not self.__is_found_with_lower_case(lsa_attribute, attribute_list):
            if not lsa_attribute.endswith('y') or not \
                   self.__is_found_with_lower_case(lsa_attribute[:len(lsa_attribute) - 1] + 'ies', attribute_list):
                if not self.__is_found_with_lower_case(lsa_attribute + 'es', attribute_list):
                    if not self.__is_found_with_lower_case(lsa_attribute + 's', attribute_list):
                        found = False
        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=Boolean(found))
        return found

    def __is_found_with_lower_case(self, attribute, mbean_list):
        _method_name = '_is_found_with_lower_case'
        _logger.entering(attribute, class_name=self.__class_name, method_name=_method_name)

        found = False
        try:
            found = len([key for key in mbean_list if key.lower() == attribute.lower()]) > 0
        except (ValueError, KeyError):
            pass

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=Boolean(found))
        return found


class MBeanAttributes(object):

    __class_name = 'MBeanAttributes'
    __interface_matcher = re.compile('Bean$')

    def __init__(self, model_context, exception_type, location):
        self.__model_context = model_context
        self.__exception_type = exception_type
        self.__location = location
        self.__aliases = Aliases(self.__model_context, wlst_mode=self.__model_context.get_target_wlst_mode())
        self.__alias_helper = AliasHelper(self.__aliases, _logger, exception_type)
        self.__wlst_helper = WlstHelper(_logger, exception_type)
        self.__mbean_instance = None

    def _get_mbean_instance(self):
        _method_name = '_get_mbean_instance'
        if self.__mbean_instance is None:
            attribute_path = self.__alias_helper.get_wlst_attributes_path(self.__location)
            self.__mbean_instance = self.__wlst_helper.get_mbean(attribute_path)
            if self.__mbean_instance is None:
                ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-01775', attribute_path)
                _logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
        return self.__mbean_instance

    def _get_mbean_interface(self):
        _method_name = '__get_mbean_interface'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)
        interfaces = [str(interface) for interface in self._get_mbean_interfaces()
                      if re.search(self.__interface_matcher, str(interface)) is not None]
        if len(interfaces) == 0:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-01777',
                                                   str(self._get_mbean_interfaces()),
                                                   self._get_mbean_instance())
            _logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        else:
            if len(interfaces) > 1:
                _logger.fine('WLSDPLY-01770', interfaces, self._get_mbean_instance(),
                             class_name=self.__class_name, method_name=_method_name)
            mbean_interface = interfaces[0]

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=mbean_interface)
        return mbean_interface

    def _get_index_of_name_in_list(self, search_list_for, name):
        _method_name = 'get_index_of_name_in_list'
        _logger.finest('WLSDPLY-01772', name, class_name=self.__class_name, method_name=_method_name)
        try:
            return [named_item.getName() for named_item in search_list_for].index(name)
        except ValueError:
            _logger.finest('WLSDPLY-01771', name, search_list_for,
                           class_name=self.__class_name, method_name=_method_name)
        return -1

    def _get_mbean_methods(self):
        return self.__get_mbean_class().getDeclaredMethods()

    def _get_mbean_interfaces(self):
        return self.__get_mbean_class().getInterfaces()

    def __get_mbean_class(self):
        _method_name = '__get_mbean_class'
        mbean_class = None
        mbean_instance = self._get_mbean_instance()
        try:
            getter = getattr(mbean_instance, 'getClass')
            mbean_class = getter()
        except AttributeError:
            pass
        if mbean_class is None:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-01776', mbean_instance)
            _logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return mbean_class


class InterfaceAttributes(MBeanAttributes):

    __class_name = 'InterfaceAttributes'

    def __init__(self,  model_context, exception_type, location):
        MBeanAttributes.__init__(self,  model_context, exception_type, location)

        self.__interface_methods_list = None
        self.__interface_attribute_map = None

    def get_interface_attributes(self):
        """
        Return the sorted list of interface attribute names including child MBeans,
        as compiled from MBean interface getter methods.
        :return: list of attribute names from the MBean interface or empty list if the MBean has no attributes.
        """
        _method_name = 'get_interface_attribute_list'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)
        map_to_list = list()
        attributes = self.__get_interface_map()
        if len(attributes) > 0:
            map_to_list = [attribute for attribute in attributes.iterkeys()]
            map_to_list.sort()
        return map_to_list

    def exists(self, attribute_name):
        """
        Determine if the attribute name exists for the MBean in MBean Interface.
        :param attribute_name: to search for in the MBean Interface
        :return: True if the attribute is found in the MBean Interface
        """
        return attribute_name in self.__get_interface_map()

    def is_child_mbean(self, attribute_name):
        """
        Determine if the attribute exists in MBean Interface and if the attribute is a child MBean.

        :param attribute_name: to search for in the MBean Interface
        :return: True if the attribute is a child MBean or None if the attribute is not found in MBean Interface
        """
        if self.exists(attribute_name):
            child = False
            for method_name in [method.getName() for method in self.__get_interface_methods()
                                if self.__is_subfolder_method(method)]:
                if attribute_name in method_name:
                    child = True
                    break
            return child
        return None

    def is_read_only(self, attribute_name):
        """
        Determine if the attribute exists in MBean Interface and if the attribute is readonly.
        :param attribute_name: to search for in the MBean Interface
        :return: True if the attribute is readonly or None if the attribute does not exist in MBean Interface
        """
        if self.exists(attribute_name):
            return self.setter(attribute_name) is None
        return None

    def getter(self, attribute_name):
        """
        Return the read method string for the attribute in the MBean Interface.
        :param attribute_name: to search for in the MBean Interface
        :return: attribute getter or None if the attribute does not exist in the MBean Interface
        """
        method_list = self.__get_mbean_attribute(attribute_name)
        if method_list is not None:
            return method_list[0]
        return None

    def setter(self, attribute_name):
        """
        Return the setter Method for the attribute in the MBean interface
        :param attribute_name: to search for in the MBean interface
        :return: setter Method or None if the attribute is readonly or the attribute does not exist in the Interface
        """
        method_list = self.__get_mbean_attribute(attribute_name)
        if method_list is not None and len(method_list) > 1:
            return method_list[1]
        return None

    def get_type(self, attribute_name):
        """
        Return the type of the attribute value if the attribute exists in MBean Interface.
        :param attribute_name: to search for in the MBean Interface
        :return: Type of the property attribute or None if the attribute does not exist in the MBean Interface
        """
        method_list = self.__get_mbean_attribute(attribute_name)
        if method_list is not None:
            return method_list[0].getReturnType()
        return None

    def get_default_value(self, attribute_name):
        pass

    def __get_interface_map(self):
        if self.__interface_attribute_map is None:
            self.__interface_attribute_map = dict()
            for getter in self.__get_mbean_getters():
                attribute_name = self.__attribute_from_getter(getter)
                self.__interface_attribute_map[attribute_name] = self.__create_method_list(attribute_name, getter)

        return self.__interface_attribute_map

    def __get_mbean_attribute(self, attribute_name):
        interface_map = self.__get_interface_map()
        if attribute_name in interface_map:
            return interface_map[attribute_name]
        return None

    def __get_interface_methods(self):
        if self.__interface_methods_list is None:
            self.__interface_methods_list = self._get_mbean_methods()
        return self.__interface_methods_list

    def __get_mbean_getters(self):
        mbean_methods = self.__get_interface_methods()
        # log and exit if no mbean methods
        return [method for method in mbean_methods if self.__is_getter(method)]

    def __get_mbean_setters(self):
        mbean_methods = self.__get_interface_methods()
        return [method for method in mbean_methods if self.__is_setter(method)]

    def __get_mbean_setter(self, attribute_name):
        setter = None
        methods = self.__get_interface_methods()
        index = self._get_index_of_name_in_list(methods, 'set' + attribute_name)
        if index >= 0:
            setter = methods[index]
        return setter

    def __create_method_list(self, attribute, getter):
        _method_name = '__get_method_list'
        _logger.entering(attribute, class_name=self.__class_name, method_name=_method_name)
        method_list = list()
        method_list.append(getter)
        setter = self.__get_mbean_setter(attribute)
        if setter is not None:
            method_list.append(setter)

        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=method_list)
        return method_list

    def __get_method_name(self, method):
        _method_name = '_get_method_name'
        _logger.finest('WLSDPLY-01773', method, class_name=self.__class_name, method_name=_method_name)
        return method.getName()

    def __is_getter(self, method):
        name = self.__get_method_name(method)
        return name is not None and (name.startswith('get') or name.startswith('is')) \
            and len(method.getParameterTypes()) == 0

    def __is_setter(self, method):
        return self.__get_method_name(method).startswith('set')

    def __is_subfolder_method(self, method):
        name = self.__get_method_name(method)
        return name.startswith('create') or name.startswith('add') or name.startswith('destroy')

    def __attribute_from_getter(self, getter_method):
        getter = self.__get_method_name(getter_method)
        if getter.startswith('get'):
            return getter[3:]
        else:
            return getter[2:]


class MBeanInfoAttributes(MBeanAttributes):

    __class_name = 'MBeanInfoAttributes'

    def __init__(self, model_context, exception_type, location):
        MBeanAttributes.__init__(self, model_context, exception_type, location)

        self.__weblogic_helper = WebLogicHelper(_logger)
        self.__mbean_info_descriptors = None
        self.__mbean_info_map = None

    def get_mbean_info_attributes(self):
        """
        Return the sorted list of attributes compiled from the MBeanInfo PropertyDescriptors including the
        child MBeans.
        :return: list of all attributes from the MBeanInfo property descriptors, or an empty list if none
        """
        _method_name = 'get_mbean_info_attribute_list'
        _logger.entering(class_name=self.__class_name, method_name=_method_name)
        map_to_list = list()
        attributes = self.__get_mbean_info_map()
        if len(attributes) > 0:
            map_to_list = [attribute for attribute in attributes.iterkeys()]
            map_to_list.sort()
        _logger.exiting(class_name=self.__class_name, method_name=_method_name, result=len(map_to_list))
        return map_to_list

    def exists(self, attribute_name):
        """
        Determine if the attribute name exists for the MBean in MBeanInfo.
        :param attribute_name: to search for in the MBeanInfo
        :return: True if the attribute is found in the MBeanInfo
        """
        return attribute_name in self.__get_mbean_info_map()

    def is_child_mbean(self, attribute_name):
        """
        Determine if the attribute exists in MBeanInfo and if the attribute is a child MBean.

        :param attribute_name: to search for in the MBeanInfo
        :return: True if the attribute is a child MBean or None if the attribute is not found in MBeanInfo
        """
        descriptor = self.__get_mbean_attribute(attribute_name)
        if descriptor is not None:
            relationship = descriptor.getValue('relationship')
            return relationship == 'containment' or (relationship == 'reference' and self.is_read_only(attribute_name))
        return None

    def is_read_only(self, attribute_name):
        """
        Determine if the attribute exists in MBeanInfo and if the attribute is readonly.
        :param attribute_name: to search for in the MBeanInfo
        :return: True if the attribute is readonly or None if the attribute does not exist in MBeanInfo
        """
        if self.exists(attribute_name):
            return self.setter(attribute_name) is None
        return None

    def getter(self, attribute_name):
        """
        Return the read method name string for the attribute in the MBeanInfo.
        :param attribute_name: to search for in the MBeanInfo
        :return: getter for the attribute or None if the attribute does not exist
        """
        descriptor = self.__get_mbean_attribute(attribute_name)
        if descriptor is not None:
            return descriptor.getReadMethod().getName()
        return None

    def setter(self, attribute_name):
        """
        Return the set method name for the attribute in the MBeanInfo.
        :param attribute_name: to search for in the MBeanInfo
        :return: setter for the attribute or None if the attribute is readonly or the attribute does not exist
        """
        descriptor = self.__get_mbean_attribute(attribute_name)
        if descriptor is not None:
            setter = descriptor.getWriteMethod()
            if setter is not None:
                return setter.getName()
        return None

    def get_type(self, attribute_name):
        """
        Return the type of the attribute value if the attribute exists in MBeanInfo.
        :param attribute_name: to search for in the MBeanInfo
        :return: Type of the property attribute or None if the attribute does not exist in the MBeanInfo
        """
        descriptor = self.__get_mbean_attribute(attribute_name)
        if descriptor is not None:
            return descriptor.getPropertyType()
        return None

    def get_default_value(self, attribute_name):
        pass

    def __get_mbean_info_map(self):
        if self.__mbean_info_map is None:
            self.__mbean_info_map = dict()
            for descriptor in self.__get_mbean_descriptors():
                self.__mbean_info_map[descriptor.getName()] = descriptor

        return self.__mbean_info_map

    def __get_mbean_descriptors(self):
        if self.__mbean_info_descriptors is None:
            mbean_info = self.__weblogic_helper.get_bean_info_for_interface(self._get_mbean_interface())
            if mbean_info is None:
                # throw it
                _logger.fine('WLSDPLY-01774', self._get_mbean_interface(), self._get_mbean_instance())
            self.__mbean_info_descriptors = mbean_info.getPropertyDescriptors()
        return self.__mbean_info_descriptors

    def __get_mbean_attribute(self, attribute):
        descriptor_map = self.__get_mbean_info_map()
        if attribute in descriptor_map:
            return descriptor_map[attribute]
        return None
