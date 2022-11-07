+++
title = "Release Notes"
date = 2019-02-22T15:27:38-05:00
weight = 5
pre = "<b> </b>"
+++

Review the following release notes for recent changes to WebLogic Deploy Tooling and known issues.

- WebLogic Deploy Tooling now incorporates the SnakeYAML parser for reading and writing model files.
This may require some changes to existing models in order to be parsed correctly.
   - Model elements that use [delete notation]({{< relref "/concepts/model#declaring-named-mbeans-to-delete" >}}) need to be escaped in single or double quotation marks.
   ```yaml
   topology:
       Server:
           '!ms1':
           ms2:
   ```


   - Model elements under the same parent should be indented to the exact same level. The previous YAML parser did not enforce this restriction,
   but it is standard for YAML. In this example, each cluster is indented four spaces.
   ```yaml
   topology:
       Cluster:
           cluster1:
               ClientCertProxyEnabled: True
           cluster2:
               WeblogicPluginEnabled: true
   ```



- Object lists in the `kubernetes` section of the model now should be specified in a hyphenated list format,
similar to how they appear in the domain resource file produced for [WebLogic Kubernetes Operator](https://oracle.github.io/weblogic-kubernetes-operator/managing-domains/domain-resource/).

   ```yaml
       clusters:
       - clusterName: 'cluster1'
         allowReplicasBelowMinDynClusterSize: true
       - clusterName: 'cluster2'
         allowReplicasBelowMinDynClusterSize: true
   ```

   - The "named object list" format is deprecated now, and will cause warning messages to be displayed.
   ```yaml
       clusters:
         'cluster1':
           allowReplicasBelowMinDynClusterSize: true
         'cluster2':
           allowReplicasBelowMinDynClusterSize: true
   ```


- The deprecated argument `-model_sample` has been removed from the Model Help Tool.
The Model Help Tool has used model sample format by default since release 1.9.2.

## Known issues for WebLogic Deploy Tooling

The following list contains known issues. Each issue may contain a workaround or an associated issue number.

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
