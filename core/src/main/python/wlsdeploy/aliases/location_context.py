"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.util import unicode_helper as str_helper


class LocationContext(object):
    """
    Class that serves as the navigation context during model processing.
    """
    def __init__(self, another_location=None):
        """
        Creates a new instance of the object that serves as the
        navigation context during model processing.

        If ``another_location`` is None, then an empty list is
        stored in the list.
        :param another_location: list of folder names that are part of the model
        """
        if another_location is None:
            self._model_folders = list()
            self._name_tokens = dict()
        else:
            self._model_folders = another_location.get_model_folders()
            self._name_tokens = another_location.get_name_tokens()

    def append_location(self, *args, **kwargs):
        """
        Push (or append) a location to the existing location context
        :param args: arguments
        :param kwargs: named arguments
        :return: self, for method chaining
        """
        if len(args) != 0:
            self._model_folders.extend(args)

        if len(kwargs) != 0:
            for key in kwargs:
                self._name_tokens[key] = kwargs[key]
        return self

    def pop_location(self, index=None):
        """
        Pops (or removes) a location from the existing location context
        :param index: integer Index of list item to pop
        :return: The ``model_folder`` of list item at ``index``
        """
        if index is None:
            retval = self._model_folders.pop()
        else:
            retval = self._model_folders.pop(index)
        return retval

    def add_name_token(self, token, value):
        """
        Adds a token-value pair to the location context
        :param token: string Name to use for NV pair
        :param value: string Value to use for NV pair
        :return: self, for method chaining
        """
        self._name_tokens[token] = value
        return self

    def remove_name_token(self, token):
        """
        Removes a name-value pair to the location context
        :param token: string Name to use for NV pair
        :return: self, for method chaining
        """
        if token in self._name_tokens:
            del self._name_tokens[token]
        return self

    def get_name_for_token(self, token_name):
        """
        Return the name value for the provided token.
        :param token_name: token associated with the name value
        :return: name value or None if the token is not currently in the context
        """
        name_value = None
        if token_name in self._name_tokens:
            name_value = self._name_tokens[token_name]
        return name_value

    def get_model_folders(self):
        """
        Copy constructor for ``model_folder`` list of location context.

        NOTE: This method is not part of the public API.

        :return: new Python list built from ``self._model_folders``
        """
        return list(self._model_folders)

    def get_current_model_folder(self):
        """
        Return the current folder name for the location. This is the last folder in the location model folder
        list, or Domain if there is no current list of folders in the location.
        :return: return the current model folder name
        """
        model_folder = "Domain"
        model_folder_list = self.get_model_folders()
        if model_folder_list:
            model_folder = model_folder_list[-1]
        return model_folder

    def get_parent_folder_path(self):
        """
        Return the parent folder path for the location. This is the parent of the last folder or None if no parent.
        :return: return the parent folder path
        """
        result = None
        model_folder_list = self.get_model_folders()
        if model_folder_list:
            result = ''
            if len(model_folder_list) > 1:
                for folder in model_folder_list[-2]:
                    result += '/' + folder
            if len(result) == 0:
                result = '/'
        return result

    def get_name_tokens(self):
        """
        Copy constructor for ``name_tokens`` dictionary of location context.

        NOTE: This method is not part of the public API.

        :return: new Python dictionary built from ``self._name_tokens``
        """
        return dict(self._name_tokens)

    def get_folder_path(self):
        """
        Get the string that represents the model path specified by the model folders in this location
        :return: the string that represents the model path
        """
        result = ''
        for folder in self._model_folders:
            result += '/' + folder
        if len(result) == 0:
            result = '/'
        return result

    def is_empty(self):
        """
        Is the location empty?
        :return: True if there are no folders, False otherwise
        """
        return len(self._model_folders) == 0

    def __str__(self):
        location_model_folders = 'model_folders = %s' % (str_helper.to_string(self._model_folders))
        tmp = ''
        for key, value in self._name_tokens.iteritems():
            tmp += "'%s': '%s'," % (key, value)
        if len(tmp) > 0:
            tmp = tmp[:-1]
        location_name_tokens = " 'name_tokens' = {%s}" % tmp
        return '%s, %s' % (location_model_folders, location_name_tokens)

    def __unicode__(self):
        location_model_folders = u'model_folders = %s' % (str_helper.to_string(self._model_folders))
        tmp = u''
        for key in self._name_tokens.keys():
            value = self._name_tokens[key]
            tmp += u"'%s': '%s'," % (str_helper.to_string(key), str_helper.to_string(value))
        if len(tmp) > 0:
            tmp = tmp[:-1]
        location_name_tokens = u" 'name_tokens' = {%s}" % str_helper.to_string(tmp)
        return u'%s, %s' % (location_model_folders, location_name_tokens)

    def __len__(self):
        return len(self._model_folders)
