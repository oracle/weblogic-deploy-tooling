"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from wlsdeploy.util.enum import Enum

ControlOptions = Enum(['NORMAL', 'RECURSIVE', 'FOLDERS_ONLY', 'ATTRIBUTES_ONLY'])


def show_attributes(control_option):
    """
    Determine if attributes should be displayed, based on the control option.
    :param control_option: the control option to be checked
    :return: True if attributes should be displayed, False otherwise
    """
    return control_option in [ControlOptions.NORMAL, ControlOptions.ATTRIBUTES_ONLY]


def show_folders(control_option):
    """
    Determine if folders should be displayed, based on the control option.
    :param control_option: the control option to be checked
    :return: True if folders should be displayed, False otherwise
    """
    return control_option != ControlOptions.ATTRIBUTES_ONLY
