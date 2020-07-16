## The Prepare Model Tool

The Prepare Model Tool prepares WDT model files for deploying to specific target environments. These customizations include:
- removing sections from the model that are not compatible with the environment
- replacing credential and attribute values with WDT macros
- generating a UNIX shell script that will help with creating any required kubernetes secrets
- generating a variable properties file to customize attribute values
- updating the model file(s)
     
To use the Prepare Model Tool, simply run the `prepareModel` shell script with the correct arguments.  To see the list of valid arguments, simply run the shell script with the `-help` option (or with no arguments) for usage information.

For example, to prepare model files for use with Oracle Weblogic Server Kubernetes Operator, run the tool with `-target k8s` as follows:
```
$WLSDEPLOY_HOME/bin/prepareModel.sh -oracle_home /u01/wls12213 -model_file model1.yaml, model2.yaml -target k8s -output_dir $HOME/k8soutput
```

In the output directory, you will find:
```
model1.yaml
model2.yaml
create_k8s_secrets.sh
k8s_variable.properties
```

You can then customize the `k8s_variable.properties` and `create_k8s_secrets.sh` to provide environment-specific values.

For more information about additional target environments and options, see [Target Environments](config/target_env.md).

