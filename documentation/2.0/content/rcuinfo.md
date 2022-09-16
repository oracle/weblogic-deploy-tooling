### Specifying RCU connection information in the model

When creating a JRF domain, you can provide all the RCU connection information in a section `RCUDbInfo` under the `domainInfo` section in the model.  
It provides you with more flexibility over the basic command-line arguments of 
`-rcu_db` and `-rcu_prefix`.  Use this when the connection string is more complex and requires extra options.

### Background on JRF domain RCU tables 

A JRF domain creates several data sources from the JRF domain template.

| Data source name        | JNDI name                  | Schema  | Target |
|-------------------------|----------------------------|---------|---|
| WLSSchemaDataSource     | jdbc/WLSSchemaDataSource   | prefix_WLS_RUNTIME | None |
| LocalSvcTblDataSource   | jdbc/WLSSchemaDataSource   | prefix_STB | admin server |
| opss-data-source        | jdbc/OpssDataSource        | prefix_OPSS | admin server and cluster |
| opss-audit-viewDS       | jdbc/AuditViewDataSource   | prefix_IAU_VIEWER | admin server and cluster |
| opss-audit-DBDS         | jdbc/AuditAppendDataSource | prefix_IAU_APPEND | admin server and cluster |
| mds-owsm                | jdbc/mds/owsm              | prefix_MDS | admin server and cluster |

By default, the JRF domain template data source has only the default information such as URL and schema with the default prefix `DEV`.  During domain creation,
WDT will use the information you provided in the command line or in the `RCUDbinfo` section to override the default values from the template so that it can connect to the database you specified.

For some advanced use cases, such as using an Oracle Active GridLink data source or Multi Data Sources, you can provide a sparse model of the data sources in a separate model file
during domain creation.  See [Advance use cases](#advanced-jrf-database-use-cases).

### Access a database using a wallet

When accessing a database, such as ATP or SSL, using a wallet, you need to obtain the wallet from your DBA and information about the database:

- `tns alias` - The network service name. You can find this in the `tnsnames.ora` file inside the database wallet.  The alias is on the left side of the equals sign.

   ```text
   xxxx = (DESCRIPTION ...)
   yyyy = (DESCRIPTION ...)
   ...
   ```

- `keystore and truststore password` - Password used to generate the wallet.
- `keystore and truststore type` - SSO or PKCS12.
- `keystore and truststore file` - `cwallet.sso` (if store type is SSO), `ewallet.p12` (if store type is PKCS12).

Depending on the type of database and the choice of method for authentication, you can provide the necessary information with `RCUDbInfo` in the model.

#### ATP database

For example, to use the Oracle Autonomous Transaction Processing Cloud Database for a JRF domain, specify the following information in the model:

```yaml
domainInfo:
    RCUDbInfo:
        databaseType : 'ATP'
        rcu_prefix : DEV
        rcu_admin_password: <database admin password is required only when you specify -run_rcu flag>
        rcu_schema_password : <RCU schema password>
        rcu_db_user : admin
        tns.alias : <tns alias name. e.g. dbname_tp>
        javax.net.ssl.keyStorePassword : <atp wallet password when generating the wallet from Oracle Cloud Console>
        javax.net.ssl.trustStorePassword : <atp wallet password when generating the wallet from Oracle Cloud Console>
        oracle.net.tns_admin: <optional: absolute path of the unzipped wallet root directory (outside of the archive), if the wallet.zip is not included in the archive>
```
The database wallet can be included in the archive file under `atpwallet` zipentry structure

`atpwallet/Walletxyz.zip`

Or, by specifying the unzipped root directory of the ATP wallet ZIP file in `oracle.net.tns_admin`.

**Note: Prior to release 0.23, the `useATP` flag only accepts values of `0`, `1`, `true`, or `false`.**

#### SSL database using SSO for authentication

For an Oracle SSL database with TW0_WAY SSL enabled, with an `SSO` wallet, use the following example:
```yaml
domainInfo:
    RCUDbInfo:
      databaseType : 'SSL'
      rcu_db_conn_string: <required URL string for use with -run_rcu>
      rcu_prefix : DEV
      rcu_admin_password: <required with -run_rcu flag>
      rcu_schema_password: <required with -run_rcu flag>
      tns.alias: <alias of ssl db in the tnsnames.ora file>
      javax.net.ssl.keyStore: <keystore found in unzipped wallet, i.e. cwallet.sso>
      javax.net.ssl.keyStoreType: SSO
      javax.net,ssl.trustStore: <truststore found in unzipped wallet, i.e cwallet.sso>
      javax.net.ssl.trustStoreType: SSO
      oracle.net.tns_admin: <absolute path of the unzipped wallet root directory>

```

For an Oracle SSL database with ONE_WAY SSL enabled, with an `SSO` wallet, use the following example:
```yaml
domainInfo:
    RCUDbInfo:
      databaseType : 'SSL'
      rcu_db_conn_string: <required URL string for use with -run_rcu>
      rcu_prefix : DEV
      rcu_admin_password: <required with -run_rcu flag>
      rcu_schema_password: <required with -run_rcu flag>
      tns.alias: <alias of ssl db in the tnsnames.ora file>
      javax.net,ssl.trustStore: <truststore found in unzipped wallet, i.e cwallet.sso>
      javax.net.ssl.trustStoreType: SSO
      oracle.net.tns_admin: <absolute path of the unzipped wallet root directory>

```

#### SSL database using PKCS12 for authentication

For an Oracle SSL database with TW0_WAY SSL enabled, with a `PKCS12` wallet, use the following example:
```yaml
domainInfo:
    RCUDbInfo:
      databaseType : 'SSL'
      rcu_db_conn_string: <required URL string for use with -run_rcu>
      rcu_prefix : DEV
      rcu_admin_password: <required with -run_rcu flag>
      rcu_schema_password: <required with -run_rcu flag>
      tns.alias: <alias of ssl db in the tnsnames.ora file>
      javax.net.ssl.keyStore: <keystore found in the unzipped wallet, i.e. ewallet.p12>
      javax.net.ssl.keyStoreType: PKCS12
      javax.net.ssl.keyStorePassword: <keystore password>
      javax.net.ssl.trustStore: <truststore found in the unzipped wallet, i.e ewallet.p12>
      javax.net.ssl.trustStoreType: PKCS12
      javax.net.ssl.trustStorePassword: <password of the truststore>
      oracle.net.tns_admin: <absolute path of the unzipped wallet root directory>

```
For an Oracle SSL database with ONE_WAY SSL enabled, with a `PKCS12` wallet, use the following example:
```yaml
domainInfo:
    RCUDbInfo:
      databaseType : 'SSL'
      rcu_db_conn_string: <required URL string for use with -run_rcu>
      rcu_prefix : DEV
      rcu_admin_password: <required with -run_rcu flag>
      rcu_schema_password: <required with -run_rcu flag>
      tns.alias: <alias of ssl db in the tnsnames.ora file>
      javax.net.ssl.trustStore: <truststore found in the unzipped wallet, i.e ewallet.p12>
      javax.net.ssl.trustStoreType: PKCS12
      javax.net.ssl.trustStorePassword: <password of the truststore>
      oracle.net.tns_admin: <absolute path of the unzipped wallet root directory>

```
When using a PKCS12 wallet, you must include the Oracle PKI provider to access your wallet. Add the Oracle PKI provider to your Java `java.security` file. For more information, see Section 2.2.4 "How can Oracle wallets be used in Java" in [SSL with Oracle JDBC Thin Driver](https://www.oracle.com/technetwork/topics/wp-oracle-jdbc-thin-ssl-130128.pdf).

### Access a database without using a wallet (non wallet-based access)

For a typical database, use the following example:

```yaml
domainInfo:
    RCUDbInfo:
        rcu_prefix : DEV
        # Optional rcu_db_user for creating RCU schema if -run_rcu flag is specified. Default user is SYS if not specified.
        # This user must have SYSDBA privilege and this is the equivalent of -dbUser in the RCU utility.
        rcu_db_user: superuser
        rcu_schema_password : <rcu schema password, will be prompted if not specified>
        rcu_admin_password : <database admin password is required only when you specify -run_rcu flag, will be prompted
         if not specified>
        rcu_db_conn_string : dbhost:1521/pdborcl
```        

### Specify variables for RCU

RCU `-variables` option of the repository creation utility can now be included in the `RCUDbInfo` section with the key `rcu_variables`:

```yaml
domainInfo:
    RCUDbInfo:
        rcu_variables : xxxx
```    

### Specify extended XML files for RCU

When creating a domain using WDT and the `-run_rcu` option, you can specify your extended XML files in the `RCUDbInfo` section.

This correlates to the `createRepository` and `dropRepository` command-line arguments `RCU -compInfoXMLLocation <file path> -storageXMLLocation <file path>`.

Include your XML files in your archive file using the location `wlsdeploy/rcu/config`. Then include this relative location in the `RCUDbInfo` section of the model.

```yaml
domainInfo:
    RCUDbInfo:
        compInfoXMLLocation: wlsdeploy/rcu/config/MyComponentInfo.xml
        storageXMLLocation: wlsdeploy/rcu/config/MyStorage.xml
```

### Advanced JRF database use cases

In the following examples of the JRF data source sparse model, you can use it to further customize the JRF domain template data sources.

#### Default template data source

This is a sparse model for JRF data sources with the RCU prefix `FMW1`.  
You will need to update at least the `URL`, `PasswordEncrypted`, and the `user` property value.  When you specify the value of `URL`, it 
must be a valid `JDBC URL` format, which is different from the `rcu_db_conn_string` which does not require the `jdbc:oracle:thin:...` part. 

```yaml
resources:
   JDBCSystemResource:
        WLSSchemaDataSource:
            JdbcResource:
                JDBCConnectionPoolParams:
                    TestTableName: SQL ISVALID
                    MaxCapacity: 75
                JDBCDataSourceParams:
                    GlobalTransactionsProtocol: None
                    JNDIName: jdbc/WLSSchemaDataSource
                JDBCDriverParams:
                    URL: --FIX ME--
                    PasswordEncrypted: --FIX ME--
                    DriverName: oracle.jdbc.OracleDriver
                    Properties:
                        user:
                            Value: FMW1_WLS_RUNTIME
        LocalSvcTblDataSource:
            Target: admin-server
            JdbcResource:
                JDBCConnectionPoolParams:
                    InitialCapacity: 0
                    CapacityIncrement: 1
                    TestConnectionsOnReserve: true
                    ConnectionCreationRetryFrequencySeconds: 10
                    TestTableName: SQL ISVALID
                    TestFrequencySeconds: 300
                    SecondsToTrustAnIdlePoolConnection: 0
                    MaxCapacity: 200
                JDBCDataSourceParams:
                    GlobalTransactionsProtocol: None
                    JNDIName: jdbc/LocalSvcTblDataSource
                JDBCDriverParams:
                    URL: --FIX ME--
                    PasswordEncrypted: --FIX ME--
                    DriverName: oracle.jdbc.OracleDriver
                    Properties:
                        user:
                            Value: FMW1_STB
                        oracle.net.CONNECT_TIMEOUT:
                            Value: '10000'
                        SendStreamAsBlob:
                            Value: 'true'
                        weblogic.jdbc.crossPartitionEnabled:
                            Value: 'true'
        opss-data-source:
            Target: cluster-1,admin-server
            JdbcResource:
                JDBCConnectionPoolParams:
                    TestTableName: SQL ISVALID
                JDBCDataSourceParams:
                    GlobalTransactionsProtocol: None
                    JNDIName: jdbc/OpssDataSource
                JDBCDriverParams:
                    URL: --FIX ME--
                    PasswordEncrypted: --FIX ME--
                    DriverName: oracle.jdbc.OracleDriver
                    Properties:
                        user:
                            Value: FMW1_OPSS
        opss-audit-viewDS:
            Target: cluster-1,admin-server
            JdbcResource:
                JDBCConnectionPoolParams:
                    TestTableName: SQL ISVALID
                JDBCDataSourceParams:
                    GlobalTransactionsProtocol: None
                    JNDIName: jdbc/AuditViewDataSource
                JDBCDriverParams:
                    URL: --FIX ME--
                    PasswordEncrypted: --FIX ME--
                    DriverName: oracle.jdbc.OracleDriver
                    Properties:
                        user:
                            Value: FMW1_IAU_VIEWER
        opss-audit-DBDS:
            Target: cluster-1,admin-server
            JdbcResource:
                JDBCConnectionPoolParams:
                    TestTableName: SQL ISVALID
                JDBCDataSourceParams:
                    GlobalTransactionsProtocol: None
                    JNDIName: jdbc/AuditAppendDataSource
                JDBCDriverParams:
                    URL: --FIX ME--
                    PasswordEncrypted: --FIX ME--
                    DriverName: oracle.jdbc.OracleDriver
                    Properties:
                        user:
                            Value: FMW1_IAU_APPEND
        mds-owsm:
            Target: cluster-1,admin-server
            JdbcResource:
                JDBCConnectionPoolParams:
                    InitialCapacity: 0
                    TestConnectionsOnReserve: true
                    ConnectionCreationRetryFrequencySeconds: 10
                    TestTableName: SQL ISVALID
                    TestFrequencySeconds: 300
                    SecondsToTrustAnIdlePoolConnection: 0
                JDBCDataSourceParams:
                    GlobalTransactionsProtocol: None
                    JNDIName: jdbc/mds/owsm
                JDBCDriverParams:
                    URL: --FIX ME--
                    PasswordEncrypted: --FIX ME--
                    DriverName: oracle.jdbc.OracleDriver
                    Properties:
                        user:
                            Value: FMW1_MDS
                        oracle.net.CONNECT_TIMEOUT:
                            Value: '120000'
                        SendStreamAsBlob:
                            Value: 'true'
```


#### Oracle Active Grid Link Data Source (AGL)

For setting the data source to access Oracle Active Grid Link database, besides updating the `URL`, `PasswordEncrypted`, and the `user` property value; 
you can specify additional `JDBCOracleParams` under `JdbcResource` of each data source.  For example,

```yaml
      mds-owsm:
            Target: cluster-1,admin-server
            JdbcResource:
              JDBCOracleParams:
                OnsNodeList:  'node1, node2'
                ....
```

For the complete list of fields, run the WDT command, 

```shell
modelHelp.sh -oracle_home <oracle home> resources:/JDBCSystemResource/JdbcResource/JDBCOracleParams
```


#### Multi Data Sources

If your database does not support high availability natively, such as RAC or AGL, then WebLogic provides a Multi Data Source option, where basically the main data source is a logical data source that
contains multiple physical data sources.   In order to create a spare model, for each data source, you can:

1. Update the templated data source `URL`, `EncryptedPassword`, and 'user' property value.  In the `URL` part, you can specify one of the accessible physical database URL.
2. Duplicate each datasource two times.
3. Change the duplicated data source name, `JNDIName` by appending `-1`, `-2`, and such. The `-1`, `-2` data sources are the physical data source; you will need to update their `URL` too.

For example (note: details replaced by `....` for easier reading):

```yaml
       opss-data-source:
           ....
                JDBCDriverParams:
                    URL: jdbc:oracle:thin://@somewhere:1521/db-node1
                    PasswordEncrypted:  'actualpassword`
           .... 
       'opss-data-source-1':
           ....
               JDBCDataSourceParams:
                 GlobalTransactionsProtocol: None
                 JNDIName: jdbc/OpssDataSource-2
                JDBCDriverParams:
                    URL: jdbc:oracle:thin://@somewhere:1521/db-node1
                    PasswordEncrypted:  'actualpassword`
           ....
       'opss-data-source-2':
          ....
           JDBCDataSourceParams:
             GlobalTransactionsProtocol: None
             JNDIName: jdbc/OpssDataSource-2
           JDBCDriverParams:
             URL: jdbc:oracle:thin://@somewhere:1521/db-node2
             PasswordEncrypted:  'actualpassword`
             DriverName: oracle.jdbc.OracleDriver
           ....
```


4. Update the original data source to include the physical data source list.

For example,

```yaml
       opss-data-source:
           ....
            JDBCDataSourceParams:
              DataSourceList:  'opss-data-source-1, opss-data-source-2'
              AlgorithmType:  'FailOver'
           ....
```


For the complete list of fields, run the WDT command,

```shell
modelHelp.sh -oracle_home <oracle home> resources:/JDBCSystemResource/JdbcResource/JDBCOracleParams
```

