"""
Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.lang import IllegalArgumentException
from java.lang import IllegalAccessException
from java.lang.reflect import InvocationTargetException
from oracle.weblogic.deploy.create import CustomBeanUtils

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.weblogic_helper import WebLogicHelper


class CustomFolderHelper(object):
    """
    Shared code for custom (user-defined) folders in the model.
    These require special handling, since they do not have alias definitions.
    """
    __class_name = 'CustomFolderHelper'
    __cipher_text_prefixes = ["{AES}", "{AES-256}"]

    def __init__(self, aliases, logger, model_context, exception_type):
        self.aliases = aliases
        self.logger = logger
        self.model_context = model_context
        self.exception_type = exception_type
        self.weblogic_helper = WebLogicHelper(self.logger)
        self.wlst_helper = WlstHelper(self.exception_type)

    def update_security_folder(self, location, model_type, model_subtype, model_name, model_nodes):
        """
        Update the specified security model nodes in WLST.
        :param location: the location for the provider
        :param model_type: the type of the provider to be updated, such as AuthenticationProvider
        :param model_subtype: the subtype of the provider to be updated, such as 'custom.my.CustomIdentityAsserter'
        :param model_name: the name of the provider to be updated, such as 'My custom IdentityAsserter'
        :param model_nodes: a child model nodes of the provider to be updated
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'update_security_folder'

        location_path = self.aliases.get_model_folder_path(location)
        self.logger.entering(location_path, model_subtype, model_name,
                             class_name=self.__class_name, method_name=_method_name)

        self.logger.info('WLSDPLY-12124', model_type, model_name, model_subtype, location_path,
                         class_name=self.__class_name, method_name=_method_name)

        create_path = self.aliases.get_wlst_subfolders_path(location)
        self.wlst_helper.cd(create_path)

        # create the MBean using the model type, name, and subtype

        type_location = LocationContext(location).append_location(model_type)
        token = self.aliases.get_name_token(type_location)
        type_location.add_name_token(token, model_name)

        mbean_type = self.aliases.get_wlst_mbean_type(type_location)
        self.wlst_helper.create(model_name, model_subtype, mbean_type)

        provider_path = self.aliases.get_wlst_attributes_path(type_location)
        provider_mbean = self.wlst_helper.cd(provider_path)

        interface_name = model_subtype + 'MBean'
        bean_info = self.weblogic_helper.get_bean_info_for_interface(interface_name)
        if bean_info is None:
            ex = exception_helper.create_exception(self.exception_type, 'WLSDPLY-12125', interface_name)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        property_map = dict()
        for property_descriptor in bean_info.getPropertyDescriptors():
            self.logger.finer('WLSDPLY-12126', str_helper.to_string(property_descriptor),
                              class_name=self.__class_name, method_name=_method_name)
            property_map[property_descriptor.getName()] = property_descriptor

        for model_key in model_nodes:
            model_value = model_nodes[model_key]
            property_descriptor = property_map.get(model_key)

            if not property_descriptor:
                folder_path = self.aliases.get_model_folder_path(type_location)
                ex = exception_helper.create_exception(self.exception_type, 'WLSDPLY-12128', model_key, folder_path)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            # find the setter method for the attribute

            method = property_descriptor.writeMethod
            if not method:
                # this must be a read-only attribute, just log it and continue with next attribute
                self.logger.info('WLSDPLY-12129', str_helper.to_string(model_key), class_name=self.__class_name,
                                 method_name=_method_name)
                continue

            self.logger.finer('WLSDPLY-12127', str_helper.to_string(model_key), str_helper.to_string(model_value),
                              class_name=self.__class_name, method_name=_method_name)

            # determine the data type from the set method

            parameter_types = method.getParameterTypes()
            parameter_count = len(parameter_types)

            if parameter_count != 1:
                ex = exception_helper.create_exception(self.exception_type, 'WLSDPLY-12130', model_key,
                                                       parameter_count)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            # if the property requires encryption, and the value is not encrypted,
            # encrypt the value with domain encryption.

            requires_encrypted = property_descriptor.getValue('encrypted')
            if requires_encrypted and not self.is_encrypted(model_value) and isinstance(model_value, basestring):
                model_value = self.weblogic_helper.encrypt(model_value, self.model_context.get_domain_home())

            property_type = parameter_types[0]

            # convert the model value to the target type and call the setter with the target value.
            # these are done together in Java to avoid automatic Jython type conversions.

            try:
                CustomBeanUtils.callMethod(provider_mbean, method, property_type, model_value)

            # failure converting value or calling method
            except (IllegalAccessException, IllegalArgumentException, InvocationTargetException), ex:
                ex = exception_helper.create_exception(self.exception_type, 'WLSDPLY-12131', method,
                                                       str_helper.to_string(model_value), ex.getLocalizedMessage(),
                                                       error=ex)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

    def is_encrypted(self, text):
        for prefix in self.__cipher_text_prefixes:
            if text.startswith(prefix):
                return True
        return False
