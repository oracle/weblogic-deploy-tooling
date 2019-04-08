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

WebLogic Deploy Tool uses python dictionary called alias to help navigating the weblogic configuration mbean tree.  The alias definition helps to define the structure and data type of the configuration mbean. The folder and attribute names are the exact name of used by WLST. All the alias defintion reside in the directory:

`/core/src/main/resources/oracle/weblogic/deploy/aliases/category_module`

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

1. `wlst_type`  

This key element uses expression expansion to derive the result of the folder name while navigating the mbean.
`${x:y}` contains two parts within the curly braces.  The first part is for WLST offline and the second part is for WLST online.  In WLST offline, the name of the folder is JCBCSystemResource and in WLST online, the name is JDBCSystemResources

2. `version`

This key element defines the version of supported for a particular mbean attribute.
`"version": "[10,)"`  This mathematical notation describe the attribute is supported from weblogic version 10 and higher

3. `wlst_mode`

This key element defines the WLST mode is supported in this particular mbean attribute.

4. `wlst_name`

This key element defines the name of the mbean attribute

5. `wlst_type`

This key element defines the data type of the WLST mbean attribute. Valid values are integer, long, string, boolean and mbean type.

6. `get_method`

This key element defines which get_method should be used for retrieving the value the the mbean attribute.  Valid values are: 

`GET`  use wlst get method to retrieve the value of the attribute
`LSA`  use ls(type='a') to retrieve the value value of the attribute
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

12. `set_method` (not shown in the example)

13. `set_mbean_type` (not shown in the example)

## Typedefs Definition

## Building WebLogic Deploy Tool

If you are making changes to the project, you can build the project by

  `mvn -Dunit-test-wlst-dir=<full path to the wlst.sh(cmd) directory> clean install`
  
This will build the entire project and run the unit test.

If you are not making changes and only interested in building the latest version, then you can 

  `mvn -Denforcer.skip -DskipTests clean install`
 
This will build the entire project without running any unit test.


