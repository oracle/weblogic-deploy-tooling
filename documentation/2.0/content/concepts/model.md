---
title: "Metadata Model"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 1
---

### Contents

- [Overview](#overview)
- [Top-level sections](#top-level-model-sections)
- [Simple example](#simple-example)
- [Model names](#model-names)
- [Model tokens](#model-tokens)
- [Model semantics](#model-semantics)
- [Declaring named MBeans to delete](#declaring-named-mbeans-to-delete)
- [Using multiple models](#using-multiple-models)

### Overview

The metadata model (or model, for short) is a version-independent description of a WebLogic Server domain configuration.  The tools are designed to support a sparse model so that the model need only describe what is required for the specific operation without describing other artifacts.  For example, to deploy an application that depends on a JDBC data source into an existing domain that may contain other applications or data sources, the model needs to describe only the application and the data source in question.  If the data source was previously created, the `deployApps` tool will not try to recreate it but may update part of that data source's configuration if the model description is different than the existing values.  If the application was previously deployed, the `deployApps` tool will compare the binaries to determine if the application needs to be redeployed or not.

The model structure, and its folder and attribute names, are based on the WLST 12.2.1.3 offline structure and names with redundant folders removed to keep the model simple.  For example, the WLST path to the URL for a JDBC data source is `/JDBCSystemResource/<data-source-name>/JdbcResource/<data-source-name>/JDBCDriverParams/NO_NAME_0/URL`.  In the model, it is `resources:/JDBCSystemResource/<data-source-name>/JdbcResource/JDBCDriverParams/URL` (where `resources` is the top-level model section where all WebLogic Server resources/services are described).

The model is written in YAML (or optionally, JSON).  The YAML parser, built into the underlying framework, is both strict with regard to the specification and supports only the subset of YAML needed to describe WebLogic Server artifacts.  For example, YAML does not support tabs as indent characters so the parser will generate parse errors if the model file contains leading tabs used for indentation purposes.  In general, names and values can be specified without quotes except when the content contains one of the restricted characters; in which case, the content must be enclosed in either single or double quotes.  The restricted characters are:

- comma
- colon
- exclamation mark
- question mark
- hyphen
- ampersand
- percent sign
- "at" sign
- star
- pound sign (also known as hash)
- equal sign
- less than
- greater than
- square brackets
- curly braces
- back quote

All assignment statements must have one or more spaces between the colon and the value.  All comments must have a space after the pound sign (also known as hash) to be considered a comment.  YAML doesn't allow comments in all locations.  While the YAML parser used by the framework does not try to enforce these restrictions, it is likely that putting comments in some locations may cause parse errors since YAML is a difficult language to parse due to its complex indentation rules.


### Top-level model sections
The tooling has five top-level model sections:

- `domainInfo`     - The location where special information not represented in WLST is specified (for example, the libraries that go in `$DOMAIN_HOME/lib`).
- `topology`       - The location where servers, clusters, machines, server templates, and other domain-level configuration is specified.
- `resources`      - The location where resources and services are specified (for example, data sources, JMS, WLDF).
- `appDeployments` - The location where shared libraries and applications are specified.
- `kubernetes`     - The location where the WLS Kubernetes Operator domain configuration is specified.

#### Simple example
Here is a simple example of a model to deploy an application and its data source:

```yaml
resources:
    JDBCSystemResource:
        MyDataSource:
            Target: '@@PROP:myjcs.cluster1.name@@'
            JdbcResource:
                JDBCDataSourceParams:
                    JNDIName: jdbc/generic1
                JDBCDriverParams:
                    DriverName: oracle.jdbc.OracleDriver
                    URL: jdbc:oracle:thin:@//@@PROP:dbcs1.url@@
                    PasswordEncrypted: '@@PROP:dbcs1.password@@'
                    Properties:
                        user:
                            Value: '@@PROP:dbcs1.user@@'
                        oracle.net.CONNECT_TIMEOUT:
                            Value: 5000
                JDBCConnectionPoolParams:
                    MaxCapacity: 50
appDeployments:
    Application:
        simpleear :
            SourcePath: wlsdeploy/applications/simpleear.ear
            Target: '@@PROP:myjcs.cluster1.name@@'
            ModuleType: ear
     Library:
        'jsf#2.0':
            SourcePath: '@@WL_HOME@@/common/deployable-libraries/jsf-2.0.war'
            Target: '@@PROP:myjcs.cluster1.name@@'
            ModuleType: war
```

The above example shows two important features of the framework.  First, notice that the `URL`, `PasswordEncrypted`, `user` property `Value` and all `Target` fields contain values that have a `@@PROP:<name>@@` pattern.  This indicates a variable placeholder whose value is specified at runtime using a variables file. For more information about this and other token types, see [Model tokens](#model-tokens).

Second, notice that the `jsf#2.0` shared library `SourcePath` attribute value starts with `@@WL_HOME@@`. This is a path token that can be used to specify that the location is relative to the location of the WebLogic Server home directory on the target environment.  For more information and a list of available path tokens, see [Model tokens](#model-tokens).

The example above shows the attribute `SourcePath` of the `simpleear` application with a value of `wlsdeploy/applications/simpleear.ear`.  The prefix `wlsdeploy/` indicates that the resource is located in the archive file in the specified location, and will be deployed to that directory within the domain, in this case `<domain-home>/wlsdeploy/applications/simpleear.ear`. See the [Archive file]({{< relref "/concepts/archive.md" >}}) for more details about using the archive file.

Users can create further directory structures underneath the above locations to organize the files and directories as they see fit.  Note that any binary that already exists on the target system need not be included in the archive provided that the model specified the correct location on the target system.

One final note is that the framework is written in such a way to allow the model to be extended for use by other tools.  Adding other top-level sections to the model is supported and the existing tooling and framework will simply ignore them, if present.  For example, it would be possible to add a `soaComposites` section to the model where SOA composite applications are described, and a location within the archive file where those binaries can be stored, so that a tool that understands SOA composites and how to deploy them could be run against the same model and archive files.

### Model names

The WebLogic Deploy Tooling handles names of WebLogic Server configuration artifacts in a very prescribed way.  To understand how names are handled, users first need a basic understanding of WLST offline naming.  In WLST offline, there are two general categories of configuration artifacts:

- Artifacts that can hold zero or more references to another configuration artifact type.
- Artifacts that can hold zero or one reference to another configuration artifact.

For example, a domain can contain zero or more `JDBCSystemResource` or `AppDeployment` instances but can only contain a single `SecurityConfiguration` artifact.  When working with configuration artifacts like `JDBCSystemResource`, the name is always modeled as a sub-element of the `JDBCSystemResource` element, as shown below.

```yaml
resources:
    JDBCSystemResource:
        MyDataSource:
            Target: mycluster
            ...
        YourDataSource:
            Target: yourcluster
            ...
```

In the example above, the model has two instances of `JDBCSystemResource`: one named `MyDataSource` and one named `YourDataSource`.  For anyone familiar with WLST, this should seem somewhat familiar because the WLST offline path to the `MyDataSource` configuration will always start with `/JDBCSystemResource/MyDataSource`.  What might not seem familiar is that in this WLST folder, there is a `Name` attribute that is also set to `MyDataSource`.  The WebLogic Deploy Tooling requires that modelers set the `JDBCSystemRTesource` name using the folder semantics as shown in the example.  It is not possible to set the Name using the `Name` attribute inside the folder and any attempts to do so, will not work; in this case, the `Name` attribute is redundant because the name was already specified as the folder name.

When working with artifacts like `SecurityConfiguration` or `JMX`, there is never more than one instance of these artifacts in a domain because they are just configuration containers and their names generally have no semantic meaning.  As such, the WebLogic Deploy Tooling does not expose these names in the model, as shown below:

```yaml
topology:
    SecurityConfiguration:
        NodeManagerUsername: weblogic
        NodeManagerPasswordEncrypted: welcome1
```

As the example above shows, the `SecurityConfiguration` element has no named sub-element, as there is with `JDBCSystemResource`, even though the WLST path to the `SecurityConfiguration` attributes is `/SecurityConfiguration/<domain-name>`.  The WebLogic Deploy Tooling has built-in rules and a knowledge base that controls how these names are handled so that it can complete the configuration of these artifacts.  As with the previous class of configuration artifact, the folder almost always contains a ` Name` attribute that, in WLST, could be used to change the name.  As with the previous class of artifact, the WebLogic Deploy Tooling does not support the use of the `Name` attribute in these folders and any attempt to set the `Name` attribute will not be honored.  In general, the only model location that uses the `Name` attribute is the top-level topology section, because this maps to where WLST stores the domain name.

### Model tokens

The model allows the use of tokens that are substituted with text values as the model is processed. This section describes several types of tokens.

**Variable tokens** are declared with the syntax `@@PROP:<variable>@@`. This type of token represents a value that is resolved at runtime using a variables file in a standard Java properties file format.  Variables can be used for any value and for some names.  For example, to automate standing up an environment with one or more applications in the Oracle Java Cloud Service, service provisioning does not allow the provisioning script to specify the server names.  For example, if the application being deployed immediately following provisioning needs to tweak the Server Start arguments to specify a Java system property, the model can use a variable placeholder in place of the server name and populate the variable file with the provisioned server names dynamically between provisioning and application deployment.

**File tokens** are declared with the syntax `@@FILE:<filename>@@`. This type of token is similar to a variable token, but it references a single value that is read from the specified file. For example, the model may reference a password attribute as follows:
```yaml
PasswordEncrypted: '@@FILE:/home/me/dbcs1.txt@@'
```
The file `/home/me/dbcs1.txt` would then contain this single line:
```yaml
password#123
```
As the model is processed, the value for the `PasswordEncrypted` would resolve to `password#123`. It is also possible to combine file placeholders with other types of tokens, to allow for variations in the name and location of the file, such as:
```yaml
PasswordEncrypted: '@@FILE:/dir/@@PROP:name@@.txt@@'
```
```yaml
PasswordEncrypted: '@@FILE:@@ORACLE_HOME@@/dir/name.txt@@'
```

**Environment tokens** are declared with the syntax `@@ENV:<name>@@`. This type of token is resolved by looking up the system environment variable `<name>`, and substituting that value for the token.

**Secret tokens** are declared with the syntax `@@SECRET:<name>:<key>@@`. This type of token is resolved by determining the location of a Kubernetes secret file, and reading the first line from that file. That line is substituted for the token.

There are two methods for deriving the location of the Kubernetes secret file. The first method involves using one or more configured root directories, and looking for the secret file in the path `<root-directory>/<name>/<key>`.

The root directories are configured as a comma-separated list of directories, using the environment variable `WDT_MODEL_SECRETS_DIRS`. For example, if `WDT_MODEL_SECRETS_DIRS` is set to `/etc/my-secrets,/etc/your-secrets`, then the token `@@SECRET:secrets:the-secret@@` will search the following locations:
```
/etc/my-secrets/secrets/the-secret
/etc/your-secrets/secrets/the-secret
```
If either of these files is found, the secret is read from that file and substituted in the model.

The second method for locating the Kubernetes secret file is to use the environment variable `WDT_MODEL_SECRETS_NAME_DIR_PAIRS` to map `<name>` values to specific directory locations. For example, if `WDT_MODEL_SECRETS_NAME_DIR_PAIRS` is set to `my-root=/etc/my-secrets,your-root=/etc/your-secrets`, then the token `@@SECRET:your-root:the-secret@@` will look for the secrets file at:
```
/etc/your-secrets/the-secret
```
If the `<name>` value has a corresponding mapped directory in `WDT_MODEL_SECRETS_NAME_DIR_PAIRS`, then that directory will take precedence over any roots specified in `WDT_MODEL_SECRETS_DIRS`.

{{% notice note %}} It is important that the secrets directories contain only secrets files, because those files are examined to create a list of available name/key pairs.
{{% /notice %}}

**Path tokens** are tokens that reference known values, and can be used to make the model more portable. For example, a model may reference a WebLogic library source path as:
```yaml
SourcePath: '@@WL_HOME@@/common/deployable-libraries/jsf-2.0.war'
```
Using the path token `@@WL_HOME@@` allows the model to be used across multiple environments, even if the WebLogic installation directory is different. Path tokens can be used at any location in the model that specifies a file or directory location.  The supported tokens are:

- `@@ORACLE_HOME@@` - The location where WebLogic Server and any other FMW products are installed (in older versions, this was known as the `MW_HOME`).
- `@@WL_HOME@@`     - The location within the Oracle Home where WebLogic Server is installed (for example, the `$ORACLE_HOME/wlserver` directory in 12.1.2+).
- `@@DOMAIN_HOME@@` - The location of the domain home directory on which the tool is working.
- `@@PWD@@`         - The current working directory from which the tool was invoked.
- `@@TMP@@`         - The location of the temporary directory, as controlled by the `java.io.tmpdir` system property.

### Model semantics

When modeling configuration attributes that can have multiple values, the WebLogic Deploy Tooling tries to make this as painless as possible.  For example, the `Target` attribute on resources can have zero or more clusters and/or servers specified.  When specifying the value of such list attributes, the user has freedom to specify them as a list or as a comma-delimited string (comma is the only recognized delimiter for lists).  For attributes where the values can legally contain commas, the items must be specified as a list.  Examples of each are shown below.

```yaml
resources:
    JDBCSystemResource:
        MyStringDataSource:
            Target: AdminServer,mycluster
            JdbcResource:
                JDBCDataSourceParams:
                    JNDIName: jdbc/generic1, jdbc/special1
                ...
        MyListDataSource:
            Target: [ AdminServer, mycluster ]
            JdbcResource:
                JDBCDataSourceParams:
                    JNDIName: [ jdbc/generic2, jdbc/special2 ]
                ...
    WLDFSystemResource:
        MyWldfModule:
            Target: mycluster
            WLDFResource:
                Harvester:
                    HarvestedType:
                        weblogic.management.runtime.ServerRuntimeMBean:
                            Enabled: true
                            HarvestedInstance: [
                                'com.bea:Name=AdminServer,Type=ServerRuntime',
                                'com.bea:Name=m1,Type=ServerRuntime'
                            ]
                ...
```

In the example above, the `Target` attribute is specified three different ways, as a comma-separated string, as a list, and as a single string in the case of where there is only a single target.  The `JNDIName` attribute is specified as a comma-separated string and as a list (a single string also works). On the other hand, the `HarvestedInstances` attribute had to be specified as a list because each element contains commas.

One of the primary goals of the WebLogic Deploy Tooling is to support a sparse model where the user can specify just the configuration needed for a particular situation.  What this implies varies somewhat between the tools but, in general, this implies that the tools are using an additive model.  That is, the tools add to what is already there in the existing domain or domain templates (when creating a new domain) rather than making the domain conform exactly to the specified model.  Where it makes sense, a similar, additive approach is taken when setting the value of multi-valued attributes.  For example, if the model specified the cluster `mycluster` as the target for an artifact, the tooling will add `mycluster` to any existing list of targets for the artifact.  While the development team has tried to mark attributes that do not make sense to merge accordingly in our knowledge base, this behavior can be disabled on an attribute-by-attribute basis, by adding an additional annotation in the knowledge base data files.  The development team is already thinking about how to handle situations that require a non-additive, converge-to-the-model approach, and how that might be supported, but this still remains a wish list item.  Users with these requirements should raise an issue for this support.

### Declaring named MBeans to delete

With WebLogic Deploy Tooling, you can specify named items in the model to be deleted using the Create Domain, Update Domain, and Deploy Applications Tools.  Named items are those that have multiple instances that are distinguished by user-provided names, such as managed servers, data sources, and security realms.  Items to be deleted are prepended with an exclamation point (!) in the model.

In this example, the managed server ```obsoleteServer``` will be deleted, and ```newServer``` will be created:

Note that the exclamation point, along with the name, should be inside quotation marks:

```yaml
    Server:
        '!obsoleteServer':
        newServer:
            ListenAddress: 127.0.0.1
            ListenPort: 9005
```
This feature can also remove items that were created by WebLogic Server templates. For example, the base template creates a default security realm called ```myrealm```.  If a user chooses to declare a custom realm, ```myrealm``` is no longer needed.  In this example, ```myrealm``` will be deleted, and the custom realm ```newrealm``` will be created, and declared as the default realm:

```yaml
    SecurityConfiguration:
        DefaultRealm: newrealm
        Realm:
            '!myrealm':
            newrealm:
                AuthenticationProvider:
                ...
```

This feature does not apply to named security providers within a realm. These items follow a special set of rules that are required to maintain their ordering. See [Modeling security providers]({{< relref "/samples/securityproviders-model.md" >}}) for detailed information.

This feature can be used to undeploy applications or remove libraries.

#### Declaring list items to delete

In addition to deleting named mbeans, you can remove items from a list. Most practically, this would be within a Target list.

```yaml
  JMSSystemResource:
      BPMJMSModule:
          Target: soa_cluster,'!AdminServer'
              
```
In this example, the BPMJMSModule has the AdminServer target removed from the target list.

### Using multiple models

The Create Domain, Update Domain, Deploy Applications, and Validate Model Tools allow the specification of multiple models on the command line. For example:

    $ weblogic-deploy\bin\createDomain.cmd -model_file modelOne,modelTwo,modelThree ...

In this case, the models are merged into a single model before being applied. Each successive model is added to the previous model. In cases where entities exist in both models, the attributes are combined and attribute values from successive models prevail.  The resulting model is then verified before being applied.
For example, if Model 1 looks like:
```yaml
topology:
    Server:
        m1:
            ListenPort: 7000
            Notes: Server 1
        m2:
            ListenPort: 9000
```
and Model 2 looks like:
```yaml
topology:
    Server:
        m1:
            ListenAddress: myhostname
            ListenPort: 8000
        m3:
            ListenPort: 10000
```
The attributes for server m1 are merged, server m2 is left unchanged, and server m3 is added. The resulting model would be:
```yaml
topology:
    Server:
        m1:
            ListenAddress: myhostname
            ListenPort: 8000
            Notes: "Server 1"
        m2:
            ListenPort: 9000
        m3:
            ListenPort: 10000
```

If variable properties are used in element names, such as ```@@PROP:my-server@@```, the names in both models will be resolved and matching elements will be merged.

#### Multiple models and delete notation

A named element using [delete notation](#declaring-named-mbeans-to-delete) will completely delete an element with a matching name and no delete notation in a previous model. For example, if Model 1 looks like:
```yaml
topology:
    Server:
        m1:
            ListenPort: 7000
            Notes: Server 1
        m2:
            ListenPort: 9000
```
and Model 2 looks like:
```yaml
topology:
    Server:
        '!m2':
```
The resulting model would be:
```yaml
topology:
    Server:
        m1:
            ListenPort: 7000
            Notes: Server 1
```

Similarly, an element without delete notation will completely replace an element with a matching name that has delete notation in a previous model. For example, if Model 1 looks like:
```yaml
topology:
    Server:
        '!m1':
```
and Model 2 looks like:
```yaml
topology:
    Server:
        m1:
            ListenPort: 7000
            Notes: Server 1
```
The resulting model would be:
```yaml
topology:
    Server:
        m1:
            ListenPort: 7000
            Notes: Server 1
```
