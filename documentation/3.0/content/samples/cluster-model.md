---
title: "Modeling a configured cluster"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 2
description: "A domain model with a typical configuration for a configured cluster."
---

This WDT domain model sample has a typical configuration for a configured cluster with a single managed server, including connection information, logging setup, and other details.

```yaml
topology:
    Cluster:
        cluster-1:
            ClientCertProxyEnabled: true
            AutoMigrationTableName: MIGRATION_1
            DataSourceForAutomaticMigration: jdbc-1
            ClusterMessagingMode: unicast
            FrontendHost: frontend.com
            FrontendHTTPPort: 9001
            FrontendHTTPSPort: 9002
            MigrationBasis: database
            NumberOfServersInClusterAddress: 5
            WeblogicPluginEnabled: true

    Server:
        server-1:
            Cluster: cluster-1  # this server belongs to cluster-1
            ListenAddress: 127.0.0.1
            ListenPort: 8001
            Machine: machine-1
            Log:
                DomainLogBroadcastSeverity: Error
                FileCount: 7
                FileMinSize: 5000
                FileName: logs/AdminServer.log
                LogFileSeverity: Info
                MemoryBufferSeverity: Notice
                NumberOfFilesLimited: true
                RotateLogOnStartup: true
                RotationType: bySize
            SSL:
                Enabled: true
                ListenPort: 8002
            ServerStart:
                Arguments: -Dosgi=true -Dtangosol.coherence.management=all
                ClassPath: /foo/bar,wlsdeploy/classpathLibraries/mylib.jar
```
There are additional sub-folders and attributes available for more configuration options. These can be determined using the [Model Help Tool]({{< relref "/userguide/tools/model_help.md" >}}). For example, this command will list the attributes and sub-folders for the `Server` folder:
```bash
$ ${WDT_HOME}/bin/modelHelp.sh -oracle_home /tmp/oracle topology:/Server
```

For this sample, the machine named `machine-1` and the data source named `jdbc-1` should be defined elsewhere within this model, or should already exist in a domain that is being updated.
