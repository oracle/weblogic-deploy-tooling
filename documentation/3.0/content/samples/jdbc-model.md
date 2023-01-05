---
title: "Modeling a JDBC data source"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 3
description: "A domain model with a typical configuration for a JDBC data source."
---

This WDT domain model sample section has a typical configuration for a JDBC data source, including targeting information, connection pool parameters, and other details.

```yaml
resources:
    JDBCSystemResource:
        datasource-1:
            Target: AdminServer,cluster-1
            JdbcResource:
                DatasourceType: GENERIC
                JDBCConnectionPoolParams:
                    ConnectionReserveTimeoutSeconds: 10
                    InitialCapacity: 0
                    MaxCapacity: 5
                    MinCapacity: 0
                    TestConnectionsOnReserve: true
                    TestTableName: SQL ISVALID
                JDBCDriverParams:
                    DriverName: oracle.jdbc.OracleDriver
                    PasswordEncrypted: '@@PROP:jdbc.password@@'
                    URL: jdbc:oracle:thin:@//localhost:1521/myDB
                    Properties:
                        user:
                            Value: scott
```
There are additional sub-folders and attributes available for more configuration options. These can be determined using the [Model Help Tool]({{< relref "/userguide/tools/model_help.md" >}}). For example, this command will list the attributes and sub-folders for the `JDBCSystemResource/JdbcResource` folder:
```bash
$ ${WDT_HOME}/bin/modelHelp.sh -oracle_home /tmp/oracle resources:/JDBCSystemResource/JdbcResource
```

For this sample, the target cluster `cluster-1` should be defined elsewhere within this model, or should already exist in a domain that is being updated.

It is recommended that credential fields, such as `PasswordEncrypted`, should not be stored as clear text in the model. Those values can be referenced in a separate variables file or in Kubernetes secrets, or the model can be encrypted using the [Encrypt Model Tool]({{< relref "/userguide/tools/encrypt.md" >}}).
