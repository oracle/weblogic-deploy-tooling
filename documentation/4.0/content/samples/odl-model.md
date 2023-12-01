---
title: "Configuring Oracle Diagnostic Logging"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 8
description: "A model for configuring Oracle Diagnostic Logging (ODL)."
---


Oracle Diagnostic Logging (ODL) can be configured and updated with Create Domain, Update Domain, and Deploy Applications Tools, starting with WDT release 1.5.2.
ODL configuration is supported only for offline mode in WDT. ODL configuration is not added when a model is created using the Discover Domain Tool.
This example shows how some common configuration elements can be represented in the model.

```yaml
resources:
    ODLConfiguration:
        config1:
            Servers: m1, m2
            AddJvmNumber: true
            HandlerDefaults:
                abc: r123
                xyz: k890
            Handler:
                my-handler:
                    Class: com.my.MyHandler
                    Level: TRACE:32
                    ErrorManager: com.my.MyErrorManager
                    Filter: com.my.MyFilter
                    Formatter: com.my.MyFormatter
                    Encoding: UTF-8
                    Properties:
                        path: /home/me/mypath
                quicktrace-handler:
                    Filter: oracle:dfw:incident:IncidentDetectionLogFilter
                    Properties:
                        path: '${domain.home}/servers/${weblogic.Name}/logs/${weblogic.Name}-myhistory.log'
                        useSourceClassandMethod: true
            Logger:
                my-logger:
                    Level: NOTIFICATION:1
                    UseParentHandlers: true
                    Filter: oracle:dfw:incident:IncidentDetectionLogFilter
                    Handlers: richard-handler,owsm-message-handler
                oracle.sysman:
                    Handlers: [
                        my-handler,
                        owsm-message-handler
                    ]
        config2:
            Servers: AdminServer
            HandlerDefaults:
                path: /home/me/otherpath
                maxFileSize: 5242880
```

Each named ODL configuration (such as `config1`) is updated for each of the managed servers in the `Servers` list. Handlers and loggers that exist in the current configuration are updated, and any new ones are created and updated.

Unlike other WDT model elements, ODL configuration is not updated using WLST MBeans. The configuration is written directly to the file system, in the file `<domain_home>/config/fmwconfig/servers/<server>/logging.xml`.
