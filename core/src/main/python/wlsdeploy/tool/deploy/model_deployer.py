"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from oracle.weblogic.deploy.util import PyWLSTException

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy.applications_deployer import ApplicationsDeployer
from wlsdeploy.tool.deploy.resources_deployer import ResourcesDeployer

_class_name = 'model_deployer.py'
_logger = PlatformLogger('wlsdeploy.deploy')


def deploy_resources(model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
    """
    Deploy the resources in specific order.
    Applications are not included, since they are processed after save/activate for online deployment.
    :param model: the model
    :param model_context: the model context
    :param aliases: the aliases object
    :param wlst_mode: the WLST mode to use
    :raises DeployException: if an error occurs
    """
    _method_name = 'deploy_resources'

    try:
        location = LocationContext()
        resources_deployer = ResourcesDeployer(model, model_context, aliases, wlst_mode=wlst_mode)
        resources_deployer.deploy(location)
    except PyWLSTException, pwe:
        ex = exception_helper.create_deploy_exception('WLSDPLY-09111', pwe.getLocalizedMessage(), error=pwe)
        _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex


def deploy_app_attributes_online(model, model_context, aliases):
    applications_deployer = ApplicationsDeployer(model, model_context, aliases, wlst_mode=WlstModes.ONLINE)
    applications_deployer.add_application_attributes_online(model,LocationContext())


def deploy_applications(model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
    """
    Deploy the applications from the model.
    :param model: the model
    :param model_context: the model context
    :param aliases: the aliases object
    :param wlst_mode: the WLST mode to use
    :raises DeployException: if an error occurs
    """
    applications_deployer = ApplicationsDeployer(model, model_context, aliases, wlst_mode=wlst_mode)
    applications_deployer.deploy()


def deploy_model_offline(model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
    """
    Deploy the topology, resources and applications, in specific order.
    This order is correct for offline. For online deployment, applications should be processed after save/activate.
    :param model: the model
    :param model_context: the model context
    :param aliases: the aliases object
    :param wlst_mode: the WLST mode to use
    :raises DeployException: if an error occurs
    """
    _method_name = 'deploy_model_offline'

    try:
        deploy_resources(model, model_context, aliases, wlst_mode=wlst_mode)
        deploy_applications(model, model_context, aliases, wlst_mode=wlst_mode)
    except PyWLSTException, pwe:
        ex = exception_helper.create_deploy_exception('WLSDPLY-09650', pwe.getLocalizedMessage(), error=pwe)
        _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex


def deploy_model_after_update(model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
    """
    Deploy the resources that must be done after WLST updateDomain.
    :param model: the model
    :param model_context: the model context
    :param aliases: the aliases object
    :param wlst_mode: the WLST mode to use
    :raises DeployException: if an error occurs
    """
    _method_name = 'deploy_model_offline_after_update'

    try:
        location = LocationContext()
        resources_deployer = ResourcesDeployer(model, model_context, aliases, wlst_mode=wlst_mode)
        resources_deployer.deploy_after_update(location)
    except PyWLSTException, pwe:
        ex = exception_helper.create_deploy_exception('WLSDPLY-09650', pwe.getLocalizedMessage(), error=pwe)
        _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex


def deploy_resources_and_apps_for_create(model, model_context, aliases):
    """
    Deploy the resources and appDeployments sections after create handles the topology section of the model.
    :param model: the model dictionary
    :param model_context: the model context
    :param aliases: the aliases
    :raises DeployException: if an error occurs
    """
    deploy_model_offline(model, model_context, aliases)
