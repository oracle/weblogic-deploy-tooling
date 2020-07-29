# Oracle WebLogic Server Deploy Tooling

Many organizations are using WebLogic Server, with or without other Oracle Fusion Middleware components, to run their enterprise applications.  As more and more organizations move toward Continuous Delivery of their applications, the importance of automated testing grows.  Automating WebLogic Server domain creation and application deployment with hand-coded WLST scripts is challenging.  After those scripts exist for a project, they must be maintained as the project evolves.  The motivation for the Oracle WebLogic Server Deploy Tooling project is to remove the need for most users to write WLST scripts for routine domain creation and application deployment tasks.  Instead, the project team can write a declarative, metadata model describing the domain and applications (with their dependent resources), and use one or more of the single-purpose tools provided that perform domain lifecycle operations based on the content of the model.  The goal is to make it easy to stand up environments and perform domain lifecycle operations in a repeatable fashion based on a metadata model that can be treated as source and evolve as the project evolves.

## Features of the Oracle WebLogic Server Deploy Tooling

Currently, the project provides several single-purpose tools, all exposed as shell scripts (both Windows and UNIX scripts are provided):

- The [Create Domain Tool](site/create.md) (`createDomain`) understands how to create a domain and populate the domain with all resources and applications specified in the model.
- The [Update Domain Tool](site/update.md) (`updateDomain`) understands how to update an existing domain and populate the domain with all resources and applications specified in the model, either in offline or online mode.
- The [Deploy Applications Tool](site/deploy.md) (`deployApps`) understands how to add resources and applications to an existing domain, either in offline or online mode.
- The [Discover Domain Tool](site/discover.md) (`discoverDomain`) introspects an existing domain and creates a model file describing the domain and an archive file of the binaries deployed to the domain.
- The [Encrypt Model Tool](site/encrypt.md) (`encryptModel`) encrypts the passwords in a model (or its variable file) using a user-provided passphrase.
- The [Validate Model Tool](site/validate.md) (`validateModel`) provides both standalone validation of a model as well as model usage information to help users write or edit their models.
- The [Compare Model Tool](site/compare.md) (`compareModel`) compares two model files.
- The [Prepare Model Tool](site/prepare.md) (`prepareModel`) prepares model files for deploying to WebLogic Server Kubernetes Operator environment.
- The [Extract Domain Resource Tool](site/kubernetes.md) (`extractDomainResource`) generates a domain resource YAML for use with the Oracle WebLogic Server Kubernetes Operator.
- The [Variable Injector Tool](site/variable_injection.md) is used to tokenize a model with variables.
- The [Model Help Tool](site/model_help.md) (`modelHelp.sh`) provides information about the folders and attributes that are valid for sections and folders of a domain model.

As new use cases are discovered, new tools will likely be added to cover those operations but all will use the metadata model to describe what needs to be done.


## Downloading and Installing the Software

The Oracle WebLogic Server Deploy Tooling project repository is located at [`https://github.com/oracle/weblogic-deploy-tooling`](https://github.com/oracle/weblogic-deploy-tooling).  Binary distributions of the `weblogic-deploy.zip` installer can be downloaded from the [GitHub Releases page](https://github.com/oracle/weblogic-deploy-tooling/releases).  To install the software, simply unzip the `weblogic-deploy.zip` installer on a machine that has the desired versions of WebLogic Server installed.  After being unzipped, the software is ready to use, just set the `JAVA_HOME` environment variable to point to a Java 7 or higher JDK  and the shell scripts are ready to run.


## Supported WLS Versions

For the supported WebLogic Server and JDK versions required to run WebLogic Server Deploy Tooling, see [Supported WLS Versions](site/wls_versions.md).


## Concepts

- [The Model](site/model.md)
- [The Archive File](site/archive.md)
- [Model Use Cases](site/use_cases.md)
- [Tool Configuration](site/tool_configuration.md)

## Developer Guide

For information for developers, see the [Developer Guide](site/developer/developer_guide.md).

## Known Issues

See the following list of [Known Issues](KnownIssues.md) and workarounds.
