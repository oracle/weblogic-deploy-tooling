"""
Copyright (c) 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import java.lang.Boolean as Boolean
import java.util.logging.Level as Level
from wlsdeploy.logging.platform_logger import PlatformLogger

import aliastest.util.all_utils as all_utils
import aliastest.generate.generator_security_configuration as generator_security_configuration
import aliastest.generate.generator_wlst as generator_wlst

from aliastest.generate.generator_helper import GeneratorHelper
from aliastest.generate.mbean_info_helper import MBeanInfoHelper
from aliastest.generate.mbean_method_helper import MBeanMethodHelper
from aliastest.generate.mbi_helper import MBIHelper


class OnlineGenerator(GeneratorHelper):
    """
    Generate MBean and attribute information into a dictionary from the online wlst session.
    The data is traversed using the registered mbean information for the online session.
    """

    def __init__(self, model_context, dictionary):
        GeneratorHelper.__init__(self,  model_context, dictionary)
        self.__class_name__ = self.__class__.__name__
        self._domain_home = None
        self.__logger = PlatformLogger('test.aliases.generate', resource_bundle_name='aliastest_rb')
        self.__logger.set_level(Level.FINER)

    def generate(self):
        """
        Generate the mbean dictionary for weblogic in wlst online mode.
        :return: the domain home of the connected session
        """
        _method_name = 'generate'
        self.__logger.entering(class_name=self.__class_name__, method_name=_method_name)
        if generator_wlst.connect(self._helper.admin_user(), self._helper.admin_password(), self._helper.admin_url()):
            try:
                self.__folder_hierarchy(self._dictionary, '/')
            finally:
                generator_wlst.disconnect()
        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name)
        return

    def __folder_hierarchy(self, mbean_dictionary, mbean_path):
        _method_name = '__folder_hierarchy'
        self.__logger.entering(mbean_path, class_name=self.__class_name__, method_name=_method_name)

        mbean_instance = generator_wlst.get_mbean_proxy(mbean_path)

        mbean_dictionary[all_utils.ATTRIBUTES] = self.__get_attributes(mbean_instance)

        mbean_map = self.__create_any_subfolders()

        info_helper = MBeanInfoHelper(mbean_instance, mbean_path)
        mbean_info_map = info_helper.get_child_mbeans()
        mbean_info_list = mbean_info_map.keys()

        mbi_helper = MBIHelper(mbean_instance, mbean_path)
        mbean_mbi_map = mbi_helper.get_child_mbeans()
        for mbean_type, attribute_helper in mbean_mbi_map.iteritems():
            mbean_name = None
            # mbean_type is the name of the child MBean attribute in the mbean Helper attribute list
            if mbean_type in mbean_map:
                mbean_name = mbean_map[mbean_type]
                del mbean_map[mbean_type]
            if mbean_type in mbean_info_list:
                mbean_info_list.remove(mbean_type)
                self.__logger.finest('Child MBean {0} is in both the MBI information and the MBeanInfo information',
                                   mbean_type, class_name=self.__class_name__, method_name=_method_name)
            else:
                self.__logger.fine('Child MBean {0} is in the MBI information but not the MBeanInfo information',
                                   mbean_type, class_name=self.__class_name__, method_name=_method_name)

            print 'mbean_type = ', mbean_type

            if attribute_helper.is_reference_only():
                mbean_dictionary[mbean_type] = all_utils.dict_obj()
                # This non-attribute might have been added as a folder, which it is not
                mbean_dictionary[mbean_type][all_utils.ONLINE_REFERENCE_ONLY] = all_utils.TRUE
                continue

            if self._is_valid_folder(attribute_helper):
                self.__logger.fine('WLSDPLYST-01115', mbean_type, generator_wlst.current_path(),
                                   class_name=self.__class_name__, method_name=_method_name)

                mbean_dictionary[mbean_type] = all_utils.dict_obj()
                if mbean_type in generator_security_configuration.PROVIDERS:
                    self.generate_security_mbean(mbean_dictionary, mbean_type)
                else:
                    attribute_helper.generate_mbean(mbean_dictionary[mbean_type])
                    if mbean_name is None:
                        mbean_name = generator_wlst.get_singleton_name(mbean_type)
                    if mbean_name is not None:
                        if mbean_type in generator_wlst.child_mbean_types():
                            mbean_dictionary[mbean_type][all_utils.INSTANCE_TYPE] = all_utils.MULTIPLE
                        else:
                            mbean_dictionary[mbean_type][all_utils.INSTANCE_TYPE] = all_utils.SINGLE
                        bean_dir = mbean_type + '/' + mbean_name
                        if not generator_wlst.cd_mbean(bean_dir):
                            self.__logger.fine('WLSDPLYST-01117', mbean_type, generator_wlst.current_path(), '',
                                               class_name=self.__class_name__, method_name=_method_name)
                            mbean_dictionary[mbean_type][all_utils.RECHECK] = \
                                'cd to mbean and mbean name returned exception'
                            continue

                        self.__folder_hierarchy(mbean_dictionary[mbean_type], generator_wlst.current_path())
                        generator_wlst.cd_mbean('../..')
            else:
                # make this a real message
                self.__logger.warning('Ignore invalid MBean folder {0} containment : {1}, deprecated : {2}',
                                      mbean_type, all_utils.str_bool(attribute_helper.is_containment()),
                                      all_utils.str_bool(attribute_helper.is_deprecated()),
                                      class_name=self.__class_name__, method_name=_method_name)

        if len(mbean_map) > 0:
            mbeans_only = [leftover for leftover in mbean_map if leftover not in mbi_helper.get_all_attributes()]
            if len(mbeans_only) > 0:
                for mbean_type in mbeans_only:
                    # If it is in the attribute list, its a reference
                    if mbi_helper.get_all_attribute(mbean_type).is_attribute_found() is False:
                        self.__logger.fine('MBean {0} was not found in the MBI map but is in the LSC map',
                                           mbean_type, class_name=self.__class_name__, method_name=_method_name)
                        info_attribute_helper = info_helper.get_child_mbean(mbean_type)
                        if info_attribute_helper.is_attribute_found():
                            self.__logger.fine('Child MBean {0} is in the MBeanInfo information but not'
                                               ' the MBI information',
                                               class_name=self.__class_name__, method_name=_method_name)
                        mbean_name = mbean_map[mbean_type]
                        if mbean_name is not None:
                            bean_dir = mbean_type + '/' + mbean_name
                            mbean_dictionary[mbean_type] = all_utils.dict_obj()
                            if generator_wlst.cd_mbean(bean_dir) is False:
                                self.__logger.fine('WLSDPLYST-01117', mbean_type, generator_wlst.current_path(), '',
                                                   class_name=self.__class_name__, method_name=_method_name)
                                mbean_dictionary[mbean_type][all_utils.RECHECK] = \
                                    'cd to mbean and mbean name returned exception'
                                continue

                            self.__folder_hierarchy(mbean_dictionary[mbean_type], generator_wlst.current_path())
                            generator_wlst.cd_mbean('../..')
        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name)
        return

    def __get_attributes(self, mbean_instance):
        _method_name = '__get_attributes'
        mbean_path = generator_wlst.current_path()
        self.__logger.entering(mbean_instance, mbean_path, class_name=self.__class_name__, method_name=_method_name)
        lsa_map = generator_wlst.lsa_map_modified()
        not_found_mbean_list = list()
        if len(lsa_map) > 0:
            not_found_mbean_list = lsa_map.keys()
            not_found_mbean_list.sort()

        mbean_instance = generator_wlst.get_mbean_proxy(mbean_path)
        operation_list = generator_wlst.ls_operations()
        info_helper = MBeanInfoHelper(mbean_instance, mbean_path)
        mbean_type = info_helper.get_mbean_type()
        mbean_info_map = info_helper.get_attributes()
        mbean_info_list = mbean_info_map.keys()
        self.__logger.finest('MBean {0} LSA map attributes are {1} at location {2} mbean_path',
                             mbean_type, not_found_mbean_list, mbean_path,
                             class_name=self.__class_name__, method_name=_method_name)

        method_helper = MBeanMethodHelper(mbean_instance, mbean_path)
        method_map = method_helper.get_attributes()

        # The main driver must have all attributes in the map
        mbi_helper = MBIHelper(mbean_instance, mbean_path)
        mbean_mbi_map = mbi_helper.get_all_attributes()

        attributes = all_utils.dict_obj()
        for attribute, attribute_helper in mbean_mbi_map.iteritems():
            self.__logger.finer('Processing MBean {0} attribute {1} from MBI map', mbean_type, attribute,
                                class_name=self.__class_name__, method_name=_method_name)
            info_attribute_helper = None
            if attribute in mbean_info_list:
                info_attribute_helper = mbean_info_map[attribute]
                mbean_info_list.remove(attribute)

            method_helper = None
            if attribute in method_map:
                method_helper = method_map[attribute]

            if attribute not in lsa_map:
                if self._is_valid_cmo_attribute(attribute_helper, info_attribute_helper):
                    self.__logger.fine('Adding MBean {0} attribute {1} from location {2} '
                                       'that is in MBI map and not in LSA map', mbean_type, attribute, mbean_path,
                                       class_name=self.__class_name__, method_name=_method_name)
                    holder = all_utils.dict_obj()
                    self.add_default_value(holder, lsa_map, attribute_helper, method_helper)
                    attribute_helper.generate_attribute(holder)
                    attributes[attribute] = all_utils.sort_dict(holder)
            else:
                not_found_mbean_list.remove(attribute)
                if self._is_valid_attribute(attribute, attribute_helper, info_attribute_helper):
                    self.__logger.finer('Adding MBean {0} attribute {1} from location {2} which is in LSA and MBI maps',
                                        mbean_type, attribute, mbean_path,
                                        class_name=self.__class_name__, method_name=_method_name)
                    holder = all_utils.dict_obj()
                    self.add_default_value(holder, lsa_map, attribute_helper, method_helper)
                    attribute_helper.generate_attribute(holder)
                    attributes[attribute] = all_utils.sort_dict(holder)

        for attribute in mbean_info_list:
            self.__logger.finer('Processing MBean {0} attribute {1} from MBeanInfo map',
                                mbean_type, attribute,
                                class_name=self.__class_name__, method_name=_method_name)
            if attribute in not_found_mbean_list:
                not_found_mbean_list.remove(attribute)
            attribute_helper = mbean_info_map[attribute]
            method_helper = None
            if attribute in method_map:
                method_helper = method_map[attribute]
            if self._is_valid_cmo_attribute(attribute_helper, method_helper):
                self.__logger.fine('Adding MBean {0} attribute {1} found in MBeanInfo but not MBI',
                                   mbean_type, attribute,
                                   class_name=self.__class_name__, method_name=_method_name)
                holder = all_utils.dict_obj()
                self.add_default_value(holder, lsa_map, attribute_helper, method_helper)
                attribute_helper.generate_attribute(holder)
                attributes[attribute] = all_utils.sort_dict(holder)

        for lsa_only in not_found_mbean_list:
            self.__logger.finer('Processing MBean {0} attribute {1} from LSA map', mbean_type, lsa_only,
                                class_name=self.__class_name__, method_name=_method_name)
            if lsa_only in operation_list:
                continue

            method_helper = None
            if lsa_only in method_map:
                method_helper = method_map[lsa_only]

            if lsa_only in mbean_info_map:
                attribute_helper = mbean_info_map[lsa_only]
                mbean_info_list.remove(lsa_only)
            elif method_helper is not None:
                attribute_helper = method_helper
            else:
                # Fake one up
                attribute_helper = mbi_helper.get_attribute(lsa_only)
            if self._is_valid_lsa(attribute_helper):
                self.__logger.fine('MBean {0} attribute {1} that is in LSA and not MBI is found in the MBeanInfo : {2}',
                                   mbean_type, lsa_only, Boolean(info_helper.get_attribute(lsa_only) is not None),
                                   class_name=self.__class_name__, method_name=_method_name)
                holder = all_utils.dict_obj()
                # Not all LSA with -rw- really are -rw-. Might need to add in a physical attempt to set
                # if to find attributes without a set method that CAN be set in offline.
                # However, I suspect that if no set method, then cannot RW
                self.add_default_value(holder, lsa_map, attribute_helper, method_helper)
                if attribute_helper.is_attribute_found():
                    self.__logger.finer('MBean {0} attribute {1} in LSA map will generate attribute info '
                                        'from additional helper', mbean_type, lsa_only,
                                        class_name=self.__class_name__, method_name=_method_name)
                    attribute_helper.generate_attribute(holder)
                else:
                    self.__logger.fine('MBean {0} attribute {1} is found only in the LSA map', mbean_type, lsa_only,
                                       class_name=self.__class_name__, method_name=_method_name)
                attributes[lsa_only] = all_utils.sort_dict(holder)

        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name)
        return all_utils.sort_dict(attributes)

    def __create_any_subfolders(self):
        _method_name = 'create_any_subfolders'
        subfolder_list = all_utils.dict_obj()
        operation_map = generator_wlst.ls_operations()
        # create_by_operation_list = HashSet(operation_map.keySet())
        # for operation in operation_map.keySet():
        #     if operation.startswith(CREATE) and not operation.endswith('FromBuiltin'):
        #         mbean_type = operation[len(CREATE):]
        #         name1, name2 = helper.mbean_name(mbean_type)
        #         if not do_operation(name1, operation) and not do_operation(name2, operation):
        #             create_by_operation_list.remove(operation)

        checklist = generator_wlst.lsc_modified()
        if checklist is None:
            self.__logger.fine('WLSDPLYST-01320', generator_wlst.current_path(), '',
                               class_name=self.__class_name__, method_name=_method_name)
            return subfolder_list

        for check in checklist:
            if check not in operation_map:
                name_list = generator_wlst.ls_mbean_names(check)
                if name_list is None:
                    self.__logger.finer('WLSDPLYST-01121', check, '',
                                       class_name=self.__class_name__, method_name=_method_name)
                    continue
                    # if empty, it returns a str

                if name_list and len(str(name_list).strip()) > 0:
                    subfolder_list[check] = name_list[0]

        child_types = generator_wlst.child_mbean_types()
        if child_types is not None:
            for child_type in child_types:
                if child_type not in subfolder_list:
                    name1, name2 = all_utils.mbean_name(child_type)
                    if generator_wlst.created(child_type, name1) or generator_wlst.created(child_type, name2):
                        name_list = generator_wlst.ls_mbean_names(child_type)
                        if name_list is not None and len(str(name_list).strip()) > 0:
                            subfolder_list[child_type] = name_list[0]

        return subfolder_list

    def generate_security_mbean(self, dictionary, mbean_type):
        dictionary[mbean_type][all_utils.TYPE] = 'Provider'
        types = generator_security_configuration.providers_map[mbean_type]
        curr_path = generator_wlst.current_path()
        generator_wlst.cd_mbean(curr_path + '/' + mbean_type)
        existing = generator_wlst.lsc()
        generator_wlst.cd_mbean(curr_path)
        for item in types:
            idx = item.rfind('.')
            short = item[idx + 1:]
            orig = generator_wlst.current_path()
            if short not in existing:
                mbean_instance = generator_wlst.created_security_provider(mbean_type, short, item)
                generator_wlst.cd_mbean(curr_path + '/' + mbean_type + '/' + short)
            else:
                mbean_instance = generator_wlst.get_mbean_proxy(curr_path + '/' + mbean_type + '/' + short)
            dictionary[mbean_type][item] = all_utils.dict_obj()
            dictionary[mbean_type][item][all_utils.ATTRIBUTES] = self.__get_attributes(mbean_instance)
            generator_wlst.cd_mbean(orig)
        generator_wlst.cd_mbean(curr_path)



