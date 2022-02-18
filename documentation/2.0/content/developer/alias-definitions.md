---
title: "Alias definitions"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 3
---

WebLogic Deploy Tool uses a set of JSON configuration files to map folders and attributes in the model to the corresponding WLST MBeans and their attributes. These mappings are referred as 'aliases' throughout the project code and documentation. Each element in the alias definition file has detailed properties that assist in this mapping.

The model's folder and attribute names usually match the names of the corresponding elements in WLST. For cases where the names of WLST elements may change across WebLogic Server releases, the names should match the names in the 12.2.1.3 release. The unit test `AttributesTestCase` verifies that this convention is used, and identifies a few exceptions.

Attributes that are introduced after the 12.2.1.3 release should, in most cases, match the name of the first WebLogic Server release in which they appear. The unit test `AttributesTestCase` will ignore these for now, because they will not be present in the 12.2.1.3 alias structure.

The alias definition files reside in the directory:

`$WLSDEPLOY_HOME/core/src/main/resources/oracle/weblogic/deploy/aliases/category_module`

Each definition file corresponds to a second-level folder within the model, such as `JDBCSystemResource`.  Any elements below a second-level folder are defined in the file of that parent. For example, the model element `resources/JDBCSystemResource/JdbcResource/JDBCConnectionPoolParams` is described in `JDBCSystemResource.json`.

Top-level elements such as `topology` and `resources` are for organizational purposes, and are not represented in the alias definition files.

No elements in the `domainInfo` section of the model are represented in the alias definitions, because they don't correspond directly to WLST elements.

This example, from the file `JDBCSystemResource.json`, will be used as a reference in the descriptions below:

```json
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
                                                 "default_value": "${__NULL__:1}",
                                                 "wlst_type": "integer",
                                                 "get_method": "LSA"} ],
                        "ConnectionCreationRetryFrequencySeconds": [ {"version": "[10,)",
                                                                     "wlst_mode": "both",
                                                                     "wlst_name": "ConnectionCreationRetryFrequencySeconds",
                                                                     "wlst_path": "WP001",
                                                                     "default_value": "${__NULL__:0}",
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

### Keys for top level and `folders` elements

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

### Keys for `attributes` elements

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

By default, an attribute is read write in both WLST and MODEL. This element is used to set an attribute to read-only. The two read-only attributes are `RO` and `ROD`. The latter indicates that the attribute is read-only and will not be written into the domain. However, it will be discovered by the Discover Domain Tool into the model.
#### `preferred_model_type`

This key element specifies the preferred data type that should be used to put data in the model during discovery. As an example, list values can be represented in the model as comma-separated text, such as `"value1, value2"`, or as a YAML list, such as `["value1", "value2"]`. If the list values can contain commas, a YAML list must be used.

#### `wlst_path`

This key element specifies the name of the path expression used for navigating to the MBean attribute's folder. This name maps to an entry in the parent folder's `"wlst_paths": { }` list.

#### `default_value`

This key element specifies the default value of the MBean attribute. For example:

`"default_value": "text"`

`"default_value": 99`

`"default_value": null`

`"default_value": "${__NULL__:1}"`

The `__NULL__` key represents a `null` value when `"${a:b}"` notation is used to specify offline and online values.

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
