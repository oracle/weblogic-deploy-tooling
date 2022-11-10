"""
Copyright (c) 2020, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re

from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.util.credential_injector import CredentialInjector
from wlsdeploy.tool.util.targets import additional_output_helper
import wlsdeploy.util.unicode_helper as str_helper

_secret_pattern = re.compile("^@@SECRET:(.*)@@$")


class DomainResourceExtractor:
    """
    Create output files for the specified target.
    """
    _class_name = "DomainResourceExtractor"

    def __init__(self, model, model_context, aliases, logger):
        self._model = model
        self._model_context = model_context
        self._aliases = aliases
        self._logger = logger

    def extract(self):
        # create a credential injector containing secrets from the model
        model_dict = self._model.get_model()
        credential_injector = CredentialInjector(DomainResourceExtractor, model_dict, self._model_context)
        _add_secrets(model_dict, credential_injector)

        # if -domain_home was specified on the extract command line, it should override any value in the model
        domain_home = self._model_context.get_domain_home()

        # create the output files with information from the model
        additional_output_helper.create_additional_output(
            self._model, self._model_context, self._aliases, credential_injector, ExceptionType.DEPLOY,
            domain_home_override=domain_home)


def _add_secrets(folder, credential_injector):
    """
    Recursively add any secrets found in the specified folder.
    :param folder: the folder to be checked
    :param credential_injector: the injector to collect secrets
    """
    for name in folder:
        value = folder[name]
        if isinstance(value, dict):
            _add_secrets(value, credential_injector)
        else:
            text = str_helper.to_string(value)
            matches = _secret_pattern.findall(text)
            for secret_name in matches:
                # remove the domain UID variable prefix, the output helper will prepend the actual UID
                secret_name = secret_name.replace('@@ENV:DOMAIN_UID@@-', '')
                if secret_name not in credential_injector.get_variable_cache():
                    credential_injector.add_to_cache(token_name=secret_name, token_value='')


def get_or_create_dictionary(dictionary, key):
    if key not in dictionary:
        dictionary[key] = PyOrderedDict()
    return dictionary[key]
