### Modeling Security Providers
WebLogic Server security configuration requires special handling and causes the need for the model semantics to differ from other folders.  Because provider ordering is important, and to make sure that the ordering is correctly set in the newly created domain, the Create Domain Tool and Update Domain Tool require that all providers be specified in the model for any provider type that will be created or altered.  For example, if you want to change one of the providers in the provider type `AuthenticationProvider`, your model must specify all of the `AuthenticationProvider` providers and any non-default attributes for those providers.  In order to apply security providers, these tools will delete all providers from the target domain for those provider types specificed in the model before adding the providers from the model to the target domain. Provider types that are omitted from the model will be unchanged.  Example provider types are `Adjudicator`, `AuthenticationProvider`, `Authorizer`, `CertPathProvider`, `CredentialMapper`, `PasswordValidator`, and `RoleMapper`.

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

#### Custom Security Providers

**NOTE:** Creating and updating domains with custom security providers is limited to WebLogic version 12.1.2 and newer.

Prior to using this tooling to create or update a domain with a custom security provider, there are several prerequisites.  First, WebLogic Server requires the custom MBean JAR to be in the Oracle Home directory before it can be configured, WLSERVER/server/lib/mbeantypes.  Second, WebLogic Scripting Tool, WLST, requires that the schema JAR be placed in the Oracle Home directory before WLST offline can be used to configure it, ORACLEHOME/oracle_common/lib/schematypes.  Generating an MBean JAR documentation can be found in the WebLogic Server [documentation](https://docs.oracle.com/middleware/12213/wls/DEVSP/generate_mbeantype.htm#DEVSP617).  Generating the schema JAR can be done with the prepareCustomProvider script provided in the WebLogic Server installation.

The format for a custom security provider is slightly different from a built-in provider in that the custom provider must supply the fully-qualified name of the class for the provider in the model between the provider name and the attributes for that provider.  Note that the generated Impl suffix is ommitted from the name. In the custom `CredentialMapper` example below, note the location in the model of 'examples.security.providers.SampleCredentialMapper':

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
