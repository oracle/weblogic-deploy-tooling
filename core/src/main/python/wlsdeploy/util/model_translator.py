"""
Copyright (c) 2017, 2021, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import java.io.File as JFile

import oracle.weblogic.deploy.json.JsonException as JJsonException
import oracle.weblogic.deploy.util.FileUtils as JFileUtils
import oracle.weblogic.deploy.yaml.YamlException as JYamlException

from wlsdeploy.logging import platform_logger
from wlsdeploy.exception import exception_helper
from wlsdeploy.util import model_config


class FileToPython(object):
    """
    Interface to parse the file contents into a python dictionary. The interface will determine the syntax of the
    contents of the file for the provided file name, and call the appropriate translator for that syntax.
    """
    _class_name = 'FileToPython'

    def __init__(self, file_name, use_ordering=False):
        self.file_name = file_name
        self.use_ordering = use_ordering
        self.logger = platform_logger.PlatformLogger('wlsdeploy.translator')
        self.model_config = model_config.get_model_config()

    def parse(self):
        """
        Based on the syntax of the file, parse the contents of the file into a python dictionary.
        :return: dictionary parsed from the file contents
        :raises TranslateException: if an error occurs
        """
        _method_name = 'parse'

        self.logger.entering(class_name=self._class_name, method_name=_method_name)
        # throws IllegalArgument if not a valid existing file
        model_file = JFileUtils.validateFileName(self.file_name)
        # yaml is the default. For now, if the file extension is not known, then parse the contents as yaml
        if JFileUtils.isJsonFile(model_file):
            result_dict = self._parse_json()
        else:
            result_dict = self._parse_yaml()

        # called method already logged result. don't log it again
        self.logger.exiting(class_name=self._class_name, method_name=_method_name)
        return result_dict

    def _parse_json(self):
        """
        Parse the JSON file and convert it into a Python dictionary.
        :return: the Python dictionary
        """
        _method_name = '_parse_json'

        from wlsdeploy.json.json_translator import JsonToPython as JJsonToPython
        self.logger.finer('WLSDPLY-03078', 'JSON', self.file_name,
                          class_name=self._class_name, method_name=_method_name)
        try:
            return JJsonToPython(self.file_name, self.use_ordering).parse()
        except JJsonException, je:
            translate_ex = exception_helper.create_translate_exception('WLSDPLY-01710', self.file_name,
                                                                       je.getLocalizedMessage(), error=je)
            self.logger.throwing(translate_ex, class_name=self._class_name, method_name=_method_name)
            raise translate_ex

    def _parse_yaml(self):
        """
        Parse the Yaml file and convert it into a Python dictionary.
        :return: the Python dictionary
        """
        _method_name = '_parse_yaml'

        from wlsdeploy.yaml.yaml_translator import YamlToPython
        self.logger.finer('WLSDPLY-01711', 'YAML', self.file_name,
                          class_name=self._class_name, method_name=_method_name)
        try:
            max_size = self.model_config.get_yaml_file_max_code_points()
            return YamlToPython(self.file_name, self.use_ordering, max_size).parse()
        except JYamlException, ye:
            translate_ex = exception_helper.create_translate_exception('WLSDPLY-01710', self.file_name,
                                                                       ye.getLocalizedMessage(), error=ye)
            self.logger.throwing(translate_ex, class_name=self._class_name, method_name=_method_name)
            raise translate_ex


class PythonToFile(object):
    """
    Interface to persist the python dictionary to the provided file name and location. The interface will
    determine the syntax required for the file, and call the appropriate translator for that syntax.
    """

    _class_name = 'PythonToFile'

    def __init__(self, dictionary):
        self.dictionary = dictionary
        self.logger = platform_logger.PlatformLogger('wlsdeploy.translator')

    def write_to_file(self, file_name):
        """
        Write the Python dictionary to a file.
        :param file_name: the file name
        :return: the java.io.File object
        """
        _method_name = 'writeToFile'
        self.logger.entering(file_name, class_name=self._class_name, method_name=_method_name)

        model_file = JFile(file_name)
        if JFileUtils.isYamlFile(model_file):
            return_file = self._write_to_yaml_file(file_name)
        else:
            return_file = self._write_to_json_file(file_name)

        # called method already logged the return_file. don't log again
        self.logger.exiting(class_name=self._class_name, method_name=_method_name)
        return return_file

    def _write_to_json_file(self, file_name):
        """
        Convert the Python dictionary to JSON and write it to a file.
        :param file_name: the JSON file name
        :return: the java.io.File object
        """
        _method_name = '_write_to_json_file'

        from wlsdeploy.json.json_translator import PythonToJson as JPythonToJson
        self.logger.finer('WLSDPLY-01712', 'JSON', file_name, class_name=self._class_name, method_name=_method_name)
        try:
            return JPythonToJson(self.dictionary).write_to_json_file(file_name)
        except JJsonException, je:
            translate_ex = exception_helper.create_translate_exception('WLSDPLY-01713', file_name,
                                                                       je.getLocalizedMessage(), error=je)
            self.logger.throwing(translate_ex, class_name=self._class_name, method_name=_method_name)
            raise translate_ex

    def _write_to_yaml_file(self, file_name):
        """
        Convert the Python dictionary to Yaml and write it to a file.
        :param file_name: the Yaml file name
        :return: the java.io.File object
        """
        _method_name = '_write_to_yaml_file'

        from wlsdeploy.yaml.yaml_translator import PythonToYaml as JPythonToYaml
        self.logger.finer('WLSDPLY-01712', 'YAML', file_name, class_name=self._class_name, method_name=_method_name)
        try:
            writer = JPythonToYaml(self.dictionary)
            writer.write_to_yaml_file(file_name)
        except JYamlException, ye:
            translate_ex = exception_helper.create_translate_exception('WLSDPLY-01713', file_name,
                                                                       ye.getLocalizedMessage(), error=ye)
            self.logger.throwing(translate_ex, class_name=self._class_name, method_name=_method_name)
            raise translate_ex
