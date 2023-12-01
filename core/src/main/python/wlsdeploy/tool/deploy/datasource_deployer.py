"""
Copyright (c) 2017, 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_PATH_PROPERTIES
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_PROPERTY_VALUE
from wlsdeploy.aliases.model_constants import PROPERTIES
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.tool.deploy.deployer import Deployer
from wlsdeploy.util import dictionary_utils
from oracle.weblogic.deploy.util import PyOrderedDict
from oracle.weblogic.deploy.util import WLSDeployArchive


class DatasourceDeployer(Deployer):
    """
    Deploy data sources to JDBCSystemResource(s) using WLST.  Entry point, add_data_sources()
    """
    _class_name = "DatasourceDeployer"

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
        Deployer.__init__(self, model, model_context, aliases, wlst_mode)

    def add_data_sources(self, parent_dict, location):
        """
        Using the provided dictionary, add the data sources from the model to the WLST location.
        :param parent_dict: model dictionary containing data sources
        :param location: the location context for these data sources, such as Domain or ResourceGroup
        """
        data_sources = dictionary_utils.get_dictionary_element(parent_dict, JDBC_SYSTEM_RESOURCE)
        self._add_named_elements(JDBC_SYSTEM_RESOURCE, data_sources, location)

    # Override
    def set_attributes(self, location, model_nodes, excludes=None):
        """
        Override this method to provide special processing for some attributes.
        :param location: the location to set attributes
        :param model_nodes: model nodes containing attributes to be set
        :param excludes: names of attributes to avoid setting
        """
        type_name, child_name = self.get_location_type_and_name(location)

        # set the Name attribute in JDBCResource folder for online deployment.
        # Bug 27091687 requires this value to be explicitly set.
        if type_name == JDBC_RESOURCE and self.wlst_mode == WlstModes.ONLINE:
            existing_name = self.wlst_helper.get('Name')
            if existing_name is None:
                parent_location = LocationContext(location)
                parent_location.pop_location()
                data_source_token = self.aliases.get_name_token(parent_location)
                data_source_name = location.get_name_for_token(data_source_token)
                self.wlst_helper.set('Name', data_source_name)
            # continue

        # some driver param properties can use archive paths, and may need adjusting.
        # for example, wlsdeploy/dbWallet/* becomes config/wlsdeploy/dbWallet/* .
        if type_name == PROPERTIES and child_name in DRIVER_PARAMS_PATH_PROPERTIES:
            new_model_nodes = PyOrderedDict()
            for key, value in model_nodes.items():
                if key == DRIVER_PARAMS_PROPERTY_VALUE:
                    new_model_nodes[key] = WLSDeployArchive.getExtractPath(value)
                else:
                    new_model_nodes[key] = value
            model_nodes = new_model_nodes
            # continue

        Deployer.set_attributes(self, location, model_nodes, excludes)
