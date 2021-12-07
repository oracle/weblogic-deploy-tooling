# Copyright (c) 2021, Oracle Corporation and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# ------------
# Description:
# ------------
# WDT filters to prepare a model for use with WKO, using the createDomain or prepareModel tools.
# These operations can be invoked as a single call, or independently of each other.

def filter_model(model):
    """
    Perform the following operations on the specified model:
    - Remove any online-only attributes
    - Check if servers in a cluster have different ports
    :param model: the model to be filtered
    """
    filter_online_attributes(model)
    check_clustered_server_ports(model)


def filter_online_attributes(model):
    """
    Remove any online-only attributes from the specified model.
    :param model: the model to be filtered
    """
    print("\n\nFILTER ONLINE ATTRIBUTES")


def check_clustered_server_ports(model):
    """
    Set the CalculatedListenPorts attribute to false for dynamic clusters in the specified model.
    Warn if servers in a static cluster have different ports in the specified model.
    :param model: the model to be filtered
    """
    print("\n\nCHECK_CLUSTERED SERVER PORTS")
