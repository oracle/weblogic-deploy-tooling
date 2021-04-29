## WebLogic Deploy Tooling

Many organizations are using WebLogic Server, with or without other Oracle Fusion Middleware components, to run their enterprise applications.  As more and more organizations move toward Continuous Delivery of their applications, the importance of automated testing grows.  Automating WebLogic Server domain creation and application deployment with hand-coded WLST scripts is challenging.  After those scripts exist for a project, they must be maintained as the project evolves.  WebLogic Deploy Tooling (WDT) removes the need for most users to write WLST scripts for routine domain creation and application deployment tasks.  Instead, you can write a declarative, metadata model describing the domain and applications (with their dependent resources), and use one or more of the single-purpose tools that perform domain lifecycle operations based on the content of the model.  This makes it easy to stand up environments and perform domain lifecycle operations in a repeatable fashion based on a metadata model that can be treated as source and evolve as the project evolves.


WDT provides several single-purpose tools, all exposed as shell scripts (for both Windows and UNIX):

- The [Create Domain Tool]({{< relref "/create.md" >}}) (`createDomain`) understands how to create a domain and populate the domain with all resources and applications specified in the model.
- The [Update Domain Tool]({{< relref "/update.md" >}}) (`updateDomain`) understands how to update an existing domain and populate the domain with all resources and applications specified in the model, either in offline or online mode.
- The [Deploy Applications Tool]({{< relref "/deploy.md" >}}) (`deployApps`) understands how to add resources and applications to an existing domain, either in offline or online mode.
- The [Discover Domain Tool]({{< relref "/discover.md" >}}) (`discoverDomain`) introspects an existing domain and creates a model file describing the domain and an archive file of the binaries deployed to the domain.
- The [Encrypt Model Tool]({{< relref "/encrypt.md" >}}) (`encryptModel`) encrypts the passwords in a model (or its variable file) using a user-provided passphrase.
- The [Validate Model Tool]({{< relref "/validate.md" >}}) (`validateModel`) provides both standalone validation of a model as well as model usage information to help users write or edit their models.
- The [Compare Model Tool]({{< relref "/compare.md" >}}) (`compareModel`) compares two model files.
- The [Prepare Model Tool]({{< relref "/prepare.md" >}}) (`prepareModel`) prepares model files for deploying to WebLogic Server Kubernetes Operator environment.
- The [Extract Domain Resource Tool]({{< relref "/kubernetes.md" >}}) (`extractDomainResource`) generates a domain resource YAML for use with the Oracle WebLogic Server Kubernetes Operator.
- The [Variable Injector Tool]({{< relref "/variable_injection.md" >}}) is used to tokenize a model with variables.
- The [Model Help Tool]({{< relref "/model_help.md" >}}) (`modelHelp.sh`) provides information about the folders and attributes that are valid for sections and folders of a domain model.

As new use cases are discovered, new tools will likely be added to cover those operations but all will use the metadata model to describe what needs to be done.


### Download and Install the Software

The Oracle WebLogic Server Deploy Tooling project repository is located at [`https://github.com/oracle/weblogic-deploy-tooling`](https://github.com/oracle/weblogic-deploy-tooling).  Binary distributions of the `weblogic-deploy.zip` installer can be downloaded from the [GitHub Releases page](https://github.com/oracle/weblogic-deploy-tooling/releases).  To install the software, simply unzip the `weblogic-deploy.zip` installer on a machine that has the desired versions of WebLogic Server installed.  After being unzipped, the software is ready to use, just set the `JAVA_HOME` environment variable to point to a Java 7 or higher JDK  and the shell scripts are ready to run.


### Supported WLS Versions

For the supported WebLogic Server and JDK versions required to run WebLogic Server Deploy Tooling, see [Supported WLS Versions]({{< relref "/wls_versions.md" >}}).


## Concepts

- [The Model]({{< relref "/model.md" >}})
- [The Archive File]({{< relref "/archive.md" >}})
- [Model Use Cases]({{< relref "/use_cases.md" >}})
- [Tools Configuration]({{< relref "/tool_configuration.md" >}})

## Developer Guide

For information for developers, see the [Developer Guide]({{< relref "/developer/_index.md" >}}).

## Known Issues

See the following list of [Known Issues]({{< relref "/KnownIssues.md" >}}) and workarounds.
