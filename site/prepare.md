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

## Customizing target 

The '-target' parameter is referring to a file on the file system '$WLSDEPLOY_HOME/lib/target/<target value>/target.json'

It has the format

```
{
  "model_filters" : {
        "discover": [
          { "name": "k8s_prep", "path": "@@TARGET_CONFIG_DIR@@/k8s_operator_filter.py" }
        ]
      },
  "variable_injectors" : {"PORT": {},"HOST": {},"URL": {}},
  "validation_method" : "lax",
  "credential_as_secret" : "true"
}
```

The json file has several attributes that can be customized

| Name | Description |
| --- | --- |
| model_filters | Specify the filters json configuration for the target configuration.  This follows the same schema of [Model Filters](tool_filters.md). Note only discover is valid | 
| variable_injectors | Specify the variable injector json configuration for the target configuration.  This follows the same schema of [Model Filters](tool_filters.md)|
| validation method | lax only |
| credential_as_secret | true only |

`"@@TARGET_CONFIG_DIR@@` resolves to the '$WDT_INSTALL/lib/target/<target value>' directory.  

If there is a need to customize your own filers or injectors, you can

1. ```mkdir $WDT_INSTALL/lib/target/mytarget```
2. Create a file named target.json follow the schema above in $WLSDEPLOY_HOME/lib/target/mytarget
3. Run the prepareModel command using the parameter -target mytarget
