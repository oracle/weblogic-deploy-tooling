"""
Copyright (c) 2021, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import java.lang.Boolean as Boolean

from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.logging.platform_logger import PlatformLogger

import aliastest.generate.generator_security_configuration as generator_security_configuration
import aliastest.generate.generator_wlst as generator_wlst
import aliastest.generate.utils as generator_utils

from aliastest.generate.generator_base import GeneratorBase
from aliastest.generate.mbean_info_helper import MBeanInfoHelper
from aliastest.generate.mbean_method_helper import MBeanMethodHelper
from aliastest.generate.mbi_helper import MBIHelper

ATTRIBUTES = generator_utils.ATTRIBUTES
FALSE = 'false'
INSTANCE_TYPE = generator_utils.INSTANCE_TYPE
MULTIPLE = generator_utils.MULTIPLE
ONLINE_REFERENCE_ONLY = 'reference_only'
RECHECK = generator_utils.RECHECK
SINGLE = generator_utils.SINGLE
SINGLE_NO_NAME = generator_utils.SINGLE_NO_NAME
TRUE = 'true'
TYPE = generator_utils.TYPE

NOT_SINGLE_INSTANCE = [
 'AppDeployments',
 'Libraries'
]

STRIP_FROM_GENERATED_FILE = {
    'Servers': {
        'ServerDebug': {
            'attributes': ['DebugJAXPOutputStream', 'DebugXMLEntityCacheOutputStream', 'DebugXMLRegistryOutputStream']
        }
    },
    'ServerTemplates': {
        'ServerDebug': {
            'attributes': ['DebugJAXPOutputStream', 'DebugXMLEntityCacheOutputStream', 'DebugXMLRegistryOutputStream']
        }
    },
    'WTCServers': {
        'attributes': ['Resource', 'tBridgeGlobal']
    }
}


class OnlineGenerator(GeneratorBase):
    """
    Generate MBean and attribute information and store into a dictionary.
    The data is traversed using the registered mbean information for the online session.
    """
    __logger = PlatformLogger('test.aliases.generate.online')

    def __init__(self, model_context, sc_providers):
        super(OnlineGenerator, self).__init__(model_context, PyOrderedDict())
        self.__class_name = self.__class__.__name__
        self._sc_providers = sc_providers

    def generate(self):
        """
        Generate the mbean dictionary for weblogic in wlst online mode.
        :return: the domain home of the connected session
        """
        _method_name = 'generate'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        self.__folder_hierarchy(self._dictionary, '/')
        self.__clean_dictionary(self._dictionary, STRIP_FROM_GENERATED_FILE)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return self._dictionary

    def __clean_dictionary(self, dictionary, remove_dict):
        _method_name = '__clean_dictionary'
        self.__logger.entering(class_name=self.__class_name, method_name=_method_name)

        for key, remove_value in remove_dict.iteritems():
            self.__logger.finest('key = {0} and remove_value ({1}) = {2}', key, type(remove_value), remove_value,
                                 class_name=self.__class_name, method_name=_method_name)
            if key == 'attributes':
                for attribute in remove_value:
                    self.__logger.finest('attribute = {0}', attribute,
                                         class_name=self.__class_name, method_name=_method_name)
                    if attribute in dictionary['attributes']:
                        self.__logger.finest('Found attribute {0} in dictionary', attribute,
                                             class_name=self.__class_name, method_name=_method_name)
                        del dictionary['attributes'][attribute]
                    else:
                        self.__logger.finest('Attribute {0} not found in dictionary', attribute,
                                             class_name=self.__class_name, method_name=_method_name)
            elif key in dictionary:
                self.__logger.finest('key {0} in dictionary', key,
                                     class_name=self.__class_name, method_name=_method_name)
                if isinstance(remove_value, dict):
                    self.__logger.finest('remove_value for key {0} is dictionary so making recursive call', key,
                                         class_name=self.__class_name, method_name=_method_name)
                    self.__clean_dictionary(dictionary[key], remove_value)
                else:
                    self.__logger.finest('remove_value for key {0} is unexpected type {1}', key, type(remove_value),
                                         class_name=self.__class_name, method_name=_method_name)
            else:
                self.__logger.finest('key {0} is not in dictionary so skipping', key,
                                     class_name=self.__class_name, method_name=_method_name)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def __folder_hierarchy(self, mbean_dictionary, mbean_path):
        _method_name = '__folder_hierarchy'
        self.__logger.entering(mbean_path, class_name=self.__class_name, method_name=_method_name)

        mbean_instance = generator_wlst.get_mbean_proxy(mbean_path)
        mbean_dictionary[ATTRIBUTES] = self.__get_attributes(mbean_instance)
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
                                     mbean_type, class_name=self.__class_name, method_name=_method_name)
            else:
                self.__logger.fine('Child MBean {0} is in the MBI information but not the MBeanInfo information',
                                   mbean_type, class_name=self.__class_name, method_name=_method_name)

            if attribute_helper.is_reference_only():
                mbean_dictionary[mbean_type] = PyOrderedDict()
                # This non-attribute might have been added as a folder, which it is not
                mbean_dictionary[mbean_type][ONLINE_REFERENCE_ONLY] = TRUE
                continue

            if self._is_valid_folder(attribute_helper):
                self.__logger.fine('Generating information for mbean {0} at location {1}', mbean_type,
                                   generator_wlst.current_path(),
                                   class_name=self.__class_name, method_name=_method_name)

                mbean_dictionary[mbean_type] = PyOrderedDict()
                if mbean_type in generator_security_configuration.PROVIDERS:
                    self.generate_security_mbean(mbean_dictionary, mbean_type)
                else:
                    attribute_helper.generate_mbean(mbean_dictionary[mbean_type])
                    if mbean_name is None:
                        mbean_name = generator_wlst.get_singleton_name(mbean_type)
                    if mbean_name is not None:
                        if mbean_type in generator_wlst.child_mbean_types() or mbean_type in NOT_SINGLE_INSTANCE:
                            mbean_dictionary[mbean_type][INSTANCE_TYPE] = MULTIPLE
                        else:
                            mbean_dictionary[mbean_type][INSTANCE_TYPE] = SINGLE
                        bean_dir = mbean_type + '/' + mbean_name
                        if not generator_wlst.cd_mbean(bean_dir):
                            self.__logger.fine('Unable to create and navigate to mbean type {0} at location {1}',
                                               mbean_type, generator_wlst.current_path(),
                                               class_name=self.__class_name, method_name=_method_name)
                            mbean_dictionary[mbean_type][RECHECK] = 'cd to mbean and mbean name returned exception'
                            continue

                        self.__folder_hierarchy(mbean_dictionary[mbean_type], generator_wlst.current_path())
                        generator_wlst.cd_mbean('../..')
            else:
                # make this a real message
                self.__logger.warning('Ignore invalid MBean folder {0} containment : {1}, deprecated : {2}',
                                      mbean_type, generator_utils.str_bool(attribute_helper.is_containment()),
                                      generator_utils.str_bool(attribute_helper.is_deprecated()),
                                      class_name=self.__class_name, method_name=_method_name)

        if len(mbean_map) > 0:
            mbeans_only = [leftover for leftover in mbean_map if leftover not in mbi_helper.get_all_attributes()]
            if len(mbeans_only) > 0:
                for mbean_type in mbeans_only:
                    # If it is in the attribute list, its a reference
                    if mbi_helper.get_all_attribute(mbean_type).is_attribute_found() is False:
                        self.__logger.fine('MBean {0} was not found in the MBI map but is in the LSC map',
                                           mbean_type, class_name=self.__class_name, method_name=_method_name)
                        info_attribute_helper = info_helper.get_child_mbean(mbean_type)
                        if info_attribute_helper.is_attribute_found():
                            self.__logger.fine(
                                'Child MBean {0} is in the MBeanInfo information but not the MBI information',
                                mbean_type, class_name=self.__class_name, method_name=_method_name)
                        mbean_name = mbean_map[mbean_type]
                        if mbean_name is not None:
                            bean_dir = mbean_type + '/' + mbean_name
                            mbean_dictionary[mbean_type] = PyOrderedDict()
                            if generator_wlst.cd_mbean(bean_dir) is False:
                                self.__logger.fine('Unable to create and navigate to mbean type {0} at location {1}',
                                                   mbean_type, generator_wlst.current_path(),
                                                   class_name=self.__class_name, method_name=_method_name)
                                mbean_dictionary[mbean_type][RECHECK] = 'cd to mbean and mbean name returned exception'
                                continue

                            self.__folder_hierarchy(mbean_dictionary[mbean_type], generator_wlst.current_path())
                            generator_wlst.cd_mbean('../..')

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def __get_attributes(self, mbean_instance):
        _method_name = '__get_attributes'
        mbean_path = generator_wlst.current_path()
        self.__logger.entering(mbean_instance, mbean_path, class_name=self.__class_name, method_name=_method_name)

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
                             class_name=self.__class_name, method_name=_method_name)

        method_helper = MBeanMethodHelper(mbean_instance, mbean_path)
        method_map = method_helper.get_attributes()

        # The main driver must have all attributes in the map
        mbi_helper = MBIHelper(mbean_instance, mbean_path)
        mbean_mbi_map = mbi_helper.get_all_attributes()

        attributes = PyOrderedDict()
        for attribute, attribute_helper in mbean_mbi_map.iteritems():
            self.__logger.finer('Processing MBean {0} attribute {1} from MBI map', mbean_type, attribute,
                                class_name=self.__class_name, method_name=_method_name)
            info_attribute_helper = None
            if attribute in mbean_info_list:
                info_attribute_helper = mbean_info_map[attribute]
                mbean_info_list.remove(attribute)

            method_helper = None
            if attribute in method_map:
                method_helper = method_map[attribute]

            if attribute not in lsa_map:
                if attribute_helper.is_reference_only():
                    self.__logger.fine(
                        'Excluding transient MBean {0} attribute {1} from location {2}'
                        ' that is in MBI map and not in LSA map', mbean_type, attribute, mbean_path,
                        class_name=self.__class_name, method_name=_method_name)

                # if attribute is not in LSA, see if it is a valid CMO attribute and add it.
                # transient attributes (is_reference_only) that are not in the LSA map
                # should be excluded at this point.
                if self._is_valid_cmo_attribute(attribute_helper, info_attribute_helper) and \
                        not attribute_helper.is_reference_only():
                    self.__logger.fine(
                        'Adding MBean {0} attribute {1} from location {2} that is in MBI map and not in LSA map',
                        mbean_type, attribute, mbean_path, class_name=self.__class_name, method_name=_method_name)
                    holder = PyOrderedDict()
                    self.add_default_value(holder, lsa_map, attribute_helper, method_helper)
                    self.add_derived_default(holder, attribute_helper, attribute)
                    attribute_helper.generate_attribute(holder)
                    attributes[attribute] = generator_utils.sort_dict(holder)
            else:
                not_found_mbean_list.remove(attribute)
                if self._is_valid_attribute(attribute, attribute_helper, info_attribute_helper):
                    self.__logger.finer('Adding MBean {0} attribute {1} from location {2} which is in LSA and MBI maps',
                                        mbean_type, attribute, mbean_path,
                                        class_name=self.__class_name, method_name=_method_name)
                    holder = PyOrderedDict()
                    self.add_default_value(holder, lsa_map, attribute_helper, method_helper)
                    self.add_derived_default(holder, info_attribute_helper, attribute)
                    attribute_helper.generate_attribute(holder)
                    attributes[attribute] = generator_utils.sort_dict(holder)

        for attribute in mbean_info_list:
            self.__logger.finer('Processing MBean {0} attribute {1} from MBeanInfo map', mbean_type, attribute,
                                class_name=self.__class_name, method_name=_method_name)
            if attribute in not_found_mbean_list:
                not_found_mbean_list.remove(attribute)
            attribute_helper = mbean_info_map[attribute]
            method_helper = None
            if attribute in method_map:
                method_helper = method_map[attribute]
            if self._is_valid_cmo_attribute(attribute_helper, method_helper):
                self.__logger.fine('Adding MBean {0} attribute {1} found in MBeanInfo but not MBI',
                                   mbean_type, attribute,
                                   class_name=self.__class_name, method_name=_method_name)
                holder = PyOrderedDict()
                self.add_default_value(holder, lsa_map, attribute_helper, method_helper)
                self.add_derived_default(holder, info_attribute_helper, attribute)
                attribute_helper.generate_attribute(holder)
                attributes[attribute] = generator_utils.sort_dict(holder)

        for lsa_only in not_found_mbean_list:
            self.__logger.finer('Processing MBean {0} attribute {1} from LSA map', mbean_type, lsa_only,
                                class_name=self.__class_name, method_name=_method_name)
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
                                   class_name=self.__class_name, method_name=_method_name)
                holder = PyOrderedDict()
                # Not all LSA with -rw- really are -rw-. Might need to add in a physical attempt to set
                # if to find attributes without a set method that CAN be set in offline.
                # However, I suspect that if no set method, then cannot RW
                self.add_default_value(holder, lsa_map, attribute_helper, method_helper)
                self.add_derived_default(holder, info_attribute_helper, attribute)
                if attribute_helper.is_attribute_found():
                    self.__logger.finer('MBean {0} attribute {1} in LSA map will generate attribute info '
                                        'from additional helper', mbean_type, lsa_only,
                                        class_name=self.__class_name, method_name=_method_name)
                    attribute_helper.generate_attribute(holder)
                else:
                    self.__logger.fine('MBean {0} attribute {1} is found only in the LSA map', mbean_type, lsa_only,
                                       class_name=self.__class_name, method_name=_method_name)
                attributes[lsa_only] = generator_utils.sort_dict(holder)

        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return generator_utils.sort_dict(attributes)

    def __create_any_subfolders(self):
        _method_name = 'create_any_subfolders'

        subfolder_list = PyOrderedDict()
        operation_map = generator_wlst.ls_operations()
        checklist = generator_wlst.lsc_modified()
        if checklist is None:
            self.__logger.fine('Invalid mbean at location {0}', generator_wlst.current_path(),
                               class_name=self.__class_name, method_name=_method_name)
            return subfolder_list

        for check in checklist:
            if check not in operation_map:
                name_list = generator_wlst.ls_mbean_names(check)
                if name_list is None:
                    self.__logger.finer('Folder name {0} returned in subfolder map but is not an mbean', check,
                                        class_name=self.__class_name, method_name=_method_name)
                    continue
                    # if empty, it returns a str

                if name_list and len(str(name_list).strip()) > 0:
                    subfolder_list[check] = name_list[0]

        child_types = generator_wlst.child_mbean_types()
        if child_types is not None:
            for child_type in child_types:
                if child_type not in subfolder_list:
                    name1, name2 = generator_utils.mbean_name(child_type)
                    if generator_wlst.created(child_type, name1) or generator_wlst.created(child_type, name2):
                        name_list = generator_wlst.ls_mbean_names(child_type)
                        if name_list is not None and len(str(name_list).strip()) > 0:
                            subfolder_list[child_type] = name_list[0]

        return subfolder_list

    def generate_security_mbean(self, dictionary, mbean_type):
        dictionary[mbean_type][TYPE] = 'Provider'
        provider_subtypes = self._sc_providers[mbean_type]
        curr_path = generator_wlst.current_path()
        generator_wlst.cd_mbean(curr_path + '/' + mbean_type)
        existing = generator_wlst.lsc()
        generator_wlst.cd_mbean(curr_path)
        for provider_subtype in provider_subtypes:
            idx = provider_subtype.rfind('.')
            name = provider_subtype[idx + 1:]
            orig = generator_wlst.current_path()
            if name not in existing:
                mbean_instance = generator_wlst.create_security_provider(name, provider_subtype, mbean_type)
                generator_wlst.cd_mbean(curr_path + '/' + mbean_type + '/' + name)
            else:
                mbean_instance = generator_wlst.get_mbean_proxy(curr_path + '/' + mbean_type + '/' + name)
            dictionary[mbean_type][provider_subtype] = PyOrderedDict()
            dictionary[mbean_type][provider_subtype][ATTRIBUTES] = self.__get_attributes(mbean_instance)
            generator_wlst.cd_mbean(orig)
        generator_wlst.cd_mbean(curr_path)



