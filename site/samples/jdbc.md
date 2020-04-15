## JDBC Sample

This sample WDT domain model section includes configuration for two JDBC data sources. It assumes that the cluster `cluster-1` was defined elsewhere within this model, or exists in a domain that is being updated.

It is recommended that credential fields, such as `PasswordEncrypted`, should not be stored as clear text in the model. Those values can be referenced in a separate variables file or Kubernetes secret, or the model can be encrypted using [Encrypt Model Tool](../encrypt.md).

```yaml
resources:
    JDBCSystemResource:
        'datasource-1':
            JdbcResource:
                JDBCConnectionPoolParams:
                    InitialCapacity: 5
                JDBCDataSourceParams:
                    JNDIName: my.datasources.ds3
        'datasource-2':
            Target: 'AdminServer,cluster-1'
            JdbcResource:
                DatasourceType: GENERIC
                JDBCConnectionPoolParams:
                    StatementCacheSize: 10
                    InitialCapacity: 0
                    MinCapacity: 0
                    TestTableName: SQL ISVALID
                    StatementCacheType: LRU
                    MaxCapacity: 5
                    ConnectionReserveTimeoutSeconds: 10
                JDBCDataSourceParams:
                    GlobalTransactionsProtocol: OnePhaseCommit
                    JNDIName: my.datasources.ds2
                JDBCDriverParams:
                    URL: 'jdbc:oracle:thin:@//localhost:1521/myDB'
                    PasswordEncrypted: 'welcome1'
                    DriverName: oracle.jdbc.OracleDriver
                    Properties:
                        user:
                            Value: scott
```
