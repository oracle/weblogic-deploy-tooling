---
title: "Modeling Oracle Platform Security Services"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 6
description: "Initializing OPSS configuration as part of WebLogic domain creation."
---


The `OPSSInitialization` section of the WDT model can be used to 
initialize credentials needed by upper-stack Fusion Middleware products. These credentials can only be applied at domain creation time.

#### Initializing Oracle Identity Governance

This example shows how to configure OPSS credentials for use by Oracle Identity Governance. 

```yaml
domainInfo:
    AdminUserName: '@@PROP:adminUser@@'
    AdminPassword: '@@PROP:adminPass@@'
    OPSSInitialization:
        Credential:
            oim:
                TargetKey:
                    keystore:
                        Username: keystore
                        Password: '@@PROP:keystorePass@@'
                    OIMSchemaPassword:
                        # database schema prefix + _OIM
                        Username: PREFIX_OIM
                        # database schema password
                        Password: '@@PROP:dbSchemaPass@@'
                    sysadmin:
                        Username: xelsysadm
                        Password: '@@PROP:sysAdminPass@@'
                    WeblogicAdminKey:
                        # match to WLS admin credentials
                        Username: '@@PROP:adminUser@@'
                        Password: '@@PROP:adminPass@@'
```

#### Initializing Oracle Data Integrator

This example shows how to configure OPSS credentials for use by Oracle Data Integrator. 

```yaml
domainInfo:
    AdminUserName: '@@PROP:adminUser@@'
    AdminPassword: '@@PROP:adminPass@@'
    RCUDbInfo:
        rcu_prefix: PREFIX
        rcu_admin_password: '@@PROP:dbAdminPass@@'
        # for ODI, the schema password has to be < 10 characters
        rcu_schema_password: '@@PROP:dbSchemaPass@@'
        rcu_db_conn_string: '@@PROP:dbConnect@@'
        # WORK_REPO_PASSWORD is the database schema password
        # SUPERVISOR_PASSWORD needs to match TargetKey password in credential
        rcu_variables: 'SUPERVISOR_PASSWORD=@@PROP:supvPass@@,WORK_REPO_PASSWORD=@@PROP:dbSchemaPass@@,WORK_REPOSITORY_TYPE=D,WORK_REPO_NAME=WORKREP,ENCRYPTION_ALGORITHM=AES-128'
    OPSSInitialization:
        Credential:
            oracle.odi.credmap:
                TargetKey:
                    SUPERVISOR:
                        Username: mySupervisor
                        Password: '@@PROP:supvPass@@'
```