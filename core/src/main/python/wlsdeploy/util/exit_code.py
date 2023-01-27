"""
Copyright (c) 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Standard exit codes for command-line utilities.
"""

from oracle.weblogic.deploy.util import ExitCode as JExitCode

class ExitCode(object):
    """
    Standard exit codes for command-line utilities.
    """

    OK                         = JExitCode.OK
    WARNING                    = JExitCode.WARNING
    ERROR                      = JExitCode.ERROR

    ARG_VALIDATION_ERROR       = JExitCode.ARG_VALIDATION_ERROR
    USAGE_ERROR                = JExitCode.USAGE_ERROR

    HELP                       = JExitCode.HELP
    DEPRECATION                = JExitCode.DEPRECATION
    RESTART_REQUIRED           = JExitCode.RESTART_REQUIRED
    CANCEL_CHANGES_IF_RESTART  = JExitCode.CANCEL_CHANGES_IF_RESTART
