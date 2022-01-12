---
title: "Custom configuration"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 3
---


WDT allows you to create or extend the pre-installed type definitions, model filters, variable injectors, and target environments. Starting with WDT 1.10.0, these additional configuration files can be stored outside the `$WLSDEPLOY_HOME/lib` directory. This allows the files to remain in place if the WDT installation is moved or upgraded to a new version.

To use a separate configuration directory, set the `WDT_CUSTOM_CONFIG` environment variable to the directory to be used for configuration. For example:
```
$ export WDT_CUSTOM_CONFIG=/etc/wdtconfig
```

The customized configuration files should be named and organized the same way they would be under the `$WLSDEPLOY_HOME/lib` directory. For example:
```
/etc/wdtconfig
    injectors
        *.json  (injector files)
    typedefs
        *.json  (typedef files)
    targets
        my-target
            target.json
            *.py  (filter files)
    model_filters.json
    model_variable_injector.json
    variable_keywords.json
```
This is a full set of files that can be configured. You will need only to add the files you have created or extended. Details for each configuration type are found at:
- [Tool property file]({{< relref "/userguide/tools-config/tool_prop.md" >}})
- [Model filters]({{< relref "/userguide/tools-config/model_filters.md" >}})
- [Type definitions]({{< relref "/userguide/tools-config/domain_def.md" >}}) (See the following [Extending a type definition](#example-extending-a-type-definition) example.)
- [Variable injection]({{< relref "/userguide/tools/variable_injection.md" >}})
- [The Prepare Model Tool]({{< relref "/userguide/tools/prepare.md" >}}); see [Target environments]({{< relref "/userguide/target_env.md" >}}).

The WDT tools will look for each configuration file under `$WDT_CUSTOM_CONFIG` if specified, then under `$WLSDEPLOY_HOME/lib`.

#### Example: Extending a type definition

To extend the `WLS` type definition, follow these steps:
- Create a directory to use for custom configurations, such as `/etc/wdtconfig`.
- Define the `WDT_CUSTOM_CONFIG` environment variable to point to that directory.
- Copy the file `$WLSDEPLOY_HOME/lib/typedefs/WLS.json` to the `$WDT_CUSTOM_CONFIG/typedefs` directory and rename it, for example `MY_WLS.json`.
- Edit `MY_WLS.json` with any required changes.
- Run the tool referencing the name of the new type definition, for example:
```
$ createDomain.cmd -oracle_home /wls12213 -domain_type MY_WLS ...
```
