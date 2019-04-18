"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

import copy
import oracle.weblogic.deploy.util.StringUtils as StringUtils
import oracle.weblogic.deploy.util.PyOrderedDict as OrderedDict
import wlsdeploy.util.dictionary_utils as dictionary_utils

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DYNAMIC_SERVERS
from wlsdeploy.aliases.model_constants import DEFAULT_ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_GROUP_TARGETING_LIMITS
from wlsdeploy.exception import exception_helper
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
        self.exception_type = exception_type

        topology = model.get_model_topology()
        if ADMIN_SERVER_NAME in topology:
            self._admin_server_name = topology[ADMIN_SERVER_NAME]
        else:
            self._admin_server_name = DEFAULT_ADMIN_SERVER_NAME

    def target_jrf_groups_to_clusters_servers(self, should_update=True):
        """
        Call applyJRF to for those versions of wlst that cannot target servers to server groups.
        This assigns the JRF resources to all managed servers. If the managed server is in a
        cluster, this method assigns the JRF resources are assigned to the cluster. Else, if
        the managed server is stand-alone, the resources are assigned to the managed server.
        :param should_update: Control how the applyJRF applies the changes. By default, allow
        the applyJRF to automatically update the values
        """
        _method_name = 'target_jrf_groups_to_clusters_servers'
        self.logger.entering(should_update, class_name=self.__class_name,
                             method_name=_method_name)

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
        cluster_map = self._get_clusters_and_members_map()

        self.wlst_helper.save_and_close(self.model_context)
        
        # Get the clusters and and their members
        for cluster_name, cluster_servers in cluster_map.iteritems():
            self.logger.info('WLSDPLY-12233', 'Cluster', cluster_name, class_name=self.__class_name,
                             method_name=_method_name)
            self.wlst_helper.apply_jrf(cluster_name, self.model_context, should_update=should_update)
            for member in cluster_servers:
                if member in server_names:
                    server_names.remove(member)
        for ms_name in server_names:
            self.logger.info('WLSDPLY-12233', 'Managed Server', ms_name, class_name=self.__class_name,
                             method_name=_method_name)
            self.wlst_helper.apply_jrf(ms_name, self.model_context, should_update=should_update)

        self.wlst_helper.reopen(self.model_context)
        
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def target_server_groups_to_servers(self, server_groups_to_target):
        """
        Target the server groups to the servers.
        :param server_groups_to_target: the list of server groups to target
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'target_server_groups_to_servers'

        self.logger.entering(server_groups_to_target, class_name=self.__class_name, method_name=_method_name)
        if len(server_groups_to_target) == 0:
            return None, None

        location = LocationContext()
        root_path = self.alias_helper.get_wlst_attributes_path(location)
        self.wlst_helper.cd(root_path)

        # We need to get the effective list of servers for the domain.  Since any servers
        # referenced in the model have already been created but the templates may have
        # defined new servers not listed in the model, get the list from WLST.
        server_names = self._get_existing_server_names()

        # Get the clusters and and their members
        cluster_map = self._get_clusters_and_members_map()
        dynamic_cluster_names = list()
        for cluster_name in cluster_map:
            if DYNAMIC_SERVERS in cluster_map[cluster_name]:
                dynamic_cluster_names.append(cluster_name)

        # Get any limits that may have been defined in the model
        domain_info = self.model.get_model_domain_info()
        server_group_targeting_limits = \
            dictionary_utils.get_dictionary_element(domain_info, SERVER_GROUP_TARGETING_LIMITS)
        if len(server_group_targeting_limits) > 0:
            server_group_targeting_limits = \
                self._get_server_group_targeting_limits(server_group_targeting_limits, cluster_map)

        self.logger.finer('WLSDPLY-12240', str(server_group_targeting_limits),
                          class_name=self.__class_name, method_name=_method_name)

        # Get the map of server names to server groups to target
        server_to_server_groups_map =\
            self._get_server_to_server_groups_map(self._admin_server_name,
                                                  server_names,
                                                  dynamic_cluster_names,
                                                  server_groups_to_target,
                                                  server_group_targeting_limits)  # type: dict
        self.logger.finer('WLSDPLY-12242', str(server_to_server_groups_map), class_name=self.__class_name,
                          method_name=_method_name)

        final_assignment_map = dict()
        if len(server_names) > 0:
            for server, server_groups in server_to_server_groups_map.iteritems():
                if server in server_names and len(server_groups) > 0:
                    final_assignment_map[server] = server_groups

        elif len(server_names) == 0 and len(dynamic_cluster_names) == 0:
            #
            # Domain has no managed servers and there were not targeting limits specified to target
            # server groups to the admin server so make sure that the server groups are targeted to
            # the admin server.
            #
            # This is really a best effort attempt.  It works for JRF domains but it is certainly possible
            # that it may cause problems with other custom domain types.  Of course, creating a domain with
            # no managed servers is not a primary use case of this tool so do it and hope for the best...
            #
            final_assignment_map[server_names[0]] = server_groups_to_target

        # Target any dynamic clusters to the server group resources
        dynamic_cluster_assigns = None
        if len(dynamic_cluster_names) > 0:
            dynamic_cluster_assigns = dict()
            for name in dynamic_cluster_names:
                if name in server_to_server_groups_map:
                    dynamic_cluster_assigns[name] = server_to_server_groups_map[name]

        self.logger.exiting(result=str(dynamic_cluster_assigns), class_name=self.__class_name, method_name=_method_name)
        return final_assignment_map, dynamic_cluster_assigns

    def target_server_groups(self, server_assigns):
        """
        Perform the targeting of the server groups to server from the list of assignments made in the
        target helper assignment step. This is separate from creating the list of assignments in order
        to control the state of the domain when the target is done.
        :param server_assigns: map of server to server group
        """
        _method_name = 'target_server_groups'
        self.logger.entering(str(server_assigns), class_name=self.__class_name, method_name=_method_name)

        for server, server_groups in server_assigns.iteritems():
            server_name = self.wlst_helper.get_quoted_name_for_wlst(server)
            self.logger.info('WLSDPLY-12224', str(server_groups), server_name,
                             class_name=self.__class_name, method_name=_method_name)
            self.wlst_helper.set_server_groups(server_name, server_groups)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def target_server_groups_to_dynamic_clusters(self, dynamic_cluster_assigns):
        """
        Dynamic clusters need special handling to assign the server group resources to the dynamic cluster.
        You cannot assign servergroups to a server template. So must search each templates that contain the server group
        for resources and specifically add the dynamic target to the resource target.
        If JRF or RestrictedJRF skip the check and do the applyJRF function to automatically target to the cluster.
        :param dynamic_cluster_assigns: The assignments from domainInfo targeting limits applied to dynamic lusters
        """
        _method_name = 'target_server_group_resources_to_dyanamic_cluster'
        self.logger.entering(str(dynamic_cluster_assigns), class_name=self.__class_name, method_name=_method_name)

        domain_typedef = self.model_context.get_domain_typedef()

        if len(dynamic_cluster_assigns) > 0:
            # TBD assign server group resources to cluster. The JRF resources could still be applied separately
            # using this technique - or remove this technique and replace with the resource targeting
            if domain_typedef.has_jrf_resources():
                self._target_jrf_resources(dynamic_cluster_assigns)
            else:
                ex = exception_helper.create_exception(self.exception_type, 'WLSDPLY-12238',
                                                       domain_typedef.get_domain_type())
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def _target_jrf_resources(self, dynamic_cluster_assigns):
        # Target the JRF resources directly using the applyJRF method.
        _method_name = '_target_jrf_resources'
        names_only = list()
        for name in dynamic_cluster_assigns:
            names_only.append(name)
        if self.model_context.is_wlst_online() and \
                self.model_context.get_domain_typedef().is_restricted_jrf_domain_type():
            self.logger.warning('WLSDPLY-12244', str(names_only), class_name=self.__class_name,
                                _method_name=_method_name)
        else:
            self.logger.info('WLSDPLY-12236', str(names_only),
                             class_name=self.__class_name, method_name=_method_name)
            self.wlst_helper.apply_jrf_control_updates(names_only, self.model_context)

    def _get_existing_server_names(self):
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

    def _get_clusters_and_members_map(self):
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

        clusters_location = LocationContext().append_location(CLUSTER)
        cluster_list_path = self.alias_helper.get_wlst_list_path(clusters_location)
        cluster_names = self.wlst_helper.get_existing_object_list(cluster_list_path)
        cluster_token = self.alias_helper.get_name_token(clusters_location)
        # Add the cluster with dynamic servers, if not already in the cluster member list.
        # A cluster may contain both dynamic and configured servers (referred to as mixed cluster).
        # Add a token marking DYNAMIC SERVERS in the member list.
        for cluster_name in cluster_names:
            cluster_location = LocationContext(clusters_location)
            cluster_location.add_name_token(cluster_token, cluster_name)
            cluster_attributes_path = self.alias_helper.get_wlst_attributes_path(cluster_location)
            self.wlst_helper.cd(cluster_attributes_path)
            cluster_location.append_location(DYNAMIC_SERVERS)
            wlst_subfolder_name = self.alias_helper.get_wlst_mbean_type(cluster_location)
            if self.wlst_helper.subfolder_exists(wlst_subfolder_name):
                if cluster_name not in cluster_map:
                    cluster_map[cluster_name] = list()
                cluster_map[cluster_name].append(DYNAMIC_SERVERS)

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

    def get_existing_cluster_names(self):
        """
        Get the list of cluster names from WLST.
        :return: the list of cluster names
        :raises: BundleAwareException of the specified type: is an error occurs reading from the aliases or WLST
        """
        _method_name = 'get_existing_cluster_names'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        cluster_location = LocationContext().append_location(CLUSTER)
        cluster_list_path = self.alias_helper.get_wlst_list_path(cluster_location)
        result = self.wlst_helper.get_existing_object_list(cluster_list_path)
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
                    if DYNAMIC_SERVERS in cluster_members:
                        # This will need special handling to target server group resources
                        cluster_members.remove(DYNAMIC_SERVERS)
                        cluster_members.add(target_name)
                    new_list.extend(cluster_members)
                else:
                    # Assume it is a server name and add it to the new list
                    # Stand-alone Managed Servers were not added to the cluster: server_name_list map
                    # which was built from the existing servers and clusters.
                    new_list.append(target_name)
            sg_targeting_limits[server_group_name] = new_list

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=sg_targeting_limits)
        return sg_targeting_limits

    def _get_server_to_server_groups_map(self, admin_server_name, server_names, dynamic_cluster_names,
                                         server_groups, sg_targeting_limits):
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
            server_groups_for_server = self.__get_server_groups_for_entity(server_name, sg_targeting_limits)
            if server_groups_for_server is not None:
                result[server_name] = server_groups_for_server
            elif server_name != admin_server_name:
                # By default, we only target managed servers unless explicitly listed in the targeting limits
                result[server_name] = list(server_groups)
            else:
                result[admin_server_name] = list()
        for cluster_name in dynamic_cluster_names:
            server_groups_for_cluster = self.__get_server_groups_for_entity(cluster_name, sg_targeting_limits)
            if server_groups_for_cluster is not None:
                result[cluster_name] = server_groups_for_cluster
            else:
                result[cluster_name] = list(server_groups)
            self.logger.finer('WLSDPLY-12239', result[cluster_name], cluster_name,
                              class_name=self.__class_name, method_name=_method_name)
        if admin_server_name not in result:
            result[admin_server_name] = list()
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def __get_server_groups_for_entity(self, entity_name, sg_targeting_limits):
        """
        Get the servers groups to target for a given server or dynamic cluster name.
        :param entity_name: the server or dynamic_cluster name
        :param sg_targeting_limits: the targeting limits
        :return: the list of server groups to target to the specified entity name, or None
                 if the entity name does not appear in the targeting limits
        """
        _method_name = '__get_server_groups_for_entity'

        result = None
        for server_group, entity_names_list in sg_targeting_limits.iteritems():
            if entity_name in entity_names_list:
                if result is None:
                    result = list()
                result.append(server_group)
        if result is not None:
            self.logger.fine('WLSDPLY-12243', entity_name, result, class_name=self.__class_name,
                             method_name=_method_name)
        return result
