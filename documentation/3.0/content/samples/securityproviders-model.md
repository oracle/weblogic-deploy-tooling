---
title: "Modeling security providers"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 5
description: "Special handling and model semantics for WebLogic Server security configuration."
---



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
 #### Trust service identity asserter

{{% notice note %}} The Trust Identity Asserter Security Provider is installed by JRF in 12c versions and newer.
{{% /notice %}}

 The JRF installed Trust Identity Asserter does not supply a schema file by default.  Before you can configure this asserter with WLST offline or WDT offline, you must first build the schema file using the `prepareCustomProvider` script.

 Here is an example of how to prepare and install a schema file from its MBean Jar File (MJF):

 ```bash
 $ export CONFIG_JVM_ARGS=-DSchemaTypeSystemName=TrustServiceIdentityAsserter

 $ ORACLE_HOME/oracle_common/common/bin/prepareCustomProvider.sh -mjf=ORACLE_HOME/oracle_common/modules/oracle.jps/jps-wls-trustprovider.jar -out ORACLE_HOME/oracle_common/lib/schematypes/jps-wls-trustprovider.schema.jar

 ```
 For FMW versions 12.1.2 and 12.1.3, replace `oracle.jps` in the example path above with:
 oracle.jps_12.1.2, or oracle.jps_12.1.3, respectively.

 #### Custom security providers

{{% notice note %}} Creating and updating domains with custom security providers is limited to WebLogic version 12.1.2 and newer.
{{% /notice %}}

 Prior to using this tooling to create or update a domain with a custom security provider, there are several prerequisites.  First, WebLogic Server requires the custom MBean JAR to be in the Oracle Home directory before it can be configured, `WLSERVER/server/lib/mbeantypes`.  Second, WebLogic Scripting Tool, WLST, requires that the schema JAR be placed in the Oracle Home directory before WLST offline can be used to discover it or configure it, `ORACLEHOME/oracle_common/lib/schematypes`.  Generating an MBean JAR documentation can be found in the WebLogic Server [documentation](https://docs.oracle.com/en/middleware/standalone/weblogic-server/14.1.1.0/devsp/generate_mbeantype.html).  Generating the schema JAR can be done with the `prepareCustomProvider` script provided in the WebLogic Server installation.

For the MBean jar, WebLogic allows you to define an alternate directory other than `WLSERVER/server/lib/mbeantypes` by using the system property `-Dfmwconfig.alternateTypesDirectory=dir`. For the WebLogic MBean schema type jar, you can use an alternate location by using `-Dfmwconfig.alternateSchemaDirectory=dir`. In order for the custom provider jars to be loaded correctly by WLST when discovering or configuring a domain, set this system property in the `WLSDEPLOY_PROPERTIES` environment variable. Both of the properties take a comma separated list of paths to directories containing the corresponding type of jar.

 The format for a custom security provider is slightly different from a built-in provider in that the custom provider must supply the fully-qualified name of the class for the provider in the model between the provider name and the attributes for that provider.  Note that the generated Impl suffix is omitted from the name. In the custom `CredentialMapper` example below, note the location in the model of 'examples.security.providers.SampleCredentialMapper':

 ```yaml
         CredentialMapper:
             Sample CredentialMapper:
                 examples.security.providers.SampleCredentialMapper:
                     UserNameMapperClassName: examples.security.providers.CredentialMapperProviderImpl
                     CredentialMappingDeploymentEnabled: true
 ```

 #### Known limitations

 - `Adjudicator` provider types cannot be added or modified due to a limitation in WLST.
 - `PasswordCredentials` provider types cannot be updated in WLST online.
