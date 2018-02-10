"""
Module to handle translating between Yaml files and Python dictionaries.
"""
import re

import java.io.FileNotFoundException as JFileNotFoundException
import java.io.FileOutputStream as JFileOutputStream
import java.io.IOException as JIOException
import java.io.PrintWriter as JPrintWriter
import java.lang.IllegalArgumentException as JIllegalArgumentException

import oracle.weblogic.deploy.util.FileUtils as JFileUtils
import oracle.weblogic.deploy.yaml.YamlStreamTranslator as JYamlStreamTranslator
import oracle.weblogic.deploy.yaml.YamlTranslator as JYamlTranslator

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger


class YamlToPython(object):
    """
    A class that translates a YAML file into a python dictionary.
    """
    _class_name = 'YamlToPython'

    def __init__(self, file_name, use_ordering=False):
        _method_name = '__init__'

        self._file_name = file_name
        self._use_ordering = use_ordering
        self._logger = PlatformLogger('wlsdeploy.yaml')
        try:
            self._translator = JYamlTranslator(self._file_name, self._use_ordering)
        except JIllegalArgumentException, iae:
            yaml_ex = \
                exception_helper.create_yaml_exception('WLSDPLY-18008', file_name, iae.getLocalizedMessage(), error=iae)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=yaml_ex)
            raise yaml_ex
        return

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
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result_dict)
        return result_dict


class YamlStreamToPython(object):
    """
    A class that translates a YAML input stream into a python dictionary.
    """
    _class_name = 'YamlStreamToPython'

    def __init__(self, file_name, input_stream, use_ordering=False):
        _method_name = '__init__'

        self._file_name = file_name
        self._use_ordering = use_ordering
        self._logger = PlatformLogger('wlsdeploy.yaml')
        try:
            self._translator = JYamlStreamTranslator(self._file_name, input_stream, self._use_ordering)
        except JIllegalArgumentException, iae:
            yaml_ex = \
                exception_helper.create_yaml_exception('WLSDPLY-18008', file_name, iae.getLocalizedMessage(), error=iae)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=yaml_ex)
            raise yaml_ex
        return

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
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result_dict)
        return result_dict


class PythonToYaml(object):
    """
    A class that converts a Python dictionary into Yaml and writes the output to a file.
    """
    _class_name = 'PythonToYaml'
    # 4 spaces
    _indent_unit = '    '
    _requires_quotes_chars_regex = '[:{}\[\],&*#?|<>=!%@`-]'

    def __init__(self, dictionary):
        # Fix error handling for None
        self._dictionary = dictionary
        self._logger = PlatformLogger('wlsdeploy.yaml')
        return

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

        fos = None
        writer = None
        try:
            fos = JFileOutputStream(yaml_file, False)
            writer = JPrintWriter(fos, True)
            self._write_dictionary_to_yaml_file(self._dictionary, writer)

        except JFileNotFoundException, fnfe:
            yaml_ex = exception_helper.create_yaml_exception('WLSDPLY-18010', file_name,
                                                             fnfe.getLocalizedMessage(), error=fnfe)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=yaml_ex)
            self._close_streams(fos, writer)
            raise yaml_ex
        except JIOException, ioe:
            yaml_ex = exception_helper.create_yaml_exception('WLSDPLY-18011', file_name,
                                                             ioe.getLocalizedMessage(), error=ioe)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=yaml_ex)
            self._close_streams(fos, writer)
            raise yaml_ex

        self._close_streams(fos, writer)
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=yaml_file)
        return yaml_file

    def _write_dictionary_to_yaml_file(self, dictionary, writer, indent=''):
        """
        Do the actual heavy lifting of converting a dictionary and writing it to the file.  This method is
        called recursively when a value of the dictionary entry is itself a dictionary.
        :param dictionary: the Python dictionarhy to converty
        :param writer: the java.io.PrintWriter for the output file
        :param indent: the amount of indent to use (based on the level of recursion)
        :raises: IOException: if an error occurs while writing the output
        """
        if dictionary is None:
            return

        for key, value in dictionary.iteritems():
            quoted_key = self._quotify_string(key)
            if isinstance(value, dict):
                writer.println(indent + quoted_key + ':')
                self._write_dictionary_to_yaml_file(value, writer, indent + self._indent_unit)
            else:
                writer.println(indent + quoted_key + ': ' + self._get_value_string(value))

        return

    def _get_value_string(self, value):
        """
        Convert the Python value into the proper Yaml value
        :param value: the Python value
        :return: the Yaml value
        """
        if value is None:
            result = 'null'
        elif type(value) is int or type(value) is long or type(value) is float:
            result = str(value)
        elif type(value) is list:
            new_value = '['
            for element in value:
                new_value += ' ' + self._get_value_string(element) + ','
            if len(new_value) > 1:
                new_value = new_value[:-1]
            new_value += ' ]'
            result = str(new_value)
        else:
            result = self._quotify_string(str(value))
        return result

    def _close_streams(self, fos, writer):
        """
        Method used to simplify closing output streams since WLST Jython does not support finally blocks...
        :param fos: the output stream
        :param writer: the print writer
        """
        _method_name = '_close_streams'

        # closing the writer also closes the fos...
        if writer is not None:
            writer.close()
        elif fos is not None:
            try:
                fos.close()
            except JIOException, ioe:
                self._logger.fine('WLSDPLY-18012', ioe, ioe.getLocalizedMessage(),
                                  class_name=self._class_name, method_name=_method_name)
        return

    def _quotify_string(self, text):
        """
        Insert quotes around the string value if it contains Yaml special characters that require it.
        :param text: the input string
        :return: the quoted string, or the original string if no quoting was required
        """
        if bool(re.search(self._requires_quotes_chars_regex, text)):
            result = '\'' + _quote_embedded_quotes(text) + '\''
        else:
            result = _quote_embedded_quotes(text)
        return result

def _quote_embedded_quotes(text):
    """
    Replace any embedded quotes with two quotes.
    :param text:  the text to quote
    :return:  the quoted text
    """
    result = text
    if '\'' in text:
        result = result.replace('\'', '\'\'')
    if '"' in text:
        result = result.replace('"', '""')
    return result
