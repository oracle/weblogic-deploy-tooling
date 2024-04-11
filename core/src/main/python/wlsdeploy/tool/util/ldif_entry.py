"""
Copyright (c) 2021, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import unicode_helper as str_helper

QUALIFIED_CN_REGEX = re.compile('(,|^)cn=([^,]*)(,|$)')
QUALIFY_VALUE_TEMPLATE = 'cn=%s,ou=groups,ou=@realm@,dc=@domain@'

__class_name = 'LDIFEntry'
__logger = PlatformLogger('wlsdeploy.tool.util')


class LDIFEntry(object):
    """
    This class represents a single LDIF entry in a file.
    It maintains a list of key/value attributes with access methods.
    """
    def __init__(self):
        self._lines = []

    def add_assignment_line(self, line):
        """
        Add a single text line containing "<key>: <value>" to the list.
        """
        self._lines.append(line)

    def get_assignment_lines(self):
        """
        :return: the list of assignment strings
        """
        return self._lines

    def get_single_value(self, key):
        for line in self._lines:
            a_key, value = _get_assignment(line)
            if a_key == key:
                return value
        return None

    def get_values(self, key):
        values = []
        for line in self._lines:
            a_key, value = _get_assignment(line)
            if a_key == key:
                values.append(value)
        return values

    def update_single_field(self, field_name, new_value):
        """
        Add or replace a single attribute assignment
        :param field_name: the name of the field
        :param new_value: the value of the field
        """
        new_lines = []
        found = False
        for line_text in self._lines:
            key, value = _get_assignment(line_text)
            if key == field_name:
                _add_assignment(field_name, new_value, new_lines)
                found = True
            else:
                new_lines.append(line_text)

        if not found:
            _add_assignment(field_name, new_value, new_lines)

        self._lines = new_lines

    def get_unqualified_names(self, key):
        names = []
        for line_text in self._lines:
            a_key, value = _get_assignment(line_text)
            if a_key == key:
                match = re.match(QUALIFIED_CN_REGEX, value)
                if match:
                    name = match.group(2)
                    names.append(name)
        return names

    def add_qualified_assignments(self, key, cn_names):
        existing_names = self.get_unqualified_names(key)

        for cn_name in cn_names:
            if cn_name not in existing_names:
                value = QUALIFY_VALUE_TEMPLATE % cn_name
                self.add_assignment(key, value)

    def add_assignment(self, key, value):
        _add_assignment(key, value, self._lines)


def read_entries(file):
    """
    Create a list of LDIF entries from a file.
    :param file: java.io.File containing original LDIF entries
    :return: the existing entries list
    """
    _method_name = 'read_entries'
    __logger.entering(file, class_name=__class_name, method_name=_method_name)

    reader = open(file.getPath(), 'r')
    all_lines = reader.readlines()
    reader.close()

    current_entry = None
    entries = []
    for line in all_lines:
        line_text = line.strip()
        if len(line_text) == 0:
            current_entry = None
        else:
            if current_entry is None:
                current_entry = LDIFEntry()
                entries.append(current_entry)
            current_entry.add_assignment_line(line_text)

    __logger.exiting(class_name=__class_name, method_name=_method_name, result=len(entries))
    return entries


def find_entry(cn_name, entries):
    for entry in entries:  # type: LDIFEntry
        for line in entry.get_assignment_lines():
            key, value = _get_assignment(line)
            if key == 'cn' and value == cn_name:
                return entry
    return None


def _add_assignment(key, value, lines):
    line = key + ': ' + str_helper.to_string(value)
    lines.append(line)


def _get_assignment(line):
    fields = line.split(':', 1)
    key = fields[0].strip()
    value = None
    if len(fields) > 1:
        value = fields[1]

        # some assignments are "key:: value", we return the key "key:"
        if value.startswith(':'):
            key += ':'
            value = value[1:]

        value = value.strip()

    return key, value
