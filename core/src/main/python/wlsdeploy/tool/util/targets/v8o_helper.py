"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Methods and constants for creating Kubernetes resource configuration files for Verrazzano.
"""
import re

from java.io import BufferedReader
from java.io import File
from java.io import InputStreamReader
from oracle.weblogic.deploy.util import FileUtils

from wlsdeploy.aliases.model_constants import DEFAULT_WLS_DOMAIN_NAME
from wlsdeploy.aliases.model_constants import NAME
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils

__class_name = 'v8o_helper'
__logger = PlatformLogger('wlsdeploy.tool.util')

_substitution_pattern = re.compile("({{{(.*)}}})")

TEMPLATE_PATH = 'oracle/weblogic/deploy/targets/v8o'

# substitution keys used in the templates
DOMAIN_UID = 'domainUid'


def create_v8o_configuration(model, model_context, exception_type):
    """
    Create and write the Kubernetes resource configuration files for Verrazzano.
    :param model: Model object, used to derive some values in the configurations
    :param model_context: used to determine location and content for the configurations
    """

    # -output_dir argument was previously verified
    output_dir = model_context.get_kubernetes_output_dir()

    template_hash = _build_template_hash(model)

    _create_file('binding.yaml', template_hash, output_dir, exception_type)
    _create_file('model.yaml', template_hash, output_dir, exception_type)


def _create_file(template_name, template_hash, output_dir, exception_type):
    """
    Read the template from the resource stream, perform any substitutions,
    and write it to a file with the same name in the output directory.
    :param template_name: the name of the template file, and the output file
    :param template_hash: a dictionary of substitution values
    :param output_dir: the directory to write the output file
    """
    _method_name = '_create_file'

    output_file = File(output_dir, template_name)
    file_writer = open(output_file.getPath(), "w")

    template_path = TEMPLATE_PATH + '/' + template_name

    template_stream = FileUtils.getResourceAsStream(template_path)
    if template_stream is None:
        ex = exception_helper.create_exception(exception_type, 'WLSDPLY-01661', template_path)
        __logger.throwing(ex, class_name=__class_name, method_name=_method_name)
        raise ex

    template_reader = BufferedReader(InputStreamReader(FileUtils.getResourceAsStream(template_path)))

    more = True
    while more:
        line = template_reader.readLine()
        if line is not None:

            line = _substitute_line(line, template_hash)

            file_writer.write(line + "\n")

        else:
            more = False

    file_writer.close()


def _build_template_hash(model):
    """
    Create a dictionary of substitution values to apply to the templates.
    :param model: used to derive values
    :return: the hash dictionary
    """
    template_hash = dict()

    domain_uid = dictionary_utils.get_element(model.get_model_topology(), NAME)
    if domain_uid is None:
        domain_uid = DEFAULT_WLS_DOMAIN_NAME

    template_hash[DOMAIN_UID] = domain_uid

    return template_hash


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
