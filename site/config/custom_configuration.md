## Custom Configuration

WDT allows you to create or extend the pre-installed type definitions, model filters, variable injectors, and target environments. Starting with WDT 1.10.0, these additional configuration files can be stored outside the `$WLSDEPLOY_HOME/lib` directory. This allows the files to remain in place if the WDT installation is moved or upgraded to a new version.

To use a separate configuration directory, set the `WDT_CUSTOM_CONFIG` environment variable to the directory to be used for configuration. For example:
```
export WDT_CUSTOM_CONFIG=/etc/wdtconfig
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
This is a full set of files that can be configured, you will only need to add the files you have created or extended.

The WDT tools will look for each configuration file under `$WDT_CUSTOM_CONFIG` if specified, then under `$WLSDEPLOY_HOME/lib`.

### Example: Extending a Type Definition

If you want to extend the `WLS` type definition to add more extension templates, you would first make a copy of `$WLSDEPLOY_HOME/lib/typedefs/WLS.json`, and make your edits to the new file. Copy the new file to `$WDT_CUSTOM_CONFIG/typedefs/MY_WLS.json`. Set the `$WDT_CUSTOM_CONFIG` environment variable, and run the tool referencing the new type definition:
```
createDomain.cmd -oracle_home /wls12213 -domain_type MY_WLS ...
```
