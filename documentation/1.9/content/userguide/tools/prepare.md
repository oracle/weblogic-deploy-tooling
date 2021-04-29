---
title: "Prepare Model Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 8
description: "Prepares model files for deploying to WebLogic Kubernetes Operator environment."
---


The Prepare Model Tool prepares WDT model files for deploying to specific target environments. These customizations include:
- Removing sections from the model that are not compatible with the environment
- Replacing credential and attribute values with WDT macros
- Generating a UNIX shell script that will help with creating any required Kubernetes secrets
- Generating a variable properties file to customize attribute values
- Generating any additional configuration files to configure the target environment
- Updating the model file(s)


To use the Prepare Model Tool, simply run the `prepareModel` shell script with the correct arguments.  To see the list of valid arguments, simply run the shell script with the `-help` option (or with no arguments) for usage information.

For example, to prepare model files for use with Oracle Weblogic Server Kubernetes Operator, run the tool with `-target wko` as follows:
```
$WLSDEPLOY_HOME/bin/prepareModel.sh -oracle_home /u01/wls12213 -model_file model1.yaml, model2.yaml -target wko -output_dir $HOME/wko-output
```

In the output directory, you will find:
```
model.yaml
model1.yaml
model2.yaml
create_k8s_secrets.sh
wko_variable.properties
```


You can then customize the `wko_variable.properties` and `create_k8s_secrets.sh` to provide environment-specific values.


For more information about additional target environments and options, see [Target Environments]({{< relref "/concepts/target_env.md" >}}).
