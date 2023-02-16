---
title: "Limitations"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 4
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
