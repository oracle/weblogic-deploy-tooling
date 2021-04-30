---
title: "Model Use Cases"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 3
---


### Contents

 - [Customizing the Administration Server](#administration-server-configuration)
 - [Modeling a Configured Cluster](#configured-cluster-sample)
 - [Modeling a JDBC Data Source](#jdbc-sample)
 - [Modeling a Work Manager](#work-manager-sample)
 - [Modeling Security Providers](#modeling-security-providers)
 - [Modeling WebLogic Users, Groups, and Roles](#modeling-weblogic-users-groups-and-roles)
 - [Modeling WebLogic User Password Credential Mapping](#modeling-weblogic-user-password-credential-mapping)
 - [Modeling ODL](#odl-configuration)
 - [Modeling Oracle HTTP Server (OHS)](#configuring-oracle-http-server)
 - [Targeting Server Groups](#targeting-server-groups)
 - [Using WDT with WebLogic Kubernetes Operator]({{< relref "/userguide/tools/kubernetes.md" >}})

 ### Administration Server Configuration

 The Create Domain Tool allows you to configure the Administration Server using a domain model. These examples show how some common configurations can be represented in the model.

 #### Using the Default Administration Server Configuration

 When the Create Domain Tool is run, the templates associated with your domain type will automatically create an Administration Server named `AdminServer`, with default values for all the attributes. If you don't need to change any of these attributes, such as `ListenAddress` or `ListenPort`, or any of the sub-folders, such as `SSL` or `ServerStart`, nothing needs to be added to the model.

 #### Customizing the Administration Server Configuration

 To customize the configuration of the default Administration Server, you will need to add a server with the default name `AdminServer`. Because you are not changing the name of the Administration Server, there is no need to specify the `AdminServerName` attribute under the topology section. This example shows some attributes and sub-folders:

 ```yaml
 topology:
     Server:
         AdminServer:
             ListenPort: 9071
             RestartDelaySeconds: 10
             ListenAddress: 'my-host-1'
             Log:
                 FileCount: 9
                 LogFileSeverity: Info
                 FileMinSize: 5000
             SSL:
                 HostnameVerificationIgnored: true
                 JSSEEnabled: true
                 ListenPort: 9072
                 Enabled: true
 ```

 The most common problem with this type of configuration is to misspell the name of the folder under `Server`, when it should be `AdminServer`. This will result in the creation of an Administration Server with the default name, and an additional Managed Server with the misspelled name.

 #### Configuring the Administration Server with a Different Name

 If you want the Administration Server to have a name other than the default `AdminServer`, you will need to specify that name in the `AdminServerName` attribute, and use that name in the `Server` section. This example uses the name `my-admin-server`:

 ```yaml
 topology:
     AdminServerName: 'my-admin-server'
     Server:
         'my-admin-server':
             ListenPort: 9071
             RestartDelaySeconds: 10
             ListenAddress: 'my-host-1'
             Log:
                 FileCount: 9
                 LogFileSeverity: Info
                 FileMinSize: 5000
             SSL:
                 HostnameVerificationIgnored: true
                 JSSEEnabled: true
                 ListenPort: 9072
                 Enabled: true
 ```

 The most common problem with this type of configuration is to mismatch the `AdminServerName` attribute with the name in the `Server` folder. This will change the name of the default Administration Server to the value of `AdminServerName`, and the folder under `Server` to be created as an additional Managed Server.

 The name of the Administration Server cannot be changed after domain creation, so any changes to the `AdminServerName` attribute will be ignored by the Update Domain Tool.


 #### Configured Cluster Sample

 This WDT domain model sample section has a typical configuration for a configured cluster with a single managed server, including connection information, logging setup, and other details.

 ```yaml
 topology:
     Cluster:
         'cluster-1':
             ClientCertProxyEnabled: true
             AutoMigrationTableName: MIGRATION_1
             DataSourceForAutomaticMigration: 'jdbc-1'
             ClusterMessagingMode: unicast
             FrontendHost: frontend.com
             FrontendHTTPPort: 9001
             FrontendHTTPSPort: 9002
             MigrationBasis: database
             NumberOfServersInClusterAddress: 5
             WeblogicPluginEnabled: true

     Server:
         'server-1':
             Cluster: 'cluster-1'  # this server belongs to cluster-1
             ListenAddress: 127.0.0.1
             ListenPort: 8001
             Machine: 'machine-1'
             Log:
                 DomainLogBroadcastSeverity: Error
                 FileCount: 7
                 FileMinSize: 5000
                 FileName: 'logs/AdminServer.log'
                 LogFileSeverity: Info
                 MemoryBufferSeverity: Notice
                 NumberOfFilesLimited: true
                 RotateLogOnStartup: true
                 RotationType: bySize
             SSL:
                 Enabled: true
                 ListenPort: 8002
             ServerStart:
                 Arguments: '-Dosgi=true -Dtangosol.coherence.management=all'
                 ClassPath: '/foo/bar,wlsdeploy/classpathLibraries/mylib.jar'
 ```
 There are additional sub-folders and attributes available for more configuration options. These can be determined using the [Model Help Tool]({{< relref "/userguide/tools/model_help.md" >}}). For example, this command will list the attributes and sub-folders for the `Server` folder:
 ```yaml
 ${WDT_HOME}/bin/modelHelp.sh -oracle_home /tmp/oracle topology:/Server
 ```

 For this sample, the machine named `machine-1` and the data source named `jdbc-1` should be defined elsewhere within this model, or should already exist in a domain that is being updated.


 #### JDBC Sample

 This WDT domain model sample section has a typical configuration for a JDBC data source, including targeting information, connection pool parameters, and other details.

 ```yaml
 resources:
     JDBCSystemResource:
         'datasource-1':
             Target: 'AdminServer,cluster-1'
             JdbcResource:
                 DatasourceType: GENERIC
                 JDBCConnectionPoolParams:
                     ConnectionReserveTimeoutSeconds: 10
                     InitialCapacity: 0
                     MaxCapacity: 5
                     MinCapacity: 0
                     TestConnectionsOnReserve: true
                     TestTableName: SQL ISVALID
                 JDBCDriverParams:
                     DriverName: oracle.jdbc.OracleDriver
                     PasswordEncrypted: '@@PROP:jdbc.password@@'
                     URL: 'jdbc:oracle:thin:@//localhost:1521/myDB'
                     Properties:
                         user:
                             Value: scott
 ```
 There are additional sub-folders and attributes available for more configuration options. These can be determined using the [Model Help Tool]({{< relref "/userguide/tools/model_help.md" >}}). For example, this command will list the attributes and sub-folders for the `JDBCSystemResource/JdbcResource` folder:
 ```yaml
 ${WDT_HOME}/bin/modelHelp.sh -oracle_home /tmp/oracle resources:/JDBCSystemResource/JdbcResource
 ```

 For this sample, the target cluster `cluster-1` should be defined elsewhere within this model, or should already exist in a domain that is being updated.

 It is recommended that credential fields, such as `PasswordEncrypted`, should not be stored as clear text in the model. Those values can be referenced in a separate variables file or in Kubernetes secrets, or the model can be encrypted using the [Encrypt Model Tool]({{< relref "/userguide/tools/encrypt.md" >}}).


 #### Work Manager Sample

 This WDT domain model sample section has typical configurations for a Work Manager and its related request classes and constraints. These elements are configured in the `SelfTuning` folder in the `resources` section of the model.
 ```yaml
 resources:
     SelfTuning:
         Capacity:
             capacity40:
                 Target: 'cluster-1'
                 Count: 40
         MaxThreadsConstraint:
             threeMax:
                 Target: 'cluster-1'
                 Count: 3
         MinThreadsConstraint:
             twoMin:
                 Target: 'cluster-1'
                 Count: 2
         FairShareRequestClass:
             appFairShare:
                 Target: 'cluster-1'
                 FairShare: 50
             highFairshare:
                 Target: 'cluster-1'
                 FairShare: 80
             lowFairshare:
                 Target: 'cluster-1'
                 FairShare: 20
         ResponseTimeRequestClass:
             fiveSecondResponse:
                 Target: 'cluster-1'
                 GoalMs: 5000
         ContextRequestClass:
             appContextRequest:
                 Target: 'cluster-1'
                 ContextCase:
                     Case1:
                         GroupName: Administrators
                         RequestClassName: highFairshare
                         Target: 'cluster-1'
                     Case2:
                         UserName: weblogic
                         RequestClassName: lowFairshare
                         Target: 'cluster-1'
         WorkManager:
             myWorkManager:
                 Capacity: capacity40
                 ContextRequestClass: appContextRequest
                 # FairShareRequestClass: appFairShare
                 IgnoreStuckThreads: true
                 MaxThreadsConstraint: threeMax
                 MinThreadsConstraint: twoMin
                 # ResponseTimeRequestClass: fiveSecondResponse
                 Target: 'cluster-1'
 ```
 In this sample, assignments for `FairShareRequestClass` and `ResponseTimeRequestClass` are included as comments under `myWorkManager`. A Work Manager can only specify one request class type.

 There are additional sub-folders and attributes available for more configuration options. These can be determined using the [Model Help Tool]({{< relref "/userguide/tools/model_help.md" >}}). For example, this command will list the attributes and sub-folders for the `WorkManager` folder:
 ```yaml
 ${WDT_HOME}/bin/modelHelp.sh -oracle_home /tmp/oracle resources:/WorkManager
 ```

 For this sample, the target cluster `cluster-1` should be defined elsewhere within this model, or should already exist in a domain that is being updated.


 ### Modeling Security Providers

 WebLogic Server security configuration requires special handling and causes the need for the model semantics to differ from other folders.  Because provider ordering is important, and to make sure that the ordering is correctly set in the newly created domain, the Create Domain Tool and Update Domain Tool require that all providers be specified in the model for any provider type that will be created or altered.  For example, if you want to change one of the providers in the provider type `AuthenticationProvider`, your model must specify all of the `AuthenticationProvider` providers and any non-default attributes for those providers.  In order to apply security providers, these tools will delete all providers from the target domain for those provider types specified in the model before adding the providers from the model to the target domain. Provider types that are omitted from the model will be unchanged.  Example provider types are `Adjudicator`, `AuthenticationProvider`, `Authorizer`, `CertPathProvider`, `CredentialMapper`, `PasswordValidator`, and `RoleMapper`.

 For example, if the model specified an `LDAPAuthenticator` and an `LDAPX509IdentityAsserter` similar to what is shown below, the `DefaultAuthenticator` and `DefaultIdentityAsserter` would be deleted.  In this example, other provider types like `RoleMapper` and `CredentialMapper` are not specified and would be left untouched by the tools.   

 ```yaml
 topology:
     SecurityConfiguration:
         Realm:
             myrealm:
                 AuthenticationProvider:
                     My LDAP authenticator:
                         LDAPAuthenticator:
                             ControlFlag: SUFFICIENT
                             PropagateCauseForLoginException: true
                             EnableGroupMembershipLookupHierarchyCaching: true
                             Host: myldap.example.com
                             Port: 389
                             UserObjectClass: person
                             GroupHierarchyCacheTTL: 600
                             SSLEnabled: true
                             UserNameAttribute: cn
                             Principal: 'cn=foo,ou=users,dc=example,dc=com'
                             UserBaseDn: 'OU=Users,DC=example,DC=com'
                             UserSearchScope: subtree
                             UserFromNameFilter: '(&(cn=%u)(objectclass=person))'
                             AllUsersFilter: '(memberOf=CN=foo,OU=mygroups,DC=example,DC=com)'
                             GroupBaseDN: 'OU=mygroups,DC=example,DC=com'
                             AllGroupsFilter: '(&(foo)(objectclass=group))'
                             StaticGroupObjectClass: group
                             StaticMemberDNAttribute: cn
                             StaticGroupDNsfromMemberDNFilter: '(&(member=%M)(objectclass=group))'
                             DynamicGroupObjectClass: group
                             DynamicGroupNameAttribute: cn
                             UseRetrievedUserNameAsPrincipal: true
                             KeepAliveEnabled: true
                             GuidAttribute: uuid
                     My LDAP IdentityAsserter:
                         LDAPX509IdentityAsserter:
                             ActiveType: AuthenticatedUser
                             Host: myldap.example.com
                             Port: 389
                             SSLEnabled: true
 ```    

 In order to keep the `DefaultAuthenticator` and `DefaultIdentityAsserter` while changing/adding providers, they must be specified in the model with any non-default attributes as shown in the example below.  Keep in mind, the ordering of providers in the model will be the order the providers are set in the WebLogic security configuration.

 ```yaml
 topology:
     SecurityConfiguration:
         Realm:
             myrealm:
                 AuthenticationProvider:
                     My LDAP authenticator:
                         LDAPAuthenticator:
                             ControlFlag: SUFFICIENT
                             PropagateCauseForLoginException: true
                             EnableGroupMembershipLookupHierarchyCaching: true
                             Host: myldap.example.com
                             Port: 389
                             UserObjectClass: person
                             GroupHierarchyCacheTTL: 600
                             SSLEnabled: true
                             UserNameAttribute: cn
                             Principal: 'cn=foo,ou=users,dc=example,dc=com'
                             UserBaseDn: 'OU=Users,DC=example,DC=com'
                             UserSearchScope: subtree
                             UserFromNameFilter: '(&(cn=%u)(objectclass=person))'
                             AllUsersFilter: '(memberOf=CN=foo,OU=mygroups,DC=example,DC=com)'
                             GroupBaseDN: 'OU=mygroups,DC=example,DC=com'
                             AllGroupsFilter: '(&(foo)(objectclass=group))'
                             StaticGroupObjectClass: group
                             StaticMemberDNAttribute: cn
                             StaticGroupDNsfromMemberDNFilter: '(&(member=%M)(objectclass=group))'
                             DynamicGroupObjectClass: group
                             DynamicGroupNameAttribute: cn
                             UseRetrievedUserNameAsPrincipal: true
                             KeepAliveEnabled: true
                             GuidAttribute: uuid
                     My LDAP IdentityAsserter:
                         LDAPX509IdentityAsserter:
                             ActiveType: AuthenticatedUser
                             Host: myldap.example.com
                             Port: 389
                             SSLEnabled: true
                     DefaultAuthenticator:
                         DefaultAuthenticator:
                             ControlFlag: SUFFICIENT
                     DefaultIdentityAsserter:
                         DefaultIdentityAsserter:

 ```
 #### Trust Service Identity Asserter

{{% notice note %}} The Trust Identity Asserter Security Provider is installed by JRF in 12c versions and newer.
{{% /notice %}}

 The JRF installed Trust Identity Asserter does not supply a schema file by default.  Before you can configure this asserter with WLST offline or WDT offline, you must first build the schema file using the `prepareCustomProvider` script.

 Here is an example of how to prepare and install a schema file from its MBean Jar File (MJF):

 ```bash
 export CONFIG_JVM_ARGS=-DSchemaTypeSystemName=TrustServiceIdentityAsserter

 ORACLE_HOME/oracle_common/common/bin/prepareCustomProvider.sh -mjf=ORACLE_HOME/oracle_common/modules/oracle.jps/jps-wls-trustprovider.jar -out ORACLE_HOME/oracle_common/lib/schematypes/jps-wls-trustprovider.schema.jar

 ```
 For FMW versions 12.1.2 and 12.1.3, replace `oracle.jps` in the example path above with:
 oracle.jps_12.1.2, or oracle.jps_12.1.3, respectively.

 #### Custom Security Providers

{{% notice note %}} Creating and updating domains with custom security providers is limited to WebLogic version 12.1.2 and newer.
{{% /notice %}}

 Prior to using this tooling to create or update a domain with a custom security provider, there are several prerequisites.  First, WebLogic Server requires the custom MBean JAR to be in the Oracle Home directory before it can be configured, `WLSERVER/server/lib/mbeantypes`.  Second, WebLogic Scripting Tool, WLST, requires that the schema JAR be placed in the Oracle Home directory before WLST offline can be used to discover it or configure it, `ORACLEHOME/oracle_common/lib/schematypes`.  Generating an MBean JAR documentation can be found in the WebLogic Server [documentation](https://docs.oracle.com/en/middleware/standalone/weblogic-server/14.1.1.0/devsp/generate_mbeantype.html).  Generating the schema JAR can be done with the `prepareCustomProvider` script provided in the WebLogic Server installation.

 WebLogic allows you to define an alternate directory other than `WLSERVER/server/lib/mbeantypes` by using the system property `-Dweblogic.alternateTypesDirectory=dir`. In order for the custom provider jars to be loaded correctly by WLST when discovering or configuring a domain, set this system property in the `WLSDEPLOY_PROPERTIES` environment variable.

 The format for a custom security provider is slightly different from a built-in provider in that the custom provider must supply the fully-qualified name of the class for the provider in the model between the provider name and the attributes for that provider.  Note that the generated Impl suffix is omitted from the name. In the custom `CredentialMapper` example below, note the location in the model of 'examples.security.providers.SampleCredentialMapper':

 ```yaml
         CredentialMapper:
             'Sample CredentialMapper':
                 'examples.security.providers.SampleCredentialMapper':
                     UserNameMapperClassName: 'examples.security.providers.CredentialMapperProviderImpl'
                     CredentialMappingDeploymentEnabled: true:
 ```

 #### Known Limitations

 - `Adjudicator` provider types cannot be added or modified due to a limitation in WLST.
 - `PasswordCredentials` provider types cannot be updated in WLST online.


 ### Modeling WebLogic Users, Groups, and Roles
 WebLogic Server has the ability to establish a set of users, groups, and global roles as part of the WebLogic domain creation. The WebLogic global roles become part of the WebLogic role mapper (for example, `XACMLRoleMapper`) and are specified under `domainInfo` in the `WLSRoles` section. The users and groups become part of the Embedded LDAP server (for example, `DefaultAuthenticator`) and are specified under `topology` in the `Security` section.

 #### WebLogic Global Roles
 The model allows for the definition of WebLogic roles that can augment the well known WebLogic global roles (for example, `Admin`, `Deployer`, `Monitor`, ...) in addition to defining new roles. When updating the well known WebLogic roles, an `UpdateMode` can be specified as `{ append | prepend | replace }` with the default being `replace` when not specified. Also, when updating the well known roles, the specified `Expression` will be a logical `OR` with the default expression. The `Expression` value for the role is the same as when using the WebLogic `RoleEditorMBean` for a WebLogic security role mapping provider.

 For example, the `WLSRoles` section below updates the well known `Admin`, `Deployer` and `Monitor` roles while adding a new global role with `Tester` as the role name:

 ```yaml
 domainInfo:
   WLSRoles:
     Admin:
       UpdateMode: append
       Expression: "?weblogic.entitlement.rules.IDCSAppRoleName(AppAdmin,@@PROP:AppName@@)"
     Deployer:
       UpdateMode: replace
       Expression: "?weblogic.entitlement.rules.AdministrativeGroup(@@PROP:Deployers@@)"
     Monitor:
       UpdateMode: prepend
       Expression: "?weblogic.entitlement.rules.AdministrativeGroup(AppMonitors)"
     Tester:
       Expression: "?weblogic.entitlement.rules.IDCSAppRoleName(AppTester,@@PROP:AppName@@)"
 ```

 The `Admin` role will have the expression appended to the default expression, the `Deployer` role expression will replace the default, the `Monitor` role expression will be prepended to the default expression and `Tester` will be a new role with the specified expression.

 In addition, the `Expression` value can use the variable placeholder syntax specified when running the [Create Tool]({{< relref "/userguide/tools/create.md" >}}) as shown in the above example.

 #### WebLogic Users and Groups
 The model allows for the definition of a set of users and groups that will be loaded into the WebLogic Embedded LDAP Server (for example, `DefaultAuthenticator`). New groups can be specified and users can be added as members of the new groups or existing groups such as the `Administrators` group which is defaulted to be in the WebLogic `Admin` global role. Please see Known Limitations below for additional information on users and groups.

 The user password can be specified with a placeholder or encrypted with the [Encrypt Tool](encrypt.md). An example `Security` section that adds an additional group `AppMonitors`, adds two new users and places the users into groups is as follows:

 ```yaml
 topology:
   Security:
     Group:
       AppMonitors:
         Description: Application Monitors
     User:
       john:
          Password: welcome1
          GroupMemberOf: [ AppMonitors, Administrators ]
       joe:
          Password: welcome1
          GroupMemberOf: [ AppMonitors ]
 ```

 #### Known Limitations

 - The processing of users, groups, and roles will only take place when using the [Create Domain Tool]({{< relref "/userguide/tools/create.md" >}}).
 - WebLogic global roles are only supported with WebLogic Server version 12.2.1 or greater.
 - WebLogic global roles are only updated for the WebLogic security XACML role mapping provider (for example, `XACMLRoleMapper`).
 - The user and group processing is not complete, currently, users cannot be assigned to groups. Users created using the `Security` section are automatically added to the `Administrators` group and are not added to the groups specified. See [Known Issues]({{< relref "/release-notes#assigning-security-groups-to-users" >}}) for information about a patch for this issue.

 ### Modeling WebLogic User Password Credential Mapping

 The Create Domain Tool can be used to create user password credential mappings for use with the `DefaultCredentialMapper` security provider. Information in the model will be used to create a credential mapping file that will be imported the first time the Administration Server is started. This example shows how mappings are represented in the model:
 ```yaml
domainInfo:
    WLSUserPasswordCredentialMappings:
        CrossDomain:
            map1:
                RemoteDomain: otherDomain
                RemoteUser: otherUser
                RemotePassword: '@@PROP:other.pwd@@'
        RemoteResource:
            map2:
                Protocol: http
                RemoteHost: remote.host
                RemotePort: 7020
                Path: /app/buy
                Method: POST
                User: user1
                RemoteUser: remoteUser
                RemotePassword: '@@PROP:remote.pwd@@'
            map3:
                Protocol: https
                RemoteHost: remote2.host
                RemotePort: 7030
                Path: /app/sell
                Method: GET
                User: 'user1,user2'
                RemoteUser: remoteUser2
                RemotePassword: '@@PROP:remote2.pwd@@'
```
 In this example, the mapping `map1` creates a cross-domain credential mapping that provides access from this domain to the remote domain `otherDomain` as the user `otherUser` with the configured password.

 The mapping `map2` creates a remote resource credential mapping that will give the local user `user1` access to a single remote resource on `remote.host` as the user `remoteUser` with the configured password. The mapping `map3` is similar, but provides access to a different remote resource for two local users, `user1` and `user2`.

 The names of the mapping sections in the model, such as `map1` and `map2`, are used to group the attributes for each mapping in the model and are not part of the resulting credential mappings. These names should be unique for each mapping of a particular type.

 ### ODL Configuration

 Oracle Diagnostic Logging (ODL) can be configured and updated with Create Domain, Update Domain, and Deploy Applications Tools, starting with WDT release 1.5.2. ODL configuration is only supported for offline mode in WDT. ODL configuration is not added when a model is created using the Discover Domain Tool. This example shows how some common configuration elements can be represented in the model.

 ```yaml
 resources:
     ODLConfiguration:
         config1:
             Servers: "m1, m2"
             AddJvmNumber: true
             HandlerDefaults:
                 abc: r123
                 xyz: k890
             Handler:
                 'my-handler':
                     Class: 'com.my.MyHandler'
                     Level: 'TRACE:32'
                     ErrorManager: 'com.my.MyErrorManager'
                     Filter: 'com.my.MyFilter'
                     Formatter: 'com.my.MyFormatter'
                     Encoding: 'UTF-8'
                     Properties:
                         'path': '/home/me/mypath"
                 'quicktrace-handler':
                     Filter: 'oracle:dfw:incident:IncidentDetectionLogFilter'
                     Properties:
                         path: '${domain.home}/servers/${weblogic.Name}/logs/${weblogic.Name}-myhistory.log'
                         useSourceClassandMethod: 'true'
             Logger:
                 'my-logger':
                     Level: 'NOTIFICATION:1'
                     UseParentHandlers: true
                     Filter: 'oracle:dfw:incident:IncidentDetectionLogFilter'
                     Handlers: 'richard-handler,owsm-message-handler'
                 'oracle.sysman':
                     Handlers: [
                         'my-handler',
                         'owsm-message-handler'
                     ]
         config2:
             Servers: 'AdminServer'
             HandlerDefaults:
                 path: '/home/me/otherpath'
                 maxFileSize: 5242880
 ```

 Each named ODL configuration (such as `config1`) is updated for each of the managed servers in the `Servers` list. Handlers and loggers that exist in the current configuration are updated, and any new ones are created and updated.

 Unlike other WDT model elements, ODL configuration is not updated using WLST MBeans. The configuration is written directly to the file system, in the file `<domain_home>/config/fmwconfig/servers/<server>/logging.xml`.  


 ### Configuring Oracle HTTP Server

 Starting with WDT 1.8.0, you can configure and update Oracle HTTP Server (OHS) using the Create Domain, Update Domain, and Deploy Applications Tools, in offline mode only. To discover the OHS configuration, use the Discover Domain Tool, in offline mode only.

 #### Prerequisites

 In order to configure and use OHS, it must be installed in the Oracle Home directory used to create the domain. You can download OHS [here](https://www.oracle.com/middleware/technologies/webtier-downloads.html).

 The OHS template must be present in the WDT domain type definition file used to create or update the domain. For more information on creating a custom definition, see [Domain Type Definitions]({{< relref "/concepts/tool_configuration#domain-type-definitions" >}}).

 You create a copy of an existing domain type definition file, add the template to that file, and then reference that file on the WDT command line. For example, if you want to create a domain with Oracle HTTP Server based on a Restricted JRF domain, then you would first create a copy of the file `WLSDEPLOY_HOME/lib/typedefs/RestrictedJRF.json` in the same directory, such as `WLSDEPLOY_HOME/lib/typedefs/HttpServer.json`. In this example, you would change the existing `extensionTemplates` section to include the additional OHS template. The original value is:
 ```
 "extensionTemplates": [ "Oracle Restricted JRF", "Oracle Enterprise Manager-Restricted JRF" ],
 ```
 The revised value would be:
 ```
 "extensionTemplates": [ "Oracle Restricted JRF", "Oracle Enterprise Manager-Restricted JRF", "Oracle HTTP Server (Restricted JRF)" ],
 ```
 The file name of this new domain type (without the `.json` extension) is used with the `-domain_type` argument on the WDT command line. For example, the command line to create a domain using the `HttpServer.json` file from the previous steps would look like:  
 ```
 WLSDEPLOY_HOME/bin/createDomain -oracle_home /etc/oracle ... -domain_type HttpServer
 ```

 #### Configuring the Model

 Configuring OHS typically involves adding two top-level folders to the `resources` section of the model, `SystemComponent` and `OHS`. Here is an example:
 ```yaml
 resources:
     SystemComponent:
         'my-ohs':
             ComponentType: 'OHS'
             Machine: 'my-machine'
     OHS:
         'my-ohs':
             AdminHost: '127.0.0.1'
             AdminPort: '9324'
             ListenAddress: '127.0.0.1'
             ListenPort: '7323'
             SSLListenPort: '4323'
             ServerName: 'http://localhost:7323'
 ```
 Each name under the `OHS` folder must match a name under the `SystemComponent` folder in the model, or the name of a `SystemComponent` element that has been previously created. In this example, the name `my-ohs` is in both places.

 The `ComponentType` field of the `SystemComponent` element must be set to `OHS` in order to allow configuration of the corresponding `OHS` folders.

 You can use the [Model Help Tool]({{< relref "/userguide/tools/model_help.md" >}}) to determine the complete list of folders and attributes that can be used in these sections of the model. For example, this command will list the attributes in the `OHS` folder:
 ```yaml
 ${WDT_HOME}/bin/modelHelp.sh -oracle_home /tmp/oracle resources:/OHS
 ```


 ### Targeting Server Groups

 To create more complex domains with clusters of different types, it is necessary to control the targeting of server groups to managed servers.  By default, all server groups in the domain type definition are targeted to all managed servers.  To create a SOA domain with SOA and OSB clusters, simply add the OSB template and server group to the SOA domain definition, as shown below.

 ```json
 {
     "name": "SOA",
     "description": "SOA type domain definitions",
     "versions": {
         "12.2.1.3": "SOA_12213"
     },
     "definitions": {
         "SOA_12213": {
             "baseTemplate": "Basic WebLogic Server Domain",
             "extensionTemplates": [
                 "Oracle SOA Suite",
                 "Oracle Service Bus"
             ],
             "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR",  "SOA-MGD-SVRS",  "OSB-MGD-SVRS-COMBINED" ],
             "dynamicClusterServerGroupsToTarget": [ "SOA-DYN-CLUSTER" ],
             "rcuSchemas": [ "STB", "WLS", "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS", "UCSUMS", "SOAINFRA" ]
         }
     }
 }
 ```

 Then, use the `ServerGroupTargetingLimits` map in the `domainInfo` section to limit the targeting of the Web Services Manager, SOA, and OSB server groups to the `soa_cluster` or `osb_cluster`, as appropriate.  In the example below, notice that the `JRF-MAN-SVR` server group is not listed; therefore, it will use the default targeting and be targeted to all managed servers.  The value of each element in this section is a logical list of server and/or cluster names.  As shown in the example, the value for each server group can be specified as a list, a comma-separated string, or a single-valued string.  There is no semantic difference between listing a cluster's member server names versus using the cluster name; the example uses these simply to show what is possible.

 ```yaml
 domainInfo:
     AdminUserName: weblogic
     AdminPassword: welcome1
     ServerStartMode: prod
     ServerGroupTargetingLimits:
         'WSMPM-MAN-SVR': soa_cluster
         'SOA-MGD-SVRS': 'soa_server1,soa_server2'
         'OSB-MGD-SVRS-COMBINED': [ osb_server1, osb_server2 ]

 topology:
     Name: soa_domain
     AdminServerName: AdminServer
     Cluster:
         soa_cluster:
         osb_cluster:
     Server:
         AdminServer:
             ListenAddress: myadmin.example.com
             ListenPort: 7001
             Machine: machine1
             SSL:
                 Enabled: true
                 ListenPort: 7002
         soa_server1:
             ListenAddress: managed1.example.com
             ListenPort: 8001
             Cluster: soa_cluster
             Machine: machine2
             SSL:
                 Enabled: true
                 ListenPort: 8002
         soa_server2:
             ListenAddress: managed2.example.com
             ListenPort: 8001
             Cluster: soa_cluster
             Machine: machine3
             SSL:
                 Enabled: true
                 ListenPort: 8002
         osb_server1:
             ListenAddress: managed1.example.com
             ListenPort: 9001
             Cluster: osb_cluster
             Machine: machine2
             SSL:
                 Enabled: true
                 ListenPort: 9002
         osb_server2:
             ListenAddress: managed2.example.com
             ListenPort: 9001
             Cluster: osb_cluster
             Machine: machine3
             SSL:
                 Enabled: true
                 ListenPort: 9002
     UnixMachine:
         machine1:
             NodeManager:
                 ListenAddress: myadmin.example.com
                 ListenPort: 5556
         machine2:
             NodeManager:
                 ListenAddress: managed1.example.com
                 ListenPort: 5556
         machine3:
             NodeManager:
                 ListenAddress: managed2.example.com
                 ListenPort: 5556
     SecurityConfiguration:
         NodeManagerUsername: weblogic
         NodeManagerPasswordEncrypted: welcome1
 ```

 #### Targeting Dynamic Cluster Server Groups
 Dynamic Cluster Server Groups are server groups that can be targeted to dynamic clusters. Dynamic clusters were added in WebLogic Server version 12.1.2. In WebLogic Server version 12.2.1.1, the ability to target a single dynamic server group to a dynamic cluster was added. In WebLogic Server Version 12.2.1.4, you now have the ability to target multiple dynamic server groups to a dynamic cluster.

 To enable targeting of dynamic server groups to dynamic clusters, add the dynamicClusterServerGroupsToTarget entry with any dynamic server groups you wish to be targeted to the dynamic clusters in your model or domain. This list must only contain one dynamic server group if you are running a version of WebLogic Server earlier than 12.2.1.4.
 ```json
 {
   "definitions": {
     "dynamicClusterServerGroupsToTarget" : [ "WSMPM-DYN-CLUSTER", "WSM-CACHE-DYN-CLUSTER" ]
   }
 }
 ```
 If you wish to specify which dynamic server group to target to a dynamic server, add DynamicClusterServerGroupTargetingLimits to the domainInfo of your model. This entry can coexist with managed servers defined in ServerGroupTargetingLimits.
 ```yaml
 domainInfo:
     AdminUserName: weblogic
     AdminPassword: welcome1
     ServerStartMode: prod
     DynamicClusterServerGroupTargetingLimits:
         'SOA-DYN-CLUSTER': 'soa_dynamic_cluster'
 ```
