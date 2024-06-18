---
title: "Limitations"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 7
description: "Review existing WDT limitations."
---


The following sections describe known limitations for WebLogic Deploy Tooling. Each issue may contain a workaround or an associated issue number.

#### WebLogic Kubernetes Operator Model-in-Image domains fail when using WebLogic Deploy Tooling 4.0.0 (and newer)
**ISSUE**:
Deploy a WebLogic Kubernetes Operator domain with Model-in-Image (MII) produces introspector failures.

**ACTION**:
WDT 4.0 made significant changes to archive file path handling that required changes in WebLogic Kubernetes Operator,
which became available starting in WebLogic Kubernetes Operator 4.2.0.  Upgrade to WebLogic Kubernetes Operator 4.2.0+
to resolve the issue.

#### Discover Domain Tool `SEVERE` messages

**ISSUE**:
The `discoverDomain` STDOUT contains many SEVERE messages about `cd()` and `ls()` when it is run against a 12.2.1.0
domain. The Discover Domain Tool navigates through the domain MBeans using WLST to determine which MBeans are present
in a domain. When it tests an MBean that is not present, an error message is logged by WLST. There is no 12.2.1.0 PSU
available to address this WLST problem. It is resolved in 12.2.1.1.

**ACTION**:
Ignore the following messages logged during discovery of a 12.2.1.0 domain.
```
<Jan 14, 2019 1:14:21 PM> <SEVERE> <CommandExceptionHandler> <handleException> <> <Error: cd() failed.>
<Jan 14, 2019 1:14:21 PM> <SEVERE> <CommandExceptionHandler> <handleException> <> <Error: ls() failed.>
```

#### Create Domain Tool with 11g JRF domains

**ISSUE**:
The Create Domain Tool cannot initialize RCU for 11g JRF domains. The tool will issue error messages in the log and
terminate the create process.

**ACTION**:
Run the WLS `rcu` command before executing `createDomain` for JRF domains

#### Credential in security configuration

**ISSUE**: For WLS versions prior to 14.1.1, there is a problem setting the `CredentialEncrypted` attribute in the
`topology/SecurityConfiguration` folder. The value is not encrypted properly in the configuration and the domain will
fail to start with the error:
```
java.lang.IllegalArgumentException: In production mode, it's not allowed to set a clear text value to the property: CredentialEncrypted of SecurityConfigurationMBean
```
**ACTION**: Contact Oracle Support to obtain the patch for bug number 30874677 for your WebLogic Server version before running the tool.

#### Problems setting `RotateLogOnStartup` attribute

**ISSUE**: For existing WLS versions, there is a problem setting the `RotateLogOnStartup` attribute in various log file
folders. The value is not persisted correctly, and the assignment will not be present when the domain is started.

**ACTION**: Contact Oracle Support to obtain the patch for bug number 29547985 for your WebLogic Server version before running the tool.

#### Discover Domain tool does not discover users or groups

**ISSUE**: Discovering a domain does not attempt to discover users and groups defined in any configured Authentication Provider type.

**ACTION**: This should only be an issue for the domains using the DefaultAuthenticator, which uses the Embedded LDAP
server that runs inside WebLogic Server as its user and group store.  To discover the users and groups in the
DefaultAuthenticator, use the `-discover_security_provider_data` switch with an argument that includes the
DefaultAuthenticator (e.g., `ALL` or a comma-separated list of provider types like `DefaultAuthenticator,DefaultCredentialMapper`).

#### JRF Domain configuration files containing clear text password

**ISSUE**: After a JRF domain is created, the `jps-config.xml` and `jps-config-jse.xml` files contain clear text password for the key store.

**ACTION**: You will need to create a key store using Oracle Wallet and change the key store provider priority in the
JVM. See Oracle Support Doc ID 2215283.1 for details. If you are creating a JRF domain using Oracle Autonomous
Transaction Database, you can use the SSO key stores instead of JKS key stores, the generated `jps-config.xml` and
`jps-config-jse.xml` files will then use the SSO key stores without any clear text password.

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

**ISSUE**: WDT does not correctly handle the `@@JAVA_HOME@@`, `@@PWD@@`, and `@@TMP` path tokens.

**ACTION**: Do not use these path tokens in an SSH context because WDT does not currently provide a way for the user
to supply "remote" values for these paths.

### Production Redeployment of Versioned Applications

**ISSUE**: WDT Update Domain does not properly deploy a new version of an application to support non-disruptive updates.

**ACTION**: While we fully intend to resolve this issue in an upcoming release, the workaround for now is to use the
`weblogic.Deployer` tool to redeploy the application pointing at the new source files, as described in the
[WebLogic Server documentation](https://docs.oracle.com/en/middleware/fusion-middleware/weblogic-server/12.2.1.4/depgd/redeploy.html#GUID-2C0A6D50-3D20-4167-8091-4A5546DEFD6C).
