# WebLogic Deploy Tooling

Many organizations are using WebLogic Server, with or without other Oracle Fusion Middleware components, to run their enterprise applications.  As more and more organizations move toward Continuous Delivery of their applications, the importance of automated testing grows.  Automating WebLogic Server domain creation and application deployment with hand-coded WLST scripts is challenging.  After those scripts exist for a project, they must be maintained as the project evolves.  The motivation for the WebLogic Deploy Tooling project is to remove the need for most users to write WLST scripts for routine domain creation and application deployment tasks.  Instead, the project team can write a declarative, metadata model describing the domain and applications (with their dependent resources), and use one or more of the single-purpose tools provided that perform domain lifecycle operations based on the content of the model.  The goal is to make it easy to stand up environments and perform domain lifecycle operations in a repeatable fashion based on a metadata model that can be treated as source and evolve as the project evolves.

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

***
The [current release](https://github.com/oracle/weblogic-deploy-tooling/releases) of WebLogic Deploy Tooling is 1.9.12.

This release was published on April, 29, 2021.
***

# Documentation

Documentation for WebLogic Deploy Tooling is [available here](https://oracle.github.io/weblogic-deploy-tooling/).

This documentation includes information for users and for developers.

# Contributing

Those who wish to contribute to the WebLogic Deploy Tooling code will find useful information [here](CONTRIBUTING.md).
