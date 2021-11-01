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
   # Main MBean required for a connection between WebLogic and Tuxedo
   WTCServer:
     myWTCServer:
       Target: admin
       # Used to configure services exported by a local Tuxedo access point.
       WTCExport:
         'WTCExportedService-1':
           # The remote name of this service.
           ResourceName: QaWls2Conv2
           # The name used to identify an exported service
           RemoteName: QaWls2Conv2
           EJBName: tuxedo.services.QaTux2wlsConvHome
           # The name of the local access point that exports this service.
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
       # Used to configure services imported and available on remote domains.
       WTCImport:
         'WTCImportedService-1':
           # The name used to identify this imported service.
           ResourceName: CONVSVC
           # The remote name of this service.
           RemoteName: CONVSVC
           # The comma-separated failover list that identifies the remote domain access points through which resources are imported.
           RemoteAccessPointList: RemoteAccessPoint
           # The name of the local access point that offers this service.
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
       # Used to configure available remote Tuxedo domains.
       WTCLocalTuxDom:
         LocalAccessPoint:
           NWAddr: '//access-host:2510'
           # Unique name to identify this local Tuxedo access point
           AccessPoint: LocalAccessPoint
           # The connection principal name used to identify this local Tuxedo access point when attempting to establish a session connection with remote Tuxedo access points.
           AccessPointId: mydomain1
         LocalAccessPoint2:
           NWAddr: '//access-host:2520'
           AccessPoint: LocalAccessPoint2
           AccessPointId: mydomain2
       # Used to configure connections to remote Tuxedo domains
       WTCRemoteTuxDom:
         RemoteAccessPoint:
           # The local domain name from which this remote Tuxedo domain is reached.
           LocalAccessPoint: LocalAccessPoint
           NWAddr: '//access-host:2500'
           # The unique name used to identify this Tuxedo remote access point
           AccessPoint: RemoteAccessPoint
           # The connection principal name used to identify this remote domain access point when attempting to establish a session connection to local Tuxedo access points
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
