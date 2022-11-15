"""
Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re

import java.lang.Boolean as Boolean
import java.lang.Exception as JException

from oracle.weblogic.deploy.exception import BundleAwareException

from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.wlst_helper import WlstHelper
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.weblogic_helper import WebLogicHelper


_logger = PlatformLogger('wlsdeploy.mbean.utils')


class MBeanUtils(object):
    """
    Utility class used to provide information about WLST attributes as retrieved from the MBeans MBeanInfo or Interface
    methods. This class has methods to provide the information stored in different combinations. All methods that want
    to combine the information from the MBeans helpers into different combinations are located in this class.
    """

    def __init__(self, model_context, aliases, exception_type):
        self.__model_context = model_context
        self.__exception_type = exception_type
        self.__aliases = aliases
        self.__wlst_helper = WlstHelper(exception_type)
        self.__helper = self.__get_helper()
        self.__ignore_list = None

    def get_attributes_not_in_lsa_map(self, location, lsa_map=None):
        """
        Return a list of all attributes from the MBeans MBeanInfo or Interface methods that are not contained in the LSA
        attributes for the location in the location context.
        :param location: current location context of the MBean
        :param lsa_map: map returned from WLST ls('a') or None to get the LSA map from the current location context
        :return: Any additional attributes or empty list if None found
        """
        _method_name = 'get_attributes_not_in_lsa_map'
        _logger.entering(location.get_folder_path(), class_name=self.__class__.__name__, method_name=_method_name)
        mbean_attributes = self.__collapse_attributes(location)
        lsa_attributes = self.__get_lsa_attributes(location, lsa_map)
        loose_attributes = [attribute for attribute in mbean_attributes
                            if not self.__helper.is_attribute_in_lsa_map(attribute, lsa_attributes)]
        _logger.exiting(class_name=self.__class__.__name__, method_name=_method_name, result=loose_attributes)
        return loose_attributes

    def get_info_attribute_helper(self, location):
        """
        Get a wrapper for the MBeanInfo attribute information for the current MBean designated in the location context.
        :param location: containing the current MBean context
        :return: MBeanAttributes class wrapping the MBeanInfo attributes with convenience methods
        """
        return self.__get_info_helper(location)

    def get_mbean_info_attributes(self, location=None, helper=None):
        """
        Get a list of attribute names for the MBean using the MBeanInfoAttributes wrapper class.
        If the helper is not provided, use the location arg to create an instance of the helper
        for the MBean designated in the location context.
        :param location: If helper is None, the location is required to create the helper instance
        :param helper: If not None, the provided helper is used to return the attribute information. The
            location arg is not required if helper is provided.
        :return: List of attribute names for the MBean
        """
        if helper is None:
            helper = self.get_info_attribute_helper(location)
        return self.get_mbean_attributes(helper)

    def get_interface_attribute_helper(self, location):
        """
        Return an instance of the InterfaceAttributes helper class for the MBean indicated in the location context.
        :param location: context for the current MBean location
        :return: InterfaceAttributes helper instance
        """
        return self.__get_interface_helper(location)

    def get_interface_attributes(self, location=None, helper=None):
        """
        Get a list of attribute names for the MBean using the InterfaceAttributes wrapper class.
        If the helper is not provided, use the location arg to create an instance of the helper
        for the MBean designated in the location context.
        :param location: If helper is None, the location is required to create the helper instance
        :param helper: If not None, the provided helper is used to return the attribute information. The
            location arg is not required if helper is provided.
        :return: List of attribute names for the MBean
        """
        if helper is None:
            helper = self.get_interface_attribute_helper(location)
        return self.get_mbean_attributes(helper)

    def get_mbean_attributes(self, helper):
        """
        Return a list of the MBean attribute names through the MBean attribute helper.
        :param helper: MBeanAttributes helper class
        :return: list of MBean attribute names
        """
        return helper.get_mbean_attributes()

    def __collapse_attributes(self, location):
        _method_name = '__filter_attributes'
        info_helper = self.__get_info_helper(location)
        info_attributes = self.get_mbean_attributes(info_helper)

        interface_helper = self.__get_interface_helper(location)
        interface_attributes = self.get_mbean_attributes(interface_helper)

        self.__remove_duplicates(interface_attributes, str_helper.to_string(interface_helper), info_attributes,
                                 str_helper.to_string(info_helper))
        # This is the main list to drive from
        info_attributes = self.__slim_list(info_attributes, info_helper)
        # Because there are very few valid attributes in the Interface methods that are not in either the LSA map
        # or MBeanInfo PropertyDescriptors, remove all the read_only attributes
        interface_attributes = self.__slim_list(interface_attributes, interface_helper, remove_readonly=True)
        consolidated = list()
        consolidated.extend(info_attributes)
        consolidated.extend(interface_attributes)
        _logger.finer('WLSDPLY-01787', consolidated, class_name=self.__class__.__name__, method_name=_method_name)
        return consolidated

    def __slim_list(self, attributes, attribute_helper, remove_readonly=False):
        return [attribute for attribute in attributes if not (
            self.__in_ignore(attribute) or
            attribute_helper.is_child_mbean(attribute) or
            (remove_readonly and attribute_helper.is_read_only(attribute)) or
            self.__is_clear_text_encrypted(attribute, attribute_helper) or
            # The following should always be the final elimination step
            not attribute_helper.is_valid_getter(attribute)
        )]

    def __get_info_helper(self, location):
        return MBeanInfoAttributes(self.__model_context, self.__aliases, self.__exception_type, location)

    def __get_interface_helper(self, location):
        return InterfaceAttributes(self.__model_context, self.__aliases, self.__exception_type, location)

    def __remove_duplicates(self, check_list, check_list_type, main_list, main_list_type):
        _method_name = '__remove_duplicates'
        _logger.entering(len(check_list), len(main_list), class_name=self.__class__.__name__, method_name=_method_name)
        for attribute in main_list:
            if attribute in check_list:
                check_list.remove(attribute)
            else:
                _logger.fine('WLSDPLY-01788', attribute, check_list_type, main_list_type,
                             class_name=self.__class__.__name__, method_name=_method_name)
        _logger.exiting(class_name=self.__class__.__name__, method_name=_method_name, result=len(check_list))

    def __is_clear_text_encrypted(self, attribute_name, attribute_helper):
        if not attribute_name.endswith('Encrypted'):
            return attribute_helper.is_encrypted(attribute_name + 'Encrypted')
        return False

    def __get_ignore_attributes(self):
        _method_name = '__get_ignore_attributes'
        if self.__ignore_list is None:
            self.__ignore_list = self.__aliases.get_ignore_attribute_names()
            _logger.finer('WLSDPLY-01779', self.__ignore_list,
                          class_name=self.__class__.__name__, method_name=_method_name)
        return self.__ignore_list

    def __in_ignore(self, attribute_name):
        return attribute_name in self.__get_ignore_attributes()

    def __get_helper(self):
        if self.__model_context.get_target_wlst_mode() == WlstModes.OFFLINE:
            helper = OfflineMBeanHelper(self.__model_context, self.__exception_type)
        else:
            helper = OnlineMBeanHelper(self.__model_context, self.__exception_type)
        return helper

    def __get_lsa_attributes(self, location, lsa_map=None):
        _method_name = '__get_lsa_attributes'
        attributes = None
        attribute_path = self.__aliases.get_wlst_attributes_path(location)
        if lsa_map is None and location is not None and attribute_path is not None:
            try:
                return_map = self.__wlst_helper.lsa(attribute_path)
                if return_map is not None:
                    attributes = return_map.keys()
                else:
                    attributes = list()
            except BundleAwareException:
                pass
        if attributes is None:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-01771', attribute_path)
            _logger.throwing(ex, class_name=self.__class__.__name__, method_name=_method_name)
            raise ex
        return attributes


class MBeanHelper(object):
    """
    Utility methods to assist with providing additional information specific to online and offline WLST techniques.
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
    """
    Assist the MBeanHelper providing mbean attribute information using a specific technique for online.
    """

    __class_name = 'OnlineMBeanHelper'

    def __init__(self, model_context, exception_type):
        """
        Create an utility helper instance for online.

        :param model_context: current context for the running tool
        """
        MBeanHelper.__init__(self,  model_context, exception_type)

    def is_attribute_in_lsa_map(self, attribute, lsa_attributes):
        """
        Look for the attribute name from one of the MBean helper lists in the online LSA map.
        This is a straight comparison and needs no alteration.
        :param attribute: to match in the LSA list
        :param lsa_attributes: list of LSA attributes
        :return: True if the attribute is found in the LSA list
        """
        _method_name = 'is_attribute_in_lsa_map'
        _logger.entering(attribute, class_name=self.__class__.__name__, method_name=_method_name)

        found = False
        if attribute in lsa_attributes:
            found = True
        _logger.exiting(class_name=self.__class__.__name__, method_name=_method_name, result=Boolean(found))
        return found

    def is_lsa_in_attributes(self, lsa_attribute, attribute_list):
        """
        Look for the online WLST LSA attribute name in one of the MBean helper lists. This is
        a straight comparison.
        :param lsa_attribute: attribute from the online WLST LSA list
        :param attribute_list: list of attributes from one of the MBean helper maps
        :return: True if the LSA attribute is found in the MBean list
        """
        _method_name = 'is_lsa_in_attributes'
        _logger.entering(lsa_attribute, class_name=self.__class__.__name__, method_name=_method_name)
        found = False
        if lsa_attribute in attribute_list:
            found = True
        _logger.exiting(class_name=self.__class__.__name__, method_name=_method_name, result=Boolean(found))
        return found


class OfflineMBeanHelper(MBeanHelper):
    """
    Assist the MBeanHelper providing mbean attribute information using a specific technique for online.
    """

    __class_name = 'OfflineMBeanUtils'

    def __init__(self, model_context, exception_type):
        """
        Create an utility helper instance for offline.

        :param model_context: current context for the running tool
        """
        MBeanHelper.__init__(self,  model_context, exception_type)

    def is_attribute_in_lsa_map(self, attribute, lsa_attributes):
        """
        Look for the attribute name from one of the MBean helper lists in the offline WLST LSA map.
        Names differ for some attributes between the offline LSA and MBean helper list. Attempt to match
        the attribute in the LSA map using different representations of the name.
        :param attribute: to match in the LSA list
        :param lsa_attributes: list of LSA attributes
        :return: True if the attribute is found in the LSA list
        """
        _method_name = 'is_attribute_in_lsa_map'
        _logger.entering(attribute, class_name=self.__class__.__name__, method_name=_method_name)
        found = True
        if attribute not in lsa_attributes and not self.__is_found_with_lower_case(attribute, lsa_attributes):
            if not attribute.endswith('ies') or \
                    not self.__is_found_with_lower_case(attribute[:len(attribute) - 3] + 'y', lsa_attributes):
                if not attribute.endswith('es') or \
                        not self.__is_found_with_lower_case(attribute[:len(attribute) - 2], lsa_attributes):
                    if not attribute.endswith('s') or \
                            not self.__is_found_with_lower_case(attribute[:len(attribute) - 1], lsa_attributes):
                        found = False
        _logger.exiting(class_name=self.__class__.__name__, method_name=_method_name, result=Boolean(found))
        return found

    def is_lsa_in_attributes(self, lsa_attribute, attribute_list):
        """
        Look for the offline WLST LSA attribute name in one of the MBean's helper lists. The names
        can differ between the LSA attribute and the MBean attribute lists. Attempt to match the LSA
        attribute using different representations of the name.
        :param lsa_attribute: attribute from the offline WLST LSA list
        :param attribute_list: list of attributes from one of the MBean helper maps
        :return: True if the LSA attribute is found in the MBean list
        """
        _method_name = 'is_lsa_in_attributes'
        _logger.entering(lsa_attribute, class_name=self.__class__.__name__, method_name=_method_name)
        found = True
        if lsa_attribute not in attribute_list and not self.__is_found_with_lower_case(lsa_attribute, attribute_list):
            if not lsa_attribute.endswith('y') or not \
                   self.__is_found_with_lower_case(lsa_attribute[:len(lsa_attribute) - 1] + 'ies', attribute_list):
                if not self.__is_found_with_lower_case(lsa_attribute + 'es', attribute_list):
                    if not self.__is_found_with_lower_case(lsa_attribute + 's', attribute_list):
                        found = False
        _logger.exiting(class_name=self.__class__.__name__, method_name=_method_name, result=Boolean(found))
        return found

    def __is_found_with_lower_case(self, attribute, mbean_list):
        _method_name = '_is_found_with_lower_case'
        _logger.entering(attribute, class_name=self.__class__.__name__, method_name=_method_name)

        found = False
        try:
            found = len([key for key in mbean_list if key.lower() == attribute.lower()]) > 0
        except (ValueError, KeyError):
            pass

        _logger.exiting(class_name=self.__class__.__name__, method_name=_method_name, result=Boolean(found))
        return found


class MBeanAttributes(object):
    """
    The MBeanAttributes class is a wrapper class encapsulating MBean information for the different types of
    MBean attribute collections. An instance of this class contains all attributes for an MBean at a specific
    location. The methods in this class operates on the attributes the class encapsulates to provide attribute
    specific information.
    """

    __interface_matcher = re.compile('Bean')

    def __init__(self, model_context, aliases, exception_type, location):
        self.__model_context = model_context
        self.__exception_type = exception_type
        self.__location = location
        self.__aliases = aliases
        self.__wlst_helper = WlstHelper(exception_type)
        self.__mbean_interface_name = None
        self.__mbean_instance = None
        self.__mbean_interface = None
        self.__mbean_name = ''

    def mbean_string(self):
        """
        Return a string representing the MBean encapsulated by the helper class.
        :return: Printable string identifying the MBean
        """
        return 'MBean %s at location %s' % (self.get_mbean_name(), self._get_mbean_path())

    def get_mbean_name(self):
        """
        Return the MBean "type" (i.e. JDBCSystemResource)
        :return: mbean type
        """
        return self.__mbean_name

    def get_mbean_interface_name(self):
        """
        Return the full name of the MBean interface class.
        :return: Interface name
        """
        self._get_mbean_interface()
        return self.__mbean_interface_name

    def get_mbean_instance(self):
        _method_name = 'get_mbean_instance'
        if self.__mbean_instance is None:
            attribute_path = self.__aliases.get_wlst_attributes_path(self.__location)
            self.__mbean_instance = self.__wlst_helper.get_mbean(attribute_path)
            if self.__mbean_instance is None:
                ex = exception_helper.create_exception(self._get_exception_type(), 'WLSDPLY-01775', attribute_path)
                _logger.throwing(ex, class_name=self.__class__.__name__, method_name=_method_name)
                raise ex
        return self.__mbean_instance

    def _get_mbean_interface(self):
        _method_name = '__get_mbean_interface'
        if self.__mbean_interface is None:
            _logger.entering(class_name=self.__class__.__name__, method_name=_method_name)
            interfaces = [interface for interface in self._get_mbean_interfaces()
                          if re.search(self.__interface_matcher, str_helper.to_string(interface)) is not None]
            if len(interfaces) == 0:
                ex = exception_helper.create_exception(self._get_exception_type(), 'WLSDPLY-01777',
                                                       str_helper.to_string(self._get_mbean_interfaces()),
                                                       self.get_mbean_instance())
                _logger.throwing(ex, class_name=self.__class__.__name__, method_name=_method_name)
                raise ex
            else:
                if len(interfaces) > 1:
                    _logger.fine('WLSDPLY-01770', interfaces, self.get_mbean_instance(),
                                 class_name=self.__class__.__name__, method_name=_method_name)
                self.__mbean_interface = interfaces[0]
                self.__mbean_name = str_helper.to_string(self.__mbean_interface.getSimpleName())
                self.__mbean_interface_name = get_interface_name(self._get_mbean_interface())
            _logger.exiting(class_name=self.__class__.__name__, method_name=_method_name,
                            result=self.__mbean_interface_name)

        return self.__mbean_interface

    def _get_mbean_methods(self):
        return self.__get_mbean_class().getDeclaredMethods()

    def _get_mbean_name(self):
        return self.__mbean_name

    def _get_mbean_interfaces(self):
        return self.__get_mbean_class().getInterfaces()

    def _get_exception_type(self):
        return self.__exception_type

    def __get_mbean_class(self):
        _method_name = '__get_mbean_class'
        mbean_class = None
        mbean_instance = self.get_mbean_instance()
        try:
            getter = getattr(mbean_instance, 'getClass')
            mbean_class = getter()
        except AttributeError:
            pass
        if mbean_class is None:
            ex = exception_helper.create_exception(self._get_exception_type(), 'WLSDPLY-01776', mbean_instance)
            _logger.throwing(ex, class_name=self.__class__.__name__, method_name=_method_name)
            raise ex
        return mbean_class

    def _get_from_bean_proxy(self, getter):
        _method_name = '__get_from_bean_proxy'
        success = False
        value = None
        try:
            get_method = getattr(self.get_mbean_instance(), getter)
            if get_method is not None:
                value = get_method()
                _logger.finest('WLSDPLY-01784', getter, self._get_mbean_name(),
                               class_name=self.__class__.__name__, method_name=_method_name)
                success = True
            else:
                _logger.finer('WLSDPLY-01786', self._get_mbean_name(), getter,
                              class_name=self.__class__.__name__, method_name=_method_name)
        except (Exception, JException), e:
            _logger.finest('WLSDPLY-01785', self._get_mbean_name(), getter, str_helper.to_string(e),
                           class_name=self.__class__.__name__, method_name=_method_name)
        return success, value

    def _get_mbean_path(self):
        return self.__location.get_folder_path()


def get_interface_name(mbean_interface):
    try:
        getname = getattr(mbean_interface, 'getTypeName')
        result = getname()
    except (Exception, JException):
        result = str_helper.to_string(mbean_interface)
    return result


def _is_empty(value):
    return value is None or len(value) == 0 or value == '[]' or value == 'null'


class InterfaceAttributes(MBeanAttributes):
    """
    This MBeanAttributes class type encapsulates the attribute information found from the
    attribute methods on the WLST CMO instance.
    """

    def __init__(self,  model_context, aliases, exception_type, location):
        MBeanAttributes.__init__(self,  model_context, aliases, exception_type, location)

        self.__interface_methods_list = None
        self.__interface_method_names_list = None
        self.__interface_attribute_map = None

    def get_mbean_attributes(self):
        """
        Return the sorted list of interface attribute names including child MBeans,
        as compiled from an MBean's interface getter methods.
        :return: list of attribute names from the MBean's interface or empty list if the MBean has no attributes.
        """
        _method_name = 'get_interface_attribute_list'
        _logger.entering(class_name=self.__class__.__name__, method_name=_method_name)
        map_to_list = list()
        attributes = self.__get_interface_map()
        if len(attributes) > 0:
            map_to_list = [attribute for attribute in attributes.iterkeys()]
            map_to_list.sort()
        return map_to_list

    def exists(self, attribute_name):
        """
        Determine if the attribute name exists for the MBean using the methods in the MBean's Interface.
        :param attribute_name: to search for in the MBean's Interface
        :return: True if the attribute is found in the MBean's Interface
        """
        return attribute_name in self.__get_interface_map()

    def is_child_mbean(self, attribute_name):
        """
        Determine if the attribute exists in the MBean's Interface and if the attribute is a child MBean.

        :param attribute_name: to search for in the MBean's Interface
        :return: True if the attribute is a child MBean or None if the attribute is not found in the MBean's Interface
        """
        _method_name = 'is_child_mbean'
        if self.exists(attribute_name):
            child = False
            for method_name in [method.getName() for method in self.__get_interface_methods()
                                if self.__is_subfolder_method(method)]:
                if attribute_name in method_name:
                    _logger.finer('WLSDPLY-01781', method_name, attribute_name,
                                  class_name=self.__class__.__name__, method_name=_method_name)
                    child = True
                    break
            return child
        return None

    def is_read_only(self, attribute_name):
        """
        Determine if the attribute exists in the MBean's Interface and if the attribute is readonly.
        :param attribute_name: to search for in the MBean's Interface
        :return: True if the attribute is readonly or None if the attribute does not exist in the MBean's Interface
        """
        if self.exists(attribute_name):
            return self.setter(attribute_name) is None
        return None

    def getter(self, attribute_name):
        """
        Return the read method string for the attribute in the MBean's Interface.
        :param attribute_name: to search for in the MBean's Interface
        :return: attribute getter or None if the attribute does not exist in the MBean's Interface
        """
        method_list = self.__get_mbean_attribute(attribute_name)
        if method_list is not None:
            return method_list[0]
        return None

    def is_valid_getter(self, attribute_name):
        """
        Try to invoke the Interface getter method on the mbean instance. Some of the methods listed
        on the Interface will fail.
        :return: True if can invoke the getter on the mbean instance
        """
        _method_name = 'is_valid_getter'
        _logger.entering(attribute_name, class_name=self.__class__.__name__, method_name=_method_name)

        valid = False
        getter = self.getter(attribute_name)
        if getter is not None:
            valid, __ = self._get_from_bean_proxy(getter)
        _logger.exiting(class_name=self.__class__.__name__, method_name=_method_name, result=Boolean(valid))
        return valid

    def setter(self, attribute_name):
        """
        Return the setter Method for the attribute in the MBean's Interface
        :param attribute_name: to search for in the MBean's Interface
        :return: setter Method or None if the attribute is readonly or the attribute does not exist in the Interface
        """
        method_list = self.__get_mbean_attribute(attribute_name)
        if method_list is not None and len(method_list) > 1:
            return method_list[1]
        return None

    def is_encrypted(self, attribute_name):
        """
        Determine if the property is encrypted by checking for a byte array return type on the getter.
        :param attribute_name: to search for in the MBean's Interface
        :return: True if the attribute is an encrypted type or None if the attribute does not exist in the Interface
        """
        return_type = self.get_type(attribute_name)
        if return_type is not None:
            if return_type == '[B':
                return True
            return False
        return None

    def is_clear_text_encrypted(self, attribute_name):
        """
        The tool does not discover encrypted attributes that are clear text. Determine if the attribute is a
        this type of attribute.
        :param attribute_name: name of the attribute to test
        :return: True if the attribute is an encrypted clear text attribute
        """
        if self.is_encrypted(attribute_name + 'Encrypted'):
            return True
        return False

    def get_type(self, attribute_name):
        """
        Return the type of the attribute value if the attribute exists in the MBean's Interface.
        :param attribute_name: to search for in the MBean's Interface
        :return: Type of the property attribute or None if the attribute does not exist in the MBean's Interface
        """
        method_list = self.__get_mbean_attribute(attribute_name)
        if method_list is not None:
            return str_helper.to_string(method_list[0].getReturnType())
        return None

    def get_default_value(self, attribute_name):
        """
        Unable to determine the default value when using only the MBean Interface.
        :param attribute_name: attribute name
        :return: None to indicate no default information available
        """
        return None

    def get_value(self, attribute_name):
        """
        Return the attribute value from the MBean instance.
        :param attribute_name: name of the attribute
        :return: value of the MBean attribute in the format retrieved from the MBean instance
        """
        value = None
        getter = self.getter(attribute_name)
        if getter is not None:
            __, value = self._get_from_bean_proxy(getter)
        return value

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

    def __get_interface_method_names(self):
        _method_name = '__get_interface_method_names'
        if self.__interface_method_names_list is None:
            self.__interface_method_names_list = [named_item.getName() for named_item in self.__get_interface_methods()]
            _logger.finest('WLSDPLY-01772', self._get_mbean_name(), self.__interface_method_names_list,
                           class_name=self.__class__.__name__, method_name=_method_name)
        return self.__interface_method_names_list

    def __get_mbean_getters(self):
        mbean_methods = self.__get_interface_methods()
        # log and exit if no mbean methods
        return [method for method in mbean_methods if self.__is_getter(method)]

    def __get_mbean_setters(self):
        mbean_methods = self.__get_interface_methods()
        return [method for method in mbean_methods if self.__is_setter(method)]

    def __get_mbean_setter(self, attribute_name):
        setter = None
        index = _get_index_of_name_in_list(self.__get_interface_method_names(), 'set' + attribute_name)
        if index >= 0:
            setter = self.__get_interface_methods()[index]
        return setter

    def __create_method_list(self, attribute, getter):
        _method_name = '__get_method_list'
        _logger.entering(attribute, class_name=self.__class__.__name__, method_name=_method_name)
        method_list = list()
        method_list.append(getter)
        setter = self.__get_mbean_setter(attribute)
        if setter is not None:
            method_list.append(setter)

        _logger.exiting(class_name=self.__class__.__name__, method_name=_method_name, result=method_list)
        return method_list

    def __get_method_name(self, method):
        return method.getName()

    def __is_getter(self, method):
        name = self.__get_method_name(method)
        return name is not None and (name.startswith('get') or name.startswith('is')) \
            and len(method.getParameterTypes()) == 0

    def __is_setter(self, method):
        setter = self.__get_method_name(method)
        return setter.startswith('set') and str_helper.to_string(setter.getReturnType) == 'void'

    def __is_subfolder_method(self, method):
        name = self.__get_method_name(method)
        return name.startswith('create') or name.startswith('add') or name.startswith('destroy')

    def __attribute_from_getter(self, getter_method):
        getter = self.__get_method_name(getter_method)
        if getter.startswith('get'):
            return getter[3:]
        else:
            return getter[2:]

    def __str__(self):
        return self.__class__.__name__ + self._get_mbean_name()


def _get_index_of_name_in_list(search_list_for, name):
    try:
        return search_list_for.index(name)
    except ValueError:
        pass
    return -1


class MBeanInfoAttributes(MBeanAttributes):
    """
    MBeanInfoAttributes extends the MBeanAttributes class. It encapsulates the attribute information found from the
    PropertyDescriptors in the MBeanInfo for the MBean type.
    """

    __class_name = 'MBeanInfoAttributes'

    def __init__(self, model_context, aliases, exception_type, location):
        MBeanAttributes.__init__(self, model_context, aliases, exception_type, location)

        self.__weblogic_helper = WebLogicHelper(_logger)
        self.__mbean_info_descriptors = None
        self.__mbean_info_map = None

    def get_mbean_attributes(self):
        """
        Return the sorted list of attributes compiled from the MBeanInfo PropertyDescriptors including the
        child MBeans.
        :return: list of all attributes from the MBeanInfo property descriptors, or an empty list if none
        """
        _method_name = 'get_mbean_attributes'
        _logger.entering(class_name=self.__class__.__name__, method_name=_method_name)
        map_to_list = list()
        attributes = self.__get_mbean_info_map()
        if len(attributes) > 0:
            map_to_list = [attribute for attribute in attributes.iterkeys()]
            map_to_list.sort()
        _logger.exiting(class_name=self.__class__.__name__, method_name=_method_name, result=len(map_to_list))
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
        _method_name = 'is_child_mbean'
        descriptor = self.__get_mbean_attribute(attribute_name)
        if descriptor is not None:
            relationship = descriptor.getValue('relationship')
            is_child = relationship == 'containment' or \
                (relationship == 'reference' and self.is_read_only(attribute_name))
            if is_child:
                _logger.finer('WLSDPLY-01780', attribute_name, class_name=self.__class__.__name__,
                              method_name=_method_name)
            return is_child
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

    def is_valid_getter(self, attribute_name):
        """
        Try to invoke the getter method on the mbean_instance. Some of the attributes in the PropertyDescriptors
        have read methods that cannot be invoked on the MBean instance.
        :return: True if can invoke the getter on the MBean instance
        """
        _method_name = 'is_valid_getter'
        _logger.entering(attribute_name, class_name=self.__class__.__name__, method_name=_method_name)

        valid = False
        getter = self.getter(attribute_name)
        if getter is not None:
            valid, __ = self._get_from_bean_proxy(getter)
        _logger.exiting(class_name=self.__class__.__name__, method_name=_method_name, result=Boolean(valid))
        return valid

    def setter(self, attribute_name):
        """
        Return the set method name for the attribute in the MBeanInfo.
        :param attribute_name: to search for in the MBeanInfo
        :return: setter for the attribute or None if the attribute is readonly or the attribute does not exist
        """
        descriptor = self.__get_mbean_attribute(attribute_name)
        if descriptor is not None:
            setter = descriptor.getWriteMethod()
            if setter is not None and (str_helper.to_string(setter.getReturnType()) == 'void' or
                                       str_helper.to_string(setter.getReturnType()) == "<type \'void\'>"):
                return setter.getName()
        return None

    def is_encrypted(self, attribute_name):
        """
        Determine if the property is an encrypted attribute.
        :param attribute_name: to search for in the MBeanInfo
        :return: True if it is an encrypted attribute or None if the attribute does not exist in the MBeanInfo
        """
        descriptor = self.__get_mbean_attribute(attribute_name)
        if descriptor is not None:
            return descriptor.getValue('encrypted') is True
        return None

    def is_clear_text_encrypted(self, attribute_name):
        """
        The tool does not discover security attributes that are clear text. Determine if the attribute is a
        an attribute returning clear text form of the matching encrypted attribute and skip if True.
        :param attribute_name: name of the attribute to test
        :return: True if the attribute is a clear text security attribute
        """
        return self.is_encrypted(attribute_name) and \
            str_helper.to_string(self.get_type(attribute_name)) == 'java.lang.String'

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
        """
        Return the default value if the attribute exists in MBeanInfo
        :param attribute_name: to search for in the MBeanInfo
        :return: The default value for the attribute
        """
        descriptor = self.__get_mbean_attribute(attribute_name)
        values = _get_descriptor_values_keys(descriptor)
        if 'defaultValueNull' in values and descriptor.getValue('defaultValueNull') is True:
            default = None
        else:
            default = descriptor.getValue('default')
        return default

    def get_value(self, attribute_name):
        """
        Return the attribute value from the mbean instance.
        :param attribute_name: name of the attribute
        :return: Value of the MBean attribute in the format retrieved from the mbean instance
        """
        value = None
        getter = self.getter(attribute_name)
        if getter is not None:
            __, value = self._get_from_bean_proxy(getter)
        return value

    def __get_mbean_info_map(self):
        if self.__mbean_info_map is None:
            self.__mbean_info_map = dict()
            for descriptor in self.__get_mbean_descriptors():
                self.__mbean_info_map[descriptor.getName()] = descriptor

        return self.__mbean_info_map

    def __get_mbean_descriptors(self):
        _method_name = '__get_mbean_descriptors'
        if self.__mbean_info_descriptors is None:
            mbean_info = self.__weblogic_helper.get_bean_info_for_interface(self.get_mbean_interface_name())
            if mbean_info is None:
                ex = exception_helper.create_exception(self._get_exception_type(), 'WLSDPLY-01774',
                                                       self.get_mbean_interface_name(), self.mbean_string())
                _logger.throwing(ex, class_name=self.__class__.__name__, method_name=_method_name)
                raise ex
            self.__mbean_info_descriptors = mbean_info.getPropertyDescriptors()
        return self.__mbean_info_descriptors

    def __get_mbean_attribute(self, attribute):
        descriptor_map = self.__get_mbean_info_map()
        if attribute in descriptor_map:
            return descriptor_map[attribute]
        return None

    def __str__(self):
        return self.__class__.__name__ + self._get_mbean_name()


def _get_descriptor_values_keys(descriptor):
    """
    Return a list of keys from the PropertyDescriptor "values" map.
    :param descriptor: MBeanInfo PropertyDescriptor with the values array
    :return: list of keys from the "values" key=value map
    """
    enumerations = descriptor.attributeNames()
    return _create_enumeration_list(enumerations)


def _create_enumeration_list(enumeration):
    enumeration_list = list()
    while enumeration.hasMoreElements():
        enumeration_list.append(enumeration.nextElement())
    return enumeration_list
