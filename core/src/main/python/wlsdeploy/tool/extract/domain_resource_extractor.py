"""
Copyright (c) 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.io import File
from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.alias_constants import BOOLEAN
from wlsdeploy.aliases.model_constants import KUBERNETES
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.util.model_translator import PythonToFile


# model names and resource file names match
EXPOSE_ADMIN_T3_CHANNEL = 'exposeAdminT3Channel'
NAMESPACE = 'namespace'


class DomainResourceExtractor:
    """
    Create a domain resource file for use with Kubernetes deployment.
    """
    _class_name = "DomainResourceExtractor"

    def __init__(self, model, model_context, aliases, logger):
        self._model = model
        self._model_context = model_context
        self._aliases = AliasHelper(aliases, logger, ExceptionType.DEPLOY)
        self._logger = logger
        return

    def extract(self):
        """
        Deploy resource model elements at the domain level, including multi-tenant elements.
        """
        _method_name = 'extract'

        resource_file = self._model_context.get_domain_resource_file()
        self._logger.info("WLSDPLY-10000", resource_file, method_name=_method_name, class_name=self._class_name)

        kubernetes_map = self._model.get_model_kubernetes()

        resource_dict = PyOrderedDict()

        location = self._aliases.get_model_section_attribute_location(KUBERNETES)
        type_map = self._aliases.get_model_attribute_names_and_types(location)

        for key, model_value in kubernetes_map.items():
            if key in type_map:
                type_name = type_map[key]
                if type_name == BOOLEAN:
                    value = _get_boolean_text(model_value)
                else:
                    value = model_value

                resource_dict[key] = value

        resource_dir = File(resource_file).getParentFile()
        if (not resource_dir.isDirectory()) and (not resource_dir.mkdirs()):
            mkdir_ex = exception_helper.create_deploy_exception('WLSDPLY-10001', resource_dir)
            raise mkdir_ex

        writer = PythonToFile(resource_dict)

        writer.write_to_file(resource_file)


def _get_boolean_text(model_value):
    # this method returns string 'true' or 'false'.
    # the model values can be true, false, 1, 0, etc.
    return alias_utils.convert_to_type('boolean', model_value)
