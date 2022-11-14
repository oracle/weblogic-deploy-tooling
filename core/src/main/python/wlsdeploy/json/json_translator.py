"""
Copyright (c) 2017, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

This model provider translation classes that convert between JSON and Python Dictionaries.
"""
import types

import java.io.FileNotFoundException as JFileNotFoundException
import java.io.FileOutputStream as JFileOutputStream
import java.io.IOException as JIOException
import java.io.PrintWriter as JPrintWriter
import java.lang.Boolean as JBoolean
import java.lang.IllegalArgumentException as JIllegalArgumentException

import oracle.weblogic.deploy.util.FileUtils as JFileUtils
import oracle.weblogic.deploy.json.JsonStreamTranslator as JJsonStreamTranslator
import oracle.weblogic.deploy.json.JsonTranslator as JJsonTranslator

from wlsdeploy.logging.platform_logger import PlatformLogger
import wlsdeploy.exception.exception_helper as exception_helper
import wlsdeploy.util.unicode_helper as str_helper


class JsonToPython(object):
    """
    This class turns JSON file into an equivalent Python dictionary.
    """
    _class_name = 'JsonToPython'

    def __init__(self, file_name, use_ordering=False):
        _method_name = '__init__'

        self._file_name = file_name
        self._logger = PlatformLogger('wlsdeploy.json')
        try:
            self._translator = JJsonTranslator(file_name, use_ordering, str_helper.use_unicode())
        except JIllegalArgumentException, iae:
            json_ex = \
                exception_helper.create_json_exception('WLSDPLY-18014', file_name, iae.getLocalizedMessage(), error=iae)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=json_ex)
            raise json_ex

    def parse(self):
        """
        Parse the JSON and convert it into a Python dictionary
        :return: a python dictionary representation of the JSON
        """
        _method_name = 'parse'

        self._logger.entering(class_name=self._class_name, method_name=_method_name)
        # throws JsonException with details, nothing we can really add here...
        result_dict = self._translator.parse()

        # don't log the model on exit, it may contain passwords
        self._logger.exiting(class_name=self._class_name, method_name=_method_name)
        return result_dict


class JsonStreamToPython(object):
    """
    This class turns JSON input stream into an equivalent Python dictionary.
    """
    _class_name = 'JsonStreamToPython'

    def __init__(self, file_name, input_stream, use_ordering=False):
        _method_name = '__init__'

        self._file_name = file_name
        self._input_stream = input_stream

        self._logger = PlatformLogger('wlsdeploy.json')
        try:
            self._translator = JJsonStreamTranslator(file_name, input_stream, use_ordering, str_helper.use_unicode())
        except JIllegalArgumentException, iae:
            json_ex = \
                exception_helper.create_json_exception('WLSDPLY-18014', file_name, iae.getLocalizedMessage(), error=iae)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=json_ex)
            raise json_ex

    def parse(self):
        """
        Parse the JSON and convert it into a Python dictionary
        :return: a python dictionary representation of the JSON
        """
        _method_name = 'parse'

        self._logger.entering(class_name=self._class_name, method_name=_method_name)
        # throws JsonException with details, nothing we can really add here...
        result_dict = self._translator.parse()
        self._logger.exiting(class_name=self._class_name, method_name=_method_name)
        return result_dict


class PythonToJson(object):
    """
    This class writes a Python dictionary out in a JSON format.
    """
    _class_name = 'PythonToJson'
    # 4 spaces of indent
    _indent_unit = '    '

    def __init__(self, dictionary):
        # Fix error handling for None
        self._dictionary = dictionary
        self._logger = PlatformLogger('wlsdeploy.json')

    def write_to_json_file(self, file_name):
        """
        Convert the Python dictionary to JSON and write it to the specified file.
        :param file_name:  the name of the file
        :return: the java.io.File object of the JSON file
        """
        _method_name = 'writeToJsonFile'

        self._logger.entering(file_name, class_name=self._class_name, method_name=_method_name)
        try:
            json_file = JFileUtils.validateWritableFile(file_name)
        except JIllegalArgumentException, iae:
            json_ex = exception_helper.create_json_exception('WLSDPLY-18015', file_name,
                                                             iae.getLocalizedMessage(), error=iae)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=json_ex)
            raise json_ex

        fos = None
        writer = None
        try:
            fos = JFileOutputStream(json_file, False)
            writer = JPrintWriter(fos, True)
            self._write_dictionary_to_json_file(self._dictionary, writer)

        except JFileNotFoundException, fnfe:
            json_ex = exception_helper.create_json_exception('WLSDPLY-18010', file_name,
                                                             fnfe.getLocalizedMessage(), error=fnfe)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=json_ex)
            self._close_streams(fos, writer)
            raise json_ex
        except JIOException, ioe:
            json_ex = exception_helper.create_json_exception('WLSDPLY-18011', file_name,
                                                             ioe.getLocalizedMessage(), error=ioe)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=json_ex)
            self._close_streams(fos, writer)
            raise json_ex

        self._close_streams(fos, writer)
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=json_file)
        return json_file

    def _write_dictionary_to_json_file(self, dictionary, writer, indent=''):
        """
        Write the python dictionary in json syntax using the provided writer stream.
        :param dictionary: python dictionary to convert to json syntax
        :param writer: where to write the dictionary into json syntax
        :param indent: current string indentation of the json syntax. If not provided, indent is an empty string
        """
        _start_dict = '{'
        _end_dict = '}'

        if dictionary is None:
            return
        end_line = ''
        # writer.print causes print to be flagged with error in ide
        writer.write(_start_dict)
        end_indent = indent

        indent += self._indent_unit
        for key, value in dictionary.iteritems():
            writer.println(end_line)
            end_line = ','
            writer.write(indent + '"' + _escape_text(key) + '" : ')
            if isinstance(value, dict):
                self._write_dictionary_to_json_file(value, writer, indent)
            elif isinstance(value, list):
                self._write_list_to_json_file(value, writer, indent)
            else:
                writer.write(_format_json_value(value))
        writer.println()
        writer.write(end_indent + _end_dict)

    def _write_list_to_json_file(self, alist, writer, indent=''):
        """
        Write the python list in json syntax using the provided writer stream.
        :param alist: python list to convert to json syntax
        :param writer: where to write the list into json syntax
        :param indent: current string indentation of the json syntax. If not provided, indent is an empty string
        """
        writer.write('[')
        end_line = ''
        list_indent = indent + self._indent_unit
        for value in alist:
            writer.write(end_line)
            writer.println()
            if isinstance(value, dict):
                writer.write(list_indent)
                self._write_dictionary_to_json_file(value, writer, list_indent)
            else:
                writer.write(list_indent)
                writer.write(_format_json_value(value))
            end_line = ','
        writer.println()
        writer.write(indent + ']')

    def _close_streams(self, fos, writer):
        """
        Close the correct output stream.
        :param fos: the file output stream
        :param writer: the writer that wraps the file output stream
        """
        _method_name = '_close_streams'

        if writer is not None:
            writer.close()
        elif fos is not None:
            try:
                fos.close()
            except JIOException, ioe:
                self._logger.fine('WLSDPLY-18016', ioe, ioe.getLocalizedMessage(),
                                  class_name=self._class_name, method_name=_method_name)


def _format_json_value(value):
    """
    Format the value as a JSON snippet.
    :param value: the value
    :return: the JSON snippet
    """
    import java.lang.StringBuilder as StringBuilder
    builder = StringBuilder()
    if type(value) == bool:
        builder.append(JBoolean.toString(value))
    elif isinstance(value, types.StringTypes):
        builder.append('"').append(_escape_text(value.strip())).append('"')
    else:
        builder.append(value)
    return builder.toString()


def _escape_text(text):
    """
    Escape the specified text for use in a double-quoted string to become valid json expression.
    :param text: the text to escape
    :return: the escaped text
    """
    result = text
    if isinstance(text, types.StringTypes):
        if '\\' in result:
            result = result.replace('\\', '\\\\')
        if '"' in result:
            result = result.replace('"', '\\"')
        if '\n' in result:
            result = result.replace("\n", "\\\\n")
        if '\b' in result:
            result = result.replace("\b", "\\\\b")
        if '\f' in result:
            result = result.replace("\f", "\\\\f")
        if '\r' in result:
            result = result.replace("\r", "\\\\r")
        if '\t' in result:
            result = result.replace("\t", "\\\\t")
        if '\/' in result:
            result = result.replace("\/", "\\\\/")
    return result
