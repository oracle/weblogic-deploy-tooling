# WebLogic Deploy Tooling

WebLogic Deploy Tooling (WDT) makes it easy to stand up WebLogic environments and perform
domain lifecycle operations in a repeatable fashion based on a metadata model that
can be treated as source and evolve as the project evolves.

Many organizations use WebLogic Server, with or without other Oracle Fusion Middleware components,
to run their enterprise applications. And, as more and more of these organizations move toward Continuous Delivery
of their applications, the importance of automated configuration application deployment grows. This automation
is often implemented using the WebLogic Scripting Tool (WLST) configuration and deployment scripting language, but this is challenging.
Such scripts must be carefully updated as the project evolves or the project is deployed to different environments,
such as test to production.

WebLogic Deploy Tooling  removes the need for most WebLogic Server deployments to rely on hand-coded WLST
scripts for automating routine domain creation and application deployment tasks. It lets you write a
declarative, metadata model, describing the domain and applications (with their dependent resources),
and provides single-purpose tools that perform domain lifecycle operations based on the content of
the model. It also lets you specify simple mutations suitable for moving your model between
different environments, such as between test and production.

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
WebLogic Deploy Tooling version and release information can be found [here](https://github.com/oracle/weblogic-deploy-tooling/releases).
***

## Documentation

Documentation for WebLogic Deploy Tooling is [available here](https://oracle.github.io/weblogic-deploy-tooling/).

This documentation includes information for users and for developers.

## Related projects

* [WebLogic Kubernetes Operator](https://github.com/oracle/weblogic-kubernetes-operator)
* [WebLogic Image Tool](https://github.com/oracle/weblogic-image-tool)
* [WebLogic Kubernetes Toolkit UI](https://github.com/oracle/weblogic-toolkit-ui)
* [WebLogic Monitoring Exporter](https://github.com/oracle/weblogic-monitoring-exporter)
* [WebLogic Logging Exporter](https://github.com/oracle/weblogic-logging-exporter)
* [WebLogic Remote Console](https://github.com/oracle/weblogic-remote-console)

## Contributing

<!-- If your project has specific contribution requirements, update the
    CONTRIBUTING.md file to ensure those requirements are clearly explained. -->

This project welcomes contributions from the community. Before submitting a pull
request, please [review our contribution guide](./CONTRIBUTING.md).

## Security

Please consult the [security guide](./SECURITY.md) for our responsible security
vulnerability disclosure process.

## License

Copyright (c) 2017, 2022, Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at
<https://oss.oracle.com/licenses/upl/>.
