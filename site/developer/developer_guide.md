# Developer Guide

## Table of Contents
- [Project Structure](#project-structure)
- [Feature Implementation](#feature-implementation)
- [Alias Definitions](#alias-definitions)
- [Building WebLogic Deploy Tool](#building-weblogic-deploy-tool)

## Project Structure

This project is structured using the Standard Directory Layout for Maven projects, with two child modules, `core` and `installer`. In addition, there is a `samples` directory with example configurations, and the `site` directory containing project documentation.

The `core` module contains the main source code for the project. This includes Jython modules and Java classes, as well as typedef files, alias definitions, and the message bundle. There are unit tests related to this module.

Alias definitions are discussed in more detail [here](#alias-definitions). 

The `installer` module builds the final installer ZIP file. It includes the assembly definitions, start scripts for each tool for Linux and Windows platforms, and configurations for variable injection and logging. 

A single installer ZIP file is built under the `WLSDEPLOY_HOME/installer/target` directory.

There are detailed instructions for building the project [here](#building-weblogic-deploy-tool).

## Feature Implementation

This section describes how specific features of WebLogic Deploy Tooling are implemented in the source code.

### Creator and Deployer Class Hierarchies

The creation of individual folders and attributes within the `topology` section of the domain model is accomplished using subclasses of the Jython class `Creator`, in the module `wlsdeploy.tool.create.creator.py`.  The `Creator` class provides base methods to recurse through nested folders in the domain model, create or update those folders, and set or update their attributes. Each subclass can override these methods to account for variations in behavior for different functional areas.

For example, the `SecurityProviderCreator` subclass overrides the method `_create_named_subtype_mbeans` with special processing to remove all existing security providers, and re-create them from the data in the model. 

The update of folders and attributes in the `resources` section of the domain model follows a similar pattern, but the base class for these modules is `Deployer` in the module `wlsdeploy.tool.deploy.deployer.py`.

The class `TopologyUpdater` is a special subclass of `Deployer` that is used to update elements in the `topology` section after their initial creation.

## Alias Definitions

WebLogic Deploy Tool uses a set of JSON configuration files to map folders and attributes in the model to the corresponding WLST MBeans and their attributes. These mappings are referred as 'aliases' throughout the project code and documentation. Each element in the alias definition file has detailed properties that assist in this mapping.

The model's folder and attribute names usually match the names of the corresponding elements in WLST. For cases where the names of WLST elements may change across WebLogic Server releases, the names should match the names in the 12.2.1.3 release. The unit test `AttributesTestCase` verifies that this convention is used, and identifies a few exceptions.

Attributes that are introduced after the 12.2.1.3 release should, in most cases, match the name of the first WebLogic Server release in which they appear. The unit test `AttributesTestCase` will ignore these for now, because they will not be present in the 12.2.1.3 alias structure.
 
The alias definition files reside in the directory:

`$WLSDEPLOY_HOME/core/src/main/resources/oracle/weblogic/deploy/aliases/category_module`

Each definition file corresponds to a second-level folder within the model, such as `JDBCSystemResource`.  Any elements below a second-level folder are defined in the file of that parent. For example, the model element `resources/JDBCSystemResource/JdbcResource/JDBCConnectionPoolParams` is described in `JDBCSystemResource.json`. 

Top-level elements such as `topology` and `resources` are for organizational purposes, and are not represented in the alias definition files.

No elements in the `domainInfo` section of the model are represented in the alias definitions, because they don't correspond directly to WLST elements.

This example, from the file `JDBCSystemResource.json`, will be used as a reference in the descriptions below: 

```yaml
{
    "copyright": "Copyright (c) 2017, 2018, Oracle Corporation and/or its affiliates.  All rights reserved.",
    "license": "Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl",
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

### Conventions

Notations similar to `${Jdbc:JDBC}Resource` appear throughout this example, and other alias definition files. It is shorthand for the common situation where a value is different between offline and online WLST. The value before the colon is used in offline processing, and the value after is used for online. In this example, the value for `wlst_type` is `JdbcResource` in offline, and `JDBCResource` in online. This notation can be used for values in most places in the model. It cannot be used for key values, such as `wlst_type`.

### Keys for Top Level and `folders` Elements

These JSON keys are applicable for the top-level element (such as `JDBCSystemResource`), and each of its nested `folders` elements (such as `JdbcResource` and `JdbcResource/JDBCConnectionPoolParams`.

#### `wlst_type`

This value is the type name of the WLST MBean that corresponds to a model folder. The `${x:y}` notation described above is often used here to distinguish offline and online folder names.

#### `child_folders_type`

This value specifies how the tool will map the domain model element to one or more WLST MBeans. The values are:

- `single` (default) - this element represents a single MBean, and the MBean name is known.

- `single-unpredictable` - this element represents a single MBean, but the MBean name must be derived at runtime.

- `multiple` - this element contains multiple named elements (such as `dataSource1`, `dataSource2`), and each represents a single MBean. 

#### `folders`

Nested WLST MBean types for the current MBean are listed here. Each has a domain model type name, followed by its own JSON keyed elements.
 
#### `wlst_attributes_path`

This key element specifies the name of the path expression used for navigating to the MBean attributes folder. The actual path expression is defined later in the `"wlst_paths": { }` element. 

#### `wlst_paths`

The dictionary key defines the various WLST path values used elsewhere in this folder's definition. Each entry maps a name to a full WLST MBean path.  In this example, `JDBCConnectionPoolParams` has a single path:

`"WP001": "/JDBCSystemResource${:s}/%DATASOURCE%/${Jdbc:JDBC}Resource/%DATASOURCE%/JDBCConnectionPoolParams/${NO_NAME_0:%DATASOURCE%}"`

The `%DATASOURCE%` text is token placeholder. It will be replaced with the name of the actual data source by the tool.

### Keys for `attributes` Elements

Each child of an `attributes` element represents a single MBean attribute, and its key is the corresponding model name, such as `CapacityIncrement`. It contains at least one description element with the JSON keys below. There may be multiple description elements for cases where the configuration varies for different WebLogic Server version ranges, or varies between offline and online WLST.

#### `version`

This key element defines the applicable versions for a particular MBean attribute description. Maven versioning conventions are used to describe ranges and limits. For example:
 
`"version": "[10,)"`
  
Specifies that an MBean attribute description is relevant for WebLogic Server version 10 and later

#### `wlst_mode`

This key element specifies the WLST modes that are applicable for an MBean attribute description. The value can be "offline", "online", or "both".

#### `wlst_name`

This key element specifies the WLST name of the MBean attribute.

#### `wlst_type`

This key element specifies the data type used to set the WLST MBean attribute. Valid values are ```integer```, ```long```, ```string```, ```delimited_string```, ```boolean``` and ```jarray```. If the `wlst_read_type` is not set, this is also the data type used to read the value from WLST.

#### `wlst_read_type`

This key element specifies the data type used to read the WLST MBean attribute. If it is not specified, the value of `wlst_type` is used for the read.

#### `get_method`

This key element specifies which method should be used for retrieving the value the MBean attribute.  Valid values are: 

- `GET`  use the WLST get method to retrieve the value of the attribute
- `LSA`  use ls(type='a') to retrieve the value of the attribute
- `NONE` do not retrieve the attribute value

#### `access`

By default, an attribute is read write in both WLST and MODEL. This element is used to set an attribute to read-only. The two read-only attributes are `RO` and `ROD`. The latter indicates that the attribute is read-only and will not be written into the domain. However, it will be discovered by the discover tool into the model.
#### `preferred_model_type`

This key element specifies the preferred data type that should be used to put data in the model during discovery. As an example, list values can be represented in the model as comma-separated text, such as `"value1, value2"`, or as a YAML list, such as `["value1", "value2"]`. If the list values can contain commas, it is preferred to use a YAML list.  

#### `wlst_path`

This key element specifies the name of the path expression used for navigating to the MBean attribute's folder. This name maps to an entry in the parent folder's `"wlst_paths": { }` list. 

#### `value`

This key element is used to specify the default value of the MBean attribute. For example:

`"value": {"default": "${None:1}"}`

#### `set_method`

For cases where attributes cannot be set with simple types, it may be necessary to use a custom method to set the value. For example, most `Target` attributes require their values to be set as lists of MBeans, in online mode. This may be defined as: 

```yaml
    "attributes": {
        "Target": [ {
            "set_method": "MBEAN.set_target_mbeans", 
            "set_mbean_type": "weblogic.management.configuration.TargetMBean"} ],
    },
```

The method `set_target_mbeans` directs the tool to call the Jython method `attribute_setter.set_target_mbeans` to set this value.

#### `set_mbean_type`

When a `set_method` key is specified, it may be required to specify the MBean type for the set method to use (see the example under `set_method`).

## Building WebLogic Deploy Tool

### Prerequisite

You will need the following software installed in your local build environment

1. Oracle WebLogic Server installation version 12.2.1 and later
2. JDK version 8
3. Maven 3 and later

### Specifying the WLST location

Execution of the unit tests requires a WebLogic Server installation, because the tests must be run within WLST.

The WLST directory can be specified in one of two ways:

- Specify the `-Dunit-test-wlst-dir=<wlst-directory>` on the mvn command line.

- Create a file `.mvn/maven.config` file in the project directory, containing a single line with the `-Dunit-test-wlst-dir=<wlst-directory>` value. The `.mvn` directory contains a `maven.config-template` file that can be copied and used as a starting point.

In these cases, `<wlst-directory>` refers to the fully-qualified path to the WLST script (`wlst.sh` or `wlst.cmd`).

If you are using an IDE for development and building, creating a `maven-config` file will allow some Maven tasks to be performed within the IDE.

### Build Commands

If you are making changes to the project, you can build the project using this command line:

  `mvn -Dunit-test-wlst-dir=<wlst-directory> clean install`
  
This will build the entire project and run the unit tests. Omit the `-Dunit-test-wlst-dir=` argument if you have created a `maven.config` file, as described above.

Another option for specifying the WLST directory is to set the environment variable WLST_DIR.  It is not necessary to use both, and
the -D setting will take precedence.

If you are not making changes and are only interested in building the latest version, then you can skip the unit tests, using this command line:

  `mvn -DskipTests clean install`

The resulting installer ZIP file built is under the `WLSDEPLOY_HOME/installer/target` directory.
