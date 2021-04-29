---
title: "Target environments"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 5
---


The [Discover Domain]({{< relref "/userguide/tools/discover.md" >}}) and [Prepare Model]({{< relref "/userguide/tools/prepare.md" >}}) Tools allow you to customize the model and other files produced to be compatible with a specific target environment. Options for a target environment may include:
- Using model tokens for some attributes in the model. See [Model Tokens]({{< relref "/concepts/model#model-tokens" >}}).
- Using Kubernetes secrets for credentials in the model.
- Applying filters to the model. See [Model Filters]({{< relref "/concepts/tool_configuration#model-filters" >}}).
- Creating additional configuration files for the target system.

### Specifying a target environment

Each tool specifies a target environment using the command-line argument `-target <target-name>`, where `<target-name>` refers to a pre-configured target environment, or a user-defined environment. In addition, the `-output_dir <output-directory>` argument specifies where the files for the target environment will be stored.

This command line shows how these arguments can be used with the Discover Domain Tool:
```yaml
 $WLSDEPLOY_HOME/bin/discoverDomain.sh ... -target k8s -output_dir /etc/files
```
This example would apply the `k8s` target type to the discovery result, and place those files in `/etc/files`.

If a variable file is specified on the tool's command line using the `-variable_file` argument, any injected variables will be added to that file. If no variable file is specified, injected variables will be written to the file `<output-directory>/<target_name>_variable.properties`.

### The Target Configuration File

A target environment is configured in a JSON file at this location:
```
$WLSDEPLOY_HOME/lib/target/<target-name>/target.json
```
The `<target-name>` value corresponds to the value of the `-target` argument on the tool's command line. The WLS installation includes two pre-defined targets:
 - [Weblogic Kubernetes Operator](#the-weblogic-kubernetes-operator-target) (named `k8s`)
 - [Verrazzano](#the-verrazzano-target) (named `vz`).

You can define a new or extended target environment with a new `target-name` in the above location, or using a [Custom Configuration]({{< relref "/concepts/tool_configuration#custom-configuration" >}}) directory, such as `$WDT_CUSTOM_CONFIG/target/<my-target-name>/target.json`.

Here is an example of a target environment file:
```
{
  "model_filters" : {
        "discover": [
          { "name": "k8s_prep", "path": "@@TARGET_CONFIG_DIR@@/k8s_operator_filter.py" }
        ]
      },
  "variable_injectors" : {"PORT": {},"HOST": {},"URL": {}},
  "validation_method" : "lax",
  "credentials_method" : "secrets",
  "wls_credentials_name" : "__weblogic-credentials__",
  "additional_output" : "binding.yaml,model.yaml"
}
```
Each of the fields in this example is optional, and can be customized.

#### `model_filters`

This field specifies the filters to be applied to the resulting model. This follows the same format and rules as the [Model Filters]({{< relref "/concepts/tool_configuration#model-filters" >}}) configuration. The `discover` type should always be used here.

The `@@TARGET_CONFIG_DIR@@` token can be used to indicate that the specified filter is in the same directory as the target configuration file.  

#### `variable_injectors`

This field specifies the variable injectors to be applied to the resulting model. This follows the same format and rules as the [Variable Injectors]({{< relref "/userguide/tools/variable_injection.md" >}}) configuration.

#### `validation_method`

This field can be used to set the validation level for the resulting model. Only the value `lax`is currently supported. With `lax` validation, variables and Kubernetes secrets referenced in the resulting model do not need to be available when the model is created.

#### `credentials_method`

This field specifies how credentials in the model should be handled. There are two values available:
- `secrets` - the credentials in the model are replaced with references to Kubernetes secrets, and a UNIX script to create those secrets is produced.
- `config_override_secrets` - the credentials in the model are replaced with placeholder values, such as `password1`, and a UNIX script to create corresponding Kubernetes secrets is produced.

In both these cases, the script to create the Kubernetes secrets is written to `<output-directory>/create_k8s_secrets.sh`. You will need to update this script with credential values before executing

#### `wls_credentials_name`

This field specifies a name for use with the WDT_MODEL_SECRETS_NAME_DIR_PAIRS environment variable to identify administration credential Secrets for the domain. This is useful when those Secrets are stored in a directory that does not follow the `<directory>/<name>/<key>` convention. For more information about using the WDT_MODEL_SECRETS_NAME_DIR_PAIRS environment variable, see [Model Tokens]({{< relref "/concepts/model#model-tokens" >}}).

#### `additional_output`

This field can be used to create additional output for use in the target environment. The value is a comma-separated list of template files in the `$WLSDEPLOY_HOME/lib/target/<target-name>` directory. These templates are populated with information derived from the model, and written to a file with the same name in the specified output directory.

Template files can be customized for specific environments. The recommended method is to copy the original template to a custom configuration directory as described above, such as `$WDT_CUSTOM_CONFIG/target/<target-name>/model.yaml`. The copied file can then be edited as needed, while maintaining the original for reference.

### Pre-configured Target Environments

These target environment configurations are included in the WebLogic Deploy Tooling installation.

#### The WebLogic Kubernetes Operator target

This target environment can be applied by providing the command-line argument `-target wko`. It will provide this additional processing:

- The `wko_operator_filter.py` filter will be applied to remove model elements that are not compatible with the Kubernetes environment
- Variables will be injected into the model for port, host, and URL attributes
- `lax` validation will be applied for the resulting model
- Credentials in the model will be replaced with references to Kubernetes secrets, and a script to create those secrets will be produced
- An additional Kubernetes resource file, `model.yaml`, will be produced, with cluster and naming information derived from the model

#### The Verrazzano Target
This target environment can be applied by providing the command-line argument `-target vz`. It will provide this additional processing:

- The `vz_filter.py` filter will be applied to remove model elements that are not compatible with the Kubernetes environment
- Variables will be injected into the model for port, host, and URL attributes
- `lax` validation will be applied for the resulting model
- Credentials in the model will be replaced with placeholder values, and a script to create corresponding secrets will be produced
- Two additional Kubernetes resource files, `model.yaml` and `binding.yaml`, will be produced, with cluster and data source information derived from the model

#### Generic Kubernetes Target

This target environment can be applied by providing the command-line argument `-target k8s`. It will provide this additional processing:

- The `k8s_operator_filter.py` filter will be applied to remove model elements that are not compatible with the Kubernetes environment
- Variables will be injected into the model for port, host, and URL attributes
- `lax` validation will be applied for the resulting model
- Credentials in the model will be replaced with references to Kubernetes secrets, and a script to create those secrets will be produced
