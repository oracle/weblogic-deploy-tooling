# Developer Guide

## Table of Contents
- [PreRequisite](#prerequisite)
- [Project Structure](#project-structure)
- [Alias definition](#alias-definition)
- [Typedefs definition](#typedefs-definition)
- [Building WebLogic Deploy Tool](#building-weblogic-deploy-tool)

## PreRequisite

You will need the following software installed in your local build environment

1. Oracle WebLogic Server installation version 10.3.6 and above
2. JDK version 8
3. Maven 3 and above

## Project Structure

There are two modules in the project

1. `core`  This module contains all the source code 
2. `installer` This module builds the final installer zip file

There is also a `sample` directory containing various samples

## Alias Definition

WebLogic Deploy Tool uses python dictionary called alias to help navigating the weblogic configuration mbean tree.  The alias definition helps to define the structure and data type of the configuration mbean. The folder and attribute names are the exact name of used by WLST. All the alias definition reside in the directory:

`$WLSDEPLOY_HOME/core/src/main/resources/oracle/weblogic/deploy/aliases/category_module`

For example, in `JDBCSystemResource.json`

```yaml
{
    "copyright": "Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.",
    "license": "The Universal Permissive License (UPL), Version 1.0",
    "wlst_type": "JDBCSystemResource${:s}",
    "child_folders_type": "multiple",
    "folders": {
        "JdbcResource" : {
            "wlst_type": "${Jdbc:JDBC}Resource",
            "folders": {
                "JDBCConnectionPoolParams": {
                    "wlst_type": "JDBCConnectionPoolParams",
                    "folders": {},
                    "attributes": {
                        "CapacityIncrement":  [ {"version": "[10,)",       
                                                 "wlst_mode": "both",    
                                                 "wlst_name": "CapacityIncrement",                                
                                                 "wlst_path": "WP001", 
                                                 "value": {"default": "${None:1}"},  
                                                 "wlst_type": "integer",       
                                                 "get_method": "LSA"} ],
                        "ConnectionCreationRetryFrequencySeconds": [ {"version": "[10,)",     
                                                                     "wlst_mode": "both",    
                                                                     "wlst_name": "ConnectionCreationRetryFrequencySeconds",
                                                                     "wlst_path": "WP001", 
                                                                     "value": {"default": "${None:0}"},        
                                                                     "wlst_type": "integer",      
                                                                     "get_method": "LSA"} ]
                    },
                    "wlst_attributes_path": "WP001",
                    "wlst_paths": {
                        "WP001": "/JDBCSystemResource${:s}/%DATASOURCE%/${Jdbc:JDBC}Resource/%DATASOURCE%/JDBCConnectionPoolParams/${NO_NAME_0:%DATASOURCE%}"
                    }
                },
...
```

There are several special constructs within the python dictionary:

1. `wlst_type` in folder level

This key element uses expression expansion to derive the result of the folder name while navigating the mbean.
`${x:y}` contains two parts within the curly braces.  The first part is for WLST offline and the second part is for WLST online.  In WLST offline, the name of the folder is JCBCSystemResource and in WLST online, the name is JDBCSystemResources

2. `version`

This key element defines the version of supported for a particular mbean attribute.
`"version": "[10,)"`  This mathematical notation describe the attribute is supported from weblogic version 10 and higher

3. `wlst_mode`

This key element defines the WLST mode is supported in this particular mbean attribute.

4. `wlst_name`

This key element defines the name of the mbean attribute

5. `wlst_type` in attribute level

This key element defines the data type of the WLST mbean attribute. Valid values are integer, long, string, boolean, jarray and mbean type.

6. `get_method`

This key element defines which get_method should be used for retrieving the value the mbean attribute.  Valid values are: 

`GET`  use wlst get method to retrieve the value of the attribute
`LSA`  use ls(type='a') to retrieve the value of the attribute
`NONE` do not retrieve the attribute value

7. `wlst_path`

This key element defines the name of the path expression used for navigating to the mbean attribute parent folder. The actual path expression is defined later in ` "wlst_paths": { } ` 
 
8. `wlst_attributes_path`

9. `child_folders_type`

10. `wlst_paths`

The dictionary key defines the various `wlst_path` name in the attribute section.  It is used to define the full path to the attribute's parent folder.  In this example, the parent folder for `JDBCConnectionPoolParams` is:

"WP001": "/JDBCSystemResource${:s}/%DATASOURCE%/${Jdbc:JDBC}Resource/%DATASOURCE%/JDBCConnectionPoolParams/${NO_NAME_0:%DATASOURCE%}"

For WLST offline use case, the full path will expand to:

`/JDBCSystemResource/%DATASOURCE%/JdbcResource/%DATASOURCE%/JDBCConnectionPoolParams/NO_NAME_0`

For WLST online use case, the full path will expand to:

`/JDBCSystemResources/%DATASOURCE%/JDBCResource/%DATASOURCE%/JDBCConnectionPoolParams/%DATASOURCE%`

The %DATASOURCE% are token placeholder, where it will be replaced with the actual datasource name by the tool.

11. `value`

This key element defines the default value of the mbean attribute.

There are cases, you can specify the methods to set the value in the alias. For example, there are two definitions for the `Target` attribute, one for WLST offline and one for WLST online, the WLST online version has `set_method`, `set_bean_type` and `preferred_model_type` keys defined in the dictionary:

```yaml
                            "attributes": {
                                    "Target": [ { 
                                        "version": "[12.2.1,)",           
                                        "wlst_mode": "offline", 
                                        "wlst_name": "Target",                              
                                        "wlst_path": "WP001", 
                                        "value": {"default": "None"  }, 
                                        "wlst_type": "delimited_string" 
                                        }, {
                                        "version": "[12.2.1,)",           
                                        "wlst_mode": "online",  
                                        "wlst_name": "Targets",                             
                                        "wlst_path": "WP002", 
                                        "value": {"default": "None"  }, 
                                        "wlst_type": "jarray",          
                                        "preferred_model_type": "delimited_string", 
                                        "get_method": "GET", 
                                        "set_method": "MBEAN.set_target_mbeans", 
                                        "set_mbean_type": "weblogic.management.configuration.TargetMBean"} ],
                            },
```

12. `set_method`

13. `set_mbean_type`

14. `prefered_model_type`


## TypeDefs Definition

The Create Domain Tool has an extensible domain type system.  The three built-in domain types (`WLS`, `RestrictedJRF`, and `JRF`) are defined in JSON files of the same name in the `WLSDEPLOY_HOME/lib/typedefs` directory.  For example, the `JRF` domain type is defined in the `WLSDEPLOY_HOME/lib/typedefs/JRF.json` file whose contents look like those shown below.

```json
{
    "copyright": "Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.",
    "license": "The Universal Permissive License (UPL), Version 1.0",
    "name": "JRF",
    "description": "JRF type domain definitions",
    "versions": {
        "12.1.2": "JRF_1212",
        "12.1.3": "JRF_1213",
        "12.2.1": "JRF_12CR2",
        "12.2.1.3": "JRF_12213"
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
        "JRF_12213": {
            "baseTemplate": "Basic WebLogic Server Domain",
            "extensionTemplates": [
                "Oracle JRF WebServices Asynchronous services",
                "Oracle WSM Policy Manager",
                "Oracle Enterprise Manager"
            ],
            "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR" ],
            "rcuSchemas": [ "WLS", "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS" ]
        }
    }
}
```

This file tells the Create Domain Tool which templates to use to create the domain, which server groups to target, and even which RCU schemas to create, all based on the version of WebLogic Server installed.  New domain types can be defined by creating a new JSON file with the same structure in the `WLSDEPLOY_HOME/lib/typedefs` directory.  For example, to define a `SOA` domain type for 12.2.1.3, add the `WLSDEPLOY_HOME/lib/typedefs/SOA.json` file with contents like those shown below.

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

    weblogic-deploy\bin\createDomain.cmd -oracle_home d:\SOA12213 -domain_type SOA -domain_parent d:\demo\domains -model_file DemoDomain.yaml -archive_file DemoDomain.zip -variable_file DemoDomain.properties -run_rcu -rcu_db mydb.example.com:1539/PDBORCL -rcu_prefix DEMO

To create more complex domains with clusters of different types, it is necessary to control the targeting of server groups to managed servers.  By default, all server groups in the domain type definition are targeted to all managed servers.  To create a SOA domain with SOA and OSB clusters, simply add the OSB template and server group to the SOA domain definition, as shown below.

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
                "Oracle SOA Suite",
                "Oracle Service Bus"
            ],
            "serverGroupsToTarget": [ "JRF-MAN-SVR", "WSMPM-MAN-SVR",  "SOA-MGD-SVRS",  "OSB-MGD-SVRS-COMBINED" ],
            "rcuSchemas": [ "STB", "WLS", "MDS", "IAU", "IAU_VIEWER", "IAU_APPEND", "OPSS", "UCSUMS", "SOAINFRA" ]
        }
    }
}
```

## Building WebLogic Deploy Tool

If you are making changes to the project, you can build the project by

  `mvn -Dunit-test-wlst-dir=<full path to the wlst.sh(cmd) directory> clean install`
  
This will build the entire project and run the unit test.

If you are not making changes and only interested in building the latest version, then you can 

  `mvn -Denforcer.skip -DskipTests clean install`
 
This will build the entire project without running any unit test.

The installer zip file built is under the `WLSDEPLOY_HOME/installer/target` directory


