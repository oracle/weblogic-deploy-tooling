"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from java.lang import IllegalArgumentException, IllegalAccessException
from java.lang.reflect import InvocationTargetException
from oracle.weblogic.deploy.util import ConvertUtils

from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util.weblogic_helper import WebLogicHelper


class CustomFolderHelper(object):
    """
    Shared code for custom (user-defined) folders in the model.
    These require special handling, since they do not have alias definitions.
    """
    __class_name = 'CustomFolderHelper'

    def __init__(self, aliases, logger, exception_type):
        self.logger = logger
        self.exception_type = exception_type
        self.alias_helper = AliasHelper(aliases, self.logger, self.exception_type)
        self.weblogic_helper = WebLogicHelper(self.logger)
        self.wlst_helper = WlstHelper(self.logger, self.exception_type)

    def update_security_folder(self, location, model_category, model_type, model_name, model_nodes):
        """
        Update the specified security model nodes in WLST.
        :param location: the location for the provider
        :param model_category: the model category of the provider to be updated
        :param model_type: the model type of the provider to be updated
        :param model_name: the model name of the provider to be updated
        :param model_nodes: a child model nodes of the provider to be updated
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'update_security_folder'

        location_path = self.alias_helper.get_model_folder_path(location)
        self.logger.entering(location_path, model_type, model_name,
                             class_name=self.__class_name, method_name=_method_name)

        self.logger.info('WLSDPLY-12124', model_category, model_name, model_type, location_path,
                         class_name=self.__class_name, method_name=_method_name)

        create_path = self.alias_helper.get_wlst_subfolders_path(location)
        self.wlst_helper.cd(create_path)

        # TODO for updateDomain: check for existing provider, just cd if present

        # create the MBean using the model name, model_type, category

        self.wlst_helper.create(model_name, model_type, model_category)

        provider_path = create_path + '/' + model_category + '/' + model_name
        provider_mbean = self.wlst_helper.cd(provider_path)

        interface_name = model_type + 'MBean'
        bean_info = self.weblogic_helper.get_bean_info_for_interface(interface_name)
        if bean_info is None:
            ex = exception_helper.create_exception(self.exception_type, 'WLSDPLY-12125', interface_name)
            self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        property_map = dict()
        for property_descriptor in bean_info.getPropertyDescriptors():
            self.logger.finer('WLSDPLY-12126', str(property_descriptor), class_name=self.__class_name,
                              method_name=_method_name)
            property_map[property_descriptor.getName()] = property_descriptor

        for model_key in model_nodes:
            model_value = model_nodes[model_key]
            property_descriptor = property_map.get(model_key)

            if not property_descriptor:
                ex = exception_helper.create_exception(self.exception_type, 'WLSDPLY-12128', model_key)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            # find the setter method for the attribute

            method = property_descriptor.writeMethod
            if not method:
                # this must be a read-only attribute, just log it and continue with next attribute
                self.logger.info('WLSDPLY-12129', str(model_key), class_name=self.__class_name,
                                 method_name=_method_name)
                continue

            self.logger.finer('WLSDPLY-12127', str(model_key), str(model_value), class_name=self.__class_name,
                              method_name=_method_name)

            # determine the data type from the set method

            parameter_types = method.getParameterTypes()
            parameter_count = len(parameter_types)

            if parameter_count != 1:
                ex = exception_helper.create_exception(self.exception_type, 'WLSDPLY-12130', model_key,
                                                       parameter_count)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            property_type = parameter_types[0]

            # convert the model value to the target type

            set_value = ConvertUtils.convertValue(model_value, property_type)
            if set_value is None:
                ex = exception_helper.create_exception(self.exception_type, 'WLSDPLY-12131', str(model_value),
                                                       str(property_type), model_key)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

            # call the setter with the target value

            try:
                method.invoke(provider_mbean, [set_value])
            except (IllegalAccessException, IllegalArgumentException, InvocationTargetException), ex:
                ex = exception_helper.create_exception(self.exception_type, 'WLSDPLY-12132', str(method),
                                                       str(set_value), ex.getLocalizedMessage(), error=ex)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex
