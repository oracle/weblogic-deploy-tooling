#### WDT Version 1.9.12

Additional features in this release:

* FMW Platform specific patches are now included in `--recommendedPatches` for all WLS-based installer types.
* Java Required Files specific patches are now included in `--recommendedPatches` for all FMW-based installer types.

Issues addressed in this release:

* Increased the default version of HTTP retries to 10 to improve reliability with retrieving patch information from Oracle.


#### WDT Version 1.9.11

Issues addressed in this release:

* Fixed validate process to recognize float values as strings.
* Fixed JMS Server issue with jarray in store.
* Fixed issue with recognizing NodeManager properties user and password as credentials.
* Fixed discovery of SAFRemoteContext.
* Fixed discovery of ServerTemplate DataSource.

#### Known Issues for WebLogic Deploy Tooling

The following list contains known issues. Each issue may contain a workaround or an associated issue number.

##### Discover Domain Tool SEVERE Messages

**ISSUE**:
The `discoverDomain` STDOUT contains many SEVERE messages about `cd()` and `ls()` when it is run against a 12.2.1.0 domain. The Discover Domain Tool navigates through the domain MBeans using WLST to determine which MBeans are present in a domain. When it tests an MBean that is not present, an error message is logged by WLST. There is no 12.2.1.0 PSU available to address this WLST problem. It is resolved in 12.2.1.1.

**ACTION**:
Ignore the following messages logged during discovery of a 12.2.1.0 domain.
```
<Jan 14, 2019 1:14:21 PM> <SEVERE> <CommandExceptionHandler> <handleException> <> <Error: cd() failed.>
<Jan 14, 2019 1:14:21 PM> <SEVERE> <CommandExceptionHandler> <handleException> <> <Error: ls() failed.>
```

##### Create Domain Tool with 11g JRF Domains

**ISSUE**:
The Create Domain Tool cannot initialize RCU for 11g JRF domains. The tool will issue error messages in the log and terminate the create process.

**ACTION**:
Run the WLS `rcu` command before executing `createDomain` for JRF domains

##### Credential in Security Configuration

**ISSUE**: For WLS versions prior to 14.1.1, there is a problem setting the `CredentialEncrypted` attribute in the `topology/SecurityConfiguration` folder. The value is not encrypted properly in the configuration and the domain will fail to start with the error:
```
java.lang.IllegalArgumentException: In production mode, it's not allowed to set a clear text value to the property: CredentialEncrypted of SecurityConfigurationMBean
```
**ACTION**: Contact Oracle Support to obtain the patch for bug number 30874677 for your WebLogic Server version before running the tool.

##### Assigning Security Groups to Users

**ISSUE**: For WLS versions prior to 14.1.1, there is a problem setting the `GroupMemberOf` attribute in the `topology/Security/User` folder. The value is not persisted correctly, and the assignment will not be present when the domain is started.

**ACTION**: Contact Oracle Support to obtain the patch for bug number 30319071 for your WebLogic Server version before running the tool.
