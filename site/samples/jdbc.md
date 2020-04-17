## JDBC Sample

These WDT domain model sample sections include configuration for JDBC data sources.
 
The first sample has a JDBC data source with a sparse configuration meant to set a minimal number of values. It is not necessary to include additional attributes and sub-folders, unless you intend to override the default values.
```yaml
resources:
    JDBCSystemResource:
        'datasource-1':
            JdbcResource:
                DatasourceType: GENERIC
                JDBCDriverParams:
                    URL: 'jdbc:oracle:thin:@//localhost:1521/myDB'
                    DriverName: oracle.jdbc.OracleDriver
                JDBCConnectionPoolParams:
                    TestTableName: SQL ISVALID
```
The second sample includes additional folders and attributes to provide further customization, including targeting information, data source parameters, and such.  
```yaml
resources:
    JDBCSystemResource:
        'datasource-2':
            Target: 'AdminServer,cluster-1'
            JdbcResource:
                DatasourceType: AGL
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
The cluster `cluster-1` should be defined elsewhere within this model, or should already exist in a domain that is being updated.
 
It is recommended that credential fields, such as `PasswordEncrypted`, should not be stored as clear text in the model. Those values can be referenced in a separate variables file or Kubernetes secret, or the model can be encrypted using the [Encrypt Model Tool](../encrypt.md).

You can use the [Model Help Tool](../model_help.md) to determine the complete list of sub-folders and attributes that can be used in a specific model location. For example, this command will list the attributes and sub-folders for the `JDBCSystemResource/JdbcResource` folder:
```yaml
${WDT_HOME}/bin/modelHelp.sh -oracle_home /tmp/oracle resources:/JDBCSystemResource/JdbcResource
```
