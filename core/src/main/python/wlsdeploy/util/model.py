"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0

This module serves as a wrapper for the model dictionary.
It has convenience methods for accessing top-level fields in the model.
"""
import pprint

import oracle.weblogic.deploy.util.PyOrderedDict as OrderedDict

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.weblogic_helper import WebLogicHelper


class Model(object):
    """
    Class documentation
    """
    _class_name = 'Model'

    def __init__(self, model_dictionary=None, wls_version=None):
        self._logger = PlatformLogger('wlsdeploy.model')
        self._wls_helper = WebLogicHelper(wls_version)
        self._topology = OrderedDict()
        self._resources = OrderedDict()
        self._deployments = OrderedDict()
        self._domain_info = OrderedDict()

        if model_dictionary is not None:
            if 'topology' in model_dictionary:
                self._topology = model_dictionary['topology']

            if 'resources' in model_dictionary:
                self._resources = model_dictionary['resources']

            if 'appDeployments' in model_dictionary:
                self._deployments = model_dictionary['appDeployments']

            if 'domainInfo' in model_dictionary:
                self._domain_info = model_dictionary['domainInfo']
        return

    def get_model_resources(self):
        """
        Get the resources section of the model.
        :return: the resources dictionary
        """
        return self._resources

    def get_model_app_deployments(self):
        """
        Get the appDeployments section of the model.
        :return: the appDeployments dictionary
        """
        return self._deployments

    def get_model_topology(self):
        """
        Get the topology section of the model.
        :return: the topology dictionary
        """
        return self._topology

    def get_model_domain_info(self):
        """
        Get the domainInfo section of the model.
        :return: the domainInfo dictionary
        """
        return self._domain_info

    def get_model(self):
        """
        Get the model.
        :return: the model dictionary
        """
        model = OrderedDict()
        if len(self._domain_info):
            model['domainInfo'] = self._domain_info
        if len(self._topology) > 0:
            model['topology'] = self._topology
        if len(self._resources) > 0:
            model['resources'] = self._resources
        if len(self._deployments) > 0:
            model['appDeployments'] = self._deployments
        return model

    def log_model(self, level, message, method_name, class_name='Model'):
        """
        Log the model.
        :param level: the level to log at
        :param message: the message to log
        :param method_name: the method requesting the logging of the model
        :param class_name: the class requesting the logging of the model
        """
        self._logger.log(level, '{0} for WebLogic {1} is:', message, self._wls_helper.wl_version,
                         method_name=method_name, class_name=class_name)
        self._logger.log(level, '"domainInfo": {0}', pprint.pformat(self._domain_info),
                         method_name=method_name, class_name=class_name)
        self._logger.log(level, '"topology": {0}', self._topology,
                         method_name=method_name, class_name=class_name)
        self._logger.log(level, '"resources": {0}', pprint.pformat(self._resources),
                         method_name=method_name, class_name=class_name)
        self._logger.log(level, '"appDeployments": {0}', pprint.pformat(self._deployments),
                         method_name=method_name, class_name=class_name)
        return

def get_model_resources_key():
    """
    Get the model resources element key
    :return: the model resources element key
    """
    return 'resources'

def get_model_deployments_key():
    """
    Get the model appDeployments element key
    :return: the model appDeployments element key
    """
    return 'appDeployments'

def get_model_topology_key():
    """
    Get the model topology element key
    :return: the model topology element key
    """
    return 'topology'

def get_model_domain_info_key():
    """
    Get the model domainInfo element key
    :return: the model domainInfo element key
    """
    return 'domainInfo'

def get_model_top_level_keys():
    """
    Get the known top-level model element keys.
    :return: a list of the known top-level model element keys
    """
    return [
        get_model_domain_info_key(),
        get_model_topology_key(),
        get_model_resources_key(),
        get_model_deployments_key()
    ]
