---
title: "Tool property file"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 4
---


 You can configure or tune WebLogic Deploy Tooling tools using the tool property file. This property file is installed as `<weblogic-deploy>/lib/tool.properties`. You may change the value of any of the properties in this file to tune the WDT tool. Another option is to configure the tool properties in a Custom Configuration directory. Create the `tool.properties` file in the `$WDT_CUSTOM_CONFIG` directory.

 If a property is removed from the file, or a property value is incorrectly formatted, a `WARNING` message is logged and an internal default value used instead of the missing or bad value.

 | Property                                   | Description                                                                                                                                                               |
 |--------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
 | `connect.timeout`                          | The number of milliseconds that WLST waits for the online `connect` command to complete. A value of 0 means the operation will not timeout.                               |
 | `activate.timeout`                         | The number of milliseconds that WLST waits for the activation of configuration changes to complete. A value of -1 means the operation will not timeout.                   |
 | `deploy.timeout`                           | The number of milliseconds that WLST waits for the undeployment process to complete. A value of 0 means the operation will not timeout.                                   |
 | `redeploy.timeout`                         | The number of milliseconds that WLST waits for the redeployment process to complete. A value of 0 means the operation will not timeout.                                   |
 | `undeploy.timeout`                         | The number of milliseconds that WLST waits for the undeployment process to complete. A value of 0 means the operation will not timeout.                                   |
 | `start.application.timeout`                | The number of milliseconds that WLST waits for the start application process to complete. A value of 0 means the operation will not timeout.                              |
 | `stop.application.timeout`                 | The number of milliseconds that WLST waits for the stop application process to complete. A value of 0 means the operation will not timeout.                               |
 | `set.server.groups.timeout`                | Specifies the amount of time the set server groups connection can be inactive before the connection times out.                                                            |
 | `wlst.edit.lock.acquire.timeout`           | Specifies the amount of time in milliseconds the WLST online `startEdit` command will wait trying to acquire the edit lock before it times out.                           |
 | `wlst.edit.lock.release.timeout`           | Specifies the amount of time in milliseconds the WLST online `startEdit` command will wait for the edit lock to be released before releasing it automatically.            |
 | `wlst.edit.lock.exclusive`                 | Specifies whether the edit lock acquired by `startEdit` should be exclusive or shared (default is `shared`).                                                              |
 | `yaml.max.file.size`                       | The maximum size of the YAML model file that the WDT SnakeYAML parser will allow.  The default value of `0` uses the SnakeYAML default setting of `3145728` (i.e., 3 MB). |
 | `use.deprecation.exit.code`                | Whether deprecation messages should cause WDT tools to exit with a non-zero exit code (default is `false`).                                                               |
 | `disable.rcu.drop.schema`                  | Whether the RCU drop step should be skipped when running Create Domain with the `-run_rco` switch (default is `false`).                                                   |
 | `enable.create.domain.password.validation` | Whether Create Domain should try to validate user passwords using the SystemPasswordValidator settings in the model (default is `true`).                                  |
 | `archive.custom.folder.size.limit`         | The size limit for the custom folder above which extracting the folder will generate a warning (default is `1048576`, which is 1 MB).                                     |
 | `ssh.private.key.default.file.name`        | The default file name of the SSH private key file (default is `id_rsa`).                                                                                                  |
 | `use.ssh.compression`                      | Whether to use SSH compression for all SSH operations (default is `true`).                                                                                                |
 | `use.server.version.for.online.operation`  | Whether to use the server's WebLogic Server version and patch level to initialize the aliases for WDT online operations (default is `true`).                              |

 You can override the value of a single property using a Java System property with the name `wdt.config.<tool-property-name>`.
 For example, adding `-Dwdt.config.connect.timeout=5000` will set the effective `connect.timeout` property to 5000 milliseconds, regardless of what the value in the tool.properties file might be.  To pass
 one or more of these properties to a WDT shell script (e.g., `createDomain.sh`), simply set the WLSDEPLOY_PROPERTIES environment variable prior to calling the shell script.  For example:
 
```shell
WLSDEPLOY_PROPERTIES="-Dwdt.config.connect.timeout=5000 -Dwdt.config.disable.rcu.drop.schema=true"
export WLSDEPLOY_PROPERTIES
$WLSDEPLOY_HOME/bin/createDomain.sh ...
```
