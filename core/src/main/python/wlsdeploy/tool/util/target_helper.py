"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

import copy
import oracle.weblogic.deploy.util.PyOrderedDict as OrderedDict
import wlsdeploy.util.dictionary_utils as dictionary_utils
from wlsdeploy.aliases.location_context import LocationContext

from wlsdeploy.aliases.model_constants import ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DEFAULT_ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_GROUP_TARGETING_LIMITS
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util import string_utils


class TargetHelper(object):
    """
    Shared code for targeting clusters and servers. Domain create and update use this code.
    """
    __class_name = 'TargetHelper'

    def __init__(self, model, model_context, aliases, exception_type, logger):
        self.logger = logger
        self.model = model
        self.model_context = model_context
        self.alias_helper = AliasHelper(aliases, self.logger, exception_type)
        self.wlst_helper = WlstHelper(self.logger, exception_type)

        topology = model.get_model_topology()
        if ADMIN_SERVER_NAME in topology:
            self._admin_server_name = topology[ADMIN_SERVER_NAME]
        else:
            self._admin_server_name = DEFAULT_ADMIN_SERVER_NAME

    def target_jrf_groups_to_clusters_servers(self, domain_home):
        """
        Use the apply_jrf only for those versions of wlst that do not have server groups.
        This assigns the JRF resources to all managed servers. If the managed server is in a
        cluster, this method assigns the JRF resources are assigned to the cluster. Else, if
        the managed server is stand-alone, the resources are assigned to the managed server.
        :param domain_home: the directory for the domain_home
        """
        _method_name = 'target_jrf_groups_to_clusters_servers'

        self.logger.entering(domain_home, class_name=self.__class_name, method_name=_method_name)

        location = LocationContext()
        root_path = self.alias_helper.get_wlst_attributes_path(location)
        self.wlst_helper.cd(root_path)
        admin_server_name = self.wlst_helper.get(ADMIN_SERVER_NAME)

        # We need to get the effective list of servers for the domain.  Since any servers
        # referenced in the model have already been created but the templates may have
        # defined new servers not listed in the model, get the list from WLST.
        server_names = self.get_existing_server_names()
        if admin_server_name in server_names:
            server_names.remove(admin_server_name)

        # Get the clusters and and their members
        cluster_map = self.get_clusters_and_members_map()

        # Get the clusters and and their members
        for cluster_name, cluster_servers in cluster_map.iteritems():
            self.logger.info('WLSDPLY-12232', 'Cluster', cluster_name, class_name=self.__class_name,
                             method_name=_method_name)
            self.wlst_helper.apply_jrf(cluster_name, domain_home, should_update=True)
            for member in cluster_servers:
                if member in server_names:
                    server_names.remove(member)
        for ms_name in server_names:
            self.logger.info('WLSDPLY-12232', 'Managed Server', ms_name, class_name=self.__class_name,
                             method_name=_method_name)
            self.wlst_helper.apply_jrf(ms_name, domain_home, should_update=True)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def target_server_groups_to_servers(self, domain_home, server_groups_to_target):
        """
        Target the server groups to the servers.
        :param server_groups_to_target: the list of server groups to target
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = '__target_server_groups_to_servers'

        self.logger.entering(server_groups_to_target, class_name=self.__class_name, method_name=_method_name)
        if len(server_groups_to_target) > 0:
            location = LocationContext()
            root_path = self.alias_helper.get_wlst_attributes_path(location)
            self.wlst_helper.cd(root_path)

            # We need to get the effective list of servers for the domain.  Since any servers
            # referenced in the model have already been created but the templates may have
            # defined new servers not listed in the model, get the list from WLST.
            server_names = self.get_existing_server_names()

            # Get the clusters and and their members
            cluster_map = self.get_clusters_and_members_map()

            location = LocationContext()
            root_path = self.alias_helper.get_wlst_attributes_path(location)
            self.wlst_helper.cd(root_path)

            # We need to get the effective list of servers for the domain.  Since any servers
            # referenced in the model have already been created but the templates may have
            # defined new servers not listed in the model, get the list from WLST.
            server_names = self.get_existing_server_names()

            # Get the clusters and and their members
            cluster_map = self.get_clusters_and_members_map()

            # Get any limits that may have been defined in the model
            domain_info = self.model.get_model_domain_info()
            server_group_targeting_limits = \
                dictionary_utils.get_dictionary_element(domain_info, SERVER_GROUP_TARGETING_LIMITS)
            if len(server_group_targeting_limits) > 0:
                server_group_targeting_limits = \
                    self._get_server_group_targeting_limits(server_group_targeting_limits, cluster_map)

            # Get the map of server names to server groups to target
            server_to_server_groups_map =\
                self._get_server_to_server_groups_map(self._admin_server_name,
                                                      server_names,
                                                      server_groups_to_target,
                                                      server_group_targeting_limits)  # type: dict

            if len(server_names) > 1:
                for server, server_groups in server_to_server_groups_map.iteritems():
                    if len(server_groups) > 0:
                        server_name = self.wlst_helper.get_quoted_name_for_wlst(server)
                        self.logger.info('WLSDPLY-12224', str(server_groups), server_name,
                                         class_name=self.__class_name, method_name=_method_name)
                        self.wlst_helper.set_server_groups(server_name, server_groups)

            elif len(server_group_targeting_limits) == 0:
                #
                # Domain has no managed servers and there were not targeting limits specified to target
                # server groups to the admin server so make sure that the server groups are targeted to
                # the admin server.
                #
                # This is really a best effort attempt.  It works for JRF domains but it is certainly possible
                # that it may cause problems with other custom domain types.  Of course, creating a domain with
                # no managed servers is not a primary use case of this tool so do it and hope for the best...
                #
                server_name = self.wlst_helper.get_quoted_name_for_wlst(server_names[0])
                self.wlst_helper.set_server_groups(server_name, server_groups_to_target)


        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def get_clusters_and_members_map(self):
        """
        Get a map keyed by cluster name with values that are a list of member server names
        :return: the cluster name to member server names map
        :raises: BundleAwareException of the specified type: is an error occurs reading from the aliases or WLST
        """
        _method_name = '_get_clusters_and_members_map'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        server_location = LocationContext().append_location(SERVER)
        server_list_path = self.alias_helper.get_wlst_list_path(server_location)
        server_names = self.wlst_helper.get_existing_object_list(server_list_path)
        server_token = self.alias_helper.get_name_token(server_location)
        cluster_map = OrderedDict()
        for server_name in server_names:
            server_location.add_name_token(server_token, server_name)
            server_attributes_path = self.alias_helper.get_wlst_attributes_path(server_location)
            self.wlst_helper.cd(server_attributes_path)

            server_attributes_map = self.wlst_helper.lsa()
            cluster_name = dictionary_utils.get_element(server_attributes_map, CLUSTER)
            if string_utils.is_empty(cluster_name):
                # if server is not part of a cluster, continue with the next server
                continue

            if cluster_name not in cluster_map:
                cluster_map[cluster_name] = list()
            cluster_map[cluster_name].append(server_name)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=cluster_map)
        return cluster_map

    def get_existing_server_names(self):
        """
        Get the list of server names from WLST.
        :return: the list of server names
        :raises: BundleAwareException of the specified type: is an error occurs reading from the aliases or WLST
        """
        _method_name = '_get_existing_server_names'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        server_location = LocationContext().append_location(SERVER)
        server_list_path = self.alias_helper.get_wlst_list_path(server_location)
        result = self.wlst_helper.get_existing_object_list(server_list_path)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def _get_server_group_targeting_limits(self, server_group_targeting_limits, clusters_map):
        """
        Get any server group targeting limits specified in the model, converting any cluster
        names to the list of members.  This method assumes that the limits dictionary is not
        None or empty.
        :param server_group_targeting_limits: the raw server group targeting_limits from the model
        :param clusters_map: the map of cluster names to member server names
        :return: the map of server groups to server names to target
        """
        _method_name = '_get_server_group_targeting_limits'

        self.logger.entering(str(server_group_targeting_limits), str(clusters_map),
                             class_name=self.__class_name, method_name=_method_name)
        sg_targeting_limits = copy.deepcopy(server_group_targeting_limits)
        for server_group_name, sg_targeting_limit in sg_targeting_limits.iteritems():
            if type(sg_targeting_limit) is str:
                if MODEL_LIST_DELIMITER in sg_targeting_limit:
                    sg_targeting_limit = sg_targeting_limit.split(MODEL_LIST_DELIMITER)
                else:
                    # convert a single value into a list of one...
                    new_list = list()
                    new_list.append(sg_targeting_limit)
                    sg_targeting_limit = new_list

            # Convert any references to a cluster name into the list of member server names
            new_list = list()
            for target_name in sg_targeting_limit:
                target_name = target_name.strip()
                if target_name in clusters_map:
                    cluster_members = dictionary_utils.get_element(clusters_map, target_name)
                    new_list.extend(cluster_members)
                else:
                    # Assume it is a server name and add it to the new list
                    new_list.append(target_name)
            sg_targeting_limits[server_group_name] = new_list

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=sg_targeting_limits)
        return sg_targeting_limits

    def _get_server_to_server_groups_map(self, admin_server_name, server_names, server_groups, sg_targeting_limits):
        """
        Get the map of server names to the list of server groups to target to that server.
        :param admin_server_name: the admin server name
        :param server_names: the list of server names
        :param server_groups: the complete list of server groups that will, by default, be targeted to
                              all managed servers unless the server is listed in the targeting limits map
        :param sg_targeting_limits: the targeting limits map
        :return: the map of server names to the list of server groups to target to that server
        """
        _method_name = '_get_server_to_server_groups_map'

        self.logger.entering(admin_server_name, str(server_names), str(server_groups), str(sg_targeting_limits),
                             class_name=self.__class_name, method_name=_method_name)
        result = OrderedDict()
        for server_name in server_names:
            server_groups_for_server = self.__get_server_groups_for_server(server_name, sg_targeting_limits)
            if server_groups_for_server is not None:
                result[server_name] = server_groups_for_server
            elif server_name != admin_server_name:
                # By default, we only target managed servers unless explicitly listed in the targeting limits
                result[server_name] = list(server_groups)
            else:
                result[admin_server_name] = list()
        if admin_server_name not in result:
            result[admin_server_name] = list()
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def __get_server_groups_for_server(self, server_name, sg_targeting_limits):
        """
        Get the servers groups to target for a given server name.
        :param server_name: the server name
        :param sg_targeting_limits: the targeting limits
        :return: the list of server groups to target to the specified server name, or None
                 if the server name does not appear in the targeting limits
        """
        _method_name = '__get_server_groups_for_server'

        self.logger.entering(server_name, str(sg_targeting_limits),
                             class_name=self.__class_name, method_name=_method_name)
        result = None
        for server_group, server_names_list in sg_targeting_limits.iteritems():
            if server_name in server_names_list:
                if result is None:
                    result = list()
                result.append(server_group)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result
