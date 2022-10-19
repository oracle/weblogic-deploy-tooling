"""
Copyright (c) 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.util import dictionary_utils

NO_FOLDER_KEY = "__NO_KEY__"


class ModelCrdFolder:
    """
    A model folder that represents the schema for a CRD document.
    """
    _class_name = "ModelCrdFolder"

    def __init__(self, model_key, schema, is_array):
        self._model_key = model_key
        self._schema = schema
        self._is_array = is_array
        self._object_list_keys = {}

    def get_model_key(self):
        return self._model_key

    def is_array(self):
        return self._is_array

    def get_schema(self):
        return self._schema

    def has_model_key(self):
        return self._model_key != NO_FOLDER_KEY

    # some object list members don't use 'name' as a key.
    # we need to know the key in order to merge object lists correctly.

    def add_object_list_key(self, schema_path, key):
        self._object_list_keys[schema_path] = key

    def get_object_list_key(self, schema_path):
        """
        Return the name of the attribute that acts as a key for objects in an object list.
        In most cases, this is 'name', but there are a few exceptions.
        :param schema_path: the path to be checked
        :return: the object key
        """
        mapped_key = dictionary_utils.get_element(self._object_list_keys, schema_path)
        if mapped_key is not None:
            return mapped_key
        return 'name'
