"""
Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from wlsdeploy.logging.platform_logger import PlatformLogger
import wlsdeploy.util.model as model_sections

_class_name = 'ModelSearchHelper'
_logger = PlatformLogger('wlsdeploy.util')


class ModelSearchHelper(object):
    """
    Class functions to facilitate searching the model.
    """

    def __init__(self, model):
        """
        Encapsulate the model on which to perform searches.
        :param model: to encapsulate
        """
        self.__model = model

    def locate_attribute_value(self, section, attribute_path):
        """
        Locate and return the dictionary entry for the attribute and value using the provided search pattern.
        <section>:<alias mbean>[.<alias mbean>...].<alias attribute>[.${search pattern}]
        where section is a section of the model, and the mbean is the path of mbeans that contains the attribute and
        search pattern is a key=value pair within the attribute's value.
        The model is traversed down to the
        :param section:
        :param attribute_path:
        :return:
        """
        _method_name = 'locate_attribute_value'
        _logger.entering(attribute_path, class_name=_class_name, method_name=_method_name)
        if section in model_sections.get_model_top_level_keys():
            model_section = self.__model[section]
            mbean_list, attribute_name = _split_attribute_path(attribute_path)
            for entry in mbean_list:
                if entry in model_section:
                    model_section = model_section[entry]
                else:
                    _logger.warning('WLSDPLY-19406', entry, attribute_path, section)
                    break



        _logger.exiting(class_name=_class_name, method_name=_method_name)


def _split_section(attribute_path):
    """
    Split the section from the attribute path.
    :param attribute_path:
    :return:
    """
    split_list = attribute_path.split(':', 1)
    section = None
    attribute = None
    segment = None
    if len(split_list) == 2 and split_list[0] in model_sections.get_model_top_level_keys():
        section = split_list[0]
        attribute_split_list = split_list[1].split('${')
        attribute = attribute_split_list[0]
        if len(attribute_split_list) == 2:
            segment = attribute_split_list[1][:len(attribute_split_list[1])-1]
    return section, attribute, segment


def _split_attribute_path(attribute_path):
    mbean_list = attribute_path.split('.')
    attribute = None
    if len(mbean_list) > 0:
        attribute = mbean_list.pop()
    return mbean_list, attribute
