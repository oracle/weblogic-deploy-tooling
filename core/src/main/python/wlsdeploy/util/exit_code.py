"""
Copyright (c) 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Standard exit codes for command-line utilities.
"""

class ExitCode(object):
    """
    Standard exit codes for command-line utilities.
    """

    OK                         = 0
    WARNING                    = 1
    ERROR                      = 2

    ARG_VALIDATION_ERROR       = 98
    USAGE_ERROR                = 99

    HELP                       = 100
    RESTART_REQUIRED           = 103
    CANCEL_CHANGES_IF_RESTART  = 104
