"""
Copyright (c) 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.aliases.model_constants import CREDENTIAL
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import OPSS_INITIALIZATION
from wlsdeploy.aliases.model_constants import TARGET_KEY
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils

_class_name = 'opss_helper'


class OPSSHelper(object):
    """
    Helper for OPSS credentials in the model dictionary.
    """
    _class_name = 'OPSSHelper'

    def __init__(self, model_dictionary, model_context, aliases, wlst_helper):
        """
        :param model_dictionary: the model dictionary to be used
        :param model_context: used to check CLI arguments
        :param aliases: used for folder lookup
        :param wlst_helper: used for WLST commands
        """
        self._model_dictionary = model_dictionary
        self._model_context = model_context
        self._aliases = aliases
        self._wlst_helper = wlst_helper
        self._logger = PlatformLogger('wlsdeploy.create')

    def create_credentials(self):
        _method_name = 'create_credentials'

        domain_info = dictionary_utils.get_dictionary_element(self._model_dictionary, DOMAIN_INFO)
        opss_initialization = dictionary_utils.get_dictionary_element(domain_info, OPSS_INITIALIZATION)
        credentials = dictionary_utils.get_dictionary_element(opss_initialization, CREDENTIAL)
        for store_key, store_folder in credentials.iteritems():
            self._logger.info('WLSDPLY-12350', store_key, class_name=self._class_name, method_name=_method_name)
            keys = dictionary_utils.get_dictionary_element(store_folder, TARGET_KEY)
            for key, key_folder in keys.iteritems():
                wlst_path = '/Credential/TargetStore/' + store_key + '/TargetKey/' + key
                self._wlst_helper.cd(wlst_path)
                self._wlst_helper.create('c', 'Credential')
                self._wlst_helper.cd('Credential')
                for field, field_value in key_folder.iteritems():
                    self._wlst_helper.set(field, field_value)


def create_credentials(model_dictionary, model_context, aliases, wlst_helper):
    """
    Static method for initializing OPSSHelper and creating credentials.
    :param model_dictionary: the model dictionary to be used
    :param model_context: used to check CLI arguments
    :param aliases: used for folder lookup
    :param wlst_helper: used for WLST commands
    """
    opss_helper = OPSSHelper(model_dictionary, model_context, aliases, wlst_helper)
    opss_helper.create_credentials()
