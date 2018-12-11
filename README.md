# Oracle WebLogic Server Deploy Tooling

Many organizations are using WebLogic Server, with or without other Oracle Fusion Middleware components, to run their enterprise applications.  As more and more organizations move toward Continuous Delivery of their applications, the importance of automated testing grows.  Automating WebLogic Server domain creation and application deployment with hand-coded WLST scripts is challenging.  After those scripts exist for a project, they must be maintained as the project evolves.  The motivation for the Oracle WebLogic Server Deploy Tooling project is to remove the need for most users to write WLST scripts for routine domain creation and application deployment tasks.  Instead, the project team can write a declarative, metadata model describing the domain and applications (with their dependent resources), and use one or more of the single-purpose tools provided that perform domain lifecycle operations based on the content of the model.  The goal is to make it easy to stand up environments and perform domain lifecycle operations in a repeatable fashion based on a metadata model that can be treated as source and evolve as the project evolves.

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

- The Create Domain Tool (`createDomain`) understands how to create a domain and populate the domain with all resources and applications specified in the model.
- The Update Domain Tool (`updateDomain`) understands how to update an existing domain and populate the domain with all resources and applications specified in the model, either in offline or online mode.
- The Deploy Applications Tool (`deployApps`) understands how to add resources and applications to an existing domain, either in offline or online mode.
- The Discover Domain Tool (`discoverDomain`) introspects an existing domain and creates a model file describing the domain and an archive file of the binaries deployed to the domain.
- The Encrypt Model Tool (`encryptModel`) encrypts the passwords in a model (or its variable file) using a user-provided passphrase.
- The Validate Model Tool (`validateModel`) provides both standalone validation of a model as well as model usage information to help users write or edit their models.

As new use cases are discovered, new tools will likely be added to cover those operations but all will use the metadata model to describe what needs to be done.

## The Metadata Model

As previously described, the metadata model (or model, for short) is a version-independent description of a WebLogic Server domain configuration.  The tools are designed to support a sparse model so that the model need only describe what is required for the specific operation without describing other artifacts.  For example, to deploy an application that depends on a JDBC data source into an existing domain that may contain other applications or data sources, the model needs to describe only the application and the data source in question.  If the datasource was previously created, the `deployApps` tool will not try to recreate it but may update part of that data source's configuration if the model description is different than the existing values.  If the application was previously deployed, the `deployApps` tool will compare the binaries to determine if the application needs to be redeployed or not.  In short, the `deployApps` tool supports an iterative deployment model so there is no need to change the model to remove pieces that were created in a previous deployment.

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

The tooling has 4 top-level model sections:

- `domainInfo`     - The location where special information not represented in WLST is specified (for example, the libraries that go in `$DOMAIN_HOME/lib`).
- `topology`       - The location where servers, clusters, machines, server templates, and other domain-level configuration is specified.
- `resources`      - The location where resources and services are specified (for example, data sources, JMS, WLDF)
- `appDeployments` - The location where shared libraries and applications are specified.

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

```$yaml
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

One place where the semantics are different is for WebLogic security providers.  Because provider ordering is important, and to make sure that the ordering is correctly set in the newly created domain, the Create Domain Tool will look for security providers of each base type (for example, Authentication Providers, Credential Mappers, and such) to see if any are included in the model.  If so, the tool will make sure that  the providers only listed for a type are present in the resulting domain so that the providers are created in the necessary order.  For example, if the model specified an `LDAPAuthenticator` and an `LDAPX509IdentityAsserter` similar to what is shown below, the `DefaultAuthenticator` and `DefaultIdentityAsserters` will be deleted.  If no providers for a base type are listed in the model, then the default providers will be left untouched.

```$yaml
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

To keep the `DefaultAuthenticator` and `DefaultIdentityAsserter`, simply add the default names and types in the correct positions in the model's `AuthenticationProvider` list.  If desired, settings on the default providers can be changed, as shown below.

```$yaml
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

## The Validate Model Tool

When working with a metadata model that drives tooling, it is critical to make it easy both to validate that the model and its related artifacts are well-formed and to provide help on the valid attributes and subfolders for a particular model location.  The Validate Model Tool provides both validation and help for model authors as a standalone tool.  In addition, the tool is integrated with the `createDomain` and `deployApps` tools to catch validation errors early, before any actions are performed on the domain.

To use the Validate Model Tool, simply run the `validateModel` shell script with the correct arguments.  To see the list of valid arguments for any tool in the Oracle WebLogic Server Deploy Tooling installation, simply run the shell script with the `-help` option (or with no arguments) to see the shell script usage information.

For example, starting with the following model shown below, where the `AdminServer` attribute `Machine` is misspelled as `Machines`:

```yaml
topology:
    Name: DemoDomain
    AdminServerName: AdminServer
    Cluster:
        mycluster:
    Server:
        AdminServer:
            ListenAddress: 192.168.1.50
            ListenPort: 7001
            Machines: machine1
            SSL:
                Enabled: true
                ListenPort: 7002
            ServerStart:
                ClassPath: 'c:\foo\bar'
        m1:
            ListenAddress: 192.168.1.50
            ListenPort: 8001
            Cluster: mycluster
            Machine: machine1
            ServerStart:
                ClassPath: 'c:\foo\bar'
        m2:
            ListenAddress: 192.168.1.51
            ListenPort: 8001
            Cluster: mycluster
            Machine: machine2
            ServerStart:
                ClassPath: 'c:\foo\bar'
    Machine:
        machine1:
            NodeManager:
                ListenAddress: 192.168.1.50
                ListenPort: 5556
        machine2:
            NodeManager:
                ListenAddress: 192.168.1.51
                ListenPort: 5556
```

To validate the standalone model file, run the tool as follows:

    weblogic-deploy\bin\validateModel.cmd -oracle_home c:\wls12213 -model_file InvalidDemoDomain.yaml

The output of the tool will look something like this:

    -----------------------------------------------
    Validation Area: topology Section
    -----------------------------------------------

      Errors: 1
        Message: Machines is not one of the folder, folder instance or attribute names allowed in model location topology:/Server/AdminServer

To get the valid list of attributes and folders at this model location, run the tool as follows:

    weblogic-deploy\bin\validateModel.cmd -oracle_home c:\wls12213 -print_usage topology:/Server

This will print out the list of attributes and valid subfolders (the full output is omitted here for brevity) that will include the following attribute in the list:

    Section: topology:/Server

      Valid Attributes are :-
        ...
        Machine                                             string
        ...

If the model contains variable definitions and the variable file is specified, the Validate Model Tool will validate that all variable references in the model are defined in the variable file.  For example, invoking the tool as shown here:

    weblogic-deploy\bin\validateModel.cmd -oracle_home c:\wls12213 -model_file InvalidDemoDomain.yaml -variable_file InvalidDemoDomain.properties

Results in output similar to that shown below, if the `db.password` variable is not defined in the variable file.

    -----------------------------------------------
    Validation Area: Variable Substitutions
    -----------------------------------------------

      Errors: 2
        Message: Model location resource:/JDBCSystemResource/Generic1/JdbcResource/JDBCDriverParams/PasswordEncrypted references variable db.password that is not defined in D:/demo/InvalidDemoDomain.properties
        Message: Model location resource:/JDBCSystemResource/Generic2/JdbcResource/JDBCDriverParams/PasswordEncrypted references variable db.password that is not defined in D:/demo/InvalidDemoDomain.properties

If the model references binaries that should be present in the archive, the Validate Model Tool will validate that all binary references in the model that point to archive file locations are present in the archive file.  For example, invoking the tool as shown here:

    weblogic-deploy\bin\validateModel.cmd -oracle_home c:\wls12213 -model_file InvalidDemoDomain.yaml -archive_file InvalidDemoDomain.zip

Results in output similar to that shown below, if the `simpleear.ear` file is not in the model-specified location inside the archive file.

    -----------------------------------------------
    Validation Area: Archive Entries
    -----------------------------------------------

      Errors: 1
        Message: Model location appDeployments:/Application/simpleear/SourcePath references file wlsdeploy/applications/simpleear.ear that is not found in the archive file D:/demo/InvalidDemoDomain.zip

## The Encrypt Model Tool

**NOTE: The current encryption algorithms require JDK 8 to execute, in order to meet Oracle's security standards.  While it is possible to run WLST with a newer JDK than what was used to install WebLogic Server, WLST on older versions of WebLogic Server 10.3.x may not work properly with JDK 8, out of the box, due to JDK 6 JVM arguments that have been removed in JDK8.  It may be necessary to modify the WLST start scripts to remove JVM arguments that have been removed between JDK 6 and JDK 8.**

Models contain WebLogic Server domain configuration.  Certain types of resources and other configurations require passwords; for example, a JDBC data source requires the password for the user establishing the database connection.  When creating or configuring a resource that requires a password, that password must be specified either in the model directly or in the variable file.  Clear-text passwords are not conducive to storing configurations as source, so the Encrypt Model Tool gives the model author the ability to encrypt the passwords in the model and variable file using passphrase-based, reversible encryption.  When using a tool with a model containing encrypted passwords, the encryption passphrase must be provided, so that the tool can decrypt the password in memory to set the necessary WebLogic Server configuration (which supports its own encryption mechanism based on a domain-specific key).  While there is no requirement to use the Oracle WebLogic Server Deploy Tooling encryption mechanism, it is highly recommended because storing clear text passwords on disk is never a good idea.

Start with the following example model:

```yaml
domainInfo:
    AdminUserName: weblogic
    AdminPassword: welcome1
    ServerStartMode: prod
topology:
    Name: DemoDomain
    AdminServerName: AdminServer
    Cluster:
        mycluster:
    Server:
        AdminServer:
            ListenAddress: 192.168.1.50
            ListenPort: 7001
            Machine: machine1
        m1:
            ListenAddress: 192.168.1.50
            ListenPort: 8001
            Cluster: mycluster
            Machine: machine1
        m2:
            ListenAddress: 192.168.1.51
            ListenPort: 8001
            Cluster: mycluster
            Machine: machine2
    Machine:
        machine1:
            NodeManager:
                ListenAddress: 192.168.1.50
                ListenPort: 5556
        machine2:
            NodeManager:
                ListenAddress: 192.168.1.51
                ListenPort: 5556
    SecurityConfiguration:
        NodeManagerUsername: weblogic
        NodeManagerPasswordEncrypted: welcome1
    RestfulManagementServices:
        Enabled: true
    Security:
        Group:
            FriscoGroup:
                Description: The WLS Deploy development group
        User:
            Robert:
                Password: welcome1
                GroupMemberOf: [ Administrators, FriscoGroup ]
            Derek:
                Password: welcome1
                GroupMemberOf: 'Administrators, FriscoGroup'
            Richard:
                Password: welcome1
                GroupMemberOf: [ FriscoGroup ]
            Carolyn:
                Password: welcome1
                GroupMemberOf: FriscoGroup
            Mike:
                Password: welcome1
                GroupMemberOf: FriscoGroup
            Johnny:
                Password: welcome1
                GroupMemberOf: FriscoGroup
            Gopi:
                Password: welcome1
                GroupMemberOf: FriscoGroup
```

To run the encryption tool on the model, run the following command:

    weblogic-deploy\bin\encryptModel.cmd -oracle_home c:\wls12213 -model_file UnencryptedDemoDomain.yaml

The tool will prompt for the encryption passphrase twice and then encrypt any passwords it finds in the model, skipping any password fields that have variable values, to produce a result that looks like the following model.

```yaml
domainInfo:
    AdminUserName: weblogic
    AdminPassword: '{AES}a0dacEQ4Q2JnTmI4VHp5NjIzVHNPRFg5ZjRiVDJ4NzU6T1M0SGYwM2xBeHdRdHFWVTpWZEh6bkd4NzZSQT0='
    ServerStartMode: prod
topology:
    Name: DemoDomain
    AdminServerName: AdminServer
    Cluster:
        mycluster:
    Server:
        AdminServer:
            ListenAddress: 192.168.1.50
            ListenPort: 7001
            Machine: machine1
        m1:
            ListenAddress: 192.168.1.50
            ListenPort: 8001
            Cluster: mycluster
            Machine: machine1
        m2:
            ListenAddress: 192.168.1.51
            ListenPort: 8001
            Cluster: mycluster
            Machine: machine2
    Machine:
        machine1:
            NodeManager:
                ListenAddress: 192.168.1.50
                ListenPort: 5556
        machine2:
            NodeManager:
                ListenAddress: 192.168.1.51
                ListenPort: 5556
    SecurityConfiguration:
        NodeManagerUsername: weblogic
        NodeManagerPasswordEncrypted: '{AES}WndJQWNySWpoY0VEbFpmR2V1RFhvamVFdGwzandtaFU6L1d4V0dPRFpsaXJIUkl2djpQdUdLaTloR1IxTT0='
    RestfulManagementServices:
        Enabled: true
    Security:
        Group:
            FriscoGroup:
                Description: The WebLogic Deploy development group
        User:
            Robert:
                Password: '{AES}VFIzVmdwcWNLeHBPaWhyRy82VER6WFV6aHRPbGcwMjQ6bS90OGVSTnJxWTIvZjkrRjpjSzBQUHlOWWpWTT0='
                GroupMemberOf: [ Administrators, FriscoGroup ]
            Derek:
                Password: '{AES}R1BTM21ZSkxpdTNIZjNqcTlsSC9PeHV4aXJoT3kxazM6M1dLOXBLeCtlc1lsVDUrWjo5VitHZUxCcjZnOD0='
                GroupMemberOf: 'Administrators, FriscoGroup'
            Richard:
                Password: '{AES}Y3FkQmRIRGhjZEtlRjVkVVdLQU1Eb09LWDIzMlhUWVo6MjllVExsMmNmNzJzZDFjaTpNcVNDbUs2cnRFRT0='
                GroupMemberOf: [ FriscoGroup ]
            Carolyn:
                Password: '{AES}cW8wczJqZXJZOHVsTGNOTmlqTGpuZGFoSkY2ME5WbTk6c0VaWGs1ME5pemlKdC9wajpFaTJPRS9ZQlcvND0='
                GroupMemberOf: FriscoGroup
            Mike:
                Password: '{AES}cnF6Z3JOVWcvc0czN3JVb1g5T2FidmRsSU51anJCa0Y6UlBsNVFsOFlXU29xUlY1aDp3VWZWYU5VOVRkMD0='
                GroupMemberOf: FriscoGroup
            Johnny:
                Password: '{AES}UWJ5Y25Ma2RHTkNMVTZ1RnlhRkNaTUxXaXV4SjBjaWg6citwTDQvelN1aUlPdnZaSDpCMEdSWGg2ZlVJUT0='
                GroupMemberOf: FriscoGroup
            Gopi:
                Password: '{AES}MWJGcnhtZlNyWXVrU1VXMVFxZFEvQThoS1hPN2FQdDc6MmRPaUF2Y1FCQ3VIK3MydDpZaFR5clBrN1FjOD0='
                GroupMemberOf: FriscoGroup
```

If the model stores passwords in the variables file, like the following model:

```yaml
resources:
    JDBCSystemResource:
        Generic1:
            Target: mycluster
            JdbcResource:
              JDBCDataSourceParams:
                  JNDIName: [ jdbc/generic1 ]
                  GlobalTransactionsProtocol: TwoPhaseCommit
              JDBCDriverParams:
                  DriverName: oracle.jdbc.xa.client.OracleXADataSource
                  URL: 'jdbc:oracle:thin:@//@@PROP:db.url@@'
                  PasswordEncrypted: '@@PROP:db.password@@'
                  Properties:
                      user:
                          Value: '@@PROP:db.user@@'
                      oracle.net.CONNECT_TIMEOUT:
                          Value: 5000
                      oracle.jdbc.ReadTimeout:
                          Value: 30000
              JDBCConnectionPoolParams:
                  InitialCapacity: 3
                  MaxCapacity: 15
                  TestTableName: SQL ISVALID
                  TestConnectionsOnReserve: true
    MailSession:
        MyMailSession:
            JNDIName: mail/MyMailSession
            Target: mycluster
            SessionUsername: 'john.smith@example.com'
            SessionPasswordEncrypted: '@@PROP:mymailsession.password@@'
            Properties:
                mail.store.protocol: imap
                mail.imap.port: 993
                mail.imap.ssl.enable: true
                mail.imap.starttls.enable: true
                mail.imap.host: imap.example.com
                mail.impa.auth: true
                mail.transport.protocol: smtp
                mail.smtp.starttls.enable: true
                mail.smtp.port: 465
                mail.smtp.ssl.enable: true
                mail.smtp.auth: true
                mail.smtp.host: smtp.example.com
```

Run the encryption tool and pass both the model and variable files, like this:

    weblogic-deploy\bin\encryptModel.cmd -oracle_home c:\wls12213 -model_file UnencryptedDemoDomain.yaml -variable_file UnencryptedDemoDomain.properties

The variable file will now look something like the following:

    #Variables updated after encryption
    #Thu Feb 01 19:12:57 CST 2018
    db.user=rpatrick
    db.url=mydb.example.com:1539/PDBORCL
    db.password={AES}czFXMkNFWNG9jNTNYd0hRL2R1anBnb0hDUlp4K1liQWFBdVM4UTlvMnE0NU1aMUZ5UVhiK25oaWFBc2lIQ20\=
    mymailsession.password={AES}RW9nRnUzcE41WGNMdnEzNDdRQVVNWm1LMGhidkFBVXg6OUN3aXcyci82cmh3cnpNQTpmY2UycUp5YWl4UT0\=

## The Create Domain Tool

The Create Domain Tool uses a model and WLST offline to create a domain.  To use the tool, at a minimum, the model must specify the domain's administrative password in the `domainInfo` section of the model, as shown below.

```yaml
domainInfo:
    AdminPassword: welcome1
```

Using the model above, simply run the `createDomain` tool, specifying the type of domain to create and where to create it.

    weblogic-deploy\bin\createDomain.cmd -oracle_home c:\wls12213 -domain_type WLS -domain_parent d:\demo\domains -model_file MinimalDemoDomain.yaml

Clearly, creating an empty domain with only the template-defined servers is not very interesting, but this example just reinforces how sparse the model can be.  When running the Create Domain Tool, the model must be provided either inside the archive file or as a standalone file.  If both the archive and model files are provided, the model file outside the archive will take precedence over any that might be inside the archive.  If the archive file is not provided, the Create Domain Tool will create the `topology` section only (using the `domainInfo` section) of the model in the domain.  This is because the `resources` and `appDeployments` sections of the model can reference files from the archive so to create the domain with the model-defined resources and applications, an archive file must be provided--even if the model does not reference anything in the archive.  At some point in the future, this restriction may be relaxed to require the archive only if it is actually needed.

The Create Domain Tool understands three domain types: `WLS`, `RestrictedJRF`, and `JRF`.  When specifying the domain type, the Oracle Home must match the requirements for the domain type.  Both `RestrictedJRF` and `JRF` require an Oracle Home with the FMW Infrastucture (also known as JRF) installed.  When creating a JRF domain, the RCU database information must be provided as arguments to the `createDomain` script.  Note that the tool will prompt for any passwords required.  Optionally, they can be piped to standard input (for example, `stdin`) of the script, to make the script run without user input.  For example, the command to create a JRF domain looks like the one below.  Note that this requires the user to have run RCU prior to running the command.

    weblogic-deploy\bin\createDomain.cmd -oracle_home c:\jrf12213 -domain_type JRF -domain_parent d:\demo\domains -model_file DemoDomain.yaml -rcu_db mydb.example.com:1539/PDBORCL -rcu_prefix DEMO

To have the Create Domain Tool run RCU, simply add the `-run_rcu` argument to the previous command line and the RCU schemas will be automatically created.  Be aware that when the tool runs RCU, it will automatically drop any conflicting schemas that already exist with the same RCU prefix prior to creating the new schemas!

The Create Domain Tool has an extensible domain type system.  The three built-in domain types (`WLS`, `RestrictedJRF`, and `JRF`) are defined in JSON files of the same name in the `WLSDEPLOY_HOME/lib/typedefs` directory.  For example, the `JRF` domain type is defined in the `WLSDEPLOY_HOME/lib/typedefs/JRF.json` file whose contents look like those shown below.

```json
{
    "copyright": "Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.",
    "license": "The Universal Permissive License (UPL), Version 1.0",
    "name": "JRF",
    "description": "JRF type domain definitions",
    "versions": {
        "12.1.2": "JRF_1212",
        "12.1.3": "JRF_1213",
        "12.2.1": "JRF_12CR2",
        "12.2.1.3": "JRF_12213"
    },
    "definitions": {
        "JRF_1212" : {
            "baseTemplate": "@@WL_HOME@@/common/templates/wls/wls.jar",
            "extensionTemplates": [
                "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.jrf_template_12.1.2.jar",
                "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.jrf.ws.async_template_12.1.2.jar",
                "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.wsmpm_template_12.1.2.jar",
                "@@ORACLE_HOME@@/em/common/templates/wls/oracle.em_wls_template_12.1.2.jar"
            ],
            "serverGroupsToTarget" : [ "JRF-MAN-SVR", "WSMPM-MAN-SVR" ],
            "rcuSchemas": [ "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS" ]
        },
        "JRF_1213" : {
            "baseTemplate": "@@WL_HOME@@/common/templates/wls/wls.jar",
            "extensionTemplates": [
                "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.jrf_template_12.1.3.jar",
                "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.jrf.ws.async_template_12.1.3.jar",
                "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.wsmpm_template_12.1.3.jar",
                "@@ORACLE_HOME@@/em/common/templates/wls/oracle.em_wls_template_12.1.3.jar"
            ],
            "serverGroupsToTarget" : [ "JRF-MAN-SVR", "WSMPM-MAN-SVR" ],
            "rcuSchemas": [ "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS" ]
        },
        "JRF_12CR2": {
            "baseTemplate": "Basic WebLogic Server Domain",
            "extensionTemplates": [
                "Oracle JRF WebServices Asynchronous services",
                "Oracle WSM Policy Manager",
                "Oracle Enterprise Manager"
            ],
            "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR" ],
            "rcuSchemas": [ "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS" ]
        },
        "JRF_12213": {
            "baseTemplate": "Basic WebLogic Server Domain",
            "extensionTemplates": [
                "Oracle JRF WebServices Asynchronous services",
                "Oracle WSM Policy Manager",
                "Oracle Enterprise Manager"
            ],
            "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR" ],
            "rcuSchemas": [ "WLS", "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS" ]
        }
    }
}
```

This file tells the Create Domain Tool which templates to use to create the domain, which server groups to target, and even which RCU schemas to create, all based on the version of WebLogic Server installed.  New domain types can be defined by creating a new JSON file with the same structure in the `WLSDEPLOY_HOME/lib/typedefs` directory.  For example, to define a `SOA` domain type for 12.2.1.3, add the `WLSDEPLOY_HOME/lib/typedefs/SOA.json` file with contents like those shown below.

```json
{
    "name": "SOA",
    "description": "SOA type domain definitions",
    "versions": {
        "12.2.1.3": "SOA_12213"
    },
    "definitions": {
        "SOA_12213": {
            "baseTemplate": "Basic WebLogic Server Domain",
            "extensionTemplates": [
                "Oracle SOA Suite"
            ],
            "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR",  "SOA-MGD-SVRS" ],
            "rcuSchemas": [ "STB", "WLS", "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS", "UCSUMS", "SOAINFRA" ]
        }
    }
}
```

After the new domain `typedef` file exists, simply specify the new domain type name to the `createDomain` script, being sure to reference an Oracle Home with the required components installed.  For pre-12.2.1 versions, the `-wlst_path` argument must be used to point to the product home where the appropriate WLST shell script exists; for example, for SOA 12.1.3, add `-wlst_path <ORACLE_HOME>/soa` so that the tool uses the WLST shell script with the proper environment for SOA domains.  In 12.2.1 and later, this is no longer necessary because the WLST shell script in the standard `<ORACLE_HOME>oracle_common/common/bin` directory will automatically load all components in the Oracle Home.  Using the new domain type, simply run the following command to run RCU and create the SOA domain with all of its resources and applications deployed.

    weblogic-deploy\bin\createDomain.cmd -oracle_home d:\SOA12213 -domain_type SOA -domain_parent d:\demo\domains -model_file DemoDomain.yaml -archive_file DemoDomain.zip -variable_file DemoDomain.properties -run_rcu -rcu_db mydb.example.com:1539/PDBORCL -rcu_prefix DEMO

To create more complex domains with clusters of different types, it is necessary to control the targeting of server groups to managed servers.  By default, all server groups in the domain type definition are targeted to all managed servers.  To create a SOA domain with SOA and OSB clusters, simply add the OSB template and server group to the SOA domain definition, as shown below.

```json
{
    "name": "SOA",
    "description": "SOA type domain definitions",
    "versions": {
        "12.2.1.3": "SOA_12213"
    },
    "definitions": {
        "SOA_12213": {
            "baseTemplate": "Basic WebLogic Server Domain",
            "extensionTemplates": [
                "Oracle SOA Suite",
                "Oracle Service Bus"
            ],
            "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR",  "SOA-MGD-SVRS",  "OSB-MGD-SVRS-COMBINED" ],
            "rcuSchemas": [ "STB", "WLS", "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS", "UCSUMS", "SOAINFRA" ]
        }
    }
}
```

Then, use the `ServerGroupTargetingLimits` map in the `domainInfo` section to limit the targeting of the Web Services Manager, SOA, and OSB server groups to the `soa_cluster` or `osb_cluster`, as appropriate.  In the example below, notice that the `JRF-MAN-SVR` server group is not listed; therefore, it will use the default targeting and be targeted to all managed servers.  The value of each element in this section is a logical list of server and/or cluster names.  As shown in the example, the value for each server group can be specified as a list, a comma-separated string, or a single-valued string.  There is no semantic difference between listing a cluster's member server names versus using the cluster name; the example uses these simply to show what is possible.

```$yaml
domainInfo:
    AdminUserName: weblogic
    AdminPassword: welcome1
    ServerStartMode: prod
    ServerGroupTargetingLimits:
        'WSMPM-MAN-SVR': soa_cluster
        'SOA-MGD-SVRS': 'soa_server1,soa_server2'
        'OSB-MGD-SVRS-COMBINED': [ osb_server1, osb_server2 ]

topology:
    Name: soa_domain
    AdminServerName: AdminServer
    Cluster:
        soa_cluster:
        osb_cluster:
    Server:
        AdminServer:
            ListenAddress: myadmin.example.com
            ListenPort: 7001
            Machine: machine1
            SSL:
                Enabled: true
                ListenPort: 7002
        soa_server1:
            ListenAddress: managed1.example.com
            ListenPort: 8001
            Cluster: soa_cluster
            Machine: machine2
            SSL:
                Enabled: true
                ListenPort: 8002
        soa_server2:
            ListenAddress: managed2.example.com
            ListenPort: 8001
            Cluster: soa_cluster
            Machine: machine3
            SSL:
                Enabled: true
                ListenPort: 8002
        osb_server1:
            ListenAddress: managed1.example.com
            ListenPort: 9001
            Cluster: osb_cluster
            Machine: machine2
            SSL:
                Enabled: true
                ListenPort: 9002
        osb_server2:
            ListenAddress: managed2.example.com
            ListenPort: 9001
            Cluster: osb_cluster
            Machine: machine3
            SSL:
                Enabled: true
                ListenPort: 9002
    UnixMachine:
        machine1:
            NodeManager:
                ListenAddress: myadmin.example.com
                ListenPort: 5556
        machine2:
            NodeManager:
                ListenAddress: managed1.example.com
                ListenPort: 5556
        machine3:
            NodeManager:
                ListenAddress: managed2.example.com
                ListenPort: 5556
    SecurityConfiguration:
        NodeManagerUsername: weblogic
        NodeManagerPasswordEncrypted: welcome1
```

One last note is that if the model or variables file contains encrypted passwords, add the `-use_encryption` flag to the command line to tell the Create Domain Tool that encryption is being used and to prompt for the encryption passphrase.  As with the database passwords, the tool can also read the passphrase from standard input (for example, `stdin`) to allow the tool to run without any user input.

## The Update Domain Tool

The Update Domain Tool uses a model, the archive, and WLST to update the configuration of an existing WebLogic Server domain, and to deploy applications and resources into the domain in either WLST online or offline mode.  The update tool will add or re-configure elements from the `topology` section of the model, and deploy applications and resources from the `resources` and `appDeployments` sections, as described in the Deploy Applications tool.

The Update Domain Tool will only add or update elements in the specified model. It will not attempt to remove any missing elements that were present in a previous model.

Running the Update Domain Tool in WLST offline mode is very similar to running the Create Domain Tool; simply provide the domain location and archive file, and separate model and variable files, if needed.  For example:

    weblogic-deploy\bin\updateDomain.cmd -oracle_home c:\wls12213 -domain_type WLS -domain_home domains\DemoDomain -archive_file DemoDomain.zip -model_file DemoDomain.yaml -variable_file DemoDomain.properties

In WLST online mode, simply add the information on how to connect to the WebLogic Server Administration Server, for example:

    weblogic-deploy\bin\updateDomain.cmd -oracle_home c:\wls12213 -domain_type WLS -domain_home domains\DemoDomain -archive_file DemoDomain.zip -model_file DemoDomain.yaml -variable_file DemoDomain.properties -admin_url t3://127.0.0.1:7001 -admin_user weblogic

As usual, the tool will prompt for the password (it can also be supplied by piping it to standard input of the tool).

Unlike the Create Domain Tool, the full domain home directory is specified, rather than the domain's parent directory, since the domain has already been established.

The Update Domain Tool will not attempt to recreate or add schemas for the RCU database, for domain types that use RCU.

When running the tool in WLST online mode, the update operation may require server restarts or a domain restart to pick up the changes.  The update operation can also encounter situations where it cannot complete its operation until the domain is restarted.  To communicate these conditions to scripts that may be calling the Update Domain Tool, the shell scripts have three special, non-zero exit codes to communicate these states:

- `101` - The domain needs to be restarted and the Update Domain Tool needs to be re-invoked with the same arguments.
- `102` - The servers impacted by the update operation need to be restarted, in a rolling fashion, starting with the Administration Server, if applicable.
- `103` - The entire domain needs to be restarted.

## The Deploy Applications Tool

**NOTE: Work on the Deploy Applications Tool to bring it in line with the text below is still in progress.**

The Deploy Applications Tool uses a model, the archive, and WLST to deploy applications and resources into an existing WebLogic Server domain in either WLST online or offline mode.  When deploying applications and resources from a model, the deploy tool focuses primarily on the `resources` and `appDeployments` sections of the model.  There are exceptions for the `domainInfo` and `topology` sections, where those configuration elements are deemed to be "application-related."  For example, the servers' `ServerStart` folder has an `Arguments` and a `ClassPath` attribute that change the server environment (when started by the Node Manager) that applications may rely on to function properly.  Likewise, the `domainInfo` section contains a list of JAR files that are to be placed in `<DOMAIN_HOME>/lib` which are relevant to applications for a similar reason.

The Deploy Applications Tool will only add or update elements in the specified model. It will not attempt to remove any missing elements that were present in a previous model.

In WLST online mode, the tool tries to minimize the need to redeploy the applications and shared libraries, and the need to restart the server.  It does this in a few ways:

- If the model references an application or shared library that is already deployed, the tool compares the binaries to determine whether redeployment is required.  Redeployment of shared libraries is particularly expensive since all applications using the shared library must be redeployed--even if the application has not changed.
- It looks at the knowledge base to determine which attributes require restart when they are changed.  If an attribute requires restart, the tool compares the current and model values to make sure that they are different before trying to apply a change.

The goal is to make the tool both able to support iterative deployment and able to minimize service disruption while doing its work when working against a running domain.

Running the Deploy Applications Tool in WLST offline mode is very similar to running the Create Domain Tool; simply provide the domain location and archive file, and separate model and variable files, if needed.  For example:

    weblogic-deploy\bin\deployApps.cmd -oracle_home c:\wls12213 -domain_home domains\DemoDomain -archive_file DemoDomain.zip -model_file DemoDomain.yaml -variable_file DemoDomain.properties

In WLST online mode, simply replace the `-domain_home` argument with the information on how to connect to the WebLogic Server Administration Server, for example:

    weblogic-deploy\bin\deployApps.cmd -oracle_home c:\wls12213 -domain_home domains\DemoDomain -archive_file DemoDomain.zip -model_file DemoDomain.yaml -variable_file DemoDomain.properties -admin_url t3://127.0.0.1:7001 -admin_user weblogic

As usual, the tool will prompt for the password (it can also be supplied by piping it to standard input of the tool).

When running the tool in WLST online mode, the deploy operation may require server restarts or a domain restart to pick up the changes.  The deploy operation can also encounter situations where it cannot complete its operation until the domain is restarted.  To communicate these conditions to scripts that may be calling the Deploy Applications Tool, the shell scripts have three special, non-zero exit codes to communicate these states:

- `101` - The domain needs to be restarted and the Deploy Applications Tool needs to be re-invoked with the same arguments.
- `102` - The servers impacted by the deploy operation need to be restarted, in a rolling fashion, starting with the Administration Server, if applicable.
- `103` - The entire domain needs to be restarted.

## The Discover Domain Tool

The Discover Domain Tool provides a bootstrapping mechanism to creating a model and archive file by inspecting an existing domain and gathering configuration and binaries from it.  Note that the model file produced by the tool is not directly usable by the Create Domain Tool or the Deploy Applications Tool because the Discover Domain Tool does not discover the passwords from the existing domain.  Instead, it puts a `--FIX ME--` placeholder for passwords it finds.  Domain users are also not discoverable so the tool does not create the `AdminUserName` and `AdminPassword` fields in the `domainInfo` section, which are needed by the Create Domain Tool.  The idea of this tool is simply to provide a starting point where the user can edit the generated model and archive file to suit their needs for running one of the other tools.

To run the Discover Domain Tool, simply provide the domain location and the name of the archive file; a separate model file can also be provided to make editing the generated model easier.  For example:

    weblogic-deploy\bin\discoverDomain.cmd -oracle_home c:\wls12213 -domain_home domains\DemoDomain -archive_file DiscoveredDemoDomain.zip -model_file DiscoveredDemoDomain.yaml

When creating the archive, the tool will try to gather all binaries, scripts, and required directories referenced by the domain configuration with the following caveats.

1. Any binaries referenced from the `ORACLE_HOME` will not be gathered, as they are assumed to exist in any target domain to which model-driven operations will be applied.  Doing this is key to allowing the model to be WebLogic Server version independent.
2. In its current form, the discover domain Tool will only gather binaries and scripts that are accessible from the local machine.  Warnings will be generated for any binaries or scripts that cannot be found but the configuration for those binaries will still be collected, where possible.  It is the user's responsibility to add those missing files to the archive in the appropriate locations and edit the the model, as needed, to point to those files inside the archive using the relative path inside the archive (for example, `wlsdeploy/applications/myapp.ear`).

## The Variable Injector Tool

The variable injector tool is used to tokenize a model with variables. The values for these variables are assigned using an external property file. This facilitates using the same domain model to create new domains in different environments. The variable injector tool can be run as an option in the Discover Domain tool, or or from the stand-alone command line interface.

To enable the Variable Injector during the Discover Domain, create a variable injector configuration by placing a json file named model_variable_injector.json into the \<WLSDEPLOY\>/lib directory using one or more of the pre-defined keywords and/or a CUSTOM list of files. A keyword points to an injector directive file. The tool applies the directives to the attributes in a model, and if the directive matches an attribute, then a property token with a unique variable name is injected into the model and replaces the attribute value. The variable name and model attribute value are placed into the external variable properties file. 

NOTE: Variable injection on an attribute is only performed once. The property token is not replaced by any subsequent matches.

If variable injection is enabled, the Discover Domain Tool calls the variable injector after the model has been discovered and after all filters run, but before model validation.

The supported keywords are as follows:

- CREDENTIALS - All MBean credentials attribute values (user and password) are injected with a variable.

- HOST - All MBean Host attribute values in the model are injected with a variable.

- PORT - All MBean Port attribute values in the model are injected with a variable.

- TARGET - All MBean Target attribute values in the model are injected with a variable.

- TOPOLOGY - Common environmental MBean attributes found in the topology section of the model are injected with a variable. 
   This includes server, machine and node manager ports, credentials and listen addresses, and cluster messaging modes, addresses and ports.

- URL - All MBean URL attribute values in the model are injected with a variable.

NOTE: The directives used by each pre-defined keyword are defined in an injector json file that is located in the \<WLSDEPLOY\>/lib/injectors folder. These files should not be changed, but could be used as .

Here is an example of a model_variable_injector.json file using the PORT keyword.

```json
{
	"PORT": {}
}
```

Below is a model snippet that shows injected variables in the port attributes.

```$yaml

topology:
    Name: soa_domain
    AdminServerName: AdminServer
    Cluster:
        soa_cluster:
        osb_cluster:
    Server:
        AdminServer:
            ListenAddress: myadmin.example.com
            ListenPort: @@PROP:Server.AdminServer.ListenPort@@
            Machine: machine1
            SSL:
                Enabled: true
                ListenPort: @@PROP:Server.SSL.AdminServer.ListenPort@@
        soa_server1:
            ListenAddress: managed1.example.com
            ListenPort: @@PROP:Server.soa_server1.ListenPort@@
            Cluster: soa_cluster
            Machine: machine2
            SSL:
                Enabled: true
                ListenPort: @@PROP:Server.SSL.soa_server1.ListenPort@@
        soa_server2:
            ListenAddress: managed2.example.com
            ListenPort: @@PROP:Server.soa_server2.ListenPort@@
            Cluster: soa_cluster
            Machine: machine3
            SSL:
                Enabled: true
                ListenPort: @@PROP:Server.SSL.soa_server2.ListenPort@@
```

And the resulting variable property file:

```
Server.AdminServer.ListenPort=7001
Server.AdminServer.SSL.ListenPort=7002
Server.soa_server1.ListenPort=8001
Server.soa_server1.SSL.ListenPort=8002
Server.soa_server2.ListenPort=8001
Server.soa_server2.SSL.ListenPort=8002
```

To specify the name and location of the variable properties file for the Discover Tool, use the argument `-variable_properties_file` on the command line. Usage of the variable_properties_file argument without the presence of the model variable injector file in the \<WLSDEPLOY\>/lib directory will cause an error condition and the tool will exit. If the model variable injector file exists in the directory, but the command line argument is not used, the variable properties file is created with the following defaults: If the model_file command line argument is used on the Discover Domain run, the properties file name and location will be the same as the model file, with the file extension `.properties`. If only the archive file argument is present, the archive file name and location will be used.

As with the archive and model file, each run of the discover domain tool will overwrite the contents of an existing variable property file with the values from the current run.

### Custom Variable Injector

To designate custom injector directives, use the CUSTOM keyword in the model_variable_injector.json. The CUSTOM keyword requires a a list of one or more custom injector directive json files. 

An injector directive contains a key that identifies an attribute to be tokenized, and an optional set of directive properties. The key is a period separated MBean hierarchy and attribute name as they are defined in the model. Always exclude the name of the model section from the injector key.

For example, an injector key for the Server SSL Listen Port is as below. This directive contains no additional properties.

```json
{
  "Server.SSL.ListenPort": {}
}
```

NOTE: The hierarchy of MBeans in the model for the ListenPort attribute and note that the MBean name of AdminServer is NOT included in the directive:

```yaml
topology:
    Server:
        AdminServer:
            ListenAddress: myadmin.example.com
            ListenPort: 7001
            Machine: machine1
            SSL:
                Enabled: true
                ListenPort: 7002
```

These custom injector json files will be processed by the Variable Injector tool before keywords, each file processed in list order. A property injected into an attribute will not be replaced by any subsequent matches.

#### Custom directive properties

Include the following properties to refine the directive as specified.

- force:<attribute>
    If the MBean hierarchy exists in the model, but the attribute does not, then the attribute will be added and persisted to the discovered model. The value stored in the
    model is the weblogic default value.

- variable_value:
    Replace the model value with the specified value in the variable properties. This may be used in conjunction with the force directive, replacing the default value with the indicated value.

- regexp:
    A list of regexp patterns that will be applied to either the string values or map values of an attribute in the model. If the pattern matches, then the matching part of the
    string or dictionary will be injected with a property token and a unique variable name .
-- pattern:
    the regular expression pattern to apply to the string value or map values of an attribute
-- suffix:
    The suffix name to append to each resulting variable name in order to create a unique variable name

The regexp list is useful when only a segment of a string value or map needs to be tokenized (giving you a clean list of property values in the variable properties file). You can inject more than one token into a string or map with multiple patterns. However, when you have more than one pattern, you must provide a suffix for each. This allows the tool to generate a unique variable name for each token in the string or map.

The following is an example of how to effectively use the regexp directive list to search for a segment in a string value. In this example, we want to search for the host and port in each Oracle JDBC URL that uses the special Oracle URL notation, and create an entry for the host and port in the variable properties file.

In the model, we expect to find a URL like the following:

```$yaml
    JDBCSystemResource:
        Database1:
            JdbcResource:
                JDBCDriverParams:
                    URL: 'jdbc:oracle:thin:@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)(HOST=slc05til.us.oracle.com)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=orcl.us.oracle.com)))'
```

We create a directive in our custom injector json file:

```json
  "JDBCSystemResource.JdbcResource.JDBCDriverParams.URL":
  {
    "regexp": [
      {
        "pattern": "(?<=PORT=)[\\w.-]+(?=\\))",
        "suffix": "Port"
      },
      {
        "pattern": "(?<=HOST=)[\\w.-]+(?=\\))",
        "suffix": "Host"
      }
    ]
  },
```

During the Discover Domain tool run, the pattern is applied to the URL string and tokens injected into the string:

```
URL: 'jdbc:oracle:thin:@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)(HOST=@@PROP:JDBCSystemResource.Database1.JdbcResource.JDBCDriverParams.URL--Host@@:)(PORT=@@PROP:JDBCSystemResource.Database1.JdbcResource.JDBCDriverParams.URL--Port@@)))(CONNECT_DATA=(SERVICE_NAME=orcl.us.oracle.com)))'
```

And The variables put in the properties file:

```
JDBCSystemResource.Database1.JdbcResource.JDBCDriverParams.URL--Host=slc05til.us.oracle.com
JDBCSystemResource.Database1.JdbcResource.JDBCDriverParams.URL--Port=1521
```

#### Selecting specific MBean names for variable injection

This final custom directive allows you to explicitly define which named entries for an MBean in the model you wish to inject properties. For instance, you might wish to tokenize an attribute just for a specific server. To define a list of one or more names for a specific MBean in the injector directive hierarchy, format the list as follows:
```
MBean[comma separated list of names]
``
To select only the admin server named AdminServer for a Server directive, use the format Server[AdminServer]. To select servers soa_server1 and soa_server2, format the key as Server[soa_server1,soa_server2]

The injector tool recognizes two KEYWORDS for a user list, MANAGED_SERVERS (all the managed servers in the model) and ADMIN_SERVER (The admin server in the model).

A custom injector for the admin server SSL listen port is:

```json
{
  "Server[ADMIN_SERVER].SSL.ListenPort": {},
}
```

### Model Filters

WebLogic Deploy Tooling supports the use of model filters to manipulate the domain model. The Create Domain, Update Domain, and Deploy Applications Tools apply filters to the model after it is read, before it is validated and applied to the domain. The Discover Domain Tool applies filters to the model after it has been discovered, before the model is validated and written.

Model filters are written in Jython, and must be compatible with the version used in the corresponding version of WLST. A filter must implement the method filter_model(model), which accepts as a single argument the domain model as a Jython dictionary. The method should make whatever adjustments are needed to the domain model. Filters can be stored in any directory, as long as they can be accessed by WebLogic Deploy Tooling.
 
The following filter example (fix-password.py) sets the password for two attributes in the SecurityConfiguration WLST folder.

```python
def filter_model(model):
	if model and 'topology' in model:
		if 'SecurityConfiguration' in model['topology']:
			model['topology']['SecurityConfiguration']['CredentialEncrypted'] = 'welcome1'
			model['topology']['SecurityConfiguration']['NodeManagerPasswordEncrypted'] = 'welcome1'
			print 'Replaced SecurityConfiguration password'
		else:
			print 'SecurityConfiguration not in the model'
```

Model filters are configured by creating a model.filters.json file in the WLSDEPLOY_HOME/lib directory. This file has separate sections for filters to be applied for specific tools. Filters in the "deploy" section are also applied for the Update Domain Tool.
 
This example deploys two filters for the Create Domain Tool: fix-password.py and no-mail.py, and one filter for the Discover Domain tool.

```json
{
  "create": [
    { "name": "fixPassword", "path": "/home/user/fix-password.py" },
    { "name": "noMail", "path": "/home/user/no-mail.py" }
  ],
  "deploy": [
  ],
  "discover": [
    { "name": "noMail", "path": "/home/user/no-mail.py" }
  ]
}
```

## Samples

A sample of a model_variable_injector.json file and a custom injector json file are installed in the WLSDEPLOY/samples directory.


## Downloading and Installing the Software

The Oracle WebLogic Server Deploy Tooling project repository is located at [`https://github.com/oracle/weblogic-deploy-tooling`](https://github.com/oracle/weblogic-deploy-tooling).  Binary distributions of the `weblogic-deploy.zip` installer can be downloaded from the [GitHub Releases page](https://github.com/oracle/weblogic-deploy-tooling/releases).  To install the software, simply unzip the `weblogic-deploy.zip` installer on a machine that has the desired versions of WebLogic Server installed.  After being unzipped, the software is ready to use, just set the `JAVA_HOME` environment variable to point to a Java 7 or higher JDK  and the shell scripts are ready to run.
