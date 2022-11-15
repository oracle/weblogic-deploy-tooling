"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import copy

import oracle.weblogic.deploy.util.PyOrderedDict as OrderedDict

import wlsdeploy.util.dictionary_utils as dictionary_utils

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DYNAMIC_CLUSTER_SERVER_GROUP_TARGETING_LIMITS
from wlsdeploy.aliases.model_constants import DYNAMIC_CLUSTER_SIZE
from wlsdeploy.aliases.model_constants import DYNAMIC_SERVERS
from wlsdeploy.aliases.model_constants import DEFAULT_ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_GROUP_TARGETING_LIMITS
from wlsdeploy.aliases.model_constants import SERVER_TEMPLATE
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util import string_utils
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.weblogic_helper import WebLogicHelper


class TargetHelper(object):
    """
    Shared code for targeting clusters and servers. Domain create and update use this code.
    """
    __class_name = 'TargetHelper'

    def __init__(self, model, model_context, aliases, exception_type, logger):
        self.logger = logger
        self.model = model
        self.model_context = model_context
        self.aliases = aliases
        self.wlst_helper = WlstHelper(exception_type)
        self.wls_helper = WebLogicHelper(self.logger)
        self.exception_type = exception_type
        self.domain_typedef = self.model_context.get_domain_typedef()
        topology = model.get_model_topology()
        if ADMIN_SERVER_NAME in topology:
            self._admin_server_name = topology[ADMIN_SERVER_NAME]
        else:
            self._admin_server_name = DEFAULT_ADMIN_SERVER_NAME

    def target_jrf_groups_to_clusters_servers(self):
        """
        Call applyJRF to for those versions of wlst that cannot target servers to server groups.
        This assigns the JRF resources to all managed servers. If the managed server is in a
        cluster, this method assigns the JRF resources are assigned to the cluster. Else, if
        the managed server is stand-alone, the resources are assigned to the managed server.
        to automatically update the domain.
        """
        _method_name = 'target_jrf_groups_to_clusters_servers'
        self.logger.entering(class_name=self.__class_name, method_name=_method_name)

        location = LocationContext()
        root_path = self.aliases.get_wlst_attributes_path(location)
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

        # Get the clusters and and their members
        for cluster_name, cluster_servers in cluster_map.iteritems():
            self.logger.info('WLSDPLY-12233', 'Cluster', cluster_name, class_name=self.__class_name,
                             method_name=_method_name)
            self.wlst_helper.apply_jrf(cluster_name, self.model_context)
            for member in cluster_servers:
                if member in server_names:
                    server_names.remove(member)
        for ms_name in server_names:
            self.logger.info('WLSDPLY-12233', 'Managed Server', ms_name, class_name=self.__class_name,
                             method_name=_method_name)
            self.wlst_helper.apply_jrf(ms_name, self.model_context.get_domain_home())

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
            return list()

        location = LocationContext()
        root_path = self.aliases.get_wlst_attributes_path(location)
        self.wlst_helper.cd(root_path)

        # We need to get the effective list of servers for the domain.  Since any servers
        # referenced in the model have already been created but the templates may have
        # defined new servers not listed in the model, get the list from WLST.
        server_names = self._get_existing_server_names()
        # Get the clusters and and their members
        cluster_map = self._get_clusters_and_members_map()
        # Get any limits that may have been defined in the model
        domain_info = self.model.get_model_domain_info()
        server_group_targeting_limits = \
            dictionary_utils.get_dictionary_element(domain_info, SERVER_GROUP_TARGETING_LIMITS)
        if len(server_group_targeting_limits) > 0:
            server_group_targeting_limits = \
                self._get_server_group_targeting_limits(server_group_targeting_limits, cluster_map)

        self.logger.finer('WLSDPLY-12240', str_helper.to_string(server_group_targeting_limits),
                          class_name=self.__class_name, method_name=_method_name)

        # Get the map of server names to server groups to target
        server_to_server_groups_map =\
            self._get_server_to_server_groups_map(self._admin_server_name,
                                                  server_names,
                                                  server_groups_to_target,
                                                  server_group_targeting_limits)  # type: dict
        self.logger.finer('WLSDPLY-12242', str_helper.to_string(server_to_server_groups_map),
                          class_name=self.__class_name, method_name=_method_name)

        final_assignment_map = dict()
        # Target servers and dynamic clusters to the server group resources
        if len(server_names) > 0:
            for server, server_groups in server_to_server_groups_map.iteritems():
                if len(server_groups) > 0:
                    if server in server_names:
                        final_assignment_map[server] = server_groups

        #
        # Domain has not targeted the server groups to managed servers (configured), or the
        # domain has no managed servers (configured) but has user server groups. The resources for the
        # user server groups must be targeted before the write/update domain or the write/update will fail.
        # Thus assign the user server groups to the admin server.
        #
        # Because of the interaction of the working context in the different wlst helpers, the dynamic
        # clusters will be applied to the resources separately and after the write/update domain.
        #
        # (From original blurb)
        #  This is really a best effort attempt.  It works for JRF domains but it is certainly possible
        # that it may cause problems with other custom domain types.  Of course, creating a domain with
        # no managed servers is not a primary use case of this tool so do it and hope for the best...
        #
        # (New comment)
        # As we have added the intricacies of the dynamic clusters, if the targeting is to dynamic
        # clusters only, the set server groups with the admin server will get through the write/update domain
        # and the applyJRF with the dynamic cluster should theoretically unset the AdminServer on the user server
        # groups. It works with JRF type domains.

        if len(server_groups_to_target) > 0:
            if len(final_assignment_map) == 0:
                # This is a quickie to fix the issue where server groups are not targeted because no configured
                #  managed servers exist in the domain
                final_assignment_map[server_names[0]] = server_groups_to_target
            else:
                # If a server group or groups is not targeted in the assignments, log it to stdout
                no_targets = [server_target for server_target in server_groups_to_target if server_target not in
                              [server_target for row in final_assignment_map.itervalues() for
                               server_target in server_groups_to_target if server_target in row]]
                if len(no_targets) > 0:
                    self.logger.info('WLSDPLY-12248', no_targets,
                                     class_name=self.__class_name, method_name=_method_name)

        self.logger.exiting(result=str_helper.to_string(final_assignment_map),
                            class_name=self.__class_name, method_name=_method_name)
        return final_assignment_map

    def target_server_groups_to_dynamic_clusters(self, server_groups_to_target):
        """
        Target dynamic clusters to dynamic cluster server groups. Dynamic cluster server groups are not user
        expandable. Thus if a dynamic server group is not targeted to a dynamic cluster, don't target to admin
        server. The dynamic cluster server groups are not required to be targeted.
        :param server_groups_to_target: the list of dynamic cluster server groups to target
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'target_server_groups_to_dynamic_clusters'

        self.logger.entering(server_groups_to_target, class_name=self.__class_name, method_name=_method_name)
        if len(server_groups_to_target) == 0:
            return list()

        location = LocationContext()
        root_path = self.aliases.get_wlst_attributes_path(location)
        self.wlst_helper.cd(root_path)

        # Get the clusters and and their members
        cluster_map = self._get_clusters_and_members_map()
        dynamic_cluster_names = list()
        for cluster_name in cluster_map:
            if DYNAMIC_SERVERS in cluster_map[cluster_name]:
                dynamic_cluster_names.append(cluster_name)

        domain_info = self.model.get_model_domain_info()
        dc_server_group_targeting_limits = \
            dictionary_utils.get_dictionary_element(domain_info, DYNAMIC_CLUSTER_SERVER_GROUP_TARGETING_LIMITS)
        if len(dc_server_group_targeting_limits) > 0:
            dc_server_group_targeting_limits = \
                self._get_dynamic_cluster_server_group_targeting_limits(dc_server_group_targeting_limits, cluster_map)
        dynamic_cluster_assigns = \
            self.get_dc_to_server_groups_map(dynamic_cluster_names, server_groups_to_target,
                                             dc_server_group_targeting_limits)  # type: dict
        self.logger.finer('WLSDPLY-12240', str_helper.to_string(dc_server_group_targeting_limits),
                          class_name=self.__class_name, method_name=_method_name)

        self.logger.exiting(result=str_helper.to_string(dynamic_cluster_assigns),
                            class_name=self.__class_name, method_name=_method_name)
        return dynamic_cluster_assigns

    def target_server_groups(self, server_assigns):
        """
        Perform the targeting of the server groups to server from the list of assignments made in the
        target helper assignment step. This is separate from creating the list of assignments in order
        to control the state of the domain when the target is done.
        :param server_assigns: map of server to server group
        """
        _method_name = 'target_server_groups'
        self.logger.entering(str_helper.to_string(server_assigns),
                             class_name=self.__class_name, method_name=_method_name)

        for server, server_groups in server_assigns.iteritems():
            server_name = self.wlst_helper.get_quoted_name_for_wlst(server)
            self.logger.info('WLSDPLY-12224', str_helper.to_string(server_groups), server_name,
                             class_name=self.__class_name, method_name=_method_name)
            self.wlst_helper.set_server_groups(server_name, server_groups,
                                               self.model_context.get_model_config().get_set_server_grps_timeout())

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def target_dynamic_server_groups(self, dynamic_cluster_assigns):
        """
        Dynamic clusters need special handling to assign the server group resources to the dynamic cluster.
        You cannot assign servergroups to a server template. So must search each templates that contain the server group
        for resources and specifically add the dynamic target to the resource target.
        If JRF or RestrictedJRF skip the check and do the applyJRF function to automatically target to the cluster.
        :param dynamic_cluster_assigns: The assignments from domainInfo targeting limits applied to dynamic lusters
        """
        _method_name = 'target_dynamic_server_groups'
        self.logger.entering(str_helper.to_string(dynamic_cluster_assigns),
                             class_name=self.__class_name, method_name=_method_name)

        domain_typedef = self.model_context.get_domain_typedef()

        if len(dynamic_cluster_assigns) > 0:
            # assign server group resources to cluster based on the version of WebLogic server version.
            if self.wls_helper.is_dynamic_cluster_multiple_server_groups_supported():
                bug_map = self.save_dyn_size(dynamic_cluster_assigns)
                self.target_server_groups(dynamic_cluster_assigns)
                self.restore_dyn_size(bug_map)
            elif self.wls_helper.is_dynamic_cluster_one_server_group_supported():
                bug_map = self.save_dyn_size(dynamic_cluster_assigns)
                self.target_dynamic_clusters(dynamic_cluster_assigns)
                self.restore_dyn_size(bug_map)
            else:
                self.logger.warning('WLSDPLY-12238', domain_typedef.get_domain_type(),
                                    class_name=self.__class_name, method_name=_method_name)

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)
        return

    def target_dynamic_clusters(self, server_assigns):
        """
        Perform the targeting of a server group to the clusters from the list of assignments made in the
        target helper assignment step. This is separate from creating the list of assignments in order
        to control the state of the domain when the target is done. The version of WebLogic Server
        supports targeting a single server group to a dynamic cluster.
        :param server_assigns: map of server to server group
        """
        _method_name = 'target_dynamic_clusters'
        self.logger.entering(str_helper.to_string(server_assigns),
                             class_name=self.__class_name, method_name=_method_name)

        for cluster, server_groups in server_assigns.iteritems():
            cluster_name = self.wlst_helper.get_quoted_name_for_wlst(cluster)
            if len(server_groups) > 1:
                ex = exception_helper.create_exception(self.exception_type, 'WLSDPLY-12256',
                                                       cluster, server_groups)
                self.logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
                raise ex 
            elif len(server_groups) > 0:
                self.logger.info('WLSDPLY-12255', server_groups[0], cluster_name,
                                 class_name=self.__class_name, method_name=_method_name)
                self.wlst_helper.set_server_group_dynamic_cluster(cluster_name, server_groups[0])

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _target_jrf_resources(self, dynamic_cluster_assigns):
        # Target the JRF resources directly using the applyJRF method.
        _method_name = '_target_jrf_resources'
        names_only = list()
        for name in dynamic_cluster_assigns:
            names_only.append(name)
        if self.model_context.is_wlst_online() and \
                self.model_context.get_domain_typedef().is_restricted_jrf_domain_type():
            self.logger.warning('WLSDPLY-12244', str_helper.to_string(names_only), class_name=self.__class_name,
                                _method_name=_method_name)
        else:
            self.logger.info('WLSDPLY-12236', str_helper.to_string(names_only),
                             class_name=self.__class_name, method_name=_method_name)
            self.wlst_helper.apply_jrf_with_context(names_only, self.model_context)

    def _get_existing_server_names(self):
        """
        Get the list of server names from WLST.
        :return: the list of server names
        :raises: BundleAwareException of the specified type: is an error occurs reading from the aliases or WLST
        """
        _method_name = '_get_existing_server_names'

        self.logger.entering(class_name=self.__class_name, method_name=_method_name)
        server_location = LocationContext().append_location(SERVER)
        server_list_path = self.aliases.get_wlst_list_path(server_location)
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
        server_list_path = self.aliases.get_wlst_list_path(server_location)
        server_names = self.wlst_helper.get_existing_object_list(server_list_path)
        server_token = self.aliases.get_name_token(server_location)
        cluster_map = OrderedDict()
        for server_name in server_names:
            server_location.add_name_token(server_token, server_name)
            server_attributes_path = self.aliases.get_wlst_attributes_path(server_location)
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
        cluster_list_path = self.aliases.get_wlst_list_path(clusters_location)
        cluster_names = self.wlst_helper.get_existing_object_list(cluster_list_path)
        cluster_token = self.aliases.get_name_token(clusters_location)
        # Add the cluster with dynamic servers, if not already in the cluster member list.
        # A cluster may contain both dynamic and configured servers (referred to as mixed cluster).
        # Add a token marking DYNAMIC SERVERS in the member list.
        for cluster_name in cluster_names:
            cluster_location = LocationContext(clusters_location)
            cluster_location.add_name_token(cluster_token, cluster_name)
            cluster_attributes_path = self.aliases.get_wlst_attributes_path(cluster_location)
            self.wlst_helper.cd(cluster_attributes_path)
            cluster_location.append_location(DYNAMIC_SERVERS)
            wlst_subfolder_name = self.aliases.get_wlst_mbean_type(cluster_location)
            if self.wlst_helper.subfolder_exists(wlst_subfolder_name):
                ds_list_path = self.aliases.get_wlst_list_path(cluster_location)
                ds_names = self.wlst_helper.get_existing_object_list(ds_list_path)
                if len(ds_names) > 0:
                    cluster_location.add_name_token(self.aliases.get_name_token(cluster_location), ds_names[0])
                    cluster_attributes_path = self.aliases.get_wlst_attributes_path(cluster_location)
                    self.wlst_helper.cd(cluster_attributes_path)
                    if self.wlst_helper.get(SERVER_TEMPLATE) is not None:
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
        server_list_path = self.aliases.get_wlst_list_path(server_location)
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
        cluster_list_path = self.aliases.get_wlst_list_path(cluster_location)
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
        self.logger.entering(str_helper.to_string(server_group_targeting_limits),
                             str_helper.to_string(clusters_map),
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
                    new_list.extend(cluster_members)
                else:
                    # Assume it is a server name and add it to the new list
                    # Stand-alone Managed Servers were not added to the cluster: server_name_list map
                    # which was built from the existing servers and clusters.
                    new_list.append(target_name)
            sg_targeting_limits[server_group_name] = new_list

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=sg_targeting_limits)
        return sg_targeting_limits

    def _get_dynamic_cluster_server_group_targeting_limits(self, targeting_limits, clusters_map):
        """
        Get any server group targeting limits specified in the model, converting any cluster
        names to the list of members.  This method assumes that the limits dictionary is not
        None or empty.
        :param targeting_limits: the raw server group targeting_limits from the model
        :param clusters_map: the map of cluster names to member server names
        :return: the map of server groups to server names to target
        """
        _method_name = '_get_dynamic_cluster_server_group_targeting_limits'
        self.logger.entering(str_helper.to_string(targeting_limits), str_helper.to_string(clusters_map),
                             class_name=self.__class_name, method_name=_method_name)

        dc_sg_targeting_limits = copy.deepcopy(targeting_limits)
        for server_group_name, dc_sg_targeting_limit in dc_sg_targeting_limits.iteritems():
            if type(dc_sg_targeting_limit) is str:
                if MODEL_LIST_DELIMITER in dc_sg_targeting_limit:
                    dc_sg_targeting_limit = dc_sg_targeting_limit.split(MODEL_LIST_DELIMITER)
                else:
                    # convert a single value into a list of one...
                    new_list = list()
                    new_list.append(dc_sg_targeting_limit)
                    dc_sg_targeting_limit = new_list

            # Convert any references to a cluster name into the list of member server names
            new_list = list()
            for target_name in dc_sg_targeting_limit:
                target_name = target_name.strip()
                if target_name in clusters_map:
                    cluster_members = dictionary_utils.get_element(clusters_map, target_name)
                    if DYNAMIC_SERVERS in cluster_members:
                        # This will need special handling to target server group resources
                        cluster_members.remove(DYNAMIC_SERVERS)
                        cluster_members.append(target_name)
                        new_list.extend(cluster_members)
            dc_sg_targeting_limits[server_group_name] = new_list

        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=dc_sg_targeting_limits)
        return dc_sg_targeting_limits

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
        self.logger.entering(admin_server_name, str_helper.to_string(server_names),
                             str_helper.to_string(server_groups), str_helper.to_string(sg_targeting_limits),
                             class_name=self.__class_name, method_name=_method_name)

        result = OrderedDict()
        revised_server_groups = self._revised_list_server_groups(server_groups, sg_targeting_limits)
        for server_name in server_names:
            server_groups_for_server = self.__get_server_groups_for_entity(server_name, sg_targeting_limits)
            if len(server_groups_for_server) > 0:
                result[server_name] = server_groups_for_server
            elif server_name != admin_server_name:
                # By default, we only target managed servers unless explicitly listed in the targeting limits
                result[server_name] = list(revised_server_groups)
            else:
                result[admin_server_name] = list()

        if admin_server_name not in result:
            result[admin_server_name] = list()
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def get_dc_to_server_groups_map(self, dynamic_cluster_names, server_groups, dc_sg_targeting_limits):
        """
        Remake the map for each dynamic cluster name and its server groups. If the dynamic cluster is not
        specifically targeted by the dynamic cluster server group targeting limits, target any remaining
        server groups not in the targeting limits, to any remaining typedef dynamic cluster server group targets.
        :param dynamic_cluster_names: list of dynamic clusters in the domain
        :param server_groups: list of dynamic server groups in the typedef
        :param dc_sg_targeting_limits: list of dynamic cluster to server group targeting limits from the domainInfo
        :return: result: map of dynamic cluster to server groups
        """
        _method_name = 'get_dc_to_server_groups_list'
        self.logger.entering(str_helper.to_string(dynamic_cluster_names), str_helper.to_string(server_groups),
                             str_helper.to_string(dc_sg_targeting_limits),
                             class_name=self.__class_name, method_name=_method_name)

        result = OrderedDict()
        revised_server_groups = self._revised_list_server_groups(server_groups, dc_sg_targeting_limits)
        for cluster_name in dynamic_cluster_names:
            server_groups_for_cluster = \
                self.__get_server_groups_for_entity(cluster_name, dc_sg_targeting_limits)
            if len(server_groups_for_cluster) > 0:
                result[cluster_name] = server_groups_for_cluster
            else:
                result[cluster_name] = list(revised_server_groups)
            self.logger.finer('WLSDPLY-12239', result[cluster_name], cluster_name,
                              class_name=self.__class_name, method_name=_method_name)
        self.logger.exiting(class_name=self.__class_name, method_name=_method_name, result=result)
        return result

    def _revised_list_server_groups(self, server_groups, sg_targeting_limits):
        """
        Remove all server groups that are explicitly targeted to a cluster, server set or stand-alone
        managed server.
        :param server_groups: list of server groups applied by the extension templates
        :param sg_targeting_limits: list of targeting from the domainInfo section
        :return: server group list with the specific targeted server groups removed
        """
        _method_name = '_revised_list_server_groups'
        self.logger.entering(sg_targeting_limits, class_name=self.__class_name, method_name=_method_name)
        result = list()
        targeted_server_groups = sg_targeting_limits.keys()
        for server_group in server_groups:
            if server_group not in targeted_server_groups:
                result.append(server_group)
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
        result = list()
        for server_group, entity_names_list in sg_targeting_limits.iteritems():
            if entity_name in entity_names_list:
                result.append(server_group)
        if len(result) > 0:
            self.logger.fine('WLSDPLY-12243', entity_name, result, class_name=self.__class_name,
                             method_name=_method_name)
        return result

    def save_dyn_size(self, cluster_map):
        """
        Collect the before attribute of dynamic cluster size for each dynamic cluster. When
        setting dynamic clusters to server groups, the parameter dynamic cluster size is reset
        based on the parameters in the template server group WSM-CACHE-DYN-CLUSTER. A bug
        was opened 32075458, but probably will be seen as not a bug.
        :param cluster_map: cluster, server groups map
        :return: map of cluster and attribute_value
        """
        _method_name = 'save_dyn_size'
        bug_map = dict()
        for cluster in cluster_map.iterkeys():
            wlst_attribute = self.__locate_dynamic_attribute(cluster)
            bug_map[cluster] = self.wlst_helper.get(wlst_attribute)
            self.logger.finer('WLSDPLY-12560', cluster, bug_map[cluster],
                              class_name=self.__class_name, method_name=_method_name)
        return bug_map

    def restore_dyn_size(self, bug_map):
        """
        The setServerGroups reset the dynamic cluster size. Reset to original value.
        :param bug_map: map with cluster, dynamic cluster size
        """
        _method_name = 'restore_dyn_size'
        self.__put_back_in_edit()
        for cluster, attribute_value in bug_map.iteritems():
            if attribute_value is not None:
                wlst_attribute = self.__locate_dynamic_attribute(cluster)
                self.wlst_helper.set(wlst_attribute, attribute_value)
                self.logger.finer('WLSDPLY-12561', cluster, wlst_attribute,
                                  class_name=self.__class_name, method_name=_method_name)

    def __put_back_in_edit(self):
        """
        setServerGroups throws you out of edit. Put it back in.
        """
        if self.model_context.is_wlst_online():
            self.wlst_helper.edit()

    def __locate_dynamic_attribute(self, cluster):

        location = LocationContext()
        location.append_location(CLUSTER)
        location.add_name_token(self.aliases.get_name_token(location), cluster)
        location.append_location(DYNAMIC_SERVERS)
        list_path = self.aliases.get_wlst_list_path(location)
        existing_names = self.wlst_helper.get_existing_object_list(list_path)
        location.add_name_token(self.aliases.get_name_token(location), existing_names[0])
        attributes_path = self.aliases.get_wlst_attributes_path(location)
        self.wlst_helper.cd(attributes_path)
        wlst_attribute = self.aliases.get_wlst_attribute_name(location, DYNAMIC_CLUSTER_SIZE)
        return wlst_attribute
