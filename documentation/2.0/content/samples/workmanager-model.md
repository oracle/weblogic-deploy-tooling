---
title: "Modeling a Work Manager"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 4
description: "A domain model with a typical configuration for Work Manager."
---


This WDT domain model sample section has typical configurations for a Work Manager and its related request classes and constraints. These elements are configured in the `SelfTuning` folder in the `resources` section of the model.
```yaml
resources:
    SelfTuning:
        Capacity:
            capacity40:
                Target: cluster-1
                Count: 40
        MaxThreadsConstraint:
            threeMax:
                Target: cluster-1
                Count: 3
        MinThreadsConstraint:
            twoMin:
                Target: cluster-1
                Count: 2
        FairShareRequestClass:
            appFairShare:
                Target: cluster-1
                FairShare: 50
            highFairshare:
                Target: cluster-1
                FairShare: 80
            lowFairshare:
                Target: cluster-1
                FairShare: 20
        ResponseTimeRequestClass:
            fiveSecondResponse:
                Target: cluster-1
                GoalMs: 5000
        ContextRequestClass:
            appContextRequest:
                Target: cluster-1
                ContextCase:
                    Case1:
                        GroupName: Administrators
                        RequestClassName: highFairshare
                        Target: cluster-1
                    Case2:
                        UserName: weblogic
                        RequestClassName: lowFairshare
                        Target: cluster-1
        WorkManager:
            myWorkManager:
                Capacity: capacity40
                ContextRequestClass: appContextRequest
                # FairShareRequestClass: appFairShare
                IgnoreStuckThreads: true
                MaxThreadsConstraint: threeMax
                MinThreadsConstraint: twoMin
                # ResponseTimeRequestClass: fiveSecondResponse
                Target: cluster-1
```
In this sample, assignments for `FairShareRequestClass` and `ResponseTimeRequestClass` are included as comments under `myWorkManager`. A Work Manager can only specify one request class type.

There are additional sub-folders and attributes available for more configuration options. These can be determined using the [Model Help Tool]({{< relref "/userguide/tools/model_help.md" >}}). For example, this command will list the attributes and sub-folders for the `WorkManager` folder:
```bash
$ ${WDT_HOME}/bin/modelHelp.sh -oracle_home /tmp/oracle resources:/WorkManager
```

For this sample, the target cluster `cluster-1` should be defined elsewhere within this model, or should already exist in a domain that is being updated.
