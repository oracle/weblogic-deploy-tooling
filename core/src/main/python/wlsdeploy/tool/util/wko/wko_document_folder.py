"""
Copyright (c) 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.tool.util.wko import wko_schema_helper


class WkoDocumentFolder:
    """
    A model folder that corresponds to a schema for a CRD document.
    """
    _class_name = "WkoDocumentFolder"

    def __init__(self, model_key, schema, is_array):
        self._model_key = model_key
        self._schema = schema
        self._is_array = is_array

    def get_model_key(self):
        return self._model_key

    def is_array(self):
        return self._is_array

    def get_schema(self):
        return self._schema

    def has_model_key(self):
        return self._model_key != wko_schema_helper.NO_DOC_FOLDER_KEY
