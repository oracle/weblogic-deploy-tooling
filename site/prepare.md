## The Prepare Model Tool

The prepare model tool prepares WDT model files for deploying to the WebLogic Kubernetes Operator environment. It removes sections 
from the model that are not compatible with the WebLogic Kubernetes Operator, replaces credential, endpoints fields with WDT macros, and generates 

1. A UNIX shell script that will creates the necessary kubernetes secrets. The script can then be updated to provide the actual credentials.
2. A variable property file. The file can be updated to customize the different end points.
3. Updated model files
     
To use the Prepare Model Tool, simply run the `prepareModel` shell script with the correct arguments.  To see the list of valid arguments, simply run the shell script with the `-help` option (or with no arguments) for usage information.

```
To prepare model files, run the tool as follows:

    $WLSDEPLOY_HOME/bin/prepareModel.sh -oracle_home /u01/wls12213 -model_file [command separed list of models] -target k8s -output_dir $HOME/k8soutput

```

In the output directory, you will find

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
  "credentials_method" : "secrets"
}
```

The json file has several attributes that can be customized

| Name | Description |
| --- | --- |
| model_filters | Specify the filters json configuration for the target configuration.  This follows the same schema of [Model Filters](tool_filters.md). Note only discover is valid | 
| variable_injectors | Specify the variable injector json configuration for the target configuration.  This follows the same schema of [Model Filters](tool_filters.md)|
| validation method | lax only |
| credentials_method | "secrets" or "config_override_secrets" |

`"@@TARGET_CONFIG_DIR@@` resolves to the '$WDT_INSTALL/lib/target/<target value>' directory.  

If there is a need to customize your own filers or injectors, you can

1. ```mkdir $WDT_INSTALL/lib/target/mytarget```
2. Create a file named target.json follow the schema above in $WLSDEPLOY_HOME/lib/target/mytarget
3. Run the prepareModel command using the parameter -target mytarget
