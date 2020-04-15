## Configuring Oracle HTTP Server (OHS)

Oracle HTTP Server (OHS) can be configured and updated with Create Domain, Update Domain, and Deploy Applications Tools, starting with WDT release 1.8.0. OHS configuration is only supported for offline mode in WDT. The OHS configuration can be discovered using the Discover Domain Tool, in offline mode only.
 
### Prerequisites

In order to configure and use OHS, the product must be installed in the Oracle Home used to create the domain. You can download OHS [here](https://www.oracle.com/middleware/technologies/webtier-downloads.html).

The OHS template must be present in the WDT domain type definition file used to create or update the domain. See [Domain Type Definitions](type_def.md) for more information on creating a custom definition.

You should create a copy of an existing domain type definition file, add the template to that file, then reference that file on the WDT command line. For example, if you want to create a domain with Oracle HTTP Server based on a Restricted JRF domain, first create a copy of the file `WLSDEPLOY_HOME/lib/typedefs/RestrictedJRF.json` in the same directory, such as `WLSDEPLOY_HOME/lib/typedefs/HttpServer.json`. In this example, you would change the existing `extensionTemplates` section to include the additional OHS template. The original value is 
```
"extensionTemplates": [ "Oracle Restricted JRF", "Oracle Enterprise Manager-Restricted JRF" ],
```
and the revised value would be:
```
"extensionTemplates": [ "Oracle Restricted JRF", "Oracle Enterprise Manager-Restricted JRF", "Oracle HTTP Server (Restricted JRF)" ],
```
The file name of this new type (without the `.json` extension) is used with the `-domain_type` argument on the WDT command line. For example, the command line to create a domain using the `HttpServer.json` file from the previous steps would look like:  
```
WLSDEPLOY_HOME/bin/createDomain -oracle_home /etc/oracle ... -domain_type HttpServer
```

### Configuring the Model

Configuring OHS usually involves adding two top-level folders to the `resources` section of the model. Here is an example:
```yaml
resources:
    SystemComponent:
        'my-ohs':
            ComponentType: 'OHS'
            Machine: 'my-machine'
    OHS:
        'my-ohs':
            AdminHost: '127.0.0.1'
            AdminPort: '9324'
            ListenAddress: '127.0.0.1'
            ListenPort: '7323'
            SSLListenPort: '4323'
            ServerName: 'http://localhost:7323'
```
Each name under the `OHS` folder must match a name under the `SystemComponent` folder in the model, or the name of a `SystemComponent` element that has been previously created. In this example, the name `my-ohs` is in both places.

The `ComponentType` field of the `SystemComponent` element must be set to `OHS` in order to allow configuration of the corresponding `OHS` folders.

The [Model Help Tool](model_help.md) can be used to determine the complete list of folders and attributes that can be used in these sections of the model. For example, this command will list the attributes in the `OHS` folder:
```yaml
<wls-deploy-home>/bin/modelHelp.sh -oracle_home /tmp/oracle resources:/OHS
```
