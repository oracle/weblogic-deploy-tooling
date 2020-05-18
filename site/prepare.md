## The Prepare Model Tool

The prepare model tool prepares WDT model files for deploying to the WebLogic Kubernetes Operator environment. It removes sections 
from the model that is not compatible with the WebLogic Kubernetes Operator, replaces credential, endpoints fields with WDT macros, and generates 
a UNIX shell script that creates the necessary kubernetes secrets for customizations.
 
    
To use the Prepare Model Tool, simply run the `prepareModel` shell script with the correct arguments.  To see the list of valid arguments, simply run the shell script with the `-help` option (or with no arguments) for usage information.

```
To prepare model files, run the tool as follows:

    weblogic-deploy\bin\prepareModel.cmd -oracle_home c:\wls12213 -model_file [command separed list of models] -target k8s -output_dir c:\k8soutput

```

In the ouptut directory, you wil found

```
model1.yaml
model2.yaml
create_k8s_secrets.sh
k8s_variable.properties

```

You can then customize the `k8s_variable.properties` and `create_k8s_secrets.sh` to provide environment specific values.