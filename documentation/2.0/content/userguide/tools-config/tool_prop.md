---
title: "Tool property file"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 4
---


 You can configure or tune WebLogic Deploy Tooling tools using the tool property file. This property file is installed as `<weblogic-deploy>/lib/tool.properties`. You may change the value of any of the properties in this file to tune the WDT tool. Another option is to configure the tool properties in a Custom Configuration directory. Create the `tool.properties` file in the `$WDT_CUSTOM_CONFIG` directory.

 If a property is removed from the file, or a property value is incorrectly formatted, a `WARNING` message is logged and an internal default value used instead of the missing or bad value.

 | Property | Description                                                                                                                                                    |
 |----------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
 | `connect.timeout` | The number of milliseconds that WLST waits for the online `connect` command to complete. A value of 0 means the operation will not timeout.                    |
 | `activate.timeout` | The number of milliseconds that WLST waits for the activation of configuration changes to complete. A value of -1 means the operation will not timeout.        |
 | `deploy.timeout` | The number of milliseconds that WLST waits for the undeployment process to complete. A value of 0 means the operation will not timeout.                        |
 | `redeploy.timeout` | The number of milliseconds that WLST waits for the redeployment process to complete. A value of 0 means the operation will not timeout.                        |
 | `start.application.timeout` | The number of milliseconds that WLST waits for the start application process to complete. A value of 0 means the operation will not timeout.                   |
 | `stop.application.timeout` | The number of milliseconds that WLST waits for the stop application process to complete. A value of 0 means the operation will not timeout.                    |
 | `set.server.groups.timeout` | Specifies the amount of time the set server groups connection can be inactive before the connection times out.                                                 |
 | `wlst.edit.lock.acquire.timeout` | Specifies the amount of time in milliseconds the WLST online `startEdit` command will wait trying to acquire the edit lock before it times out.                |
 | `wlst.edit.lock.release.timeout` | Specifies the amount of time in milliseconds the WLST online `startEdit` command will wait for the edit lock to be released before releasing it automatically. |
 | `wlst.edit.lock.exclusive` | Specifies whether the edit lock acquired by `startEdit` should be exclusive or shared (default is shared).                                                     |

 You can override the value of a single property using a Java System property with the name `wdt.config.<tool-property-name>`.
 For example, adding `-Dwdt.config.connect.timeout=5000` will set the effective `connect.timeout` property to 5000 milliseconds, regardless of what the value in the tool.properties file might be. 