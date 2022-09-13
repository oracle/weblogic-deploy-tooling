"""
Copyright (c) 2018, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from oracle.weblogic.deploy.util import WLSDeployExit
from oracle.weblogic.deploy.util import WLSDeployContext
import oracle.weblogic.deploy.util.WLSDeployContext.WLSTMode as mode

from wlsdeploy.aliases.wlst_modes import WlstModes

def end(model_context, exit_code):
    """
    Tools python code should use this tool to perform end actions, clean-up, and exit with exit code
    :param model_context: tool python context
    :param exit_code: for completion of tool
    """
    program = None
    version = None
    wlst_mode = mode.OFFLINE
    if model_context:
        program = model_context.get_program_name()
        version = model_context.get_target_wls_version()
        if model_context.get_target_wlst_mode() == WlstModes.ONLINE:
            wlst_mode = mode.ONLINE
    WLSDeployExit.exit(WLSDeployContext(program, version, wlst_mode), exit_code)

def __log_and_exit(logger, model_context, exit_code, class_name, _method_name=None):
    """
    Helper method to log the exiting message and exit
    :param logger:  the logger to use
    :param model_context:  the model_context to use
    :param exit_code: the exit code to use
    :param class_name: the class name to pass  to the logger
    :param _method_name: the method name to pass to the logger
    """
    logger.exiting(result=exit_code, class_name=class_name, method_name=_method_name)
    end(model_context, exit_code)
