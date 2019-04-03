# Oracle WebLogic Server Deploy Tooling

Many organizations are using WebLogic Server, with or without other Oracle Fusion Middleware components, to run their enterprise applications.  As more and more organizations move toward Continuous Delivery of their applications, the importance of automated testing grows.  Automating WebLogic Server domain creation and application deployment with hand-coded WLST scripts is challenging.  After those scripts exist for a project, they must be maintained as the project evolves.  The motivation for the Oracle WebLogic Server Deploy Tooling project is to remove the need for most users to write WLST scripts for routine domain creation and application deployment tasks.  Instead, the project team can write a declarative, metadata model describing the domain and applications (with their dependent resources), and use one or more of the single-purpose tools provided that perform domain lifecycle operations based on the content of the model.  The goal is to make it easy to stand up environments and perform domain lifecycle operations in a repeatable fashion based on a metadata model that can be treated as source and evolve as the project evolves.

## Table of Contents
- [Features](#features-of-the-oracle-weblogic-server-deploy-tooling)
    - [Create Domain Tool](site/create.md)
    - [Update Domain Tool](site/update.md)
    - [Deploy Applications Tool](site/deploy.md)
    - [Discover Domain Tool](site/discover.md)
    - [Encrypt Model Tool](site/encrypt.md)
    - [Validate Model Tool](site/validate.md)
- [The Model](#the-metadata-model)
    - [Top-Level Sections](#top-level-model-sections)
    - [Simple Example](#simple-example)
    - [Model Names](#model-names)
    - [Model Semantics](#model-semantics)
    - [Modeling Security Providers](site/security_providers.md)
        - [JRF Trust Service Identity Asserter](site/security_providers.md#trust-service-identity-asserter)
        - [Custom Security Providers](site/security_providers.md#custom-security-providers)
    - [Variable Injection](site/variable_injection.md)
    - [Model Filters](site/tool_filters.md)
- [Downloading and Installing](#downloading-and-installing-the-software)
- [Known Issues](site/KnownIssues.md)

## Features of the Oracle WebLogic Server Deploy Tooling

The Oracle WebLogic Server Deploy Tooling is designed to support a wide range of WebLogic Server versions.  Testing has been done with versions ranging from WebLogic Server 10.3.3 to the very latest version 12.2.1.3 (and beyond).  This is possible because the underlying framework, upon which the tools are built, embeds a knowledge base that encodes information about WLST folders and attributes, making it possible for the tooling to know:

- The folder structures
- Which folders are valid in the version of WLST being used
- How to create folders
- Which attributes a folder has in the version of WLST being used
- The attribute data types and how to get/set their values (which isn't as easy as it might sound)
- The differences between WLST online and WLST offline for working with folders and attributes

The metadata model, described in detail in the next section, is WebLogic Server version and WLST mode independent.  As such, a metadata model written for an earlier version of WebLogic Server is designed to work with a newer version.  There is no need to port your metadata model as part of the upgrade process.  Of course, you may wish to add data to your metadata model to take advantage of new features in newer versions of WebLogic Server.

Currently, the project provides five single-purpose tools, all exposed as shell scripts (both Windows and UNIX scripts are provided):

- The [Create Domain Tool](site/create.md) (`createDomain`) understands how to create a domain and populate the domain with all resources and applications specified in the model.
- The [Update Domain Tool](site/update.md) (`updateDomain`) understands how to update an existing domain and populate the domain with all resources and applications specified in the model, either in offline or online mode.
- The [Deploy Applications Tool](site/deploy.md) (`deployApps`) understands how to add resources and applications to an existing domain, either in offline or online mode.
- The [Discover Domain Tool](site/discover.md) (`discoverDomain`) introspects an existing domain and creates a model file describing the domain and an archive file of the binaries deployed to the domain.
- The [Encrypt Model Tool](site/encrypt.md) (`encryptModel`) encrypts the passwords in a model (or its variable file) using a user-provided passphrase.
- The [Validate Model Tool](site/validate.md) (`validateModel`) provides both standalone validation of a model as well as model usage information to help users write or edit their models.

As new use cases are discovered, new tools will likely be added to cover those operations but all will use the metadata model to describe what needs to be done.

## The Metadata Model

The metadata model (or model, for short) is a version-independent description of a WebLogic Server domain configuration.  The tools are designed to support a sparse model so that the model need only describe what is required for the specific operation without describing other artifacts.  For example, to deploy an application that depends on a JDBC data source into an existing domain that may contain other applications or data sources, the model needs to describe only the application and the data source in question.  If the datasource was previously created, the `deployApps` tool will not try to recreate it but may update part of that data source's configuration if the model description is different than the existing values.  If the application was previously deployed, the `deployApps` tool will compare the binaries to determine if the application needs to be redeployed or not.  In short, the `deployApps` tool supports an iterative deployment model so there is no need to change the model to remove pieces that were created in a previous deployment.

The model structure, and its folder and attribute names, are based on the WLST 12.2.1.3 offline structure and names with redundant folders removed to keep the model simple.  For example, the WLST path to the URL for a JDBC data source is `/JDBCSystemResource/<data-source-name>/JdbcResource/<data-source-name>/JDBCDriverParams/NO_NAME_0/URL`.  In the model, it is `resources:/JDBCSystemResource/<data-source-name>/JdbcResource/JDBCDriverParams/URL` (where `resources` is the top-level model section where all WebLogic Server resources/services are described).

The model is written in YAML (or optionally, JSON).  The YAML parser, built into the underlying framework, is both strict with regard to the specification and supports only the subset of YAML needed to describe WebLogic Server artifacts.  For example, YAML does not support tabs as indent characters so the parser will generate parse errors if the model file contains leading tabs used for indention purposes.  In general, names and values can be specified without quotes except when the content contains one of the restricted characters; in which case, the content must be enclosed in either single or double quotes.  The restricted characters are:

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

All assignment statements must have one or more spaces between the colon and the value.  All comments must have a space after the pound sign (also known as hash) to be considered a comment.  YAML doesn't allow comments in all locations.  While the YAML parser used by the framework does not try to enforce these restrictions, it is likely that putting comments in some locations may cause parse errors since YAML is a difficult language to parse due to its complex indention rules.

##### Top-Level Model Sections
The tooling has four top-level model sections:

- `domainInfo`     - The location where special information not represented in WLST is specified (for example, the libraries that go in `$DOMAIN_HOME/lib`).
- `topology`       - The location where servers, clusters, machines, server templates, and other domain-level configuration is specified.
- `resources`      - The location where resources and services are specified (for example, data sources, JMS, WLDF).
- `appDeployments` - The location where shared libraries and applications are specified.

##### Simple Example
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
                    URL: 'jdbc:oracle:thin:@//@@PROP:dbcs1.url@@'
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

The above example shows two important features of the framework.  First, notice that the `URL`, `PasswordEncrypted`, `user` property `Value` and all `Target` fields contain values that have a `@@PROP:<name>@@` pattern.  This syntax denotes a variable placeholder whose value is specified at runtime using a variables file (in a standard Java properties file format).  Variables can be used for any value and even for some names.  For example, to automate standing up an environment with one or more applications in the Oracle Java Cloud Service, service provisioning does not allow the provisioning script to specify the server names.  For example, if the application being deployed immediately following provisioning needs to tweak the Server Start arguments to specify a Java system property, the model can use a variable placeholder in place of the server name and populate the variable file with the provisioned server names dynamically between provisioning and application deployment.

Second, notice that the `jsf#2.0` shared library `SourcePath` attribute value starts with `@@WL_HOME@@`.  This is a path token that can be used to specify that the location is relative to the location of the WebLogic Server home directory on the target environment.  This path token is automatically resolved to the proper location when the tool runs.  The tooling supports path tokens at any location in the model that specifies a file or directory location.  The supported tokens are:

- `@@ORACLE_HOME@@` - The location where WebLogic Server and any other FMW products are installed (in older versions, this was known as the `MW_HOME`).
- `@@WL_HOME@@`     - The location within the Oracle Home where WebLogic Server is installed (for example, the `$ORACLE_HOME/wlserver` directory in 12.1.2+).
- `@@DOMAIN_HOME@@` - The location of the domain home directory on which the tool is working.
- `@@PWD@@`         - The current working directory from which the tool was invoked.
- `@@TMP@@`         - The location of the temporary directory, as controlled by the `java.io.tmpdir` system property.

All binaries needed to supplement the model must be specified in an archive file, which is just a ZIP file with a specified directory structure.  For convenience, the model can also be stored inside the ZIP file, if desired.  Any binaries not already on the target system at the model-specified location must be stored in the correct location in the ZIP file and the model must reflect the path into the ZIP file.  For example, the example above shows the `simpleear` application `SourcePath` value of `wlsdeploy/applications/simpleear.ear`.  This is the location of the application binary within the archive file.  It will also be the location of the binary in the target environment; that location is relative to the domain home directory.  The archive structure is as follows:

- `model`     - The directory where the model is optionally located.  Only one model file, either in YAML or JSON, is allowed and it must have the appropriate YAML or JSON file extension.
- `wlsdeploy` - The root directory of all binaries, scripts, and directories created by the Oracle WebLogic Server Deploy Tooling.

Within the `wlsdeploy` directory, the binaries are further segregated as follows:

- `wlsdeploy/applications`       - The root directory under which all applications are stored.
- `wlsdeploy/sharedLibraries`    - The root directory under which all shared libraries are stored.
- `wlsdeploy/domainLibraries`    - The root directory under which all `$DOMAIN_HOME/lib` libraries are stored.
- `wlsdeploy/classpathLibraries` - The root directory under which all JARs/directories that are to be added to the server classpath are stored.
- `wlsdeploy/stores`             - The root directory under which empty File Store directories must exist.
- `wlsdeploy/coherence`          - The root directory under which empty Coherence persistent store directories must exist.
- `wlsdeploy/scripts`            - The root directory under which any scripts are stored.

Users can create further directory structures underneath the above locations to organize the files and directories as they see fit.  Note that any binary that already exists on the target system need not be included in the archive provided that the model specified the correct location on the target system.

One final note is that the framework is written in such a way to allow the model to be extended for use by other tools.  Adding other top-level sections to the model is supported and the existing tooling and framework will simply ignore them, if present.  For example, it would be possible to add a `soaComposites` section to the model where SOA composite applications are described, and a location within the archive file where those binaries can be stored, so that a tool that understands SOA composites and how to deploy them could be run against the same model and archive files.

### Model Names

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

### Model Semantics

When modeling configuration attributes that can have multiple values, the WebLogic Deploy Tooling tries to make this as painless as possible.  For example, the `Target` attribute on resources can have zero or more clusters and/or servers specified.  When specifying the value of such list attributes, the user has freedom to specify them as a list or as a comma-delimited string (comma is the only recognized delimiter for lists).  For attributes where the values can legally contain commas, the items must be specified as a list.  Examples of each are shown below.

```yaml
resources:
    JDBCSystemResource:
        MyStringDataSource:
            Target: 'AdminServer,mycluster'
            JdbcResource:        
                JDBCDataSourceParams:
                    JNDIName: 'jdbc/generic1, jdbc/special1'
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

## Downloading and Installing the Software

The Oracle WebLogic Server Deploy Tooling project repository is located at [`https://github.com/oracle/weblogic-deploy-tooling`](https://github.com/oracle/weblogic-deploy-tooling).  Binary distributions of the `weblogic-deploy.zip` installer can be downloaded from the [GitHub Releases page](https://github.com/oracle/weblogic-deploy-tooling/releases).  To install the software, simply unzip the `weblogic-deploy.zip` installer on a machine that has the desired versions of WebLogic Server installed.  After being unzipped, the software is ready to use, just set the `JAVA_HOME` environment variable to point to a Java 7 or higher JDK  and the shell scripts are ready to run.
