---
title: "Limitations"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 7
description: "Review existing WDT limitations."
---


The following sections describe known limitations for WebLogic Deploy Tooling. Each issue may contain a workaround or an associated issue number.

#### Discover Domain Tool `SEVERE` messages

**ISSUE**:
The `discoverDomain` STDOUT contains many SEVERE messages about `cd()` and `ls()` when it is run against a 12.2.1.0 domain. The Discover Domain Tool navigates through the domain MBeans using WLST to determine which MBeans are present in a domain. When it tests an MBean that is not present, an error message is logged by WLST. There is no 12.2.1.0 PSU available to address this WLST problem. It is resolved in 12.2.1.1.

**ACTION**:
Ignore the following messages logged during discovery of a 12.2.1.0 domain.
```
<Jan 14, 2019 1:14:21 PM> <SEVERE> <CommandExceptionHandler> <handleException> <> <Error: cd() failed.>
<Jan 14, 2019 1:14:21 PM> <SEVERE> <CommandExceptionHandler> <handleException> <> <Error: ls() failed.>
```

#### Create Domain Tool with 11g JRF domains

**ISSUE**:
The Create Domain Tool cannot initialize RCU for 11g JRF domains. The tool will issue error messages in the log and terminate the create process.

**ACTION**:
Run the WLS `rcu` command before executing `createDomain` for JRF domains

#### Credential in security configuration

**ISSUE**: For WLS versions prior to 14.1.1, there is a problem setting the `CredentialEncrypted` attribute in the `topology/SecurityConfiguration` folder. The value is not encrypted properly in the configuration and the domain will fail to start with the error:
```
java.lang.IllegalArgumentException: In production mode, it's not allowed to set a clear text value to the property: CredentialEncrypted of SecurityConfigurationMBean
```
**ACTION**: Contact Oracle Support to obtain the patch for bug number 30874677 for your WebLogic Server version before running the tool.

#### Assigning security groups to users

**ISSUE**: For WLS versions prior to 14.1.1, there is a problem setting the `GroupMemberOf` attribute in the `topology/Security/User` folder. The value is not persisted correctly, and the assignment will not be present when the domain is started.

**ACTION**: Contact Oracle Support to obtain the patch for bug number 30319071 for your WebLogic Server version before running the tool.

#### Problems setting `RotateLogOnStartup` attribute

**ISSUE**: For existing WLS versions, there is a problem setting the `RotateLogOnStartup` attribute in various log file folders. The value is not persisted correctly, and the assignment will not be present when the domain is started.

**ACTION**: Contact Oracle Support to obtain the patch for bug number 29547985 for your WebLogic Server version before running the tool.

#### Discover Domain tool does not discover users or groups

**ISSUE**: Discovering a domain does not attempt to discover users and groups defined in any configured Authentication Provider type.

**ACTION**: This should only be an issue for the domains using the DefaultAuthenticator, which uses the Embedded LDAP
server that runs inside WebLogic Server as its user and group store.  Oracle recommends using an authentication provider
with an external user and group store for managing users and groups.  For example, a Microsoft Active Directory server
with the LDAP Authenticator or a database server with the SQL Authenticator.  This allows any domain created using the
discovered model to use the same user and group store so that there is no need to export/import users and groups.  If a
new user and group store is desired, these external stores natively provide export and import mechanisms for moving
users and groups.  If this is not an option, then the user will need to hand-edit the discovered model file to add any
users and groups not created by default.

#### JRF Domain configuration files containing clear text password

**ISSUE**: After a JRF domain is created, the `jps-config.xml` and `jps-config-jse.xml` files contain clear text password for the key store.

**ACTION**: You will need to create a key store using Oracle Wallet and change the key store provider priority in the JVM. See Oracle Support Doc ID 2215283.1 for details.
If you are creating a JRF domain using Oracle Autonomous Transaction Database, you can use the SSO key stores instead of JKS key stores,  
the generated `jps-config.xml` and `jps-config-jse.xml` files will then use the SSO key stores without any clear text password.

```yaml
domainInfo:
    RCUDbInfo:
     databaseType : ATP
     rcu_prefix : FMW
     rcu_schema_password : '...'
     rcu_admin_password: '...'
     rcu_db_user : admin
     tns.alias : myatp_tp
     javax.net.ssl.keyStoreType: SSO
     javax.net.ssl.trustStoreType: SSO
```

### SSH usage

**ISSUE**: WDT Create Domain does not appear to support SSH.

**ACTION**: WDT Create Domain does not support SSH cause domain creation needs to run on the machine where the domain
will exist to ensure that paths in the generated domain files point to the actual Java and Oracle Homes.  To support
Create Domain via SSH, WDT would need to install itself on the remote machine and then execute its commands there.
The workaround is for the user to temporarily install WDT, create the domain, and uninstall WDT.

**ISSUE**: WDT always uses the local Oracle Home to determine the WebLogic version and patch level, which determines
what alias data WDT loads.  If the remote Oracle Home version is different, this may cause issues where WDT incorrectly
considers folders or attributes to be available or not available for the remote domain.

**ACTION**: Ensure that the local and remote Oracle Homes are using the same WebLogic version and patch levels.

**ISSUE**: WDT does not correctly handle the `@@WL_HOME@@` path token.

**ACTION**: WDT computes the effective WL_HOME value based off the `-remote_oracle_home` argument and the local WebLogic
version.  This should not be a problem unless the local and remote Oracle Homes are using different WebLogic versions.
Update the local WebLogic version to match the remote version to resolve this problem.

**ISSUE**: WDT does not correctly handle the `@@JAVA_HOME@@`, `@@PWD@@`, and `@@TMP` path tokens.

**ACTION**: Do not use these path tokens in an SSH context because WDT does not currently provide a way for the user
to supply "remote" values for these paths.
