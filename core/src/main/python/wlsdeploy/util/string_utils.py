"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0

This module provides string manipulation helper methods that are not found in the WLST version of Jython
"""
from wlsdeploy.logging.platform_logger import PlatformLogger

__logger = PlatformLogger('wlsdeploy.util')
_class_name = 'string_utils'

def is_empty(text):
    """
    Determine if a string value is either None or an empty string.
    :param text: the string to test
    :return: True, if the string has no content, False otherwise
    """
    return text is None or len(text) == 0

def rsplit(text, token=' ', maxsplit=-1):
    """
    Returns a list of the words in the provided string, separated by the delimiter string (starting from right).
    :param text: the string should be rsplit
    :param token: token dividing the string into split groups; default is space.
    :param maxsplit: Number of splits to do; default is -1 which splits all the items.
    :return: list of string elements
    """
    if maxsplit == 0:
        result = [text]
    else:
        components = text.split(token)
        if maxsplit > 0:
            desired_length = maxsplit + 1
            result = []
            if len(components) > desired_length:
                result.append('')
                for index, value in enumerate(components):
                    if index < len(components) - maxsplit:
                        if index > 0:
                            result[0] += token
                        result[0] += value
                    else:
                        result.append(value)
        else:
            result = components
    return result

def to_boolean(input_value):
    """
    Convert the input value to a proper boolean value.
    :param input_value: the value to convert
    :return: the corresponding boolean value, or False if the value is not convertible to a boolean
    """
    _method_name = 'to_boolean'

    if input_value in ['True', 'true', 1]:
        result = True
    elif input_value in ['False', 'false', 0]:
        result = False
    else:
        __logger.fine('WLSDPLY-01720', input_value, class_name=_class_name, method_name=_method_name)
        result = False
    return result
