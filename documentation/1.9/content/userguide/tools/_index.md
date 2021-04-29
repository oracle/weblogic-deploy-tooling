+++
title = "WDT Tools"
date = 2019-02-22T15:27:54-05:00
weight = 1
pre = "<b> </b>"
+++


The [Create Domain Tool]({{< relref "/create.md" >}}) (`createDomain`) understands how to create a domain and populate the domain with all resources and applications specified in the model.

The [Update Domain Tool]({{< relref "/update.md" >}}) (`updateDomain`) understands how to update an existing domain and populate the domain with all resources and applications specified in the model, either in offline or online mode.

The [Deploy Applications Tool]({{< relref "/deploy.md" >}}) (`deployApps`) understands how to add resources and applications to an existing domain, either in offline or online mode.

The [Discover Domain Tool]({{< relref "/discover.md" >}}) (`discoverDomain`) introspects an existing domain and creates a model file describing the domain and an archive file of the binaries deployed to the domain.

The [Encrypt Model Tool]({{< relref "/encrypt.md" >}}) (`encryptModel`) encrypts the passwords in a model (or its variable file) using a user-provided passphrase.

The [Validate Model Tool]({{< relref "/validate.md" >}}) (`validateModel`) provides both standalone validation of a model as well as model usage information to help users write or edit their models.

The [Compare Model Tool]({{< relref "/compare.md" >}}) (`compareModel`) compares two model files.

The [Prepare Model Tool]({{< relref "/prepare.md" >}}) (`prepareModel`) prepares model files for deploying to WebLogic Kubernetes Operator environment.

The [Extract Domain Resource Tool]({{< relref "/kubernetes.md" >}}) (`extractDomainResource`) generates a domain resource YAML for use with the WebLogic Kubernetes Operator.

The [Variable Injector Tool]({{< relref "/variable_injection.md" >}}) is used to tokenize a model with variables.

The [Model Help Tool]({{< relref "/model_help.md" >}}) (`modelHelp.sh`) provides information about the folders and attributes that are valid for sections and folders of a domain model.
