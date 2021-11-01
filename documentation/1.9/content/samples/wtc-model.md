---
title: "Modeling a WTC configuration"
date: 2021-11-01T10:19:24-05:00
draft: false
weight: 3
description: "A domain model with a typical queue based configuration for a WebLogic Tuxedo Connector."
---

This WDT domain model sample section shows a remote and local queue for a WTC configuration. 

```yaml
 resources:
   StartupClass:
     WtcServerSideHelper:
       Target: admin
       ClassName: wlstest.functional.core.wtc.conversation.common.apps.Helper.WtcServerSideHelperImpl
   WTCServer:
     myWTCServer:
       Target: admin
       WTCExport:
         'WTCExportedService-1':
           ResourceName: QaWls2Conv2
           RemoteName: QaWls2Conv2
           EJBName: tuxedo.services.QaTux2wlsConvHome
           LocalAccessPoint: LocalAccessPoint2
         'WTCExportedService-2':
           ResourceName: QaWls1Conv2
           RemoteName: QaWls1Conv2
           EJBName: tuxedo.services.QaTux2wlsConvHome
           LocalAccessPoint: LocalAccessPoint
         'WTCExportedService-3':
           ResourceName: QaWlsConvSvc
           RemoteName: QaWlsConvSvc
           EJBName: tuxedo.services.QaTux2wlsConvHome
           LocalAccessPoint: LocalAccessPoint
       WTCImport:
         'WTCImportedService-1':
           ResourceName: CONVSVC
           RemoteName: CONVSVC
           RemoteAccessPointList: RemoteAccessPoint
           LocalAccessPoint: LocalAccessPoint
         'WTCImportedService-2':
           ResourceName: QaTux1Conv2
           RemoteName: QaTux1Conv2
           RemoteAccessPointList: RemoteAccessPoint
           LocalAccessPoint: LocalAccessPoint
         'WTCImportedService-3':
           ResourceName: QaTux1Conv3
           RemoteName: QaTux1Conv3
           RemoteAccessPointList: RemoteAccessPoint
           LocalAccessPoint: LocalAccessPoint
       WTCLocalTuxDom:
         LocalAccessPoint:
           NWAddr: '//access-host:2510'
           AccessPoint: LocalAccessPoint
           AccessPointId: mydomain1
         LocalAccessPoint2:
           NWAddr: '//access-host:2520'
           AccessPoint: LocalAccessPoint2
           AccessPointId: mydomain2
       WTCRemoteTuxDom:
         RemoteAccessPoint:
           LocalAccessPoint: LocalAccessPoint
           NWAddr: '//access-host:2500'
           AccessPoint: RemoteAccessPoint
           AccessPointId: domain1
         RemoteAccessPoint2:
           LocalAccessPoint: LocalAccessPoint2
           NWAddr: '//access-host:2500'
           AccessPoint: RemoteAccessPoint2
           AccessPointId: domain1

```
This sample has a startup class that must be collected into the archive file under wlsdeploy/domainLibs. Refer to [Archive structure]({{< relref "/concepts/archive#archive-structure" >}}) .
In this configuration, the WTC is queue-based with remote and local access points. To see other WTC configuration options, use the model help as shown in the following.

```bash
$ ${WDT_HOME}/bin/modelHelp.sh -oracle_home /tmp/oracle resources:/WTCServer
```
