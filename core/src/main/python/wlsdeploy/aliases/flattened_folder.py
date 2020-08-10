"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""


class FlattenedFolder(object):
    """
    Class containing information for processing a flattened folder.
    """
    def __init__(self, mbean_type, mbean_name, path_token):
        """
        Creates a new instance of the object containing flattened folder information.
        :param mbean_type: the type of the MBean represented by the folder
        :param mbean_name: the name of the MBean represented by the folder
        :param path_token: the path token used to update the location context
        """
        self.mbean_type = mbean_type
        self.mbean_name = mbean_name
        self.path_token = path_token

    def get_mbean_type(self):
        """
        Get the MBean type for the flattened folder.
        :return: the MBean type
        """
        return self.mbean_type

    def get_mbean_name(self):
        """
        Get the MBean name for the flattened folder.
        :return: the MBean name
        """
        return self.mbean_name

    def get_path_token(self):
        """
        Get the path token for the flattened folder.
        :return: the path token
        """
        return self.path_token
