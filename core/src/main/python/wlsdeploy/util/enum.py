"""
Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from oracle.weblogic.deploy.exception import ExceptionHelper


class Enum(object):
    """
    A class that can be extended to implement Enums in Jython 2.2.1
    """
    def __init__(self, enum_list):
        self.enum_list = enum_list
        self.current = 0

    def __getattr__(self, name):
        if name in self.enum_list:
            return self.enum_list.index(name)
        raise AttributeError

    def __str__(self):
        tmp = ""
        for name in self.enum_list:
            tmp += "'key': '%s', 'value': %d," % (name, self.enum_list.index(name))

        if len(tmp) > 0:
            tmp = tmp[:-1]
        return "{" + tmp + "}"

    def __iter__(self):
        return self

    def __contains__(self, name):
        return name in self.enum_list

    def __getitem__(self, name):
        return self.enum_list.index(name)

    def next(self):
        if self.current < len(self.enum_list):
            result = self.enum_list[self.current]
            self.current += 1
            return result

    def values(self):
        """
        Get the list of all enum field names
        :return: the list of actual enum field names
        """
        return list(self.enum_list)

    def from_value(self, value):
        """
        Get the actual enum field name associated with the specified value.
        :param value: the value
        :return: the enum field name
        :raises: ValueError: If the value is not a valid value for the Enum
        """
        if value not in range(0, len(self.enum_list)):
            message = ExceptionHelper.getMessage('WLSDPLY-01700', value, self.__class__.__name__)
            raise ValueError(message)
        return self.enum_list[value]
