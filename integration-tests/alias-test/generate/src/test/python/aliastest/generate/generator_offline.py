"""
Copyright (c) 2021, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import copy

import java.lang.Boolean as Boolean
import java.lang.String as String
import java.util.logging.Level as Level

from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.logging.platform_logger import PlatformLogger

from aliastest.generate.generator_base import GeneratorBase
import aliastest.generate.generator_wlst as generator_wlst
from aliastest.generate.mbean_info_helper import MBeanInfoHelper
from aliastest.generate.mbean_method_helper import MBeanMethodHelper
import aliastest.generate.utils as generator_utils

ADDITIONAL_RECHECK = 'additional'
ATTRIBUTES = generator_utils.ATTRIBUTES
INSTANCE_TYPE = generator_utils.INSTANCE_TYPE
MULTIPLE = generator_utils.MULTIPLE
RECHECK = generator_utils.RECHECK
RESTART = generator_utils.RESTART
RESTART_NO_CHECK = 'none'
SINGLE = generator_utils.SINGLE
SINGLE_NO_NAME = generator_utils.SINGLE_NO_NAME
TYPE = generator_utils.TYPE

OFFLINE_ONLY_FOLDERS_MAP = {
    'NMProperties': {
        'top': 'true',
        'create': 'false',
        'path': 'NMProperties'
    }
}

PROVIDERS = generator_utils.PROVIDERS


class OfflineGenerator(GeneratorBase):
    """
    Generate the offline folder and attribute information into a dictionary. The offline generate is seeded
    by the mbean information in dictionary generated from online.
    """
    __logger = PlatformLogger('test.aliases.generate.offline')

    def __init__(self, model_context, sc_providers, online_dictionary):
        super(OfflineGenerator, self).__init__(model_context, PyOrderedDict())
        self.__class_name = self.__class__.__name__
        self.__model_context = model_context
        self._sc_providers = sc_providers
        self._online_dictionary = online_dictionary

    def generate(self):
        """
        Generate the data from an offline domain using the dictionary provided on the construction of this instance.
        """
        _method_name = 'generate'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        domain_home = self.__model_context.get_domain_home()
        if not generator_wlst.read_domain(domain_home):
            return self._dictionary

        self.__folder_hierarchy(self._dictionary, self._online_dictionary, '/')
        for mbean_type, mbean_type_map in OFFLINE_ONLY_FOLDERS_MAP.items():
            # create code to walk through array of mbeans with dictionary
            if 'top' not in mbean_type_map or not mbean_type_map['top']:
                self.__logger.warning('Processing offline-only MBeans for top level MBeans only: {0}={1}',
                                      mbean_type, mbean_type_map,
                                      class_name=self.__class_name, method_name=_method_name)
            else:
                self.__folder_hierarchy_offline_only(self._dictionary, mbean_type, mbean_type_map)

        generator_wlst.close_domain()

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return self._dictionary

    def __folder_hierarchy(self, mbean_dictionary, online_dictionary, mbean_path, parent_mbean_type=None):
        _method_name = '__folder_hierarchy'
        self.__logger.entering(len(online_dictionary), mbean_path,
                               class_name=self.__class_name, method_name=_method_name)
        if 'DatabaseLessLeasingBasis' in mbean_path:
            mbean_path.replace('DatabaseLessLeasingBasis', '\(DatabaseLessLeasingBasis\)')
        mbean_instance = generator_wlst.get_mbean_proxy(mbean_path)

        mbean_dictionary[ATTRIBUTES] = self.__get_attributes(mbean_instance)

        info_helper = MBeanInfoHelper(mbean_instance, mbean_path)
        info_map = generator_utils.reorder_info_map(mbean_path, info_helper.get_child_mbeans())
        self.__logger.finest('At {0}, MBeanInfoHelper found child MBeans: {1}', mbean_path, info_map.keys(),
                             class_name=self.__class_name, method_name=_method_name)

        methods_helper = MBeanMethodHelper(mbean_instance, mbean_path)
        methods_map = methods_helper.get_child_mbeans()
        methods_name_list = methods_map.keys()
        methods_name_list.sort()
        self.__logger.finest('At {0}, MBeanMethodHelper found child MBeans: {1}', mbean_path, methods_name_list,
                             class_name=self.__class_name, method_name=_method_name)

        online_dictionary_names = copy.copy(online_dictionary.keys())
        online_dictionary_names.sort()
        self.__logger.finest('At {0}, online dictionary names: {1}', mbean_path, online_dictionary_names,
                             class_name=self.__class_name, method_name=_method_name)

        for mbean_type, mbean_helper in info_map.iteritems():
            if mbean_type in methods_name_list:
                self.__logger.fine('Child MBean {0} of {1} in both the MBeanInfo and the CMO methods',
                                   mbean_type, parent_mbean_type,
                                   class_name=self.__class_name, method_name=_method_name)
                methods_name_list.remove(mbean_type)
            else:
                self.__logger.fine('Info MBean {0} not found in CMO methods',
                                   mbean_type, methods_name_list,
                                   class_name=self.__class_name, method_name=_method_name)
            if mbean_type in online_dictionary_names:
                online_dictionary_names.remove(mbean_type)
            else:
                self.__logger.fine('MBean {0} child {1} at location {3} not in online dictionary : {2}',
                                   parent_mbean_type, mbean_type, online_dictionary_names, mbean_path,
                                   class_name=self.__class_name, method_name=_method_name)

            if self._is_valid_folder(mbean_helper):
                if mbean_type in PROVIDERS:
                    self.__logger.fine('Found security provider folder {0}', mbean_type)
                    success, lsc_name, attributes = self.create_security_type(mbean_type)
                    if attributes is not None:
                        mbean_dictionary[lsc_name] = attributes
                    continue
                else:
                    success, lsc_name, attributes = \
                        self.__generate_folder(mbean_instance, parent_mbean_type, mbean_type, mbean_helper)
                    if attributes is not None:
                        if lsc_name == '(DatabaseLessLeasingBasis)':
                            lsc_name = 'DatabaseLessLeasingBasis'
                        mbean_dictionary[lsc_name] = attributes

                if success:
                    next_online_dictionary = dict()
                    if mbean_type in online_dictionary:
                        next_online_dictionary = online_dictionary[mbean_type]
                    self.__folder_hierarchy(mbean_dictionary[lsc_name], next_online_dictionary,
                                            generator_wlst.current_path(), parent_mbean_type=lsc_name)
                    generator_wlst.cd_mbean('../..')
            else:
                self.__logger.finer('Skipping invalid child MBean {0} for MBean {1}', mbean_type, parent_mbean_type,
                                    class_name=self.__class_name, method_name=_method_name)

        if len(online_dictionary_names) > 0:
            self.__logger.finest('The online dictionary names at path {0} has MBeans not in MBeanInfo or methods',
                                 mbean_path, class_name=self.__class_name, method_name=_method_name)
            for online_dictionary_name in online_dictionary_names:
                self.__logger.finest('Processing online_dictionary_name {0} at path {1}', online_dictionary_name,
                                     mbean_path, class_name=self.__class_name, method_name=_method_name)
                if online_dictionary_name in methods_name_list:
                    self.__logger.fine('Found Child MBean {0} of {1} found in CMO methods', online_dictionary_name,
                                       parent_mbean_type, class_name=self.__class_name, method_name=_method_name)
                    methods_name_list.remove(online_dictionary_name)

                # Have to make sure what we are processing is not a security provider type.
                if online_dictionary_name in PROVIDERS:
                    self.__logger.fine('Found security provider folder {0} in online_dictionary_names',
                                       online_dictionary_name, class_name=self.__class_name, method_name=_method_name)
                    success, lsc_name, attributes = self.create_security_type(online_dictionary_name)
                    if attributes is not None:
                        mbean_dictionary[lsc_name] = attributes
                    continue
                else:
                    self.__logger.fine('Found folder {0} in online_dictionary_names', online_dictionary_name,
                                       class_name=self.__class_name, method_name=_method_name)
                    success, lsc_name, attributes = \
                        self.__generate_folder(mbean_instance, parent_mbean_type, online_dictionary_name, None)
                if success:
                    self.__logger.fine('Processing MBean {0} child {1} from online dictionary',
                                       lsc_name, parent_mbean_type,
                                       class_name=self.__class_name, method_name=_method_name)
                    if attributes is not None:
                        mbean_dictionary[lsc_name] = attributes
                    next_online_dictionary = online_dictionary[online_dictionary_name]
                    self.__folder_hierarchy(mbean_dictionary[lsc_name], next_online_dictionary,
                                            generator_wlst.current_path(), lsc_name)
                    generator_wlst.cd_mbean('../..')

        if len(methods_name_list) > 0:
            self.__logger.finest('Looking at leftover CMO methods {0}', methods_name_list,
                                 class_name=self.__class_name, method_name=_method_name)
            look_at_all_info = info_helper.get_all_attributes().keys()
            look_at_all_info.sort()
            extra_mbeans = list()
            for method_mbean_type in methods_name_list:
                if method_mbean_type not in look_at_all_info and \
                        self._is_valid_method_only_attribute(methods_helper.get_attribute(method_mbean_type)):
                    extra_mbeans.append(method_mbean_type)
            if len(extra_mbeans) > 0:
                self.__logger.info('Method MBeans found for parent {0} that'
                                   ' are not in MBeanInfo, LSA map or online {1}', parent_mbean_type, extra_mbeans,
                                   class_name=self.__class_name, method_name=_method_name)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __folder_hierarchy_offline_only(self, mbean_dictionary, mbean_type, mbean_type_map):
        _method_name = '__folder_hierarchy_offline_only'
        self.__logger.entering(mbean_type, class_name=self.__class_name, method_name=_method_name)

        mbean_dictionary[mbean_type] = PyOrderedDict()
        # CD to the indicated path. Else work from the current directory
        if 'path' in mbean_type_map:
            path = mbean_type_map['path']
            self.__logger.fine('Using path {0} to navigate to offline MBean {1}', path, mbean_type,
                               class_name=self.__class_name, _method_name=_method_name)
            generator_wlst.cd_mbean(path)

        success = True
        if 'create' in mbean_type_map and mbean_type_map['create'] == 'true':
            if not self.__create_subfolder(mbean_type, mbean_dictionary[mbean_type]):
                self.__logger.warning('Unable to create offline only MBean {0}', mbean_type,
                                      class_name=self.__class_name, method_name=_method_name)
                mbean_dictionary[mbean_type][RECHECK] = 'Cannot create MBean instance'
                success = False
            else:
                self.__logger.fine('Normal operations used to create and navigate to the offline mbean {0}', mbean_type,
                                   class_name=self.__class_name, method_name=_method_name)
                if not self.__cd_to_mbean_name(mbean_type):
                    self.__logger.warning('Unable to navigate to the MBean {0} created at location {1}',
                                          mbean_type, generator_wlst.current_path(),
                                          class_name=self.__class_name, method_name=_method_name)
                    mbean_dictionary[mbean_type][RECHECK] = 'Cannot navigate to created MBean instance'
                    success = False
        if success:
            mbean_instance = generator_wlst.get_mbean_proxy()
            mbean_dictionary[mbean_type][ATTRIBUTES] = self.__get_attributes_offline_only(mbean_instance)
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __generate_folder(self, mbean_instance, parent_mbean_type, mbean_type, mbean_helper):
        _method_name = '__generate_folder'
        self.__logger.entering(parent_mbean_type, mbean_type, class_name=self.__class_name, method_name=_method_name)

        folder_dict = PyOrderedDict()
        lsc_name = self.__create_offline_mbean(mbean_type, folder_dict)
        success = False
        if lsc_name is None:
            if mbean_helper is not None:
                lsc_name = mbean_type
                self.__logger.fine('MBean {0} from MBeanInfo cannot be created with wlst.create()', lsc_name,
                                   class_name=self.__class_name, method_name=_method_name)
                if self.__create_subfolder_mbeaninfo(mbean_type, mbean_helper, folder_dict):
                    success = True
                else:
                    self.__logger.fine('MBean {0} from MBeanInfo cannot be created with invoke', lsc_name,
                                       class_name=self.__class_name, method_name=_method_name)
                    if self._is_coherence_mt_mbean(lsc_name):
                        folder_dict = None
                    else:
                        folder_dict[RECHECK] = 'Unable to create MBean instance'
        else:
            success = True

        if success:
            if mbean_type != lsc_name:
                self.__logger.finer('MBean type {0} converted to name {1}', mbean_type, lsc_name,
                                    class_name=self.__class_name, method_name=_method_name)

            if parent_mbean_type == lsc_name:
                success = False
                folder_dict[RECHECK] = 'MBean type is same as Parent MBean type'
            else:
                if not self.__cd_to_mbean_name(lsc_name):
                    success = False
                    self.__logger.finer('Unable to navigate to child MBean {0} for parent MBean {1}',
                                        lsc_name, parent_mbean_type,
                                        class_name=self.__class_name, method_name=_method_name)
                    folder_dict[RECHECK] = 'Cannot create and navigate to MBean instance'
                    getter, creator = self.__check_how_implemented(mbean_instance, lsc_name)
                    if getter and creator:
                        folder_dict[ADDITIONAL_RECHECK] = \
                            'Possible cause is spelling difference between online and offline name'
                    if getter:
                        folder_dict[ADDITIONAL_RECHECK] = \
                            'This bean does not have a creator method and should have been automatically created'
                elif mbean_helper is not None:
                    mbean_helper.generate_mbean(folder_dict)

        self.__logger.exiting(result=lsc_name, class_name=self.__class_name, method_name=_method_name)
        return success, lsc_name, folder_dict

    def __get_attributes(self, mbean_instance):
        _method_name = '__get_attributes'
        mbean_path = generator_wlst.current_path()
        self.__logger.entering(mbean_instance, mbean_path, class_name=self.__class_name, method_name=_method_name)

        attribute_map = PyOrderedDict()
        lsa_map = generator_wlst.lsa_map()
        self.__logger.finer('lsa_map = {0}', lsa_map, class_name=self.__class_name, method_name=_method_name)
        not_found_mbean_list = list()
        if len(lsa_map) > 0:
            not_found_mbean_list = lsa_map.keys()
            not_found_mbean_list.sort()

        method_helper = MBeanMethodHelper(mbean_instance, mbean_path)
        methods_map = method_helper.get_attributes()
        methods_attributes = methods_map.keys()
        self.__logger.finer('At {0}, MBeanMethodHelper found attributes: {1}', mbean_path, methods_attributes,
                            class_name=self.__class_name, method_name=_method_name)

        # As the driver it needs to have all attributes
        info_helper = MBeanInfoHelper(mbean_instance, mbean_path)
        info_map = info_helper.get_all_attributes()
        mbean_type = info_helper.get_mbean_type()
        self.__logger.finer('At {0}, MBeanInfoHelper for MBean type {0} found attributes: {1}', mbean_type,
                            info_map.keys(), class_name=self.__class_name, method_name=_method_name)

        for attribute, attribute_helper in info_map.iteritems():
            method_attribute_helper = None
            if attribute in methods_attributes:
                method_attribute_helper = methods_map[attribute]
                methods_attributes.remove(attribute)
                self.__logger.finest('Removed {0} from methods list for mbean {1}', attribute, mbean_type,
                                     class_name=self.__class_name, method_name=_method_name)

            if not attribute_helper.is_attribute():
                continue

            self.__logger.finer('Generating information for mbean {0} attribute {1}', mbean_type, attribute,
                                class_name=self.__class_name, method_name=_method_name)
            # return type and other info from the info map. Be sure and add in set arg type and get return type
            # to the generated entry.
            lsa_name = self.__find_ls_name(attribute, lsa_map)

            if lsa_name is None:
                if self._is_valid_cmo_attribute(attribute_helper):
                    if attribute not in methods_map:
                        self.__logger.finest('MBeanInfo attribute {0} not found in methods list for mbean {1}',
                                             attribute, mbean_type,
                                             class_name=self.__class_name, method_name=_method_name)
                    # find the descriptor and find the lsa value and do the get with the get method and get the
                    self.__logger.finest('Attribute {0} not found in the LSA map', attribute,
                                         class_name=self.__class_name, method_name=_method_name)
                    self.__logger.fine('Processing attribute {0} from MBeanInfo not found in LSA map',
                                       lsa_name, class_name=self.__class_name, method_name=_method_name)
                    dict_name = attribute
                    holder = PyOrderedDict()
                    self.add_default_value(holder, lsa_map, attribute_helper, method_attribute_helper)
                    self.add_derived_default(holder, attribute_helper, attribute)
                    attribute_helper.generate_attribute(holder)
                    _add_restart_value(holder)
                    attribute_map[dict_name] = generator_utils.sort_dict(holder)
            else:
                self.__logger.fine('Attribute {0} is in the LSA map and has MBeanInfo property descriptor', lsa_name,
                                   class_name=self.__class_name, method_name=_method_name)
                dict_name = lsa_name
                if lsa_name in not_found_mbean_list:
                    not_found_mbean_list.remove(lsa_name)
                else:
                    self.__logger.finer('MBean {0} attribute {1} converted to {2} not found in LSA list : {3} ',
                                        mbean_type, attribute, lsa_name, not_found_mbean_list,
                                        class_name=self.__class_name, method_name=_method_name)
                if self._is_valid_attribute(lsa_name, attribute_helper):
                    self.__logger.finer('Processing attribute {0} with lsa_name {1} found in '
                                        'both the MBeanInfo and LSA map', attribute, lsa_name,
                                        class_name=self.__class_name, method_name=_method_name)
                    holder = PyOrderedDict()
                    self.add_default_value(holder, lsa_map, attribute_helper, method_attribute_helper,
                                           attribute_name=dict_name)
                    self.add_derived_default(holder, attribute_helper, dict_name)
                    attribute_helper.generate_attribute(holder)
                    _add_restart_value(holder)
                    attribute_map[dict_name] = generator_utils.sort_dict(holder)

        if len(not_found_mbean_list) > 0:
            self.__logger.finest('Remaining attributes in LSA map for MBean {0} are {1}',
                                 mbean_type, not_found_mbean_list,
                                 class_name=self.__class_name, method_name=_method_name)
        for lsa_only in not_found_mbean_list:
            found, attribute = self.__find_attribute_name(lsa_only, methods_map)
            if found:
                method_attribute_helper = methods_map[attribute]
                if attribute in methods_attributes:
                    methods_attributes.remove(attribute)
                attribute_helper = method_attribute_helper
            else:
                method_attribute_helper = method_helper.get_attribute(lsa_only)
                attribute_helper = info_helper.get_attribute(lsa_only)
            if self._is_valid_lsa(attribute_helper):
                self.__logger.finest('Generating information for mbean {0} attribute {1}', mbean_type, lsa_only,
                                     class_name=self.__class_name, method_name=_method_name)
                self.__logger.fine('Processing LSA map attribute {0} not found in MBeanInfo', lsa_only,
                                   class_name=self.__class_name, method_name=_method_name)
                holder = PyOrderedDict()
                self.add_default_value(holder, lsa_map, attribute_helper, method_attribute_helper,
                                       attribute_name=lsa_only)
                self.add_derived_default(holder, attribute_helper, lsa_only)
                method_attribute_helper.generate_attribute(holder)
                _add_restart_value(holder)
                attribute_map[lsa_only] = generator_utils.sort_dict(holder)

        remaining = list()
        for attribute in methods_attributes:
            attribute_helper = methods_map[attribute]
            if self._is_valid_attribute(attribute, attribute_helper) and not attribute_helper.is_readonly():
                remaining.append(attribute)
        if len(remaining) > 0:
            self.__logger.info('Methods has additional attributes for MBean {0} : {1}', mbean_type, remaining,
                               class_name=self.__class_name, method_name=_method_name)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return generator_utils.sort_dict(attribute_map)

    def __get_attributes_offline_only(self, mbean_instance):
        _method_name = '__get_attributes_offline_only'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        mbean_path = generator_wlst.current_path()
        attribute_map = PyOrderedDict()
        lsa_map = generator_wlst.lsa_map()
        method_helper = MBeanMethodHelper(mbean_instance, mbean_path)
        methods_map = method_helper.get_attributes()
        mbean_type = method_helper.get_mbean_type()
        for attribute in lsa_map:
            method_attribute_helper = None
            found, mbean_method_name = self.__find_attribute_name(attribute, methods_map)
            if found:
                method_attribute_helper = methods_map[mbean_method_name]
                attribute_helper = method_attribute_helper
            else:
                # Fake one up
                attribute_helper = method_helper.get_attribute(attribute)
            if self._is_valid_no_mbean(mbean_type, attribute_helper):
                self.__logger.finer('Generating information for offline only mbean {0} attribute {1}', mbean_type,
                                    attribute, class_name=self.__class_name, method_name=_method_name)
                holder = PyOrderedDict()
                self.add_default_value(holder, lsa_map, attribute_helper, method_attribute_helper,
                                       attribute_name=attribute)
                attribute_helper.generate_attribute(holder)
                _add_restart_value(holder)
                attribute_map[attribute] = generator_utils.sort_dict(holder)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return generator_utils.sort_dict(attribute_map)

    def create_security_type(self, mbean_type):
        _method_name = 'create_security_type'
        self.__logger.entering(mbean_type, class_name=self.__class_name, method_name=_method_name)

        folder_dict = PyOrderedDict()
        folder_dict[TYPE] = 'Provider'
        provider_sub_types = self._sc_providers[mbean_type]

        singular_mbean_type = mbean_type
        if singular_mbean_type.endswith('s'):
            lenm = len(mbean_type)-1
            singular_mbean_type = mbean_type[0:lenm]

        curr_path = generator_wlst.current_path()
        existing_provider_types = generator_wlst.lsc()
        existing_providers = []
        if mbean_type in existing_provider_types:
            generator_wlst.cd_mbean(curr_path + '/' + mbean_type)
            existing_providers = generator_wlst.lsc()
            self.__logger.fine('existing providers for mbean_type {0}: {1}', mbean_type, existing_providers,
                               class_name=self.__class_name, method_name=_method_name)
            generator_wlst.cd_mbean(curr_path)

        for provider_sub_type in provider_sub_types:
            # Remove the package name from the subclass.
            idx = provider_sub_type.rfind('.')
            mbean_name = provider_sub_type[idx + 1:]
            shortened_provider_sub_type = mbean_name

            mbean_path = '%s/%s/%s' % (curr_path, mbean_type, mbean_name)
            if mbean_name not in existing_providers:
                mbean_instance = generator_wlst.create_security_provider(mbean_name, provider_sub_type,
                                                                         singular_mbean_type)
            else:
                mbean_instance = generator_wlst.get_mbean_proxy(mbean_path)

            generator_wlst.cd_mbean(mbean_path)
            folder_dict[shortened_provider_sub_type] = PyOrderedDict()
            folder_dict[shortened_provider_sub_type][ATTRIBUTES] = self.__get_attributes(mbean_instance)
            generator_wlst.cd_mbean(curr_path)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=singular_mbean_type)
        return True, singular_mbean_type, folder_dict

    def __cd_to_mbean_name(self, mbean_type):
        _method_name = '__cd_to_mbean_name'
        self.__logger.entering(mbean_type, class_name=self.__class_name, method_name=_method_name)

        success = True
        converted_mbean_type, mbean_name_list = self.__get_mbean_name_list(mbean_type)
        if mbean_name_list is not None and len(mbean_name_list) > 0:
            cd_mbean_name = mbean_name_list[0]
            bean_dir = converted_mbean_type + '/' + cd_mbean_name
            if not generator_wlst.cd_mbean(bean_dir):
                self.__logger.fine('Unable to create and navigate to mbean type {0} at location {1}',
                                   converted_mbean_type, generator_wlst.current_path(),
                                   class_name=self.__class_name, method_name=_method_name)
                success = False

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=Boolean(success))
        return success

    def __find_ls_name(self, attribute, mbean_map):
        _method_name = '__find_ls_name'
        self.__logger.entering(attribute, class_name=self.__class_name, method_name=_method_name)

        if attribute in mbean_map:
            result = attribute
        else:
            lower_case_map = generator_utils.get_lower_case_dict(mbean_map.keys())
            lower_case = attribute.lower()
            result = _key_in_case_map(lower_case, lower_case_map)
            if result is None and lower_case.endswith('ies'):
                result = _key_in_case_map(lower_case[:len(lower_case) - 3] + 'y', lower_case_map)
            if result is None and lower_case.endswith('es'):
                result = _key_in_case_map(lower_case[:len(lower_case) - 2], lower_case_map)
            if result is None and lower_case.endswith('s'):
                result = _key_in_case_map(lower_case[:len(lower_case) - 1], lower_case_map)

        self.__logger.exiting(result=result, class_name=self.__class_name, method_name=_method_name)
        return result

    def __find_attribute_name(self, lsa_name, mbean_map):
        _method_name = '__find_attribute_name'
        self.__logger.entering(lsa_name, class_name=self.__class_name, method_name=_method_name)

        result = lsa_name
        found = False
        if result in mbean_map:
            found = True
        else:
            lower_case_map = generator_utils.get_lower_case_dict(mbean_map.keys())
            lower_case = lsa_name.lower()
            result = _key_in_case_map(lower_case, lower_case_map)
            if result is None and lower_case.endswith('y'):
                result = _key_in_case_map(lower_case[:len(lower_case) - 1] + 'ies', lower_case_map)
            if result is None:
                result = _key_in_case_map(lower_case + 'es', lower_case_map)
            if result is None:
                result = _key_in_case_map(lower_case + 's', lower_case_map)
            if result is None:
                result = lsa_name
            else:
                found = True

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return found, result
    
    def __get_mbean_name_list(self, mbean_type, try_special=False):
        _method_name = '__get_mbean_name_list'
        self.__logger.entering(mbean_type, class_name=self.__class_name, method_name=_method_name)

        mbean_name_list = generator_wlst.ls_mbean_names(mbean_type)
        if mbean_name_list is None and not try_special:
            mbean_type, mbean_name_list = self.__get_mbean_name_list('(' + mbean_type + ')', try_special=True)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=mbean_name_list)
        return mbean_type, mbean_name_list
    
    def __check_how_implemented(self, mbean_proxy, search_mbean):
        _method_name = '__check_how_implemented'
        self.__logger.entering(search_mbean, class_name=self.__class_name, method_name=_method_name)

        get_method = False
        add_method = False
        for mbean_method in mbean_proxy.getClass().getMethods():
            name = mbean_method.getName()
            if search_mbean in name:
                if name.startswith('get'):
                    get_method = True
                elif name.startswith('create') or name.startswith('add') or name.startswith('set'):
                    add_method = True
    
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return get_method, add_method
    
    def __create_offline_mbean(self, mbean_type, folder_type):
        _method_name = '__create_offline_mbean'
        self.__logger.entering(mbean_type, class_name=self.__class_name, method_name=_method_name)

        converted = mbean_type
        if not self.__create_with(mbean_type, folder_type):
            fixed, converted = self.__find_with_special_case(mbean_type, folder_type)
            if not fixed:
                fixed, converted = self.__find_with_singular(mbean_type, folder_type)
                if not fixed:
                    fixed, converted = self.__find_with_case(mbean_type, folder_type)
                    if not fixed:
                        self.__logger.finest('Cannot generate MBean {0} in offline mode', mbean_type,
                                             class_name=self.__class_name, method_name=_method_name)
                        converted = None

        self.__logger.exiting(result=converted, class_name=self.__class_name, method_name=_method_name)
        return converted
    
    def __find_with_special_case(self, mbean_type, folder_type):
        if mbean_type == 'CoherenceClusterResource':
            return True, 'CoherenceResource'
        if mbean_type == 'DatabaseLessLeasingBasis':
            return True, '(DatabaseLessLeasingBasis)'
        return False, mbean_type
    
    def __find_with_case(self, mbean_type, folder_type):
        try_case, case_fixed = self.__fix_case(mbean_type)
        if try_case:
            if not self.__create_with(case_fixed, folder_type):
                return self.__find_with_singular(case_fixed, folder_type)
            return True, case_fixed
        return False, mbean_type
    
    def __find_with_singular(self, mbean_type, folder_type):
        try_ies, converted = _fix_plural_with_ies(mbean_type)
        if try_ies:
            if self.__create_with(converted, folder_type):
                return True, converted
        try_es, converted = _fix_plural_with_es(mbean_type)
        if try_es:
            if self.__create_with(converted, folder_type):
                return True, converted
        try_s, converted = _fix_plural_with_s(mbean_type)
        if try_s:
            if self.__create_with(converted, folder_type):
                return True, converted

        return False, mbean_type

    def __create_subfolder(self, mbean_type, folder_type):
        _method_name = '__create_subfolder'
        self.__logger.entering(mbean_type, class_name=self.__class_name, method_name=_method_name)

        type_list = generator_wlst.lsc()
        result = True
        if mbean_type not in type_list:
            name1, name2 = generator_utils.mbean_name(mbean_type)
            success1 = generator_wlst.created(mbean_type, name1)
            success2 = generator_wlst.created(mbean_type, name2)
            if not success1 and not success2:
                result = False
            else:
                name_list = generator_wlst.ls_mbean_names(mbean_type)
                # some mbeans are named different from what created with
                if name_list is None or len(name_list) == 0:
                    result = False
                elif len(name_list) == 2:
                    folder_type[INSTANCE_TYPE] = MULTIPLE
                elif name_list[0] == 'NO_NAME_0':
                    folder_type[INSTANCE_TYPE] = SINGLE_NO_NAME
                else:
                    folder_type[INSTANCE_TYPE] = SINGLE

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=Boolean(result))
        return result

    def __create_subfolder_mbeaninfo(self, mbean_type, mbean_helper, folder_type):
        _method_name = '__create_subfolder_mbeaninfo'
        self.__logger.entering(mbean_type, class_name=self.__class_name, method_name=_method_name)

        result = False
        creator_name = mbean_helper.creator_method_name()
        if creator_name is not None:
            name1, name2 = generator_utils.mbean_name(mbean_type)
            mbean_instance = mbean_helper.mbean_instance()
            parent_mbean_type = mbean_helper.get_mbean_type()
            success1 = self.invoke_creator(mbean_instance, parent_mbean_type, mbean_type, creator_name, name1)
            success2 = self.invoke_creator(mbean_instance, parent_mbean_type, mbean_type, creator_name, name2)
            if success1 or success2:
                name_list = generator_wlst.ls_mbean_names(mbean_type)
                # some mbeans are named different from what created with
                if name_list is None or len(name_list) == 0:
                    self.__logger.info('Mbean {0} created using MBeanInfo create method but is not present in domain',
                                       mbean_type, class_name=self.__class_name, method_name=_method_name)
                else:
                    result = True
                    if len(name_list) == 2:
                        folder_type[INSTANCE_TYPE] = MULTIPLE
                    elif name_list[0] == 'NO_NAME_0':
                        folder_type[INSTANCE_TYPE] = SINGLE_NO_NAME
                    else:
                        folder_type[INSTANCE_TYPE] = SINGLE

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=Boolean(result))
        return result

    def __create_with(self, mbean_type, folder_type):
        _method_name = '__create_with'
        self.__logger.entering(mbean_type, class_name=self.__class_name, method_name=_method_name)

        result = self.__create_subfolder(mbean_type, folder_type)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=Boolean(result))
        return result

    def __fix_case(self, mbean_type):
        _method_name = '__fix_case'
        self.__logger.entering(mbean_type, class_name=self.__class_name, method_name=_method_name)

        startswith = String(mbean_type).split("(?=\\p{Upper})")
        return_converted = False
        found_case = False
        converted = mbean_type
        if len(startswith) > 1:
            converted = ''
            for item in startswith:
                if len(item) == 1:
                    if found_case:
                        return_converted = True
                        converted += item.lower()
                        continue
                    else:
                        found_case = True
                else:
                    found_case = False
                converted += item

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=converted)
        return return_converted, converted

    def _is_coherence_mt_mbean(self, mbean_type):
        _method_name = '_is_coherence_mt_mbean'
        current_path = generator_wlst.current_path()
        self.__logger.entering(mbean_type, current_path, class_name=self.__class_name, method_name=_method_name)

        result = mbean_type == 'CoherenceClusterSystemResources' and 'ResourceGroup' in current_path

        self.__logger.exiting(result=result, class_name=self.__class_name, method_name=_method_name)
        return result


def _add_restart_value(attribute_map):
    attribute_map[RESTART] = RESTART_NO_CHECK


def _key_in_case_map(key, case_map):
    if key in case_map:
        return case_map[key]
    return None


def _fix_plural_with_ies(mbean_type):
    if mbean_type.endswith('ies'):
        return True, mbean_type[:len(mbean_type)-3] + 'y'
    return False, mbean_type


def _fix_plural_with_es(mbean_type):
    if mbean_type.endswith('es'):
        return True, mbean_type[:len(mbean_type) - 2]
    return False, mbean_type


def _fix_plural_with_s(mbean_type):
    if mbean_type.endswith('s'):
        return True, mbean_type[:len(mbean_type)-1]
    return False, mbean_type
