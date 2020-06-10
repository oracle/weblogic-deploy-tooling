"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Methods and constants for building Kubernetes resource files,
including domain resource configuration for WebLogic Kubernetes Operator.
"""


def get_domain_uid(domain_name):
    """
    Determine the domain UID based on domain name.
    :param domain_name: the domain name to be checked
    :return: the domain UID
    """
    return domain_name.lower()
