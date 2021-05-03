## WebLogic Deploy Tooling

Many organizations are using WebLogic Server, with or without other Oracle Fusion Middleware components, to run their enterprise applications.  As more and more organizations move toward Continuous Delivery of their applications, the importance of automated testing grows.  Automating WebLogic Server domain creation and application deployment with hand-coded WLST scripts is challenging.  After those scripts exist for a project, they must be maintained as the project evolves.  WebLogic Deploy Tooling (WDT) removes the need for most users to write WLST scripts for routine domain creation and application deployment tasks.  Instead, you can write a declarative, metadata model describing the domain and applications (with their dependent resources), and use one or more of the single-purpose tools that perform domain lifecycle operations based on the content of the model.  This makes it easy to stand up environments and perform domain lifecycle operations in a repeatable fashion based on a metadata model that can be treated as source and evolve as the project evolves.


WDT provides several single-purpose tools, all exposed as shell scripts (for both Windows and UNIX), that can:

* Create or update a domain.  
* Populate a domain with all the resources and applications specified in a model.
* Add resources and applications to an existing domain.
* Introspect an existing domain and create a model file describing the domain and an archive file of the binaries deployed to the domain.
* Encrypt the passwords in a model (or its variable file).
* Validate a model as well as provide model usage information.
* Compare model files.
* Prepare model files for deploying to the WebLogic Kubernetes Operator environment.
* Generate a domain resource YAML file for use with the WebLogic Kubernetes Operator.
* Tokenize a model with variables.
* Provide information about the folders and attributes that are valid for sections and folders of a domain model.

For detailed information, see [WDT Tools]({{< relref "/userguide/tools/" >}}).

***
### Current production release

WebLogic Deploy Tooling version and release information is found [here](https://github.com/oracle/weblogic-deploy-tooling/releases).
***
### Recent changes and known issues

See the [Release Notes]({{< relref "/release-notes.md" >}}) for known issues and workarounds.

### About this documentation

This documentation includes sections targeted to different audiences:

* [Concepts]({{< relref "/concepts/" >}}) explains the underlying metadata models and archive files.
* The [User guide]({{< relref "/userguide/" >}}) contains detailed usage information, including how to install and configure WebLogic Deploy Tooling, and how to use each tool.
* The [Samples]({{< relref "/samples/" >}}) provide informative use case scenarios.
* The [Developer guide]({{< relref "/developer/" >}}) provides details for people who want to understand how WDT is built, its features mapped and implemented.


### Contributing
Those who wish to contribute to the WebLogic Deploy Tooling code will find useful information [here](https://github.com/oracle/weblogic-deploy-tooling/blob/master/CONTRIBUTING.md).
