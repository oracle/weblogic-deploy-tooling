---
title: "Customizing the Administration Server"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 1
description: "Configure the Administration Server using a domain model."
---

 ### Administration Server configuration

 The Create Domain Tool lets you configure the Administration Server using a domain model. These examples show how some common configurations can be represented in the model.

 #### Using the default Administration Server configuration

 When the Create Domain Tool is run, the templates associated with your domain type will automatically create an Administration Server named `AdminServer`, with default values for all the attributes. If you don't need to change any of these attributes, such as `ListenAddress` or `ListenPort`, or any of the sub-folders, such as `SSL` or `ServerStart`, nothing needs to be added to the model.

 #### Customizing the Administration Server configuration

 To customize the configuration of the default Administration Server, you will need to add a server with the default name `AdminServer`. Because you are not changing the name of the Administration Server, there is no need to specify the `AdminServerName` attribute under the topology section. This example shows some attributes and sub-folders:

 ```yaml
 topology:
     Server:
         AdminServer:
             ListenPort: 9071
             RestartDelaySeconds: 10
             ListenAddress: my-host-1
             Log:
                 FileCount: 9
                 LogFileSeverity: Info
                 FileMinSize: 5000
             SSL:
                 HostnameVerificationIgnored: true
                 JSSEEnabled: true
                 ListenPort: 9072
                 Enabled: true
 ```

 The most common problem with this type of configuration is to misspell the name of the folder under `Server`, when it should be `AdminServer`. This will result in the creation of an Administration Server with the default name, and an additional Managed Server with the misspelled name.

 #### Configuring the Administration Server with a different name

 If you want the Administration Server to have a name other than the default `AdminServer`, you will need to specify that name in the `AdminServerName` attribute, and use that name in the `Server` section. This example uses the name `my-admin-server`:

 ```yaml
 topology:
     AdminServerName: my-admin-server
     Server:
         'my-admin-server':
             ListenPort: 9071
             RestartDelaySeconds: 10
             ListenAddress: my-host-1
             Log:
                 FileCount: 9
                 LogFileSeverity: Info
                 FileMinSize: 5000
             SSL:
                 HostnameVerificationIgnored: true
                 JSSEEnabled: true
                 ListenPort: 9072
                 Enabled: true
 ```

 The most common problem with this type of configuration is to mismatch the `AdminServerName` attribute with the name in the `Server` folder. This will change the name of the default Administration Server to the value of `AdminServerName`, and the folder under `Server` to be created as an additional Managed Server.

 The name of the Administration Server cannot be changed after domain creation, so any changes to the `AdminServerName` attribute will be ignored by the Update Domain Tool.
