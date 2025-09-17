---
title: "Model Help Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 11
description: "Provides information about the folders and attributes that are valid for sections and folders of a domain model."
---


The Model Help Tool provides information about the folders and attributes that are valid for sections and folders of a
domain model. This is useful when creating a new domain model, or expanding an existing model, including discovered models.

Here is a simple example using the Model Help Tool:

    $ weblogic-deploy/bin/modelHelp.sh -oracle_home /tmp/oracle resources:/JDBCSystemResource

This will result in the following output:

```yaml
Attributes and sub-folders for resources:/JDBCSystemResource

resources:
    JDBCSystemResource:
        'JDBC-1':
            CompatibilityName:       # string            *
            DeploymentOrder:         # integer           (default=100) *
            DeploymentPrincipalName: # string            *
            DescriptorFileName:      # string            *
            ModuleType:              # string            *
            Notes:                   # string            *
            SourcePath:              # string            *
            Target:                  # delimited_string  *

            JdbcResource:
                # see /JDBCSystemResource/JdbcResource

            SubDeployment:
                'SubDeployment-1':
                    # see /JDBCSystemResource/SubDeployment


This bean defines a system-level JDBC resource.  It links a separate
descriptor that specifies the definition.
```

There are several important parts of this output.
- the list of attributes for the folder
- the list of sub-folders
- the MBean description

The following three sections discuss each of these in more detail.

#### Attributes
The sample output shows the eight attributes and two sub-folders available for the `JDBCSystemResource` folder in the 
`resources` section of the model. Each attribute includes a comment describing the type of the value to be added.  An
asterisk (`*`) next to an attribute indicates that the attribute has additional information available, possibly
including a default value, valid range, and a description.  To access this additional information, simply add the
attribute name to the end of the path and re-invoke the Model Help Tool.

    $ weblogic-deploy/bin/modelHelp.sh -oracle_home /tmp/oracle /JDBCSystemResource/DeploymentOrder

```yaml
Attributes and sub-folders for resources:/JDBCSystemResource/DeploymentOrder

resources:
    JDBCSystemResource:
        JDBC-1:
            DeploymentOrder: # integer

Default=100

An integer value that indicates when this unit is deployed, relative 
to other deployable units on a server, during startup. 
 Units with lower values are deployed before those with higher 
values.
```

#### Sub-folders
Folders that support multiple instances, such as `SubDeployment` in this example, are shown with a derived name,
such as `'SubDeployment-1'`.  Each sub-folder includes a comment with a model path that can be used to display additional
information about that sub-folder.  For example, to determine the attributes and sub-folders for `'SubDeployment-1'`,
the Model Help Tool could be re-invoked with the model path from the comment:

    $ weblogic-deploy/bin/modelHelp.sh -oracle_home /tmp/oracle /JDBCSystemResource/SubDeployment

```yaml
Attributes and sub-folders for resources:/JDBCSystemResource/SubDeployment

resources:
    JDBCSystemResource:
        JDBC-1:
            SubDeployment:
                SubDeployment-1:
                    CompatibilityName: # string            *
                    ModuleType:        # string            *
                    Notes:             # string            *
                    Target:            # delimited_string  *

This bean represents an individually targetable entity within 
a deployment package, which is deployable on WLS. This includes 
: 
 Modules in an EAR 
 
 JMS resources within a app scoped JMS module in an EAR
```

{{% notice note %}}
The `/JDBCSystemResource/SubDeployment` path omits the leading `resources:` element but still works because the Model
Help Tool is able to determine which folder is being requested.
{{% /notice %}}

#### MBean description
The text at the bottom of the output comes directly from the WebLogic Server MBean description.  This text varies by
MBean and some MBeans have more useful information than others.

### Path patterns
There are a number of ways to specify model location in the path argument. Here are some examples:

#### `top`
List all the top-level model sections, such as `topology`, `resources`, and such.

    $ weblogic-deploy/bin/modelHelp.sh -oracle_home /tmp/oracle top

```yaml
Attributes and sub-folders for top:/

domainInfo:
# see domainInfo:

topology:
# see topology:

resources:
# see resources:

appDeployments:
# see appDeployments:

kubernetes:
# see kubernetes:

```

#### Section names
List the attributes and folders within a section, such as `topology`, `resources`, and such.

    $ weblogic-deploy/bin/modelHelp.sh -oracle_home /tmp/oracle appDeployments

```yaml
Attributes and sub-folders for appDeployments:/

appDeployments:

  Application:
    App-1:
    # see /Application

  Library:
    Lib-1:
    # see /Library
```

#### Folders
List all the attributes and folders within a folder.  As previously discussed, the path to the folder can include or
exclude the top-level section name.  If the section is not provided for a folder, then it will be derived and included
in the output text.  For example, `resources:/JDBCSystemResource/JdbcResource` and `/JDBCSystemResource/JdbcResource`
are equivalent and will produce the same output.

    $ weblogic-deploy/bin/modelHelp.sh -oracle_home /tmp/oracle /JDBCSystemResource/JdbcResource

```yaml
Attributes and sub-folders for resources:/JDBCSystemResource/JdbcResource

resources:
    JDBCSystemResource:
        JDBC-1:
            JdbcResource:
                Version: # string  *

                JDBCConnectionPoolParams:
                    # see /JDBCSystemResource/JdbcResource/JDBCConnectionPoolParams

                JDBCDataSourceParams:
                    # see /JDBCSystemResource/JdbcResource/JDBCDataSourceParams

                JDBCDriverParams:
                    # see /JDBCSystemResource/JdbcResource/JDBCDriverParams

                JDBCOracleParams:
                    # see /JDBCSystemResource/JdbcResource/JDBCOracleParams

                JDBCXAParams:
                    # see /JDBCSystemResource/JdbcResource/JDBCXAParams

The top of the JDBC data source bean tree. 
 JDBC data sources all have a JDBCDataSourceBean as their root 
bean (a bean with no parent).  The schema namespace that corresponds 
to this bean is "http://xmlns.oracle.com/weblogic/jdbc-data-source"
```

#### Attribute help
To show help for a particular attribute in a folder, simply add it to the model path.  Note that the folder listing
will include an asterisk at the end of an attribute line that has additional help information.

    $ weblogic-deploy/bin/modelHelp.sh -oracle_home /tmp/oracle topology:/Server/Log/StdoutSeverity

```yaml
Attributes and sub-folders for topology:/Server/Log/StdoutSeverity

topology:
    Server:
        'Server-1':
            Log:
                StdoutSeverity: # string

Default=Notice
Legal values:
   'Trace'
   'Debug'
   'Info'
   'Warning'
   'Error'
   'Notice'
   'Critical'
   'Alert'
   'Emergency'
   'Off'


The minimum severity of log messages going to the standard out.
Messages with a lower severity than the specified value will
not be published to standard out.
```


#### Output options
There are several command-line options that you can use to control the output text for the model path. Use only one of
these options at a time. If no output options are specified, then the attributes and immediate sub-folders for the
specified path are listed.

{{% notice note %}}
When the top sections are listed using the path ```top```, any output options are ignored.  
{{% /notice %}}

##### ```-attributes_only```
This option will list only the attributes for the specified path.

##### ```-folders_only```
This option will list only the immediate sub-folders for the specified path.

##### ```-recursive```
This option will recursively list all the sub-folders within the specified path. No attributes are listed.

    $ weblogic-deploy/bin/modelHelp.sh -oracle_home /tmp/oracle -recursive resources:/JDBCSystemResource

```yaml
Recursive sub-folders only for resources:/JDBCSystemResource

resources:
    JDBCSystemResource:
        'JDBC-1':
            JdbcResource:
                JDBCConnectionPoolParams:
                JDBCDataSourceParams:
                JDBCDriverParams:
                    Properties:
                        'Properties-1':
                JDBCOracleParams:
                JDBCXAParams:
            SubDeployment:
                'SubDeployment-1':
```

#### Interactive option
To access an interactive command line for exploring model paths using a directory style syntax, omit the model path from
the command line.

    $ modelHelp.sh -oracle_home /tmp/oracle

```text
Model Help running in interactive mode.  Type help for help.

Starting at location top

[top] --> help

Commands:

  ls                      - List contents of current location
  ls [path]               - List contents of specified location
  top, cd, cd /, cd top   - Change to the top-level location
  cd [path]               - Change to the specified location
  cat [path]              - Show details for the specified attribute location
  history                 - Show the history of visited locations
  exit                    - Exit interactive mode and the tool

  [path] Examples:
    x/y/z               - Relative path from the current location
    ../../a             - Relative path from the current location
    section[:[/a/b/c]]  - Absolute path to section and location, if specified
    /a[/b[/c]]          - Find the section that contains the specified folder

Sections:

  domainInfo, topology, resources, appDeployments, kubernetes

Examples:

  cd topology
  cd topology:/Server/Log/StdoutSeverity
  cd /Server/Log/StdoutSeverity
  cd ../../../ServerTemplate/DynamicServers


[top] -->
```

### Environment variables
The following environment variables may be set.

-  `JAVA_HOME`             The location of the JDK. This must be a valid Java 7 or later JDK.
-  `WLSDEPLOY_PROPERTIES`  System properties that will be passed to Java.

Since the Model Help Tool uses Jython directly without using WLST, the `JAVA_HOME` will be the JDK used to execute
the command (unlike other tools that use WLST).

### Parameter table for `model_help`
| Parameter             | Definition                                                                                                                                                                              | Default |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| `-attributes_only`    | List only the attributes for the specified model path.                                                                                                                                  |         |
| `-folders_only`       | List only the folders for the specified model path.                                                                                                                                     |         |
| `-oracle_home`        | Home directory of the Oracle WebLogic installation. Required if the `ORACLE_HOME` environment variable is not set.                                                                      |         |
| `-recursive`          | List only the folders for the specified model path, and recursively include the folders below that path.                                                                                |         |
| `-target <target>`    | The target platform, such as `wko` (the default). This determines the structure of the `kubernetes` section.  |         |
| `-target_mode <mode>` | The WLST mode to use to load the aliases. The mode is either `online` or `offline` (the default).                                                                                       |         |
| `<model_path>`        | The path to the model element to be examined. The format is `[^<section^>:][/^<folder^>]...`  Omit this argument to start in interactive mode.                                          |         |
