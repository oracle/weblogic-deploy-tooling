"""
Copyright (c) 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import copy

import java.lang.Boolean as Boolean
import java.lang.String as String
import java.util.logging.Level as Level

from wlsdeploy.logging.platform_logger import PlatformLogger

import aliastest.util.all_utils as all_utils
import aliastest.generate.generator_wlst as generator_wlst
import aliastest.generate.generator_security_configuration as generator_security_configuration
from aliastest.generate.generator_helper import GeneratorHelper
from aliastest.generate.mbean_info_helper import MBeanInfoHelper
from aliastest.generate.mbean_method_helper import MBeanMethodHelper

CLASS_NAME = 'OfflineGenerator'

OFFLINE_ONLY_FOLDERS_MAP = {
    'NMProperties': {
        'top': 'true',
        'create': 'false',
        'path': 'NMProperties'
    }
}


class OfflineGenerator(GeneratorHelper):
    """
    Generate the offline folder and attribute information into a dictionary. The offline generate is seeded
    by the mbean information in dictionary generated from online.
    """
    __logger = PlatformLogger('test.aliases.generate', resource_bundle_name='aliastest_rb')
    __logger.set_level(Level.FINER)
    
    def __init__(self, model_context, dictionary):
        GeneratorHelper.__init__(self, model_context, dictionary)
        self.__online_dictionary = dictionary
        self.__class_name__ = self.__class__.__name__

    def generate(self):
        """
        Generate the data from an offline domain using the dictionary provided on the construction of this instance.
        """
        _method_name = 'generate'
        self.__logger.entering(class_name=self.__class_name__, method_name=_method_name)
        offline_dictionary = all_utils.dict_obj()
        isRead = generator_wlst.read_domain(self._helper.domain_home())
        if not isRead:
            return
        top_mbean_path = '/'
        self.__folder_hierarchy(offline_dictionary, self.__online_dictionary, top_mbean_path)
        for mbean_type, mbean_type_map in OFFLINE_ONLY_FOLDERS_MAP.items():
            # create code to walk through array of mbeans with dictionary
            if 'top' not in mbean_type_map or not mbean_type_map['top']:
                self.__logger.warning('WLSDPLYST-01124', mbean_type, mbean_type_map,
                                      class_name=self.__class_name__, method_name=_method_name)
            else:
                self.__folder_hierarchy_offline_only(offline_dictionary, mbean_type, mbean_type_map)

        generator_wlst.close_domain()
        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name)
        return offline_dictionary

    def __folder_hierarchy(self, mbean_dictionary, online_dictionary, mbean_path, parent_mbean_type=None):
        _method_name = '__folder_hierarchy'
        self.__logger.entering(len(online_dictionary), mbean_path,
                               class_name=self.__class_name__, method_name=_method_name)

        mbean_instance = generator_wlst.get_mbean_proxy(mbean_path)

        mbean_dictionary[all_utils.ATTRIBUTES] = self.__get_attributes(mbean_instance)

        info_helper = MBeanInfoHelper(mbean_instance, mbean_path)
        info_map = info_helper.get_child_mbeans()

        methods_helper = MBeanMethodHelper(mbean_instance, mbean_path)
        methods_map = methods_helper.get_child_mbeans()
        methods_name_list = methods_map.keys()
        methods_name_list.sort()

        online_dictionary_names = copy.copy(online_dictionary.keys())
        online_dictionary_names.sort()
        self.__logger.fine('Online dictionary names for location {0} : {1}', mbean_path, online_dictionary_names,
                           class_name=self.__class_name__, method_name=_method_name)
        for mbean_type, mbean_helper in info_map.iteritems():
            if mbean_type in methods_name_list:
                self.__logger.fine('Child MBean {0} of {1} in both the MBeanInfo and the CMO methods',
                                   mbean_type, parent_mbean_type,
                                   class_name=self.__class_name__, method_name=_method_name)
                methods_name_list.remove(mbean_type)
            else:
                self.__logger.fine('Info MBean {0} not found in CMO methods',
                                   mbean_type, methods_name_list,
                                   class_name=self.__class_name__, method_name=_method_name)
            if mbean_type in online_dictionary_names:
                online_dictionary_names.remove(mbean_type)
            else:
                self.__logger.fine('MBean {0} child {1} at location {3} not in online dictionary : {2}',
                                   parent_mbean_type, mbean_type, online_dictionary_names, mbean_path,
                                   class_name=self.__class_name__, method_name=_method_name)

            if self._is_valid_folder(mbean_helper):
                if mbean_type in generator_security_configuration.PROVIDERS:
                    print 'Found security provider folder ', mbean_type
                    success, lsc_name, attributes = self.create_security_type(mbean_type)
                    mbean_dictionary[lsc_name] = attributes
                    continue
                else:
                    success, lsc_name, attributes = \
                        self.__generate_folder(mbean_instance, parent_mbean_type, mbean_type, mbean_helper)
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
                                    class_name=self.__class_name__, method_name=_method_name)

        if len(online_dictionary_names) > 0:
            self.__logger.finest('The online dictionary names has MBeans not in MBeanInfo or methods',
                                 class_name=self.__class_name__, method_name=_method_name)
            for online_dictionary_name in online_dictionary_names:
                if online_dictionary_name in methods_name_list:
                    self.__logger.fine('Child MBean {0} of {1} found in CMO methods',
                                       online_dictionary_name, parent_mbean_type,
                                       class_name=self.__class_name__, method_name=_method_name)
                    methods_name_list.remove(online_dictionary_name)
                success, lsc_name, attributes = \
                    self.__generate_folder(mbean_instance, parent_mbean_type, online_dictionary_name, None)
                if success:
                    self.__logger.fine('Processing MBean {0} child {1} from online dictionary',
                                       lsc_name, parent_mbean_type,
                                       class_name=self.__class_name__, method_name=_method_name)
                    mbean_dictionary[lsc_name] = attributes
                    next_online_dictionary = online_dictionary[online_dictionary_name]
                    self.__folder_hierarchy(mbean_dictionary[lsc_name], next_online_dictionary,
                                            generator_wlst.current_path(), lsc_name)
                    generator_wlst.cd_mbean('../..')

        if len(methods_name_list) > 0:
            self.__logger.finest('Looking at leftover CMO methods {0}', methods_name_list,
                                 class_name=self.__class_name__, method_name=_method_name)
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
                                   class_name=self.__class_name__, method_name=_method_name)

        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name)
        return

    def __folder_hierarchy_offline_only(self, mbean_dictionary, mbean_type, mbean_type_map):
        _method_name = '__folder_hierarchy_offline_only'
        self.__logger.entering(mbean_type, class_name=self.__class_name__, method_name=_method_name)

        mbean_dictionary[mbean_type] = all_utils.dict_obj()
        # CD to the indicated path. Else work from the current directory
        if 'path' in mbean_type_map:
            path = mbean_type_map['path']
            self.__logger.fine('WLSDPLYST-01127', path, mbean_type, _method_name=_method_name,
                               class_name=self.__class_name__)
            generator_wlst.cd_mbean(path)

        success = True
        if 'create' in mbean_type_map and mbean_type_map['create'] == 'true':
            if not self.__create_subfolder(mbean_type, mbean_dictionary[mbean_type]):
                self.__logger.warning('WLSDPLYST-01122', mbean_type, class_name=self.__class_name__,
                                      method_name=_method_name)
                mbean_dictionary[mbean_type][all_utils.RECHECK] = 'Cannot create MBean instance'
                success = False
            else:
                self.__logger.fine('WLSDPLYST=01129', mbean_type)
                if not self.__cd_to_mbean_name(mbean_type):
                    self.__logger.warning('Unable to navigate to the MBean {0} created at location {1}',
                                          mbean_type, generator_wlst.current_path())
                    mbean_dictionary[mbean_type][all_utils.RECHECK] = 'Cannot navigate to created MBean instance'
                    success = False
        if success:
            mbean_instance = generator_wlst.get_mbean_proxy()
            mbean_dictionary[mbean_type][all_utils.ATTRIBUTES] = self.__get_attributes_offline_only(mbean_instance)
        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name)
        return

    def __generate_folder(self, mbean_instance, parent_mbean_type, mbean_type, mbean_helper):
        _method_name = '__generate_folder'
        self.__logger.entering(parent_mbean_type, mbean_type, class_name=self.__class_name__, method_name=_method_name)

        folder_dict = all_utils.dict_obj()
        lsc_name = self.__create_offline_mbean(mbean_type, folder_dict)
        success = False
        if lsc_name is None:
            if mbean_helper is not None:
                lsc_name = mbean_type
                self.__logger.fine('MBean {0} from MBeanInfo cannot be created with wlst.create()', lsc_name,
                                   class_name=self.__class_name__, method_name=_method_name)
                if self.__create_subfolder_mbeaninfo(mbean_type, mbean_helper, folder_dict):
                    success = True
                else:
                    self.__logger.fine('MBean {0} from MBeanInfo cannot be created with invoke', lsc_name,
                                       class_name=self.__class_name__, method_name=_method_name)
                    folder_dict[all_utils.RECHECK] = 'Unable to create MBean instance'
        else:
            success = True

        if success:
            if mbean_type != lsc_name:
                self.__logger.finer('MBean type {0} converted to name {1}', mbean_type, lsc_name,
                                    class_name=self.__class_name__, method_name=_method_name)

            if parent_mbean_type == lsc_name:
                success = False
                folder_dict[all_utils.RECHECK] = 'MBean type is same as Parent MBean type'
            else:
                if not self.__cd_to_mbean_name(lsc_name):
                    success = False
                    self.__logger.finer('Unable to navigate to child MBean {0} for parent MBean {1}',
                                        lsc_name, parent_mbean_type,
                                        class_name=self.__class_name__, method_name=_method_name)
                    folder_dict[all_utils.RECHECK] = 'Cannot create and navigate to MBean instance'
                    getter, creator = self.__check_how_implemented(mbean_instance, lsc_name)
                    if getter and creator:
                        folder_dict[all_utils.ADDITIONAL_RECHECK] = \
                            'Possible cause is spelling difference between online and offline name'
                    if getter:
                        folder_dict[all_utils.ADDITIONAL_RECHECK] = \
                            'This bean does not have a creator method and should have been automatically created'
                elif mbean_helper is not None:
                    mbean_helper.generate_mbean(folder_dict)
        self.__logger.exiting(result=lsc_name, class_name=self.__class_name__, method_name=_method_name)
        return success, lsc_name, folder_dict

    def __get_attributes(self, mbean_instance):
        _method_name = '__get_attributes'
        mbean_path = generator_wlst.current_path()
        self.__logger.entering(mbean_instance, mbean_path, class_name=self.__class_name__, method_name=_method_name)
        attribute_map = all_utils.dict_obj()
        lsa_map = generator_wlst.lsa_map()
        not_found_mbean_list = list()
        if len(lsa_map) > 0:
            not_found_mbean_list = lsa_map.keys()
            not_found_mbean_list.sort()

        method_helper = MBeanMethodHelper(mbean_instance, mbean_path)
        methods_map = method_helper.get_attributes()
        methods_attributes = methods_map.keys()

        # As the driver it needs to have all attributes
        info_helper = MBeanInfoHelper(mbean_instance, mbean_path)
        info_map = info_helper.get_all_attributes()
        mbean_type = info_helper.get_mbean_type()

        #
        # if self.__logger.is_finest_enabled():
        #     interface_name, methods_map =all_utils.get_mbean_interface_method_map(mbean_proxy)
        #     mbean_type = None
        #     bean_info_name, mbean_info_map =all_utils.get_mbean_info_descriptor_map(mbean_proxy)
        #     self._report_differences(mbean_proxy, mbean_type, lsa_map, methods_map, mbean_info_map)

        for attribute, attribute_helper in info_map.iteritems():

            method_attribute_helper = None
            if attribute in methods_attributes:
                method_attribute_helper = methods_map[attribute]
                methods_attributes.remove(attribute)
                self.__logger.finest('Removed {0} from methods list for mbean {1}', attribute, mbean_type,
                                     class_name=self.__class_name__, method_name=_method_name)

            if not attribute_helper.is_attribute():
                continue

            self.__logger.finer('WLSDPLYST-01119', mbean_type, attribute, class_name=self.__class_name__,
                                method_name=_method_name)
            # return type and other info from the info map. Be sure and add in set arg type and get return type
            # to the generated entry.
            lsa_name = self.__find_ls_name(attribute, lsa_map)

            if lsa_name is None:
                if self._is_valid_cmo_attribute(attribute_helper):
                    if attribute not in methods_map:
                        self.__logger.finest('MBeanInfo attribute {0} not found in methods list for mbean {1}',
                                             attribute, mbean_type,
                                             class_name=self.__class_name__, method_name=_method_name)
                    # find the descriptor and find the lsa value and do the get with the get method and get the
                    self.__logger.finest('WLSDPLYST-01132', attribute,
                                         class_name=self.__class_name__, method_name=_method_name)
                    self.__logger.fine('Processing attribute {0} from MBeanInfo not found in LSA map',
                                       lsa_name, class_name=self.__class_name__, method_name=_method_name)
                    dict_name = attribute
                    holder = all_utils.dict_obj()
                    self.add_default_value(holder, lsa_map, attribute_helper, method_attribute_helper)
                    attribute_helper.generate_attribute(holder)
                    _add_restart_value(holder)
                    attribute_map[dict_name] = all_utils.sort_dict(holder)
            else:
                self.__logger.fine('WLSDPLYST-01133', lsa_name,
                                   class_name=self.__class_name__, method_name=_method_name)
                dict_name = lsa_name
                if lsa_name in not_found_mbean_list:
                    not_found_mbean_list.remove(lsa_name)
                else:
                    self.__logger.finer('MBean {0} attribute {1} converted to {2} not found in LSA list : {3} ',
                                        mbean_type, attribute, lsa_name, not_found_mbean_list,
                                        class_name=self.__class_name__, method_name=_method_name)
                if self._is_valid_attribute(lsa_name, attribute_helper):
                    self.__logger.finer('Processing attribute {0} with lsa_name {1} found in '
                                        'both the MBeanInfo and LSA map', attribute, lsa_name,
                                        class_name=self.__class_name__, method_name=_method_name)
                    holder = all_utils.dict_obj()
                    self.add_default_value(holder, lsa_map, attribute_helper, method_attribute_helper,
                                           attribute_name=dict_name)
                    attribute_helper.generate_attribute(holder)
                    _add_restart_value(holder)
                    attribute_map[dict_name] = all_utils.sort_dict(holder)

        if len(not_found_mbean_list) > 0:
            self.__logger.finest('Remaining attributes in LSA map for MBean {0} are {1}',
                                 mbean_type, not_found_mbean_list,
                                 class_name=self.__class_name__, method_name=_method_name)
        for lsa_only in not_found_mbean_list:
            method_attribute_helper = None
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
                self.__logger.finest('WLSDPLYST-01119', mbean_type, lsa_only, class_name=self.__class_name__,
                                     method_name=_method_name)
                self.__logger.fine('Processing LSA map attribute {0} not found in MBeanInfo', lsa_only,
                                   class_name=self.__class_name__, method_name=_method_name)
                holder = all_utils.dict_obj()
                self.add_default_value(holder, lsa_map, attribute_helper, method_attribute_helper,
                                       attribute_name=lsa_only)
                method_attribute_helper.generate_attribute(holder)
                _add_restart_value(holder)
                attribute_map[lsa_only] = all_utils.sort_dict(holder)

        remaining = list()
        for attribute in methods_attributes:
            attribute_helper = methods_map[attribute]
            if self._is_valid_attribute(attribute, attribute_helper) and not attribute_helper.is_readonly():
                remaining.append(attribute)
        if len(remaining) > 0:
            self.__logger.info('Methods has additional attributes for MBean {0} : {1}',
                               mbean_type, remaining,
                               class_name=self.__class_name__, method_name=_method_name)

        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name)
        return all_utils.sort_dict(attribute_map)

    def __get_attributes_offline_only(self, mbean_instance):
        _method_name = '__get_attributes_offline_only'
        self.__logger.entering(class_name=self.__class_name__, method_name=_method_name)
        mbean_path = generator_wlst.current_path()
        attribute_map = all_utils.dict_obj()
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
                self.__logger.finer('WLSDPLYST-01139', mbean_type, attribute, class_name=self.__class_name__,
                                    method_name=_method_name)
                holder = all_utils.dict_obj()
                self.add_default_value(holder, lsa_map, attribute_helper, method_attribute_helper,
                                       attribute_name=attribute)
                attribute_helper.generate_attribute(holder)
                _add_restart_value(holder)
                attribute_map[attribute] = all_utils.sort_dict(holder)
        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name)
        return all_utils.sort_dict(attribute_map)

    def create_security_type(self, mbean_type):
        folder_dict = all_utils.dict_obj()
        folder_dict[all_utils.TYPE] = 'Provider'
        types = generator_security_configuration.providers_map[mbean_type]

        singular = mbean_type
        if singular.endswith('s'):
            lenm = len(mbean_type)-1
            singular = mbean_type[0:lenm]
        for item in types:
            idx = item.rfind('.')
            short = item[idx + 1:]
            package = short
            mbean_instance = generator_wlst.created_security_provider(singular, short, package)
            orig = generator_wlst.current_path()
            folder_dict[short] = all_utils.dict_obj()
            folder_dict[short][all_utils.ATTRIBUTES] = self.__get_attributes(mbean_instance)
            generator_wlst.cd_mbean(orig)
        return True, singular, folder_dict

    def _slim_maps_for_report(self, mbean_proxy, mbean_type, lsa_map, methods_map, mbean_info_map):
        # Unlike the slim_maps method, this report discards additional information to determine how
        # different is the usable information in LSA, versus cmo.getClass().getMethods versus
        # MBeanInfo PropertyDescriptor.
        _lsa_remove_read_only(lsa_map)
        _methods_remove_read_only(methods_map)
        _mbean_info_remove_read_only(mbean_info_map)
        print 'After removing read only '
        print '    lsa_map size ', len(lsa_map), '  methods_map size ', len(methods_map), \
            ' mbean_info_size ', len(mbean_info_map)

        _remove_invalid_getters_methods(mbean_proxy, mbean_type, methods_map)
        _remove_invalid_getters_mbean_info(mbean_proxy, mbean_type, mbean_info_map)
        print 'After removing invalid getters from methods and mbean_info '
        print ' lsa_map size ', len(lsa_map), '  methods_map size ', len(methods_map), \
            ' mbean_info_size ', len(mbean_info_map)

        self._remove_should_ignores(lsa_map)
        self._remove_should_ignores(methods_map)
        self._remove_should_ignores(mbean_info_map)
        print 'After removing alias ignores '
        print ' lsa_map size ', len(lsa_map), '  methods_map size ', len(methods_map), \
            ' mbean_info_size ', len(mbean_info_map)

        self._remove_subfolders(methods_map, mbean_info_map)
        print 'After removing subfolders from methods and mbean_info '
        print ' lsa_map size ', len(lsa_map), '  methods_map size ', len(methods_map), \
            ' mbean_info_size ', len(mbean_info_map)

    def _report_differences(self, mbean_proxy, mbean_type, lsa_map, methods_map, mbean_info_map):
        print '*************************************************************'
        print 'Reporting on MBean ', str(mbean_proxy)
        self._slim_maps_for_report(mbean_proxy, mbean_type, lsa_map, methods_map, mbean_info_map)
        print ''
        lsa_keys = lsa_map.keys()
        lsa_keys.sort()
        methods_keys = methods_map.keys()
        methods_keys.sort()
        mbean_info_keys = mbean_info_map.keys()
        mbean_info_keys.sort()
        _report_lsa_not_in(lsa_keys, methods_keys, mbean_info_keys)

        _report_attribute_not_in(methods_keys,    'Method attribute    ', lsa_keys, mbean_info_keys, 'MBeanInfo ')
        _report_attribute_not_in(mbean_info_keys, 'MBeanInfo attribute ', lsa_keys, methods_keys, 'Method ')
        print '*************************************************************'
        print ''

    def __valid_child_folder(self, mbean_helper):
        _method_name = '__valid_child_folder'
        mbean_type = mbean_helper.get_name()
        valid = True
        # if mbean_type == parent_type:
        #     print 'MBean is same as parent ', mbean_type
        #     self.__logger.finest('Ignore MBean {0} whose parent is the same MBean type at location {1}',
        #                    mbean_type,all_utils.current_path(), class_name=self.__class_namecmethod_name=_method_name)
        if mbean_helper.is_reference():
            self.__logger.finest('Ignore MBean {0} which is a reference to an MBean at location {1}', mbean_type,
                                 generator_wlst.current_path(),
                                 class_name=self.__class_name__, method_name=_method_name)
            valid = False
        elif self._should_ignore(mbean_helper):
            self.__logger.finest('MBean {0} found in ignore list at location {1}',
                                 mbean_type, generator_wlst.current_path(),
                                 class_name=self.__class_name__, method_name=_method_name)
            valid = False
        return valid

    def __cd_to_mbean_name(self, mbean_type):
        _method_name = '__cd_to_mbean_name'
        self.__logger.entering(mbean_type, class_name=self.__class_name__, method_name=_method_name)
        success = True
        converted_mbean_type, mbean_name_list = self.__get_mbean_name_list(mbean_type)
        if mbean_name_list is not None and len(mbean_name_list) > 0:
            cd_mbean_name = mbean_name_list[0]
            bean_dir = converted_mbean_type + '/' + cd_mbean_name
            if not generator_wlst.cd_mbean(bean_dir):
                self.__logger.fine('WLSDPLYST-01117', converted_mbean_type, generator_wlst.current_path(), '',
                                   class_name=self.__class_name__, method_name=_method_name)
                success = False

        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name, result=Boolean(success))
        return success

    def __find_ls_name(self, attribute, mbean_map):
        _method_name = '__find_ls_name'
        self.__logger.entering(attribute, class_name=self.__class_name__, method_name=_method_name)
        if attribute in mbean_map:
            result = attribute
        else:
            lower_case_map = all_utils.get_lower_case_dict(mbean_map.keys())
            lower_case = attribute.lower()
            result = _key_in_case_map(lower_case, lower_case_map)
            if result is None and lower_case.endswith('ies'):
                result = _key_in_case_map(lower_case[:len(lower_case) - 3] + 'y', lower_case_map)
            if result is None and lower_case.endswith('es'):
                result = _key_in_case_map(lower_case[:len(lower_case) - 2], lower_case_map)
            if result is None and lower_case.endswith('s'):
                result = _key_in_case_map(lower_case[:len(lower_case) - 1], lower_case_map)

        self.__logger.exiting(result=result, class_name=self.__class_name__, method_name=_method_name)
        return result

    def __find_attribute_name(self, lsa_name, mbean_map):
        _method_name = '__find_attribute_name'
        self.__logger.entering(lsa_name, class_name=self.__class_name__, method_name=_method_name)
        result = lsa_name
        found = False
        if result in mbean_map:
            found = True
        else:
            lower_case_map = all_utils.get_lower_case_dict(mbean_map.keys())
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

        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name, result=result)
        return found, result
    
    def __get_name_from_map_using_lower_case(self, attribute, mbean_map):
        _method_name = '__get_name_from_map_using_lower_case'
        self.__logger.entering(attribute, class_name=self.__class_name__, method_name=_method_name)

        lower_case_attribute = attribute.lower()
    
        name = None
        try:
            found_list = [key for key in mbean_map if key.lower() == lower_case_attribute]
            if len(found_list) > 0:
                name = found_list[0]
            else:
                self.__logger.finest('lower case attribute {0} not found in map {1}',
                                     lower_case_attribute, [key.lower() for key in mbean_map],
                                     class_name=self.__class_name__, method_name=_method_name)
        except (ValueError, KeyError), e:
            self.__logger.fine('Attribute name {0} had error in mbean map : {1}',
                               attribute, str(e), class_name=self.__class_name__, method_name=_method_name)
            pass
    
        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name, result=name)
        return name

    def __get_mbean_name_list(self, mbean_type, try_special=False):
        _method_name = '__get_mbean_name_list'
        self.__logger.entering(mbean_type, class_name=self.__class_name__, method_name=_method_name)
        mbean_name_list = generator_wlst.ls_mbean_names(mbean_type)
        if mbean_name_list is None and not try_special:
            mbean_type, mbean_name_list = self.__get_mbean_name_list('(' + mbean_type + ')', try_special=True)
        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name, result=mbean_name_list)
        return mbean_type, mbean_name_list
    
    def __check_how_implemented(self, mbean_proxy, search_mbean):
        _method_name = '_check_how_implemented'
        self.__logger.entering(search_mbean, class_name=self.__class_name__, method_name=_method_name)
        get_method = False
        add_method = False
        for mbean_method in mbean_proxy.getClass().getMethods():
            name = mbean_method.getName()
            if search_mbean in name:
                if name.startswith('get'):
                    get_method = True
                elif name.startswith('create') or name.startswith('add') or name.startswith('set'):
                    add_method = True
    
        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name)
        return get_method, add_method
    
    def __create_offline_mbean(self, mbean_type, folder_type):
        _method_name = '__create_offline_mbean'
        self.__logger.entering(mbean_type, class_name=self.__class_name__, method_name=_method_name)
        converted = mbean_type
        if not self.__create_with(mbean_type, folder_type):
            fixed, converted = self.__find_with_special_case(mbean_type, folder_type)
            if not fixed:
                fixed, converted = self.__find_with_singular(mbean_type, folder_type)
                if not fixed:
                    fixed, converted = self.__find_with_case(mbean_type, folder_type)
                    if not fixed:
                        self.__logger.finest('WLSDPLYST-01125', mbean_type,
                                             class_name=self.__class_name__, method_name=_method_name)
                        converted = None
        self.__logger.exiting(result=converted, class_name=self.__class_name__, method_name=_method_name)
        return converted
    
    def __find_with_special_case(self, mbean_type, folder_type):
        _method_name = '__find_with_special_case'
        if mbean_type == 'CoherenceClusterResource':
            return True, 'CoherenceResource'
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
        self.__logger.entering(mbean_type, class_name=self.__class_name__, method_name=_method_name)
        type_list = generator_wlst.lsc()
        result = True
        if mbean_type not in type_list:
            name1, name2 = all_utils.mbean_name(mbean_type)
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
                    folder_type[all_utils.INSTANCE_TYPE] = all_utils.MULTIPLE
                elif name_list[0] == 'NO_NAME_0':
                    folder_type[all_utils.INSTANCE_TYPE] = all_utils.SINGLE_NO_NAME
                else:
                    folder_type[all_utils.INSTANCE_TYPE] = all_utils.SINGLE
        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name, result=Boolean(result))
        return result

    def __create_subfolder_mbeaninfo(self, mbean_type, mbean_helper, folder_type):
        _method_name = '__create_subfolder_mbeaninfo'
        self.__logger.entering(mbean_type, class_name=self.__class_name__, method_name=_method_name)

        result = False
        creator_name = mbean_helper.creator_method_name()
        if creator_name is not None:
            name1, name2 = all_utils.mbean_name(mbean_type)
            mbean_instance = mbean_helper.mbean_instance()
            parent_mbean_type = mbean_helper.get_mbean_type()
            success1 = self.invoke_creator(mbean_instance, parent_mbean_type, mbean_type, creator_name, name1)
            success2 = self.invoke_creator(mbean_instance, parent_mbean_type, mbean_type, creator_name, name2)
            if success1 or success2:
                name_list = generator_wlst.ls_mbean_names(mbean_type)
                # some mbeans are named different from what created with
                if name_list is None or len(name_list) == 0:
                    self.__logger.info('Mbean {0} created using MBeanInfo create method but is not present in domain',
                                       mbean_type,
                                       class_name=self.__class_name__, method_name=_method_name)
                else:
                    result = True
                    if len(name_list) == 2:
                        folder_type[all_utils.INSTANCE_TYPE] = all_utils.MULTIPLE
                    elif name_list[0] == 'NO_NAME_0':
                        folder_type[all_utils.INSTANCE_TYPE] = all_utils.SINGLE_NO_NAME
                    else:
                        folder_type[all_utils.INSTANCE_TYPE] = all_utils.SINGLE
        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name, result=Boolean(result))
        return result

    def __create_with(self, mbean_type, folder_type):
        _method_name = '__create_with'
        self.__logger.entering(mbean_type, class_name=self.__class_name__, method_name=_method_name)
        result = self.__create_subfolder(mbean_type, folder_type)
        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name, result=Boolean(result))
        return result

    def __fix_case(self, mbean_type):
        _method_name = '__fix_case'
        self.__logger.entering(mbean_type, class_name=self.__class_name__, method_name=_method_name)
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

        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name, result=converted)
        return return_converted, converted
    
    
def _remove_invalid_getters(mbean_instance, mbean_type, methods_map, mbean_info_map):
    for name, method_list in methods_map.iteritems():
        getter = method_list[0].getName()
        if not all_utils.is_valid_getter(mbean_instance, mbean_type, getter, name):
            del methods_map[name]
            if name in mbean_info_map:
                del mbean_info_map[name]


def _remove_invalid_getters_mbean_info(mbean_proxy, mbean_type, mbean_info_map):
    remove_list = list()
    for name, descriptor in mbean_info_map.iteritems():
        if not all_utils.is_valid_getter(mbean_proxy, mbean_type, descriptor.getReadMethod().getName(), name):
            remove_list.append(name)

    for name in remove_list:
        mbean_info_map.pop(name)


def _remove_invalid_getters_methods(mbean_proxy, mbean_type, method_map):
    remove_list = list()
    for name, method_list in method_map.iteritems():
        if not all_utils.is_valid_getter(mbean_proxy, mbean_type, method_list[0].getName(), name):
            remove_list.append(name)

    for name in remove_list:
        method_map.pop(name)


def _report_lsa_not_in(lsa_keys, methods_keys, mbean_info_keys):
    for lsa_name in lsa_keys:
        if not _find_lsa_in_other_map(lsa_name, methods_keys):
            print '   LSA attribute         ', lsa_name, ' not in Methods map '
        if not _find_lsa_in_other_map(lsa_name, mbean_info_keys):
            print '   LSA attribute         ', lsa_name, ' not in MBeanInfo map '


def _report_attribute_not_in(this_map_keys, this_map_type, lsa_map_keys, other_map_keys, other_map_type):
    for attribute in this_map_keys:
        not_in_lsa = False
        not_in_other = False
        if not _find_attribute_in_lsa_map(attribute, lsa_map_keys):
            print '  ', this_map_type, ' ', attribute, ' not in LSA map'
            not_in_lsa = True
        if not _find_lsa_in_other_map(attribute, other_map_keys):
            append = ''
            if not not_in_lsa:
                append = ' BUT is in LSA map'
            print '  ', this_map_type, ' ', attribute, ' ** not in ', other_map_type, append, ' **'
            not_in_other = True
        if not_in_lsa and not_in_other:
            print '   Attribute ', attribute, '** not in LSA and not in ', other_map_type, ' **'


def _find_lsa_in_other_map(lsa_name, bean_map_keys):
    if lsa_name not in bean_map_keys and not _is_found_with_lower_case(lsa_name, bean_map_keys):
        if not lsa_name.endswith('y') or not _is_found_with_lower_case(lsa_name[:len(lsa_name) - 1] + 'ies',
                                                                       bean_map_keys):
            if not _is_found_with_lower_case(lsa_name + 'es', bean_map_keys):
                if not _is_found_with_lower_case(lsa_name + 's', bean_map_keys):
                    return False
    return True


def _find_attribute_in_lsa_map(attribute_name, lsa_map_keys):
    if attribute_name not in lsa_map_keys and not _is_found_with_lower_case(attribute_name, lsa_map_keys):
        if not attribute_name.endswith('ies') or \
                        not _is_found_with_lower_case(attribute_name[:len(attribute_name) - 3] + 'y', lsa_map_keys):
            if not attribute_name.endswith('es') or \
                            not _is_found_with_lower_case(attribute_name[:len(attribute_name) - 2], lsa_map_keys):
                if not attribute_name.endswith('s') or \
                                not _is_found_with_lower_case(attribute_name[:len(attribute_name) - 1],
                                                              lsa_map_keys):
                    return False
    return True


def _is_found_with_lower_case(attribute, mbean_list):
    found = False
    try:
        found = len([key for key in mbean_list if key.lower() == attribute.lower()]) > 0
    except (ValueError, KeyError):
        pass

    return found


def _lsa_remove_read_only(lsa_map):
    remove_list = list()
    attributes_str = generator_wlst.lsa_string()
    for attribute_str in attributes_str.split('\n'):
        if attribute_str:
            read_type = attribute_str[0:4].strip()
            attr = attribute_str[7:attribute_str.find(' ', 7)+1].strip()
            if read_type == '-r--' and attr in lsa_map:
                remove_list.append(attr)

    for attr in remove_list:
        lsa_map.pop(attr)


def _mbean_info_remove_read_only(mbean_info_map):
    remove_list = list()
    for attribute_name, descriptor in mbean_info_map.iteritems():
        if descriptor.getWriteMethod() is None:
            remove_list.append(attribute_name)

    for attribute_name in remove_list:
        mbean_info_map.pop(attribute_name)


def _methods_remove_read_only(methods_map):
    remove_list = list()
    for attribute_name, method_list in methods_map.iteritems():
        if len(method_list) != 2:
            remove_list.append(attribute_name)

    for attribute_name in remove_list:
        methods_map.pop(attribute_name)


def _remove_method_subfolders(mbean_proxy, methods_map):
    # already removed read_only
    methods_list = [method.getName() for method in mbean_proxy.getClass().getMethods()
                    if method.getName().startswith('create') or method.getName().startswith('add')]
    remove_list = list()
    for attribute in methods_map:
        if 'create' + attribute in methods_list or 'add' + attribute in methods_list:
            remove_list.append(attribute)

    for attribute in remove_list:
        methods_map.pop(attribute)


def _remove_mbean_info_subfolders(mbean_info):
    remove_list = list()

    for attribute, descriptor in mbean_info.iteritems():
        relationship = descriptor.getValue('relationship')
        if relationship == 'containment' or (relationship == 'reference' and descriptor.getWriteMethod() is None):
            remove_list.append(attribute)

    for attribute in remove_list:
        mbean_info.pop(attribute)


def _add_restart_value(attribute_map):
    attribute_map[all_utils.RESTART] = all_utils.RESTART_NO_CHECK


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


def _not_at_top():
    return generator_wlst.current_path().find('/', 1) > 0
