## WebLogic Deploy Tooling

Many organizations are using WebLogic Server, with or without other Oracle Fusion Middleware components, to run their enterprise applications.  As more and more organizations move toward Continuous Delivery of their applications, the importance of automated testing grows.  Automating WebLogic Server domain creation and application deployment with hand-coded WLST scripts is challenging.  After those scripts exist for a project, they must be maintained as the project evolves.  WebLogic Deploy Tooling (WDT) removes the need for most users to write WLST scripts for routine domain creation and application deployment tasks.  Instead, you can write a declarative, metadata model describing the domain and applications (with their dependent resources), and use one or more of the single-purpose tools that perform domain lifecycle operations based on the content of the model.  This makes it easy to stand up environments and perform domain lifecycle operations in a repeatable fashion based on a metadata model that can be treated as source and evolve as the project evolves.


WDT provides several single-purpose tools, all exposed as shell scripts (for both Windows and UNIX). For detailed information, see [WDT Tools]({{< relref "/userguide/tools/" >}}).


### Current production release

The current [release](https://github.com/oracle/weblogic-deploy-tooling/releases) of WebLogic Deploy Tooling is 1.9.11. This release was published on March, 2021.

### Recent changes and known issues

See the [Release Notes]({{< relref "/release-notes.md" >}}) for recent changes, known issues, and workarounds.

### About this documentation

This documentation includes sections targeted to different audiences. To help you find what you are looking for more easily, please consult this table of contents:

* [Concepts]({{< relref "/concepts/" >}}) explains the underlying metadata model, files, and configurations...
* The [User guide]({{< relref "/userguide/" >}}) contains detailed usage information, including how to install and configure WebLogic Deploy Tooling, and how to use each tool.
* The [Samples]({{< relref "/samples/" >}}) provide detailed example code and instructions that show you how to perform various tasks.
* The [Developer guide]({{< relref "/developer/" >}}) provides details for people who want to understand how WDT is built, tested, and so on.


### Contributing
Those who wish to contribute to the WebLogic Deploy Tooling code will find useful information [here](https://github.com/oracle/weblogic-deploy-tooling/blob/master/CONTRIBUTING.md).
