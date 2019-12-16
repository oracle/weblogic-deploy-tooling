"""
Copyright (c) 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.io import File
from oracle.weblogic.deploy.util import PyOrderedDict, FileUtils

from wlsdeploy.exception import exception_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.model_translator import PythonToFile


class DomainResourceExtractor:
    """
    Create a domain resource file for use with Kubernetes deployment.
    """
    _class_name = "DomainResourceExtractor"

    def __init__(self, model, model_context, aliases, logger):
        self._model = model
        self._model_context = model_context
        self._aliases = aliases
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

        namespace = dictionary_utils.get_element(kubernetes_map, 'Namespace')
        if namespace is None:
            namespace = ''

        resource_dict['namespace'] = namespace

        resource_dir = File(resource_file).getParentFile()
        if (not resource_dir.isDirectory()) and (not resource_dir.mkdirs()):
            mkdir_ex = exception_helper.create_deploy_exception('WLSDPLY-10001', resource_dir)
            raise mkdir_ex

        writer = PythonToFile(resource_dict)

        writer.write_to_file(resource_file)

