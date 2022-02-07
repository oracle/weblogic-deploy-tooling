---
title: "Variable Injector Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 10
description: "Adds token to a model with variables."
---


The Variable Injector Tool is used to tokenize a model with variables. The values for these variables are assigned using an external property file. This facilitates using the same domain model to create new domains in different environments. The Variable Injector Tool can be run as an option in the Discover Domain Tool, or from the standalone command-line interface.

To enable the Variable Injector Tool during the Discover Domain Tool run, create a variable injector configuration by placing a JSON file named `model_variable_injector.json` into the `<WLSDEPLOY>/lib` directory using one or more of the pre-defined keywords and/or a CUSTOM list of files.

Another option is to configure variable injection in a [Custom configuration]({{< relref "/userguide/tools-config/custom_config.md" >}}) directory. Create the `model_variable_injector.json` file in the `$WDT_CUSTOM_CONFIG` directory.

A keyword points to an injector directive file. The tool applies the directives to the attributes in a model, and if the directive matches an attribute, then a property token with a unique variable name is injected into the model and replaces the attribute value. The variable name and model attribute value are placed into the external variable properties file.

{{% notice note %}} Variable injection on an attribute is only performed once. The property token is not replaced by any subsequent matches.
{{% /notice %}}

If variable injection is enabled, the Discover Domain Tool calls the variable injector after the model has been discovered and after all filters run, but before model validation.

The supported keywords are as follows:

- `CREDENTIALS` - All MBean credentials attribute values (user and password) are injected with a variable.
- `HOST` - All MBean host attribute values in the model are injected with a variable.
- `PORT` - All MBean port attribute values in the model are injected with a variable.
- `TARGET` - All MBean target attribute values in the model are injected with a variable.
- `TOPOLOGY` - Common environmental MBean attributes found in the topology section of the model are injected with a variable.
   This includes server, machine and Node Manager ports, credentials and listen addresses, and cluster messaging modes, addresses and ports.
- `URL` - All MBean URL attribute values in the model are injected with a variable.

{{% notice note %}} The directives used by each pre-defined keyword are defined in an injector JSON file that is located in the `<WLSDEPLOY>/lib/injectors` folder. These files should not be changed, but could be used as is.
{{% /notice %}}

Here is an example of a `model_variable_injector.json` file using the PORT keyword.

```json
{
	"PORT": {}
}
```

Below is a model snippet that shows injected variables in the port attributes.

```yaml

topology:
    Name: soa_domain
    AdminServerName: AdminServer
    Cluster:
        soa_cluster:
        osb_cluster:
    Server:
        AdminServer:
            ListenAddress: myadmin.example.com
            ListenPort: @@PROP:Server.AdminServer.ListenPort@@
            Machine: machine1
            SSL:
                Enabled: true
                ListenPort: @@PROP:Server.SSL.AdminServer.ListenPort@@
        soa_server1:
            ListenAddress: managed1.example.com
            ListenPort: @@PROP:Server.soa_server1.ListenPort@@
            Cluster: soa_cluster
            Machine: machine2
            SSL:
                Enabled: true
                ListenPort: @@PROP:Server.SSL.soa_server1.ListenPort@@
        soa_server2:
            ListenAddress: managed2.example.com
            ListenPort: @@PROP:Server.soa_server2.ListenPort@@
            Cluster: soa_cluster
            Machine: machine3
            SSL:
                Enabled: true
                ListenPort: @@PROP:Server.SSL.soa_server2.ListenPort@@
```

And the resulting variable property file:

```
Server.AdminServer.ListenPort=7001
Server.AdminServer.SSL.ListenPort=7002
Server.soa_server1.ListenPort=8001
Server.soa_server1.SSL.ListenPort=8002
Server.soa_server2.ListenPort=8001
Server.soa_server2.SSL.ListenPort=8002
```

To specify the name and location of the variable properties file for the Discover Domain Tool, use the argument `-variable_properties_file` on the command line. Usage of the `-variable_properties_file` argument without the presence of the model variable injector file in the `<WLSDEPLOY>/lib` directory will cause an error condition and the tool will exit. If the model variable injector file exists in the directory, but the command-line argument is not used, the variable properties file is created with the following defaults:
* If the `-model_file` command-line argument is used on the Discover Domain Tool run, the properties file name and location will be the same as the model file, with the file extension `.properties`.
* If only the archive file argument is present, the archive file name and location will be used.

As with the archive and model file, each run of the Discover Domain Tool will overwrite the contents of an existing variable property file with the values from the current run.

### Custom variable injector

To designate custom injector directives, use the `CUSTOM` keyword in the `model_variable_injector.json` file. The `CUSTOM` keyword requires a list of one or more custom injector directive JSON files.

An injector directive contains a key that identifies an attribute to be tokenized, and an optional set of directive properties. The key is a period-separated MBean hierarchy and attribute name as they are defined in the model. Always exclude the name of the model section from the injector key.

For example, an injector key for the Server SSL Listen Port is as below. This directive contains no additional properties.

```json
{
  "Server.SSL.ListenPort": {}
}
```

**NOTE**: The hierarchy of MBeans in the model for the `ListenPort` attribute. Note that the MBean name of `AdminServer` is NOT included in the directive:

```yaml
topology:
    Server:
        AdminServer:
            ListenAddress: myadmin.example.com
            ListenPort: 7001
            Machine: machine1
            SSL:
                Enabled: true
                ListenPort: 7002
```

These custom injector JSON files will be processed by the Variable Injector Tool before keywords, each file processed in list order. A property injected into an attribute will not be replaced by any subsequent matches.

#### Custom directive properties

Include the following properties to refine the directive as specified.

- `force:<attribute>`
    If the MBean hierarchy exists in the model, but the attribute does not, then the attribute will be added and persisted to the discovered model. The value stored in the
    model is the WebLogic default value.

- `variable_value`:
    Replace the model value with the specified value in the variable properties. This may be used in conjunction with the force directive, replacing the default value with the indicated value.

- `regexp`:
    A list of `regexp` patterns that will be applied to either the string values or map values of an attribute in the model. If the pattern matches, then the matching part of the
    string or dictionary will be injected with a property token and a unique variable name.

  - `pattern`:
    The regular expression pattern to apply to the string value or map values of an attribute.

  - `suffix`:
    The suffix name to append to each resulting variable name in order to create a unique variable name.

The `regexp` list is useful when only a segment of a string value or map needs to be tokenized (giving you a clean list of property values in the variable properties file). You can inject more than one token into a string or map with multiple patterns. However, when you have more than one pattern, you must provide a suffix for each. This allows the tool to generate a unique variable name for each token in the string or map.

The following is an example of how to effectively use the `regexp` directive list to search for a segment in a string value. In this example, we want to search for the host and port in each Oracle JDBC URL that uses the special Oracle URL notation, and create an entry for the host and port in the variable properties file.

In the model, we expect to find a URL like the following:

```yaml
    JDBCSystemResource:
        Database1:
            JdbcResource:
                JDBCDriverParams:
                    URL: 'jdbc:oracle:thin:@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)(HOST=slc05til.us.oracle.com)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=orcl.us.oracle.com)))'
```

We create a directive in our custom injector JSON file:

```json
  "JDBCSystemResource.JdbcResource.JDBCDriverParams.URL":
  {
    "regexp": [
      {
        "pattern": "(?<=PORT=)[\\w.-]+(?=\\))",
        "suffix": "Port"
      },
      {
        "pattern": "(?<=HOST=)[\\w.-]+(?=\\))",
        "suffix": "Host"
      }
    ]
  },
```

During the Discover Domain Tool run, the pattern is applied to the URL string and tokens injected into the string:

```
URL: 'jdbc:oracle:thin:@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)(HOST=@@PROP:JDBCSystemResource.Database1.JdbcResource.JDBCDriverParams.URL--Host@@:)(PORT=@@PROP:JDBCSystemResource.Database1.JdbcResource.JDBCDriverParams.URL--Port@@)))(CONNECT_DATA=(SERVICE_NAME=orcl.us.oracle.com)))'
```

And the variables put in the properties file:

```
JDBCSystemResource.Database1.JdbcResource.JDBCDriverParams.URL--Host=slc05til.us.oracle.com
JDBCSystemResource.Database1.JdbcResource.JDBCDriverParams.URL--Port=1521
```

#### Selecting specific MBean names for variable injection

This final custom directive allows you to explicitly define which named entries for an MBean in the model you want to inject properties. For instance, you might want to tokenize an attribute just for a specific server. To define a list of one or more names for a specific MBean in the injector directive hierarchy, format the list as follows:

```
MBean[comma separated list of names]

```

To select only the Administration Server named `AdminServer` for a Server directive, use the format `Server[AdminServer]`. To select servers `soa_server1` and `soa_server2`, format the key as `Server[soa_server1,soa_server2]`.

The injector tool recognizes two KEYWORDS for a user list, `MANAGED_SERVERS` (all the Managed Servers in the model) and `ADMIN_SERVER` (the Administration Server in the model).

A custom injector for the Administration Server SSL listen port is:

```json
{
  "Server[ADMIN_SERVER].SSL.ListenPort": {},
}
```

### Variable injector sample

A sample of a `model_variable_injector.json` file and a custom injector JSON file are installed in the `WLSDEPLOY/samples` directory.

### Parameter table for `injectVariables`
| Parameter | Definition | Default |
| ---- | ---- | ---- |
| `-archive_file` | The path to the archive file that contains a model in which the variables will be injected. If the `-model_file` argument is used, this argument will be ignored. |    |
| `-model_file` | The location of the model file in which variables will be injected. If not specified, the tool will look for the model in the archive file. Either the `-model_file` or the `-archive_file` argument must be provided. |    |
| `-oracle_home` | Home directory for the Oracle WebLogic installation. This is required unless the `ORACLE_HOME` environment variable is set. |    |
| `-variable_injector_file` | The location of the variable injector file which contains the variable injector keywords for this model injection run. If this argument is not provided, the `model_variable_injector.json` file must exist in the `lib` directory in the `WLSDEPLOY_HOME` location. |    |
| `-variable_properties_file` | The location of the property file in which to store any variable names injected into the model. If this command-line argument is not specified, the variable will be located and named based on the model file or archive file name and location. If the file exists, the file will be updated with new variable values. |    |
