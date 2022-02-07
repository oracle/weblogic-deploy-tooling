---
title: "Compare Model Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 7
description: "Compares two model files."
---


When working with a domain model, sometimes it is useful to know the differences between different models.
 The Compare Model Tool compares two model files and generates a model that shows the differences between them.

To use the Compare Model Tool, simply run the `compareModel` shell script with the correct arguments.  To see the list of valid arguments, simply run the shell script with the `-help` option (or with no arguments) for usage information.

For example, comparing the following models.  

#### New model

```yaml
domainInfo:
    AdminUserName: weblogic
    AdminPassword: welcome2
    ServerStartMode: 'prod'
topology:
    Name: domain1
    AdminServerName: admin-server
    SecurityConfiguration:
        NodeManagerUsername : weblogic
        NodeManagerPasswordEncrypted : welcome1
    Cluster:
        cluster-1:
            DynamicServers:
                ServerTemplate:  cluster-1-template
                ServerNamePrefix: managed-server
                DynamicClusterSize: 5
                MaxDynamicClusterSize: 5
                CalculatedListenPorts: false
        cluster-2:
            DynamicServers:
                ServerTemplate:  cluster-2-template
                ServerNamePrefix: managed-server
                DynamicClusterSize: 2
                MaxDynamicClusterSize: 3
                CalculatedListenPorts: false
    Server:
        admin-server:
            ListenPort: 10011
    ServerTemplate:
        cluster-1-template:
            Cluster: cluster-1
            ListenPort : 5001
            JTAMigratableTarget:
                    StrictOwnershipCheck: true
                    Cluster: cluster-1
        cluster-2-template:
            Cluster: cluster-2
            ListenPort : 8001
            ServerStart:
                    Arguments: ['-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=6006']
            JTAMigratableTarget:
                    StrictOwnershipCheck: true
                    Cluster: cluster-2
appDeployments:
     Application:
         myear:
             SourcePath: /home/johnny/dimtemp23/sample_app_stage/wlsdeploy/applications/sample_app.ear
             Target: [cluster-2,cluster-1]
         yourear:
             SourcePath: /home/johnny/dimtemp23/sample_app_stage/wlsdeploy/applications/sample_app2.ear
             ModuleType: ear
             Target: [cluster-2,cluster-1]
resources:
    JMSServer:
        JMSServer1:
            Target: m1
        JMSServer2:
            Target: m2
    JMSSystemResource:
        MyJmsModule:
            Target: mycluster
            SubDeployment:
                JMSServer1Subdeployment:
                    Target: JMSServer1
                JMSServer2Subdeployment:
                    Target: JMSServer2
            JmsResource:
                ConnectionFactory:
                    WebAppConnectionFactory:
                        DefaultTargetingEnabled: true
                        JNDIName: jms/WebCF
                        ClientParams:
                            AllowCloseInOnMessage: true
                            MessagesMaximum: 1
                        DefaultDeliveryParams:
                            DefaultTimeToDeliver: 3
                            DefaultTimeToLive: 3600
                        FlowControlParams:
                            FlowControlEnabled: false
                        LoadBalancingParams:
                            LoadBalancingEnabled: false
                        SecurityParams:
                            AttachJMSXUserId: true
                        TransactionParams:
                            XAConnectionFactoryEnabled: true
                UniformDistributedQueue:
                    MyUniformDistributedQueue:
                        DefaultTargetingEnabled: true
                        JNDIName: jms/myUDQ
```

#### Old model

```yaml
domainInfo:
    AdminUserName: weblogic
    AdminPassword: welcome2
    ServerStartMode: prod
topology:
    Name: domain1
    AdminServerName: admin-server
    SecurityConfiguration:
        NodeManagerUsername : weblogic
        NodeManagerPasswordEncrypted : welcome1
    Cluster:
        cluster-1:
            DynamicServers:
                ServerTemplate:  cluster-1-template
                ServerNamePrefix: managed-server
                DynamicClusterSize: 5
                MaxDynamicClusterSize: 5
                CalculatedListenPorts: false
    Server:
        admin-server:
            ListenPort: 10011
    ServerTemplate:
        cluster-1-template:
            Cluster: cluster-1
            ListenPort : 5001
            ServerStart:
                    Arguments: ['-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=6006']
            JTAMigratableTarget:
                    StrictOwnershipCheck: true
                    Cluster: cluster-1
appDeployments:
     Application:
         myear:
             SourcePath: /home/johnny/dimtemp23/sample_app_stage/wlsdeploy/applications/sample_app.ear
             ModuleType: ear
             Target: [cluster-1,cluster-2]
         myear2:
             SourcePath: /home/johnny/dimtemp23/sample_app_stage/wlsdeploy/applications/sample_app2.ear
             ModuleType: ear
             Target: [cluster-1,cluster-2]
resources:
    WebAppContainer:
        WAPEnabled: '@@PROP:WAPENABLED@@'
        FilterDispatchedRequestsEnabled: true
        AllowAllRoles: true
        XPoweredByHeaderLevel: NONE
        ServletAuthenticationFormURL: true
        ServletReloadCheckSecs: 1
        ChangeSessionIDOnAuthentication: true
        MimeMappingFile: wlsdeploy/config/amimemappings.properties
        AuthCookieEnabled: true
        WorkContextPropagationEnabled: true
        ReloginEnabled: true
        GzipCompression:
            GzipCompressionContentType: [ text/html, text/xml, text/plain ]
            GzipCompressionEnabled: true
    JMSServer:
        JMSServer1:
            Target: m1
        JMSServer2:
            Target: m2
    JMSSystemResource:
        MyJmsModule:
            Target: mycluster
            SubDeployment:
                JMSServer1Subdeployment:
                    Target: JMSServer1
                JMSServer2Subdeployment:
                    Target: JMSServer2
            JmsResource:
                ConnectionFactory:
                    WebAppConnectionFactory:
                        DefaultTargetingEnabled: true
                        JNDIName: jms/WebCF
                        ClientParams:
                            AllowCloseInOnMessage: true
                            MessagesMaximum: 1
                        DefaultDeliveryParams:
                            DefaultTimeToDeliver: 3
                            DefaultTimeToLive: 3600
                        FlowControlParams:
                            FlowControlEnabled: false
                        LoadBalancingParams:
                            LoadBalancingEnabled: false
                        SecurityParams:
                            AttachJMSXUserId: true
                        TransactionParams:
                            XAConnectionFactoryEnabled: true
                    MDBConnectionFactory:
                        DefaultTargetingEnabled: true
                        JNDIName: jms/mdbCF
                        TransactionParams:
                            XAConnectionFactoryEnabled: true
                UniformDistributedQueue:
                    MyUniformDistributedQueue:
                        DefaultTargetingEnabled: true
                        JNDIName: jms/myUDQ
                        ResetDeliveryCountOnForward: true
```
To compare the two model files, run the tool as follows:

    $ weblogic-deploy\bin\compareModel.cmd -oracle_home c:\wls12213 new_model.yaml old_model.yaml

The output of the tool will look something like this:


Comparing Models: new=/tmp/model2.yaml vs old=/tmp/model1.yaml

Differences between new model and old model:
```
resources:
    JMSSystemResource:
        MyJmsModule:
            JmsResource:
                ConnectionFactory:
                    '!MDBConnectionFactory':
    '!WebAppContainer':
appDeployments:
    Application:
        '!myear2':
        yourear:
            SourcePath: /home/johnny/dimtemp23/sample_app_stage/wlsdeploy/applications/sample_app2.ear
            ModuleType: ear
            Target: [ cluster-2, cluster-1 ]
        myear:
            Target: [ cluster-2, cluster-1 ]
topology:
    ServerTemplate:
        cluster-1-template:
            '!ServerStart':
        cluster-2-template:
            Cluster: cluster-2
            ListenPort: 8001
            ServerStart:
                Arguments: [ '-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=6006' ]
            JTAMigratableTarget:
                StrictOwnershipCheck: True
                Cluster: cluster-2
    Cluster:
        cluster-2:
            DynamicServers:
                ServerTemplate: cluster-2-template
                ServerNamePrefix: managed-server
                DynamicClusterSize: 2
                MaxDynamicClusterSize: 3
                CalculatedListenPorts: False
```

1. Model Path: resources-->JMSSystemResource-->MyJmsModule-->JmsResource-->UniformDistributedQueue-->MyUniformDistributedQueue-->ResetDeliveryCountOnForward does not exist in new model but exists in previous model

2. Model Path: appDeployments-->Application-->myear-->ModuleType does not exist in new model but exists in previous model


Comparing the new and old models:

 1. Added `cluster-2` and `cluster-2-template` in the `topology` section.
 2. Removed `ServerStart` of `cluster-1-template` in the `topology` section.
 3. Deployed two applications `yourear` and `myear` in the `appDeployments` section.
 4. Removed application `myear` in the `appDeployments` section.
 4. Removed `MDBConnectionFactory` from the `MyJmsModule` JMS Module in the `resource` section.
 5. Removed `WebAppContainer` in the `resource` section.
 6. Removed the attribute `ResetDeliveryCountOnForward` from `MyUniformDistributedQueue`.
 7. Changed deployment targets for application `myear`.
 8. Removed the attribute 'ModuleType' for application `myear`.

{{% notice note %}}  The `!` is a notation for the deletion of a non-attribute key element from the model. Missing attributes
 will be omitted from the resulting model, but shown as messages in the output.  If the attribute value is a list, even
 if all the individual items within the list are identical but the ordering is different, the attribute is counted as
 different.
 {{% /notice %}}

 To compare the two model files and generate the output to files, run the tool as follows:

    $ weblogic-deploy\bin\compareModel.cmd -oracle_home c:\wls12213 -output_dir c:\cm-output new_model.yaml old_model.yaml

    The following files will be written to the directory:

    diffed_model.json
    diffed_model.yaml
    compare_model_stdout

### Parameter table for `compareModel`
| Parameter | Definition | Default |
| --- | --- | --- |
| `-oracle_home` | Home directory of the Oracle installation. Required if the `ORACLE_HOME` environment variable is not set. |    |
| `-output_dir` | (Required) Directory in which to store the output. |    |
| `-variable_file` | Variable file used for token substitution. |    |
