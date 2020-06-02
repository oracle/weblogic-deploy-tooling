## The Model Help Tool

The Model Help Tool provides information about the folders and attributes that are valid for sections and folders of a domain model. This is useful when creating a new domain model, or expanding an existing model, including discovered models.

**NOTE:** The Model Help Tool is new in WebLogic Deploy Tooling 1.8.

Here is a simple example using the Model Help Tool:
```yaml
<wls-deploy-home>/bin/modelHelp.sh -oracle_home /tmp/oracle resources:/JDBCSystemResource
```
This will result in the following output:
```yaml
Path: resources:/JDBCSystemResource

  Valid Attributes:
    CompatibilityName           string
    DeploymentOrder             integer
    DeploymentPrincipalName     string
    DescriptorFileName          string
    ModuleType                  string
    Notes                       string
    SourcePath                  string
    Target                      delimited_string

  Valid Folders:
    JdbcResource
    SubDeployment (multiple)
```
This result lists the attributes and folders available for the `JDBCSystemResource` folder in the `resources` section of the model. You can use this information to construct this model section:
```yaml
resources:
    JDBCSystemResource:
        CompatibilityName: 'myName'
        DeploymentOrder: 5
        Target: 'ms1,ms2'
        JdbcSystemResource:
            # JdbcSystemResource attributes and folders
        SubDeployment:
            deployment1:
                # SubDeployment attributes and folders
            deployment2:
                # SubDeployment attributes and folders
```
The `(multiple)` notation on the `SubDeployment` folder indicates that it should have one or more named sub-folders containing its attributes and sub-folders.

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
This option will list only the attributes for the specified path. If there are no attributes, then the section heading will appear with an empty list.

#### ```-folders_only```
This option will list only the immediate sub-folders for the specified path. If there are no sub-folders, then the section heading will appear with an empty list.

#### ```-recursive```
This option will recursively list all the sub-folders within the specified path. No attributes are listed. If there are no sub-folders, then the section heading will appear with an empty list.
  
Here is an example using the `-recursive` option:
```yaml
<wls-deploy-home>/bin/modelHelp.sh -oracle_home /tmp/oracle -recursive resources:/JDBCSystemResource
```
The output is:
```yaml
Filtering output to recursively display the sub-folders of the specified model section or path

Path: resources:/JDBCSystemResource

  Valid Folders:
    JdbcResource
      JDBCConnectionPoolParams
      JDBCDataSourceParams
      JDBCDriverParams
        Properties (multiple)
      JDBCOracleParams
      JDBCXAParams
    SubDeployment (multiple)
```

### Model Sample Output
You can use the `-model_sample` argument to output a model sample for the specified model path. Depending on the output options specified, this argument will create a sample with the available attributes and sub-folders for the specified path.

If you are copying elements from the sample model to create a full domain model, you should exclude any attributes or sub-folders that you do not intend to declare or override. 

Here is an example using the `-model_sample` argument:
```yaml
<wls-deploy-home>/bin/modelHelp.sh -oracle_home /tmp/oracle -model_sample resources:/JDBCSystemResource
```
The output is:
```yaml
resources:
    JDBCSystemResource:
        'JDBC-1':
            CompatibilityName: # string
            DeploymentOrder: # integer
            DeploymentPrincipalName: # string
            DescriptorFileName: # string
            ModuleType: # string
            Notes: # string
            SourcePath: # string
            Target: # delimited_string

            JdbcResource:
                # see /JDBCSystemResource/JdbcResource

            SubDeployment:
                'SubDeployment-1':
                    # see /JDBCSystemResource/SubDeployment
```
This output shows the eight attributes and two sub-folders available for the model path. Each attribute includes a comment describing the type of the value to be added.
 
Each sub-folder includes a comment with a model path that can be used to display additional information about that sub-folder. For example, to determine the attributes and sub-folders for `'SubDeployment-1'`, the Model Help Tool could be re-invoked with the model path from the comment:
```yaml
<wls-deploy-home>/bin/modelHelp.sh -oracle_home /tmp/oracle -model_sample /JDBCSystemResource/SubDeployment
```