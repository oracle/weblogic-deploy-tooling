## Known Issues for Oracle WebLogic Server Deploy Tooling

The following list are known issues. The issue may contain a workaround or an associated issue number.

### Discover Domain Tool Severe Messages

**ISSUE**:
The discoverDomain STDOUT contains many SEVERE messages about cd() and ls() when it is run against a 12.2.1 domain. The discover tool navigates through the domain MBeans using wlst to determine which MBeans are present in a domain. When it tests an MBean that is not present, the erroneous message is logged by Weblogic WLST. There is no 12.2.1 PSU available to address this WLST problem. It is resolved in 12.2.1.1.

**ACTION**:
Ignore the following messages logged during discover of a 12.2.1 domain.
```
<Jan 14, 2019 1:14:21 PM> <SEVERE> <CommandExceptionHandler> <handleException> <> <Error: cd() failed.>
<Jan 14, 2019 1:14:21 PM> <SEVERE> <CommandExceptionHandler> <handleException> <> <Error: ls() failed.>
```

### Create Domain Tool with 11G JRF Domains

**ISSUE**:
The Create Domain Tool cannot initialize RCU for 11g JRF domains. The tool will issue error messages in the log, and terminate the create process.

**ACTION**:
Run the WLS `rcu` command before executing createDomain for JRF domains

### Credential in Security Configuration

**ISSUE**: For WLS versions before 14.1.1, there is a problem setting the `CredentialEncrypted` attribute in the `topology/SecurityConfiguration` folder. The value is not encrypted properly in the configuration, and the domain will fail to start with the error:
```
java.lang.IllegalArgumentException: In production mode, it's not allowed to set a clear text value to the property: CredentialEncrypted of SecurityConfigurationMBean
```
**ACTION**: Contact Oracle Support to obtain the patch for the bug number 30874677 for your WebLogic version before running the tool.
