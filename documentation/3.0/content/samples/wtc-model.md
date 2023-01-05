---
title: "Modeling a WTC configuration"
date: 2021-11-01T10:19:24-05:00
draft: false
weight: 3
description: "A domain model with a typical configuration for a WebLogic Tuxedo Connector."
---

This sample shows the WDT model for configuring WebLogic Tuxedo Connector (WTC) for both importing services from Tuxedo and exporting EJB methods to Tuxedo as services.

```yaml
 resources:
   # A logical WLS server name for the WLS configuration found on the console under interoperability
   WTCServer:
     myWTCServer:
       Target: admin
       # Exported EJB services to be consumed by Tuxedo services.
       WTCExport:
         WTCExportedService-1:
           # The remote name of this service.
           ResourceName: QaWls2Conv2
           # The name used to identify an exported service
           RemoteName: QaWls2Conv2
           EJBName: tuxedo.services.QaTux2wlsConvHome
           # The name of the local access point that exports this service.
           LocalAccessPoint: LocalAccessPoint2
         WTCExportedService-2:
           ResourceName: QaWls1Conv2
           RemoteName: QaWls1Conv2
           EJBName: tuxedo.services.QaTux2wlsConvHome
           LocalAccessPoint: LocalAccessPoint
         WTCExportedService-3:
           ResourceName: QaWlsConvSvc
           RemoteName: QaWlsConvSvc
           EJBName: tuxedo.services.QaTux2wlsConvHome
           LocalAccessPoint: LocalAccessPoint
       # Imported Tuxedo services to be consumed by WLS services.
       WTCImport:
         WTCImportedService-1:
           # The name used to identify this imported service.
           ResourceName: CONVSVC
           # The remote name of this service.
           RemoteName: CONVSVC
           # The comma-separated failover list that identifies the remote domain access points through which resources are imported.
           RemoteAccessPointList: RemoteAccessPoint
           # The name of the local access point that offers this service. Matches the Tuxedo domain
           LocalAccessPoint: LocalAccessPoint
         WTCImportedService-2:
           ResourceName: QaTux1Conv2
           RemoteName: QaTux1Conv2
           RemoteAccessPointList: RemoteAccessPoint
           LocalAccessPoint: LocalAccessPoint
         WTCImportedService-3:
           ResourceName: QaTux1Conv3
           RemoteName: QaTux1Conv3
           RemoteAccessPointList: RemoteAccessPoint
           LocalAccessPoint: LocalAccessPoint
       # Local access points so that Tuxedo services can act as a client to WLS services.
       WTCLocalTuxDom:
         LocalAccessPoint:
           # The local listen address on the WLS side
           NWAddr: //access-host:2510
           # A logical and unique name to identify this local Tuxedo access point
           AccessPoint: LocalAccessPoint
           # The connection principal name used to identify this local Tuxedo access point when attempting to establish a session connection with remote Tuxedo access points.
           AccessPointId: mydomain1
         LocalAccessPoint2:
           NWAddr: //access-host:2520
           AccessPoint: LocalAccessPoint2
           AccessPointId: mydomain2
       # Remote access points so that WLS can act as a client to Tuxedo services
       WTCRemoteTuxDom:
         RemoteAccessPoint:
           # The local domain name from which this remote Tuxedo domain is reached.
           LocalAccessPoint: LocalAccessPoint
           # The remote listen address of the Tuxedo domain gateway.
           NWAddr: //access-host:2500
           # A logical and unique name used to identify this Tuxedo remote access point
           AccessPoint: RemoteAccessPoint
           # The connection principal name used to identify this remote domain access point when attempting to establish a session connection to local Tuxedo access points
          # This ID needs to be configured as a user in the WLS security realm.
          AccessPointId: domain1
         RemoteAccessPoint2:
           LocalAccessPoint: LocalAccessPoint2
           NWAddr: //access-host:2500
           AccessPoint: RemoteAccessPoint2
           AccessPointId: domain1

```
In this configuration, the WTC uses EJB and communicates with remote and local access points. To see other WTC configuration options, use the model help as shown in the following.

```bash
$ ${WDT_HOME}/bin/modelHelp.sh -oracle_home /tmp/oracle resources:/WTCServer
```
