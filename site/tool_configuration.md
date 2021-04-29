## Tools Configuration
 - [Tool Property File](#tool-property-file)
 - [Model Filters](#model-filters)
 - [Target Environments](config/target_env.md)
 - [Type Definitions](#domain-type-definitions)
 - [Variable Injection](variable_injection.md)
 - [Custom Configuration](#custom-configuration)

 ### Tool Property File
 You can configure or tune WebLogic Deploy Tooling tools using the tool property file. This property file is installed as `<weblogic-deploy>/lib/tool.properties`. You may change the value of any of the properties in this file to tune the WDT tool. Another option is to configure the tool properties in a Custom Configuration directory. Create the `tool.properties` file in the $WDT_CUSTOM_CONFIG directory.

 If a property is removed from the file, or a property value is incorrectly formatted, a `WARNING` message is logged and an internal default value used instead of the missing or bad value.

 | Property | Description |
 | -------- | ----- |
 | `connect.timeout` | The number of milliseconds that WLST waits for the online `connect` command to complete. A value of 0 means the operation will not timeout. |        
 | `activate.timeout` | The number of milliseconds that WLST waits for the activation of configuration changes to complete. A value of -1 means the operation will not timeout. |
 | `deploy.timeout` | The number of milliseconds that WLST waits for the undeployment process to complete. A value of 0 means the operation will not timeout. |
 | `redeploy.timeout` | The number of milliseconds that WLST waits for the redeployment process to complete. A value of 0 means the operation will not timeout. |
 | `start.application.timeout` | The number of milliseconds that WLST waits for the start application process to complete. A value of 0 means the operation will not timeout. |
 | `stop.application.timeout` | The number of milliseconds that WLST waits for the stop application process to complete. A value of 0 means the operation will not timeout. |
 | `set.server.groups.timeout` | Specifies the amount of time the set server groups connection can be inactive before the connection times out. |

 ### Model Filters

 WebLogic Deploy Tooling supports the use of model filters to manipulate the domain model. The Create Domain, Update Domain, and Deploy Applications Tools apply filters to the model after it is read, before it is validated and applied to the domain. The Discover Domain Tool applies filters to the model after it has been discovered, before the model is validated and written.

 Model filters are written in Jython, and must be compatible with the version used in the corresponding version of WLST. A filter must implement the method `filter_model(model)`, which accepts as a single argument the domain model as a Jython dictionary. This method can make any adjustments to the domain model that are required. Filters can be stored in any directory, as long as they can be accessed by WebLogic Deploy Tooling.

 The following filter example (`fix-password.py`) sets the password for two attributes in the `SecurityConfiguration` WLST folder.

 ```python
def filter_model(model):
    if model and 'topology' in model:
        if 'SecurityConfiguration' in model['topology']:
            model['topology']['SecurityConfiguration']['CredentialEncrypted'] = 'welcome1'
            model['topology']['SecurityConfiguration']['NodeManagerPasswordEncrypted'] = 'welcome1'
            print 'Replaced SecurityConfiguration password'
        else:
            print 'SecurityConfiguration not in the model'
 ```

 Model filters are configured by creating a `model_filters.json` file in the `WLSDEPLOY_HOME/lib` directory. This file has separate sections for filters to be applied for specific tools.

 Another option is to configure model filters in a [Custom Configuration](#custom-configuration) directory. Create the `model_filters.json` file in the `$WDT_CUSTOM_CONFIG` directory.

 This example configures two filters for the Create Domain Tool: `fix-password.py` and `no-mail.py`, and one filter for the Discover Domain tool.

 ```json
 {
   "create": [
     { "name": "fixPassword", "path": "/home/user/fix-password.py" },
     { "name": "noMail", "path": "/home/user/no-mail.py" }
   ],
   "deploy": [
   ],
   "discover": [
     { "name": "noMail", "path": "/home/user/no-mail.py" }
   ],
   "update": [
   ]
 }
 ```

 ### Domain Type Definitions

 WebLogic Deploy Tooling has an extensible domain type system.  The three built-in domain types (`WLS`, `RestrictedJRF`, and `JRF`) are defined in JSON files of the same name in the `WLSDEPLOY_HOME/lib/typedefs` directory.  For example, the `JRF` domain type is defined in the `WLSDEPLOY_HOME/lib/typedefs/JRF.json` file with similar content, as shown below.

 ```json
 {
     "copyright": "Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.",
     "license": "Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl",
     "name": "JRF",
     "description": "JRF type domain definitions",
     "versions": {
         "12.1.2": "JRF_1212",
         "12.1.3": "JRF_1213",
         "12.2.1.0": "JRF_12CR2",
         "12.2.1.1": "JRF_12C_DYN",
         "12.2.1.2": "JRF_12C_DYN",
         "12.2.1.3": "JRF_12C_DYN",
         "12.2.1.4": "JRF_12214"
     },
     "definitions": {
         "JRF_1212" : {
             "baseTemplate": "@@WL_HOME@@/common/templates/wls/wls.jar",
             "extensionTemplates": [
                 "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.jrf_template_12.1.2.jar",
                 "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.jrf.ws.async_template_12.1.2.jar",
                 "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.wsmpm_template_12.1.2.jar",
                 "@@ORACLE_HOME@@/em/common/templates/wls/oracle.em_wls_template_12.1.2.jar"
             ],
             "serverGroupsToTarget" : [ "JRF-MAN-SVR", "WSMPM-MAN-SVR" ],
             "rcuSchemas": [ "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS" ]
         },
         "JRF_1213" : {
             "baseTemplate": "@@WL_HOME@@/common/templates/wls/wls.jar",
             "extensionTemplates": [
                 "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.jrf_template_12.1.3.jar",
                 "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.jrf.ws.async_template_12.1.3.jar",
                 "@@ORACLE_HOME@@/oracle_common/common/templates/wls/oracle.wsmpm_template_12.1.3.jar",
                 "@@ORACLE_HOME@@/em/common/templates/wls/oracle.em_wls_template_12.1.3.jar"
             ],
             "serverGroupsToTarget" : [ "JRF-MAN-SVR", "WSMPM-MAN-SVR" ],
             "rcuSchemas": [ "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS" ]
         },
         "JRF_12CR2": {
             "baseTemplate": "Basic WebLogic Server Domain",
             "extensionTemplates": [
                 "Oracle JRF WebServices Asynchronous services",
                 "Oracle WSM Policy Manager",
                 "Oracle Enterprise Manager"
             ],
             "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR" ],
             "rcuSchemas": [ "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS" ]
         },
         "JRF_12C-DYN": {
             "baseTemplate": "Basic WebLogic Server Domain",
             "extensionTemplates": [
                 "Oracle JRF WebServices Asynchronous services",
                 "Oracle WSM Policy Manager",
                 "Oracle Enterprise Manager"
             ],
             "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR" ],
             "dynamicClusterServerGroupsToTarget": [ "WSMPM-DYN-CLUSTER" ],
             "rcuSchemas": [ "WLS", "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS" ]
         },
         "JRF_12214": {
              "baseTemplate": "Basic WebLogic Server Domain",
              "extensionTemplates": [
                  "Oracle JRF WebServices Asynchronous services",
                  "Oracle WSM Policy Manager",
                  "Oracle Enterprise Manager"
              ],
              "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR" ],
              "dynamicClusterServerGroupsToTarget": [ "WSMPM-DYN-CLUSTER", "WSM-CACHE-DYN-CLUSTER" ],
              "rcuSchemas": [ "WLS", "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS" ]
          }
     }
 }
 ```

 This file tells the Create Domain Tool which templates to use to create the domain, which server groups to target, and even which RCU schemas to create, all based on the installed version of WebLogic Server.

 New domain types can be defined by creating a new JSON file with the same structure in the `WLSDEPLOY_HOME/lib/typedefs` directory.

 Another option is to create this file in the [Custom Configuration](#custom-configuration) directory `$WDT_CUSTOM_CONFIG/typedefs`.

 For example, to define a `SOA` domain type for 12.2.1.3, add the `typedefs/SOA.json` file with similar content, as shown below.

 ```json
 {
     "name": "SOA",
     "description": "SOA type domain definitions",
     "versions": {
         "12.2.1.3": "SOA_12213"
     },
     "definitions": {
         "SOA_12213": {
             "baseTemplate": "Basic WebLogic Server Domain",
             "extensionTemplates": [
                 "Oracle SOA Suite"
             ],
             "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR",  "SOA-MGD-SVRS" ],
             "rcuSchemas": [ "STB", "WLS", "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS", "UCSUMS", "SOAINFRA" ]
         }
     }
 }
 ```

 After the new domain `typedef` file exists, simply specify the new domain type name to the `createDomain` script, being sure to reference an Oracle Home with the required components installed.  For pre-12.2.1 versions, the `-wlst_path` argument must be used to point to the product home where the appropriate WLST shell script exists; for example, for SOA 12.1.3, add `-wlst_path <ORACLE_HOME>/soa` so that the tool uses the WLST shell script with the proper environment for SOA domains.  In 12.2.1 and later, this is no longer necessary because the WLST shell script in the standard `<ORACLE_HOME>oracle_common/common/bin` directory will automatically load all components in the Oracle Home.  Using the new domain type, simply run the following command to run RCU and create the SOA domain with all of its resources and applications deployed.

     weblogic-deploy\bin\createDomain.cmd -oracle_home d:\SOA12213 -domain_type SOA -domain_parent d:\demo\domains -model_file DemoDomain.yaml -archive_file DemoDomain.zip -variable_file DemoDomain.properties -run_rcu -rcu_db mydb.example.com:1539/PDBORCL -rcu_prefix DEMO [-rcu_db_user SYS]

 #### Custom Extension Templates

 The `customExtensionTemplates` attribute can be used to specify custom extension templates to be applied to the domain. These should be specified as absolute file paths, and can use tokens.  

 ```json
 {
     "name": "MyCustom",
     "description": "My custom type domain definitions",
     "versions": {
         "12.2.1.3": "My_12213"
     },
     "definitions": {
         "My_12213": {
             "baseTemplate": "Basic WebLogic Server Domain",
             "extensionTemplates": [ ],
             "customExtensionTemplates": [
                 "/user/me/templates/my-template.jar",
                 "@@ORACLE_HOME@@/user_templates/other-template.jar"
             ],
             "serverGroupsToTarget": [ "MY-MAN-SVR" ],
             "rcuSchemas": [ ]
         }
     }
 }
 ```

 If there are any server groups in the custom template that should be targeted to managed servers, they should be specified in the `serverGroupsToTarget` attribute, similar to `MY_MAN_SVR` in the example above.

 #### Targeting in Earlier WebLogic Server Versions

 Templates in WebLogic Server versions prior to 12.2.1 may require the use of the `applyJRF` WLST command to correctly target resources to the correct clusters and servers. The default behavior for WebLogic Deploy Tooling is to invoke `applyJRF` only when the `extensionTemplates` list includes JRF templates.

 A custom type definition file can require `applyJRF` to be invoked after the templates are added. This is done by setting the `targeting` attribute to `APPLY_JRF`, as in this example:

 ```json
 {
     "name": "MyCustom",
     "description": "My custom type domain definitions",
     "versions": {
         "10.3.6": "My_11G"
     },
     "definitions": {
         "My_11G": {
             "baseTemplate": "@@WL_HOME@@/common/templates/wls/wls.jar",
             "extensionTemplates": [
                 "/user/me/templates/my-template.jar"
              ],
             "targeting": "APPLY_JRF",
             "serverGroupsToTarget": [ "MY-MAN-SVR" ],
             "rcuSchemas": [ ]
         }
     }
 }
 ```

 The `targeting` attribute is not valid for WebLogic Server versions 12.2.1 and up.


 ### Custom Configuration

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
 This is a full set of files that can be configured. You will need only to add the files you have created or extended. Details for each configuration type are found at:
 - [Tool Property File](#tool-property-file)
 - [Model Filters](#model-filters)
 - [Type Definitions](#domain-type-definitions) (See the [example](#example-extending-a-type-definition) below.)
 - [Variable Injection](variable_injection.md)
 - [The Prepare Model Tool](prepare.md) (target environments)

 The WDT tools will look for each configuration file under `$WDT_CUSTOM_CONFIG` if specified, then under `$WLSDEPLOY_HOME/lib`.

 #### Example: Extending a Type Definition

 To extend the `WLS` type definition, follow these steps:
 - Create a directory to use for custom configurations, such as `/etc/wdtconfig`.
 - Define the `WDT_CUSTOM_CONFIG` environment variable to point to that directory.
 - Copy the file `$WLSDEPLOY_HOME/lib/typedefs/WLS.json` to the `$WDT_CUSTOM_CONFIG/typedefs` directory and rename it, for example `MY_WLS.json`.
 - Edit `MY_WLS.json` with any required changes.
 - Run the tool referencing the name of the new type definition, for example:
 ```
 createDomain.cmd -oracle_home /wls12213 -domain_type MY_WLS ...
 ```
