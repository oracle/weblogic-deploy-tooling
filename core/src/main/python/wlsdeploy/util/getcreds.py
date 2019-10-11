"""
Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from oracle.weblogic.deploy.util import CLAUtils


def getuser(message_key, *args):
    """
    Prompts the user to enter non-sensitive information such as their username.

    :param message_key: The wlsdeploy resource bundle message key or any message
    :param args: The arguments to use to format the wlsdeploy resource bundle message key
    :return: the username as a Java String
    :raises IOException: if an IO error occurs prompting the user or reading their response
    """
    return CLAUtils.getUserInput(message_key, list(args))

def getpass(message_key, *args):
    """
    Prompts the user to enter sensitive information such as their password.

    :param message_key: The wlsdeploy resource bundle message key or any message
    :param args: The arguments to use to format the wlsdeploy resource bundle message key
    :return: the password as a Java char array
    :raises IOException: if an IO error occurs prompting the user or reading their response
    """
    return CLAUtils.getPasswordInput(message_key, list(args))
