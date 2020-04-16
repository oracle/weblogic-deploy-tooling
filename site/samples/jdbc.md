## JDBC Sample

This sample WDT domain model section includes configuration for two JDBC data sources.
 
The data source `datasource-1` has a sparse configuration meant to set a minimal number of values. It is not necessary to include additional attributes and sub-folders, unless you intend to override default values.

The data source `datasource-2` includes additional folders and attributes to provide further customization, including targeting information, connection pool configuration, and such. The cluster `cluster-1` should be defined elsewhere within this model, or should already exist in a domain that is being updated.  

It is recommended that credential fields, such as `PasswordEncrypted`, should not be stored as clear text in the model. Those values can be referenced in a separate variables file or Kubernetes secret, or the model can be encrypted using [Encrypt Model Tool](../encrypt.md).

```yaml
resources:
    JDBCSystemResource:
        'datasource-1':
            JdbcResource:
                DatasourceType: GENERIC
                JDBCDriverParams:
                    URL: 'jdbc:oracle:thin:@//localhost:1521/myDB'
                    DriverName: oracle.jdbc.OracleDriver
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
                    PasswordEncrypted: '@@PROP:jdbc2.password@@'
                    DriverName: oracle.jdbc.OracleDriver
                    Properties:
                        user:
                            Value: scott
```
