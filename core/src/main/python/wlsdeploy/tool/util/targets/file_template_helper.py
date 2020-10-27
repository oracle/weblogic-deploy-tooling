"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Methods for template substitution.
"""
import re

from java.io import BufferedReader
from java.io import IOException
from java.io import InputStreamReader
from java.lang import IllegalArgumentException
from oracle.weblogic.deploy.util import FileUtils

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils

__class_name = 'file_template_helper'
__logger = PlatformLogger('wlsdeploy.tool.util')

_substitution_pattern = re.compile("({{{(.*)}}})")
_block_start_pattern = re.compile("({{#(.*)}})")
_block_end_pattern = re.compile("({{/(.*)}})")


def create_file_from_resource(resource_path, template_hash, output_file, exception_type):
    """
    Read the template from the resource stream, perform any substitutions,
    and write it to the output file.
    :param resource_path: the resource path of the source template
    :param template_hash: a dictionary of substitution values
    :param output_file: the file to write
    :param exception_type: the type of exception to throw if needed
    """
    _method_name = 'create_file_from_resource'

    template_stream = FileUtils.getResourceAsStream(resource_path)
    if template_stream is None:
        ex = exception_helper.create_exception(exception_type, 'WLSDPLY-01661', resource_path)
        __logger.throwing(ex, class_name=__class_name, method_name=_method_name)
        raise ex

    _create_file_from_stream(template_stream, template_hash, output_file, exception_type)


def create_file_from_file(file_path, template_hash, output_file, exception_type):
    """
    Read the template from the template file, perform any substitutions,
    and write it to the output file.
    :param file_path: the absolute file path of the source template
    :param template_hash: a dictionary of substitution values
    :param output_file: the file to write
    :param exception_type: the type of exception to throw if needed
    """
    _method_name = 'create_file_from_file'

    try:
        template_stream = FileUtils.getFileAsStream(file_path)
        if template_stream is not None:
            _create_file_from_stream(template_stream, template_hash, output_file, exception_type)
    except (IOException, IllegalArgumentException), ie:
        ex = exception_helper.create_exception(exception_type, 'WLSDPLY-01666', file_path, ie)
        __logger.throwing(ex, class_name=__class_name, method_name=_method_name)
        raise ex


def _create_file_from_stream(template_stream, template_hash, output_file, exception_type):
    template_reader = BufferedReader(InputStreamReader(template_stream))
    file_writer = open(output_file.getPath(), "w")

    current_block_key = None
    block_lines = []

    more = True
    while more:
        line = template_reader.readLine()
        if line is not None:
            block_start_key = _get_block_start_key(line)
            block_end_key = _get_block_end_key(line)

            # if this is a nested block start, continue and add without substitution
            if (block_start_key is not None) and (current_block_key is None):
                current_block_key = block_start_key
                block_lines = []

            # if this is a nested block end, continue and add without substitution
            elif (block_end_key == current_block_key) and (current_block_key is not None):
                _write_block(current_block_key, block_lines, template_hash, file_writer)
                current_block_key = None

            else:
                line = _substitute_line(line, template_hash)

                if current_block_key is not None:
                    block_lines.append(line)
                else:
                    file_writer.write(line + "\n")

        else:
            more = False

    file_writer.close()


def _get_block_start_key(line):
    """
    If the line contains a start block tag, return the associated key.
    Any other text on the line is discarded.
    :param line: the line to be evaluated
    :return: the revised line
    """
    matches = _block_start_pattern.findall(line)
    if matches:
        return matches[0][1]
    return None


def _get_block_end_key(line):
    """
    If the line contains a start block tag, return the associated key.
    Any other text on the line is discarded.
    :param line: the line to be evaluated
    :return: the revised line
    """
    matches = _block_end_pattern.findall(line)
    if matches:
        return matches[0][1]
    return None


def _substitute_line(line, template_hash):
    """
    Substitute any tokens in the specified line with values from the template hash.
    :param line: the line to be evaluated
    :param template_hash: a map of keys and values
    :return: the revised line
    """
    matches = _substitution_pattern.findall(line)
    for token, value in matches:
        replacement = dictionary_utils.get_element(template_hash, value)
        if replacement is not None:
            line = line.replace(token, replacement)
    return line


def _write_block(key, lines, template_hash, file_writer):
    """
    Write a block of lines to the file writer, making substitutions as necessary.
    This method does not currently handle nested blocks.
    :param key: the key of this block
    :param lines: the lines to be output
    :param template_hash: the parent hash
    :param file_writer: to write the output
    """
    value = dictionary_utils.get_element(template_hash, key)

    # skip block for value of False, None, or empty collection
    if not value:
        return

    # if value is not a list, make it a list with one item
    if not isinstance(value, list):
        value = [value]

    for list_element in value:
        for line in lines:
            # this does not account for nested blocks

            if isinstance(list_element, dict):
                line = _substitute_line(line, list_element)
            file_writer.write(line + "\n")
