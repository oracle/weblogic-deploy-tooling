---
title: "Domain type definitions"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 2
---


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

 Another option is to create this file in the [Custom configuration]({{< relref "/userguide/tools-config/custom_config.md" >}}) directory `$WDT_CUSTOM_CONFIG/typedefs`.

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

 #### Custom extension templates

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

 #### Using compact profile

 The `topologyProfile` field can be used to create a domain using a specific profile for each of the templates. This partial example will apply the compact profile for each of the specified templates.
```json
{
  "copyright": "Copyright (c) 2022, Oracle Corporation and/or its affiliates.  All rights reserved.",
  "license": "Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl",
  "name": "JRF-Compact",
  "description": "JRF type domain with a compact profile definitions",
  "topologyProfile": "Compact",
  ...
}
```
 WebLogic Deploy Tooling provides the `JRF-Compact.json` type definition file that can be used to create a JRF domain using the compact profile.

 #### Targeting in earlier WebLogic Server versions

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
 The `targeting` attribute is not valid for WebLogic Server versions 12.2.1 and later.


#### Using the typedef file to exclude template installed resources from the model and archive

 The Discover Domain Tool attempts to provide a sparse model by employing strategies such as not including attributes that are default values. It is important to not install template resources through the model. First, the templates will install the same resources in the target domain. Second, if you install resources from a on-premises domain into a target domain that is a later WebLogic version, it could cause conflicts.
 The `system-elements` section of the typedef file is used to assist the Discover Domain Tool. The `system-elements` section comprises a list that tells the tool what to exclude from the model and archive files.

 The list contains an entry for the type of resource to exclude along with a name or a regexp and name.

 The different types of resources are as follows:

| Resource name |
| --- |
| `apps` |
|`coherence-clusters` |
| `datasources` |
| `file-stores`|
| `jms` |
| `jms-servers` |
| `shared-libraries` |
| `startup-classes` |
| `wldf` |

The following example is the `system-elements` list in the `JRF.json` typedef file.

```json
   "system-elements": {
        "apps": [
            "^coherence-transaction-rar$",
            "^DMS Application.*",
            "^em$",
            "^FMW Welcome Page Application.*",
            "^opss-rest$",
            "^state-management-provider-memory-rar.*",
            "^wsil-wls.*",
            "^wsm-pm$"
        ],
        "coherence-clusters": [
            "^defaultCoherenceCluster$"
        ],
        "datasources": [
            ".*LocalSvcTblDataSource$",
            ".*mds-owsm$",
            ".*opss-audit-DBDS$",
            ".*opss-audit-viewDS$",
            ".*opss-data-source$",
            ".*opss-ds$",
            ".*WLSSchemaDataSource$"
        ],
        "file-stores": [
            "^JRFWSAsyncFileStore$",
            "^mds-owsm$"
        ],
        "jms": [
            "^JRFWSAsyncJmsModule$"
        ],
        "jms-servers": [
            "^JRFWSAsyncJmsServer$"
        ],
        "shared-libraries": [
            "^adf\\.oracle\\.businesseditor.*",
            "^adf\\.oracle\\.domain.*",
            "^adf\\.oracle\\.domain\\.webapp.*",
            "^em_common.*",
            "^em_core_ppc_pojo_jar$",
            "^em_error.*",
            "^em_sdkcore_ppc_public_pojo_jar$",
            "^emagentsdk_jar.*",
            "^emagentsdkimpl_jar.*",
            "^emagentsdkimplpriv_jar.*",
            "^emas$",
            "^emcore$",
            "^emcore_jar$",
            "^emcoreclient_jar$",
            "^emcorecommon_jar$",
            "^emcoreconsole_jar$",
            "^emcoreintsdk_jar.*",
            "^emcorepbs_jar$",
            "^emcoresdk_jar.*",
            "^emcoresdkimpl_jar.*",
            "^jsf.*",
            "^jstl.*",
            "^log4j_jar.*",
            "^odl\\.clickhistory.*",
            "^odl\\.clickhistory\\.webapp.*",
            "^ohw-rcf.*",
            "^ohw-uix.*",
            "^oracle\\.adf\\.dconfigbeans.*",
            "^oracle\\.adf\\.desktopintegration.*",
            "^oracle\\.adf\\.desktopintegration\\.model.*",
            "^oracle\\.adf\\.management.*",
            "^oracle\\.bi\\.adf\\.model\\.slib.*",
            "^oracle\\.bi\\.adf\\.view\\.slib.*",
            "^oracle\\.bi\\.adf\\.webcenter\\.slib.*",
            "^oracle\\.bi\\.composer.*",
            "^oracle\\.bi\\.jbips.*",
            "^oracle\\.dconfig-infra.*",
            "^oracle\\.jrf\\.system\\.filter$",
            "^oracle\\.jsp\\.next.*",
            "^oracle\\.pwdgen.*",
            "^oracle\\.sdp\\.client.*",
            "^oracle\\.sdp\\.messaging.*",
            "^oracle\\.webcenter\\.composer.*",
            "^oracle\\.webcenter\\.skin.*",
            "^oracle\\.wsm\\.console.*",
            "^oracle\\.wsm\\.idmrest.*",
            "^oracle\\.wsm\\.seedpolicies.*",
            "^orai18n-adf.*",
            "^owasp\\.esapi.*",
            "^UIX.*"
        ],
        "shutdown-classes": [
            "^DMSShutdown$",
            "^JOC-Shutdown$"
        ],
        "startup-classes": [
            "^JMX Framework Startup Class$",
            "^JOC-Startup$",
            "^JPS Startup Class$",
            "^JPS Startup Post-Activation Class$",
            "^WSM Startup Class$",
            "^Web Services Startup Class$",
            "^JRF Startup Class$",
            "^ODL-Startup$",
            "^DMS-Startup$",
            "^AWT Application Context Startup Class$"
        ],
        "wldf": [
            "^Module-FMWDFW$"
        ]
    }
```