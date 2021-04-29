---
title: "Model Help Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 11
description: "Provides information about the folders and attributes that are valid for sections and folders of a domain model."
---


The Model Help Tool provides information about the folders and attributes that are valid for sections and folders of a domain model. This is useful when creating a new domain model, or expanding an existing model, including discovered models.

**NOTE:** The Model Help Tool is new in WebLogic Deploy Tooling 1.8.

**NOTE:** The `-model_sample` argument is deprecated starting with WebLogic Deploy Tooling 1.9.2, when model sample became the default output format.

Here is a simple example using the Model Help Tool:
```yaml
<wls-deploy-home>/bin/modelHelp.sh -oracle_home /tmp/oracle resources:/JDBCSystemResource
```
This will result in the following output:
```yaml
Attributes and sub-folders for resources:/JDBCSystemResource

resources:
    JDBCSystemResource:
        'JDBC-1':
            CompatibilityName:       # string
            DeploymentOrder:         # integer
            DeploymentPrincipalName: # string
            DescriptorFileName:      # string
            ModuleType:              # string
            Notes:                   # string
            SourcePath:              # string
            Target:                  # delimited_string

            JdbcResource:
                # see /JDBCSystemResource/JdbcResource

            SubDeployment:
                'SubDeployment-1':
                    # see /JDBCSystemResource/SubDeployment
```
This output shows the eight attributes and two sub-folders available for the `JDBCSystemResource` folder in the `resources` section of the model. Each attribute includes a comment describing the type of the value to be added.

Folders that support multiple instances, such as `JDBCSystemResource` in this example, are shown with a derived name, such as `'JDBC-1'`.

Each sub-folder includes a comment with a model path that can be used to display additional information about that sub-folder. For example, to determine the attributes and sub-folders for `'SubDeployment-1'`, the Model Help Tool could be re-invoked with the model path from the comment:
```yaml
<wls-deploy-home>/bin/modelHelp.sh -oracle_home /tmp/oracle -model_sample /JDBCSystemResource/SubDeployment
```
You can use the information above to construct this model section:
```yaml
resources:
    JDBCSystemResource:
        CompatibilityName: 'myName'
        DeploymentOrder: 5
        Target: 'ms1,ms2'
        'JDBC-1':
            # JdbcSystemResource attributes and folders
        SubDeployment:
            deployment1:
                # SubDeployment attributes and folders
            deployment2:
                # SubDeployment attributes and folders
```
If you are copying elements from the sample model to create a full domain model, you should exclude any attributes or sub-folders that you do not intend to declare or override.

### Path Patterns
There are a number of ways to specify model location in the path argument. Here are some examples:

List all the top-level model sections, such as `topology`, `resources`, and such:
```yaml
top
```

List the attributes and folders within a section, such as `topology`, `resources`, and such:
```yaml
topology
```

List all the attributes and folders within a folder:
```yaml
resources:/JDBCSystemResource/JdbcResource
```

If the section is not provided for a folder, then it will be derived and included in the output text:
```yaml
/JDBCSystemResource/JdbcResource
```

### Output Options
There are several command-line options that you can use to control the output text for the model path. Use only one of these options at a time. If no output options are specified, then the attributes and immediate sub-folders for the specified path are listed.

**NOTE:**
When the top sections are listed using the path ```top```, any output options are ignored.  

#### ```-attributes_only```
This option will list only the attributes for the specified path.

#### ```-folders_only```
This option will list only the immediate sub-folders for the specified path.

#### ```-recursive```
This option will recursively list all the sub-folders within the specified path. No attributes are listed.

Here is an example using the `-recursive` option:
```yaml
<wls-deploy-home>/bin/modelHelp.sh -oracle_home /tmp/oracle -recursive resources:/JDBCSystemResource
```
The output is:
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
