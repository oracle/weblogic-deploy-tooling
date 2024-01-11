---
title: "Variable injectors"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 10
---


Variable injectors are used to tokenize a model by substituting variable keys in place of attribute values, and creating a separate property file containing the variable values. This facilitates using the same domain model to create new domains in different environments. WebLogic Deploy Tooling includes several built-in injector directive files that can be used as-is or with modifications, and allows for creation of custom injector files.

Variable injectors are used by the [Discover Domain Tool]({{< relref "/userguide/tools/discover.md" >}}), the [Prepare Model Tool]({{< relref "/userguide/tools/prepare.md" >}}), and the standalone [Variable Injector Tool]({{< relref "/userguide/tools/variable_injection.md" >}}) to tokenize the models they produce.

{{% notice note %}} Variable injection on an attribute is only performed once. After being tokenized, an attribute is not re-tokenized by any subsequent injector directives.
{{% /notice %}}

#### Default configuration

The default injector configuration is used by the standalone Variable Injector Tool, and by the Discover Domain Tool when it is run without the `-target` option. To enable variable injection for these tools, create a variable injector configuration by placing a JSON file named `model_variable_injector.json` into the `<WLSDEPLOY>/lib` directory.

Another option is to configure variable injection in a [Custom configuration]({{< relref "/userguide/tools-config/custom_config.md" >}}) directory. Create the `model_variable_injector.json` file in the `$WDT_CUSTOM_CONFIG` directory.

The variable injector configuration file contains a list of injector names that map to the names of the injector files to be applied to the model. 

Here is an example of a `model_variable_injector.json` file that will apply `topology` and `custom` injectors to the model.

```json
{
  "injectors": [
    "topology",
    "custom"
  ]
}
```

Each injector name in the list refers to an [injector directive file](#injector-directive-files), and they are applied to the attributes in the model in the specified order.

A sample of a `model_variable_injector.json` file is included in the `WLSDEPLOY/samples` directory.

#### Targeted configuration

Targeted injector configuration is used by the Prepare Model Tool, and by the Discover Domain Tool when it is run with the `-target` option. In this case, the list of injector names to be applied is specified in the `variable_injectors` field of the `$WLSDEPLOY_HOME/lib/targets/<target-name>/target.json` configuration file. For example, the `$WLSDEPLOY_HOME/lib/targets/wko/target.json` file contains this value:

```json
{
  ...
  "variable_injectors" : ["port", "host", "url"],
  ...
}
```

Each injector name in the list refers to an [injector directive file](#injector-directive-files), and they are applied to the attributes in the model in the specified order.

For more information on creating and extending target configurations, see [Target environments]({{< relref "/userguide/target_env.md" >}}).

#### Injector directive files

Injector directive files contain a list of qualified attribute paths and associated directives. When a matching attribute is found in the model, the associated directive is applied to that attribute, then a property token with a unique variable name is injected into the model and replaces the attribute value. The variable name and model attribute value are placed into the external variable properties file.

Injector directive files are placed in the `$WLSDEPLOY_HOME/lib/injectors` directory. User-defined files can be placed there or in a [Custom configuration]({{< relref "/userguide/tools-config/custom_config.md" >}}) directory. To use the custom configuration directory, place these files in `$WDT_CUSTOM_CONFIG/lib/injectors`.

WebLogic Deploy Tool includes these pre-configured injector directive files:

- `host.json` - All MBean host attribute values in the model are injected with a variable.
- `port.json` - All MBean port attribute values in the model are injected with a variable.
- `target.json` - All MBean target attribute values in the model are injected with a variable.
- `topology.json` - Common environmental MBean attributes found in the topology section of the model are injected with a variable. This includes server, machine and Node Manager ports, listen addresses, and cluster messaging modes, addresses and ports.
- `url.json` - All MBean URL attribute values in the model are injected with a variable.

The following is a model snippet that shows injected variables after applying the `port` injector directive file.

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

#### Custom variable injector

To use custom injector directives, create an injector directive file with a meaningful name, and place it in the `$WLSDEPLOY_HOME/lib/injectors` directory, or `$WDT_CUSTOM_CONFIG/lib/injectors` if using a custom configuration directory. Add the file prefix to the list in the `model_variable_injector.json` file, or in the `target.json` file if targeted configuration is used. For example, create the file `custom.json`, and add a `custom` entry to the list.

An injector directive contains a key that identifies an attribute to be tokenized, and an optional set of directive properties. The key is a period-separated MBean hierarchy and attribute name as they are defined in the model. Always exclude the name of the model section from the injector key.

For example, an injector directive for the Server SSL Listen Port is as follows. This directive contains no additional properties.

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

A sample of a custom injector directive file is included in the `$WLSDEPLOY_HOME/samples/injectors` directory.

#### Injector directive properties

Include the following properties to refine the directive as specified.

- `force:<attribute>`
    If the MBean hierarchy exists in the model, but the attribute does not, then the attribute will be added and persisted to the resulting model. The value stored in the
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

When the tool is run, the pattern is applied to the URL string and tokens injected into the string:

```properties
URL: 'jdbc:oracle:thin:@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)(HOST=@@PROP:JDBCSystemResource.Database1.JdbcResource.JDBCDriverParams.URL--Host@@:)(PORT=@@PROP:JDBCSystemResource.Database1.JdbcResource.JDBCDriverParams.URL--Port@@)))(CONNECT_DATA=(SERVICE_NAME=orcl.us.oracle.com)))'
```

And the variables put in the properties file:

```properties
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
  "Server[ADMIN_SERVER].SSL.ListenPort": {}
}
```
