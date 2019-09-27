"""
Copyright (c) 2017, 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import wlsdeploy.util.dictionary_utils as dictionary_utils
from wlsdeploy.aliases.model_constants import WATCH
from wlsdeploy.aliases.model_constants import WATCH_NOTIFICATION
from wlsdeploy.aliases.model_constants import WLDF_SYSTEM_RESOURCE
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.tool.deploy.deployer import Deployer


class WldfResourcesDeployer(Deployer):
    """
    Deploy resources for WLDF
    """
    _class_name = "WldfResourcesDeployer"

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
        Deployer.__init__(self, model, model_context, aliases, wlst_mode)

    def add_wldf_modules(self, parent_dict, location):
        """
        Deploy WLDF module elements from the specified dictionary to the specified location.
        :param parent_dict: a dictionary containing WLDF elements
        :param location: the location to be deployed
        """
        wldf_resources = dictionary_utils.get_dictionary_element(parent_dict, WLDF_SYSTEM_RESOURCE)
        self._add_named_elements(WLDF_SYSTEM_RESOURCE, wldf_resources, location)

    # Override
    def _add_subfolders(self, model_nodes, location, excludes=None):
        """
        Override the base method for sub-folders of watch notification.
        The watch sub-folder must be processed last.
        """
        parent_type = self.get_location_type(location)
        if parent_type == WATCH_NOTIFICATION:
            # add all sub-folders except watch
            Deployer._add_subfolders(self, model_nodes, location, excludes=[WATCH])

            # add the watch sub-folder last
            watch_nodes = dictionary_utils.get_dictionary_element(model_nodes, WATCH)
            self._add_named_elements(WATCH, watch_nodes, location)
            return

        Deployer._add_subfolders(self, model_nodes, location, excludes=excludes)
        return
