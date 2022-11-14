"""
Copyright (c) 2019, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Module to handle translating between Yaml files and Python dictionaries.
"""
import java.io.FileNotFoundException as JFileNotFoundException
import java.io.FileWriter as JFileWriter
import java.io.IOException as JIOException
import java.lang.Boolean as JBoolean
import java.lang.Double as JDouble
import java.lang.IllegalArgumentException as JIllegalArgumentException
import java.lang.Integer as JInteger
import java.lang.Long as JLong
import java.lang.String as JString
import java.util.ArrayList as JArrayList
from java.io import OutputStreamWriter

import oracle.weblogic.deploy.util.FileUtils as JFileUtils
import oracle.weblogic.deploy.yaml.YamlStreamTranslator as JYamlStreamTranslator
import oracle.weblogic.deploy.yaml.YamlTranslator as JYamlTranslator
from oracle.weblogic.deploy.util import OrderedMap
from oracle.weblogic.deploy.util import PyRealBoolean
from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
import wlsdeploy.util.unicode_helper as str_helper


class YamlToPython(object):
    """
    A class that translates a YAML file into a python dictionary.
    """
    _class_name = 'YamlToPython'

    def __init__(self, file_name, use_ordering=False, max_size=0):
        _method_name = '__init__'

        self._file_name = file_name
        self._use_ordering = use_ordering
        self._use_unicode = str_helper.use_unicode()
        self._logger = PlatformLogger('wlsdeploy.yaml')
        try:
            self._translator = JYamlTranslator(self._file_name, self._use_ordering, self._use_unicode, max_size)
        except JIllegalArgumentException, iae:
            yaml_ex = \
                exception_helper.create_yaml_exception('WLSDPLY-18008', file_name, iae.getLocalizedMessage(), error=iae)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=yaml_ex)
            raise yaml_ex

    def parse(self):
        """
        Parse the Yaml content from the file and convert it to a Python dictionary.
        :return: the Python dictionary
        :raises: YamlException: if an error occurs while parsing the Yaml or converting it to the dictionary
        """
        _method_name = 'parse'

        self._logger.entering(class_name=self._class_name, method_name=_method_name)
        # throws YamlException with details, nothing we can really add here...
        result_dict = self._translator.parse()

        # don't log the model on exit, it may contain passwords
        self._logger.exiting(class_name=self._class_name, method_name=_method_name)
        return result_dict

    def parse_documents(self):
        """
        Parse the Yaml content from the file and convert it to a list of Python dictionaries.
        :return: a list of documents as Python dictionaries
        :raises: YamlException: if an error occurs while parsing the Yaml or converting it to the list
        """
        _method_name = 'parse_documents'

        self._logger.entering(class_name=self._class_name, method_name=_method_name)
        # throws YamlException with details, nothing we can really add here...
        result_dict = self._translator.parseDocuments(True)

        # don't log the model on exit, it may contain passwords
        self._logger.exiting(class_name=self._class_name, method_name=_method_name)
        return result_dict


class YamlStreamToPython(object):
    """
    A class that translates a YAML input stream into a python dictionary.
    """
    _class_name = 'YamlStreamToPython'

    def __init__(self, file_name, input_stream, use_ordering=False, max_size=0):
        _method_name = '__init__'

        self._file_name = file_name
        self._use_ordering = use_ordering
        self._use_unicode = str_helper.use_unicode()
        self._logger = PlatformLogger('wlsdeploy.yaml')
        try:
            self._translator = JYamlStreamTranslator(self._file_name, input_stream, self._use_ordering,
                                                     self._use_unicode, max_size)
        except JIllegalArgumentException, iae:
            yaml_ex = \
                exception_helper.create_yaml_exception('WLSDPLY-18008', file_name, iae.getLocalizedMessage(), error=iae)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=yaml_ex)
            raise yaml_ex

    def parse(self):
        """
        Parse the Yaml content from the input stream and convert it to a Python dictionary.
        :return: the Python dictionary
        :raises: YamlException: if an error occurs while parsing the Yaml or converting it to the dictionary
        """
        _method_name = 'parse'

        self._logger.entering(class_name=self._class_name, method_name=_method_name)
        # throws YamlException with details, nothing we can really add here...
        result_dict = self._translator.parse()
        self._logger.exiting(class_name=self._class_name, method_name=_method_name)
        return result_dict


class PythonToJava(object):
    """
    A class that converts a Python dictionary or document list and its contents
    to the Java types expected by snakeyaml.
    """
    _class_name = 'PythonToJava'

    def __init__(self, collection):
        self._collection = collection
        self._logger = PlatformLogger('wlsdeploy.yaml')

    def convert_to_java(self):
        _method_name = 'convert_to_java'

        if self._collection is None:
            return None
        if isinstance(self._collection, dict):
            return self.convert_dict_to_java_map(self._collection)
        if isinstance(self._collection, list):
            return self.convert_list_to_java_list(self._collection)
        else:
            yaml_ex = exception_helper.create_yaml_exception('WLSDPLY-18200')
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=yaml_ex)
            raise yaml_ex

    def convert_dict_to_java_map(self, dictionary):
        result = OrderedMap()
        if isinstance(dictionary, PyOrderedDict):
            result.setCommentMap(dictionary.getCommentMap())

        for key, value in dictionary.iteritems():
            java_key = JString(key)
            if isinstance(value, dict):
                java_value = self.convert_dict_to_java_map(value)
                result.put(java_key, java_value)
            elif isinstance(value, list):
                java_value = self.convert_list_to_java_list(value)
                result.put(java_key, java_value)
            else:
                java_value = self.convert_scalar_to_java_type(value)
                result.put(java_key, java_value)
        return result

    def convert_list_to_java_list(self, py_list):
        result = JArrayList()
        for value in py_list:
            if isinstance(value, dict):
                java_value = self.convert_dict_to_java_map(value)
                result.add(java_value)
            elif isinstance(value, list):
                java_value = self.convert_list_to_java_list(value)
                result.add(java_value)
            else:
                java_value = self.convert_scalar_to_java_type(value)
                result.add(java_value)
        return result

    def convert_scalar_to_java_type(self, py_value):
        _method_name = 'convert_scalar_to_java_type'

        result = None
        if py_value is None:
            result = None
        elif type(py_value) is bool:
            result = JBoolean(py_value is True)
        elif type(py_value) in [str, unicode]:
            result = JString(py_value)
        elif type(py_value) is int:
            result = JInteger(py_value)
        elif type(py_value) is long:
            result = JLong(JString(str_helper.to_string(py_value)))
        elif type(py_value) is float:
            result = JDouble(py_value)
        elif isinstance(py_value, PyRealBoolean):
            result = JBoolean(py_value.getValue())
        else:
            yaml_ex = exception_helper.create_yaml_exception('WLSDPLY-18201', type(py_value))
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=yaml_ex)
            raise yaml_ex
        return result


class PythonToYaml(object):
    """
    A class that converts a Python dictionary or document list into Yaml and writes the output to a file.
    """
    _class_name = 'PythonToYaml'

    def __init__(self, collection):
        # Fix error handling for None
        self._collection = collection
        self._logger = PlatformLogger('wlsdeploy.yaml')

    def write_to_yaml_file(self, file_name):
        """
        Convert the Python dictionary to Yaml and write it to the specified file.
        :param file_name: the file name to which to write the Yaml output
        :return: The canonical java.io.File object for the Yaml File
        :raises: YamlException: if an error occurs while converting the dictionary to Yaml or writing to the file
        """
        _method_name = 'writeToYamlFile'

        self._logger.entering(file_name, class_name=self._class_name, method_name=_method_name)
        try:
            yaml_file = JFileUtils.validateWritableFile(file_name)
        except JIllegalArgumentException, iae:
            yaml_ex = exception_helper.create_yaml_exception('WLSDPLY-18009', file_name,
                                                             iae.getLocalizedMessage(), error=iae)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=yaml_ex)
            raise yaml_ex

        writer = None
        try:
            writer = JFileWriter(yaml_file)
            self._write_collection_to_yaml_file(self._collection, writer, file_name)
        except JFileNotFoundException, fnfe:
            yaml_ex = exception_helper.create_yaml_exception('WLSDPLY-18010', file_name,
                                                             fnfe.getLocalizedMessage(), error=fnfe)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=yaml_ex)
            self._close_writer(writer)
            raise yaml_ex
        except JIOException, ioe:
            yaml_ex = exception_helper.create_yaml_exception('WLSDPLY-18011', file_name,
                                                             ioe.getLocalizedMessage(), error=ioe)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=yaml_ex)
            self._close_writer(writer)
            raise yaml_ex

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def write_to_stream(self, output_stream):
        self._write_collection_to_yaml_file(self._collection, OutputStreamWriter(output_stream))

    def _write_collection_to_yaml_file(self, collection, writer, file_name='<None>'):
        """
        Do the actual heavy lifting of converting a dictionary or document list and writing it to the file.
        :param collection: the Python dictionary or document list to convert
        :param writer: the java.io.Writer for the output file
        :param file_name: the file_name for the output file
        :raises: YamlException: if an error occurs while writing the output
        """
        if collection is None:
            return

        java_object = PythonToJava(collection).convert_to_java()
        yaml_stream_translator = JYamlStreamTranslator(file_name, writer)

        if isinstance(collection, list):
            yaml_stream_translator.dumpDocuments(java_object)
        else:
            yaml_stream_translator.dump(java_object)

    def _close_writer(self, writer):
        """
        Method used to simplify closing output streams since WLST Jython does not support finally blocks...
        :param writer: the print writer
        """

        if writer is not None:
            writer.close()
