---
title: "Prepare Model Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 8
description: "Prepares model files for deploying to WebLogic Kubernetes Operator environment."
---


The Prepare Model Tool prepares WDT model files for deploying to specific target environments. These customizations include:
- Removing sections from the model that are not compatible with the environment
- Removing files from the archive that are not compatible with the environment
- Updating model file(s) to set parameters required by the environment
- Replacing credential and attribute values with WDT macros
- Generating a UNIX shell script that will help with creating any required Kubernetes secrets
- Generating a variable properties file to customize attribute values
- Generating any additional configuration files to configure the target environment


To use the Prepare Model Tool, simply run the `prepareModel` shell script with the correct arguments.  To see the list of valid arguments, simply run the shell script with the `-help` option (or with no arguments) for usage information.

For example, to prepare model files for use with WebLogic Kubernetes Operator, run the tool with `-target wko` as follows:
```
$ $WLSDEPLOY_HOME/bin/prepareModel.sh -oracle_home /u01/wls12213 -model_file model1.yaml, model2.yaml -target wko -output_dir $HOME/wko-output
```

In the output directory, you will find:
```
model1.yaml
model2.yaml
wko_variable.properties
create_k8s_secrets.sh
wko-domain.yaml
```


You can then customize the `wko_variable.properties` and `create_k8s_secrets.sh` to provide environment-specific values.


For more information about additional target environments and options, see [Target environments]({{< relref "/userguide/target_env.md" >}}).

### Parameter table for `prepareModel`
| Parameter | Definition | Default |
| ---- | ---- | ---- |
| `-model_file` | (Required). Location of the model file. This can also be specified as a comma-separated list of models, where each successive model layers on top of the previous ones. |    |
| `-oracle_home` | Home directory of the Oracle WebLogic installation. Required if the `ORACLE_HOME` environment variable is not set. |    |
| `-output_dir` | (Required) Location where to write the output files. |    |
| `-target` | (Required) Name of the target configuration such as `wko`, `vz`, `k8s`. |    |
| `-variable_file` | The location of the property file containing the values for variables used in the model. This can also be specified as a comma-separated list of property files, where each successive set of properties layers on top of the previous ones. |    |
