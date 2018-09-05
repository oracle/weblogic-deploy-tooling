
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