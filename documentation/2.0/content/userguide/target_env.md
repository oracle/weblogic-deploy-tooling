---
title: "Target environments"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 2
---

### Contents

- [Overview](#overview)
- [Specifying a target environment](#specifying-a-target-environment)
- [Pre-configured target environments](#pre-configured-target-environments)
- [Using secret credentials in the model](#using-secret-credentials-in-the-model)
- [Merging content from the WDT model](#merging-content-from-the-wdt-model)
- [Target configuration files](#target-environment-configuration-files)

### Overview

The [Discover Domain]({{< relref "/userguide/tools/discover.md" >}}) and [Prepare Model]({{< relref "/userguide/tools/prepare.md" >}}) Tools allow you to customize the model and other files produced to be compatible with a specific target environment. Options for a target environment may include:
- Using model tokens for some attributes in the model. For more details, see [Model tokens]({{< relref "/concepts/model#model-tokens" >}}).
- Using Kubernetes secrets for credentials in the model. For more details, see [Using secret credentials in the model](#using-secret-credentials-in-the-model).
- Applying filters to the model. For more details, see [Model filters]({{< relref "/userguide/tools-config/model_filters.md" >}}).
- Creating additional configuration files for the target system.

### Specifying a target environment

Each tool specifies a target environment using the command-line argument `-target <target-name>`, where `<target-name>` refers to a pre-configured target environment, or a user-defined environment. In addition, the `-output_dir <output-directory>` argument specifies where the files for the target environment will be stored.

This command line shows how you can use these arguments with the Discover Domain Tool:
```yaml
 $ $WLSDEPLOY_HOME/bin/discoverDomain.sh ... -target k8s -output_dir /etc/files
```
This example would apply the `k8s` target type to the discovery result, and place those files in `/etc/files`.

If a variable file is specified on the tool's command line using the `-variable_file` argument, any injected variables will be added to that file. If no variable file is specified, injected variables will be written to the file `<output-directory>/<target_name>_variable.properties`.

### Pre-configured target environments

These target environment configurations are included in the WebLogic Deploy Tooling installation.

#### The WebLogic Kubernetes Operator targets

You can use these targets to customize the model and create a domain resource file for use with WebLogic Kubernetes Operator. There are three targets for specific [domain home source types](https://oracle.github.io/weblogic-kubernetes-operator/managing-domains/choosing-a-model/):

- `wko` and `wko4` for [Model in Image](https://oracle.github.io/weblogic-kubernetes-operator/managing-domains/model-in-image/) deployments
- `wko-dii` and `wko4-dii` for Domain in Image deployments
- `wko-pv`and `wko4-pv` for Domain in PV deployments

Targets beginning with `wko` are for use with WebLogic Kubernetes Operator versions 3.*, and those beginning with `wko4` are for use with versions 4.0.0 and later.

Each of these targets provides this additional processing:

- The `wko_filter` filter will be applied to remove model elements that are not compatible with the Kubernetes environment, and adjust some attribute values
- Variables will be injected into the model for port, host, and URL attributes
- `lax` validation will be applied for the resulting model
- An additional Kubernetes resource file, `wko-domain.yaml`, will be produced, with cluster and naming information derived from the model

In addition, the `wko` target will replace credentials in the model with references to Kubernetes secrets, and produce a script to create those secrets. The `wko-dii` and `wko-pv` targets will replace credentials in the model with variable references.

#### The Verrazzano targets

You can use these targets to customize the model and create a Kubernetes resource file for use with Verrazzano. There are three targets for specific [domain home source types](https://oracle.github.io/weblogic-kubernetes-operator/managing-domains/choosing-a-model/):

- `vz` for [Model in Image](https://oracle.github.io/weblogic-kubernetes-operator/managing-domains/model-in-image/) deployments
- `vz-dii` for Domain in Image deployments
- `vz-pv` for Domain in PV deployments

Each of these targets provides this additional processing:

- The `vz_filter` filter will be applied to remove model elements that are not compatible with the Kubernetes environment, and adjust some attribute values
- Variables will be injected into the model for port, host, and URL attributes
- `lax` validation will be applied for the resulting model
- An additional Kubernetes resource file, `vz-application.yaml`, will be produced, with cluster and data source information derived from the model

In addition, the `vz` target will replace credentials in the model with references to Kubernetes secrets, and produce a script to create those secrets. The `vz-dii` and `vz-pv` targets will replace credentials in the model with variable references.

#### Generic Kubernetes target

You can apply this target environment by providing the command-line argument `-target k8s`. It will provide this additional processing:

- The `k8s_filter` filter will be applied to remove model elements that are not compatible with the Kubernetes environment, and adjust some attribute values
- Variables will be injected into the model for port, host, and URL attributes
- `lax` validation will be applied for the resulting model
- Credentials in the model will be replaced with references to Kubernetes secrets, and a script to create those secrets will be produced

### Using secret credentials in the model

If a target environment is configured to use Kubernetes secrets for credential attribute values, each of those values is replaced with a token using the format `@@SECRET:@@ENV:DOMAIN_UID@@<secret-suffix>:<key>`. For example:
```yaml
PasswordEncrypted: '@@SECRET:@@ENV:DOMAIN_UID@@-jdbc-generic1:password@@'
```
When a domain is created or updated using a model with these tokens, the environment variable `DOMAIN_UID` should be set to the domain's UID, and secrets with corresponding names should have been created. For more details about using secret tokens, see [Model Tokens]({{< relref "/concepts/model#model-tokens" >}}).

For some target environments, the WebLogic admin credentials use a variation of this token format. For example:
```yaml
domainInfo:
    AdminUserName: '@@SECRET:__weblogic-credentials__:username@@'
    AdminPassword: '@@SECRET:__weblogic-credentials__:password@@'
```
In this case, the token `__weblogic-credentials__` allows these attributes to reference secrets in a specific location. The `WDT_MODEL_SECRETS_NAME_DIR_PAIRS` environment variable should be set to associate `__weblogic-credentials__` to this location. For example:
```shell
WDT_MODEL_SECRETS_NAME_DIR_PAIRS=__weblogic-credentials__=/etc/my-secrets
```
For more details about using the `WDT_MODEL_SECRETS_NAME_DIR_PAIRS` environment variable, see [Model Tokens]({{< relref "/concepts/model#model-tokens" >}}) .

In WebLogic Kubernetes Operator [Model in Image](https://oracle.github.io/weblogic-kubernetes-operator/managing-domains/model-in-image/) environments, the environment variable `DOMAIN_UID` is automatically set from the value in the domain resource file. The variable `WDT_MODEL_SECRETS_NAME_DIR_PAIRS` is automatically set to the directory containing WebLogic admin credentials.

#### The create secrets script

For target environments that use Kubernetes secret tokens, a shell script is created to generate the required secrets. The script is named `create_k8s_secrets.sh`, and is created in the target output directory. The script has commands to create each secret, for example: 
```shell
# Update <user> and <password> for weblogic-credentials
create_paired_k8s_secret weblogic-credentials <user> <password>
```
The script should be updated with correct `<user>` and `<password>` values as required. It may be necessary to change the `NAMESPACE` and `DOMAIN_UID` variables at the top of the script if they are different in the target environment.

The script performs a check to determine if any generated secret names are more than 63 characters in length, because that will prevent them from being mounted correctly in the Kubernetes environment. If any secret names exceed this limit, they will need to be shortened in this script, in the model files, and in the Kubernetes resource file. Each shortened name should be distinct from other secret names.   

### Merging content from the WDT model

When a Kubernetes resource file is created using a target environment, content from the `kubernetes` section of the WDT model will be merged into the resulting output, if that section is present. For example, if the `-target wko` option is used, you can define this section in the model:
```yaml
kubernetes:
  spec:
    domainHome: /etc/domainHome
    image: my-image
    clusters:
    - clusterName: my-cluster
      replicas: 4
    - clusterName: other-cluster
      replicas: 6
```
These fields will override the values in the output file, and the file would be rewritten with the revised values. List values in the model will be combined with existing values in the output file. For example, if `my-cluster` was in the original output file, the model content for `my-cluster` would be merged with it, overriding the `replicas` value. If `my-cluster` was not in the original output file, it would be added to the list of clusters.

When creating a resource file for WebLogic Kubernetes Operator version 4.0.0 and later, the `kubernetes` section of the model has to be structured differently. This is because there are multiple documents in the resource file for those versions. This example uses `domain` and `cluster` folders that will merge with the corresponding documents in the resource file:
```yaml
kubernetes:
  domain:
    spec:
      domainHome: /etc/domainHome
      image: my-image
  clusters:
  - spec:
      clusterName: my-cluster
      replicas: 4
  - spec:
      clusterName: other-cluster
      replicas: 6
```

### Target environment configuration files

A target environment is configured in a JSON file at this location:
```
$WLSDEPLOY_HOME/lib/targets/<target-name>/target.json
```
The `<target-name>` value corresponds to the value of the `-target` argument on the tool's command line. The WLS installation includes pre-defined targets for these environments:
 - [WebLogic Kubernetes Operator](#the-weblogic-kubernetes-operator-targets)
 - [Verrazzano](#the-verrazzano-targets)
 - [Kubernetes](#generic-kubernetes-target)

You can define a new or extended target environment with a new `target-name` in the above location, or using a [Custom configuration]({{< relref "/userguide/tools-config/custom_config.md" >}}) directory, such as `$WDT_CUSTOM_CONFIG/target/<my-target-name>/target.json`.

You can customize existing template files for specific environments. The recommended method is to copy the original template to a custom configuration directory as described above, such as `$WDT_CUSTOM_CONFIG/target/<target-name>/model.yaml`. The copied file can then be edited as needed, while maintaining the original for reference.

Here is an example of a target environment file:
```
{
    "model_filters" : {
        "discover": [
            { "name": "vz_prep", "path": "@@TARGET_CONFIG_DIR@@/vz_filter.py" },
            { "id": "wko_filter" }
        ]
    },
    "variable_injectors" : {"PORT": {},"HOST": {},"URL": {}},
    "validation_method" : "lax",
    "credentials_method" : "secrets",
    "exclude_domain_bin_contents": true,
    "wls_credentials_name" : "__weblogic-credentials__",
    "use_persistent_volume" : true,
    "additional_secrets": "runtime-encryption-secret",
    "additional_output" : "vz-application.yaml"
}
```
Each of the fields in this example is optional, and you can customize them.

#### `model_filters`

This field specifies the filters to be applied to the resulting model. This follows the same format and rules as the [Model filters]({{< relref "/userguide/tools-config/model_filters.md" >}}) configuration. The `discover` type should always be used here.

You can use the `@@TARGET_CONFIG_DIR@@` token to indicate that the specified filter is in the same directory as the target configuration file.  

#### `variable_injectors`

This field specifies the variable injectors to be applied to the resulting model. This follows the same format and rules as the [Variable injectors]({{< relref "/userguide/tools/variable_injection.md" >}}) configuration.

#### `validation_method`

You can use this field to set the validation level for the resulting model. Only the value `lax`is currently supported. With `lax` validation, variables and Kubernetes secrets referenced in the resulting model do not need to be available when the model is created.

#### `credentials_method`

This field specifies how credentials in the model should be handled. There are two values available:
- `secrets` - the credentials in the model are replaced with references to Kubernetes secrets, and a UNIX script to create those secrets is produced.
- `config_override_secrets` - the credentials in the model are replaced with placeholder values, such as `password1`, and a UNIX script to create corresponding Kubernetes secrets is produced.

In both these cases, the script to create the Kubernetes secrets is written to `<output-directory>/create_k8s_secrets.sh`. You will need to update this script with credential values before executing

#### `exclude_domain_bin_contents`

This field specifies how the domain's `bin` directory contents should be handled.  If set to `true`, then discovery will skip over the domain's `bin` directory resulting in a model and archive file without any references to any scripts that might typically be collected (for example, `setUserOverrides.sh`).

#### `wls_credentials_name`

This field specifies a name for use with the WDT_MODEL_SECRETS_NAME_DIR_PAIRS environment variable to identify administration credential Secrets for the domain. This is useful when those Secrets are stored in a directory that does not follow the `<directory>/<name>/<key>` convention. For more information about using the WDT_MODEL_SECRETS_NAME_DIR_PAIRS environment variable, see [Model tokens]({{< relref "/concepts/model#model-tokens" >}}).

#### `use_persistent_volume`

This field specifies if the domain is to be created for the Domain in PV [domain home source type](https://oracle.github.io/weblogic-kubernetes-operator/managing-domains/choosing-a-model/). If set to `true`, volume information will be added to the Kubernetes resource file that is generated.

#### `additional_secrets`

This field specifies a comma-separated list of secret types that are to be included in the Kubernetes resource file and the create secrets script. There is one secret type available:
- `runtime-encryption-secret` - this will add a `runtimeEncryptionSecret` attribute to the Kubernetes resource file with the value `<DOMAIN_UID>-runtime-encryption-secret`, and that secret name will be added to the [create secrets script](#the-create-secrets-script).

#### `additional_output`

You can use this field to create additional output for use in the target environment. The value is a comma-separated list of template files in the `$WLSDEPLOY_HOME/lib/targets/templates` directory. These templates are populated with information derived from the model, and written to a file with the same name in the specified output directory.

**Note: Prior to release 2.0.1, template files were stored in the `$WLSDEPLOY_HOME/lib/targets/<target-name>` directory.**

