"""
Copyright (c) 2021, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Contains a boolean value that can be recognized by the YAML and JSON writers.
"""
from wlsdeploy.aliases import alias_utils


class BooleanValue(object):

    def __init__(self, value):
        self.value = alias_utils.convert_boolean(value)

    def get_value(self):
        return self.value

    def get_string_value(self):
        if self.value:
            return 'true'
        else:
            return 'false'
