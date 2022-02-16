"""
Copyright (c) 2022 Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Methods to update a resource file with information from the kubernetes section of the model.
"""
from java.io import File

from oracle.weblogic.deploy.yaml import YamlException

from oracle.weblogic.deploy.util import PyOrderedDict
from wlsdeploy.aliases.model_constants import KUBERNETES
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.extract import wko_schema_helper
from wlsdeploy.tool.extract.domain_resource_extractor import COMPONENT
from wlsdeploy.tool.extract.domain_resource_extractor import DEFAULT_KIND
from wlsdeploy.tool.extract.domain_resource_extractor import KIND
from wlsdeploy.tool.extract.domain_resource_extractor import SPEC
from wlsdeploy.tool.extract.domain_resource_extractor import TEMPLATE
from wlsdeploy.tool.extract.domain_resource_extractor import VERRAZZANO_WEBLOGIC_WORKLOAD
from wlsdeploy.tool.extract.domain_resource_extractor import WORKLOAD
from wlsdeploy.util import dictionary_utils
from wlsdeploy.yaml.yaml_translator import PythonToYaml
from wlsdeploy.yaml.yaml_translator import YamlToPython

__class_name = 'resource_file_helper'
__logger = PlatformLogger('wlsdeploy.tool.util')


def update_from_model(output_dir, template_name, model):
    """
    Update the template output with information from the kubernetes section of the model.
    Template output is (currently) always Kubernetes resource files.
    :param output_dir: the directory of the output file to update
    :param template_name: the name of the output file
    :param model: the model to use for update
    """
    _method_name = 'update_from_model'

    # if model doesn't have kubernetes section, return
    kubernetes_content = model.get_model_kubernetes()
    if not kubernetes_content:
        return

    # failures will be logged as severe, but not cause tool failure.
    # this will allow the unaltered resource file to be examined for problems.

    resource_file = File(output_dir, template_name)
    __logger.info('WLSDPLY-01675', resource_file, KUBERNETES, class_name=__class_name, method_name=_method_name)

    try:
        reader = YamlToPython(resource_file.getPath(), True)
        documents = reader.parse_documents()
    except YamlException, ex:
        __logger.severe('WLSDPLY-01673', resource_file, str(ex), error=ex, class_name=__class_name,
                        method_name=_method_name)
        return

    _update_documents(documents, kubernetes_content, resource_file.getPath())

    try:
        writer = PythonToYaml(documents)
        writer.write_to_yaml_file(resource_file.getPath())
    except YamlException, ex:
        __logger.severe('WLSDPLY-01674', resource_file, str(ex), error=ex, class_name=__class_name,
                        method_name=_method_name)
    return


def _update_documents(documents, kubernetes_content, resource_file_path):
    _method_name = '_update_documents'
    found = False

    # update section(s) based on their kind, etc.
    for document in documents:
        if isinstance(document, dict):
            kind = dictionary_utils.get_element(document, KIND)

            # is this a standard WKO document?
            if kind == DEFAULT_KIND:
                _update_dictionary(document, kubernetes_content, None, resource_file_path)
                found = True

            # is this a Verrazzano WebLogic workload document?
            elif kind == COMPONENT:
                spec = dictionary_utils.get_dictionary_element(document, SPEC)
                workload = dictionary_utils.get_dictionary_element(spec, WORKLOAD)
                component_kind = dictionary_utils.get_element(workload, KIND)
                if component_kind == VERRAZZANO_WEBLOGIC_WORKLOAD:
                    component_spec = _get_or_create_dictionary(workload, SPEC)
                    component_template = _get_or_create_dictionary(component_spec, TEMPLATE)
                    _update_dictionary(component_template, kubernetes_content, None, resource_file_path)
                    found = True

    if not found:
        __logger.warning('WLSDPLY-01676', resource_file_path, class_name=__class_name, method_name=_method_name)


def _update_dictionary(output_dictionary, model_content, element_path, resource_file_path):
    _method_name = '_update_list'
    if not isinstance(output_dictionary, dict):
        __logger.warning('WLSDPLY-01677', element_path, resource_file_path, class_name=__class_name,
                         method_name=_method_name)
        return

    for key, value in model_content.items():
        if key not in output_dictionary:
            output_dictionary[key] = value
        elif isinstance(value, dict):
            element_path = wko_schema_helper.append_path(element_path, key)
            _update_dictionary(output_dictionary[key], value, element_path, resource_file_path)
        elif isinstance(value, list):
            if not value:
                # if the model has an empty list, override output value
                output_dictionary[key] = value
            else:
                element_path = wko_schema_helper.append_path(element_path, key)
                _update_list(output_dictionary[key], value, element_path, resource_file_path)
        else:
            output_dictionary[key] = value
    pass


def _update_list(output_list, model_list, element_path, resource_file_path):
    _method_name = '_update_list'
    if not isinstance(output_list, list):
        __logger.warning('WLSDPLY-01678', element_path, resource_file_path, class_name=__class_name,
                         method_name=_method_name)
        return

    output_list.extend(model_list)
    pass


def _get_or_create_dictionary(dictionary, key):
    if key not in dictionary:
        dictionary[key] = PyOrderedDict()

    return dictionary[key]
