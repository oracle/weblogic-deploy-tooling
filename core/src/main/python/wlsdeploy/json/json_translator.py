"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0

This model provider translation classes that convert between JSON and Python Dictionaries.
"""
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
            self._translator = JJsonTranslator(file_name, use_ordering)
        except JIllegalArgumentException, iae:
            json_ex = \
                exception_helper.create_json_exception('WLSDPLY-18014', file_name, iae.getLocalizedMessage(), error=iae)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=json_ex)
            raise json_ex
        return

    def parse(self):
        """
        Parse the JSON and convert it into a Python dictionary
        :return: a python dictionary representation of the JSON
        """
        _method_name = 'parse'

        self._logger.entering(class_name=self._class_name, method_name=_method_name)
        # throws JsonException with details, nothing we can really add here...
        result_dict = self._translator.parse()
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result_dict)
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
            self._translator = JJsonStreamTranslator(file_name, input_stream, use_ordering)
        except JIllegalArgumentException, iae:
            json_ex = \
                exception_helper.create_json_exception('WLSDPLY-18014', file_name, iae.getLocalizedMessage(), error=iae)
            self._logger.throwing(class_name=self._class_name, method_name=_method_name, error=json_ex)
            raise json_ex
        return

    def parse(self):
        """
        Parse the JSON and convert it into a Python dictionary
        :return: a python dictionary representation of the JSON
        """
        _method_name = 'parse'

        self._logger.entering(class_name=self._class_name, method_name=_method_name)
        # throws JsonException with details, nothing we can really add here...
        result_dict = self._translator.parse()
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result_dict)
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
        return

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
        :param indent: current string indention of the json syntax. If not provided, indent is an empty string
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
            writer.write(indent + '"' + _quote_embedded_quotes(key) + '" : ')
            if isinstance(value, dict):
                self._write_dictionary_to_json_file(value, writer, indent)
            else:
                writer.write(_format_json_value(value))
        writer.println()
        writer.write(end_indent + _end_dict)

        return

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
        return


def _format_json_value(value):
    """
    Format the value as a JSON snippet.
    :param value: the value
    :return: the JSON snippet
    """
    import java.lang.StringBuilder as StringBuilder
    builder = StringBuilder()
    if type(value) == bool or (type(value) == str and (value == 'true' or value == 'false')):
        builder.append(JBoolean.toString(value))
    elif type(value) == str:
        builder.append('"').append(_quote_embedded_quotes(value)).append('"')
    else:
        builder.append(value)
    return builder.toString()

def _quote_embedded_quotes(text):
    """
    Quote all embedded double quotes in a string with a backslash.
    :param text: the text to quote
    :return: the quotes result
    """
    result = text
    if type(text) is str and '"' in text:
        result = text.replace('"', '\\"')
    return result
