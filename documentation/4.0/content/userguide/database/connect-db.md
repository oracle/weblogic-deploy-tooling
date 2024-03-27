---
title: "Connect to a database"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 5
description: "Create a connection to access your database."
---

### Specifying RCU connection information in the model

When creating a JRF domain, you can provide all the RCU connection information in a section `RCUDbInfo` under the 
`domainInfo` section in the model.


### Background on JRF domain RCU tables

A JRF domain creates several data sources from the JRF domain template.

| Data source name        | JNDI name                  | Schema             | Target                   |
|-------------------------|----------------------------|--------------------|--------------------------|
| WLSSchemaDataSource     | jdbc/WLSSchemaDataSource   | prefix_WLS_RUNTIME | None                     |
| LocalSvcTblDataSource   | jdbc/WLSSchemaDataSource   | prefix_STB         | admin server             |
| opss-data-source        | jdbc/OpssDataSource        | prefix_OPSS        | admin server and cluster |
| opss-audit-viewDS       | jdbc/AuditViewDataSource   | prefix_IAU_VIEWER  | admin server and cluster |
| opss-audit-DBDS         | jdbc/AuditAppendDataSource | prefix_IAU_APPEND  | admin server and cluster |
| mds-owsm                | jdbc/mds/owsm              | prefix_MDS         | admin server and cluster |

By default, the JRF domain template data source has only the default information such as URL and schema with the
default prefix `DEV`.  During domain creation,  WDT will use the information you provided in the `RCUDbinfo` section to
override the default values from the template so that it can connect to the database you specified.

For some advanced use cases, such as using an Oracle Active GridLink data source or Multi Data Sources, you can provide
a sparse model of the data sources in a separate model file during domain creation.  See [Advance use cases](#advanced-jrf-database-use-cases).

### Creating a new domain to connect to an existing RCU schema

If you ever find a situation where your JRF domain home directory is corrupted or lost, it is possible to create a new
domain home directory using the existing RCU schemas provided that you have previously exported the domain's encryption
key into an Oracle wallet.  To export the encryption key into a wallet, use the OPSS WLST offline [exportEncryptionKey](https://docs.oracle.com/en/middleware/fusion-middleware/platform-security/12.2.1.4/idmcr/security_wlst.html#GUID-3EF2815D-45B9-46EE-A4D7-34A6841195DB)
function.

When you want to recreate the JRF domain home, you have two options:

1. Use the Create Domain tool's `-opss_wallet <path-to-wallet-file>` argument and one of the following arguments to pass
  the wallet passphrase:

   - `-opss_wallet_passphrase_env <environment-variable-name>` - Simply pass the name of the environment variable to read
     to get the wallet passphrase.
   - `-opss_wallet_passphrase_file <path-to-file>` - Simply pass the file name for the file containing the wallet passphrase.

2. Add the OPSS wallet to the archive file in the prescribed location (i.e., `wlsdeploy/opsswallet/`) using the Archive
   Helper tool's `add opssWallet` command and then provide the passphrase in the `domainInfo` section's `OPSSWalletPassphrase` field.

    ```yaml
    domainInfo:
        OPSSWalletPassphrase: MySecureOPSSWalletPassphrase
    ```

### Using wallets to access the RCU database

The term `wallet` can refer to either an Oracle PKI-created wallet file such as `cwallet.sso` or `ewallet.p12` or a bundle
of files used to establish the database connection such as the contents of the ZIP file downloaded from an OCI ATP database.
In WDT, the term `wallet` is simply a location where one or more files related to connecting to the database can be stored.

The Archive Helper Tool supports adding database wallets to the archive using the `add databaseWallet -wallet_name <name>`.
The standard name of the wallet used for the RCU database is `rcu` and the Archive Helper Tool provides a shortcut for adding
the files by using the `add rcuWallet` command.  WDT supports adding one or more files to an archive-stored wallet directory
by:

- Adding one or more files directly, or
- Adding a single ZIP file containing the files (such as one downloaded from an ATP database).

If the archive wallet contains a single ZIP file, the ZIP file will be automatically extracted when WDT extracts it from
the archive file.

Please obtain the necessary wallet file(s) from your DBA.

### Using a tnsnames.ora file instead of the database connection string

When accessing an Oracle database for the RCU schemas, you can use a `tnsnames.ora` file to specify the database connection string.
Instead of specifying the `rcu_db_conn_string` explicitly, do one of the following:

1. Place the `tnsnames.ora` file in the `rcu` wallet inside the archive file, or
2. Set the `oracle.net.tns_admin` attribute to point to the path to the directory where the `tnsnames.ora` file resides.  
   This may either be a relative path from the domain directory (which may be the path into the archive such as 
   `config/wlsdeploy/dbWallets/myWallet`) or an absolute path.

In both cases, the `tns.alias` attribute must be set.  The `tns.alias` is the network service name of an entry inside the
`tnsnames.ora` file.  The alias is on the left side and the connect string is on the right side of the equals sign.

   ```text
   xxxx = (DESCRIPTION ...)
   yyyy = (DESCRIPTION ...)
   ...
   ```

WDT will parse the `tnsnames.ora` file to find the connect string that matches the specified `tns.alias` to obtain the RCU
database connect string.

### Access a database using SSL connections

When accessing an Oracle database using a TLS connection (such as an `oracle_database_connection_type` of ATP or SSL),
the database may use ONE_WAY or TWO_WAY (also known as mutual TLS or simply mTLS) SSL.  

For ONE_WAY SSL, the connection requires only a "trust store"; that is, a keystore that contains the Certificate Authority's
(CA) certificate used to sign the database server's certificate.  This trust store is used by the database client to determine
whether it trusts the certificate presented by the database server during the SSL handshake.

When using TWO_WAY SSL, the connection requires both a "trust store" and an "identity store"; that is, a certificate that
the database client presents to the database server during the SSL handshake.

In the `RCUDbInfo` section, the trust and identity stores are specified using the following attributes.

#### Trust Store
- `javax.net.ssl.trustStore`         - The key store file to use as the trust store.  This may be a relative path from
  the domain home (for example, the path into the archive such as `config/wlsdeploy/dbWallets/rcu/truststore.jks`) or
  the absolute path to the key store file.
- `javax.net.ssl.trustStoreType`     - The key store type (JKS, PKCS12, or SSO).
- `javax.net.ssl.trustStorePassword` - The passphrase used to open the key store file, if required. 

#### Identity Store
- `javax.net.ssl.keyStore`         - The key store file to use as the trust store.  This may be a relative path from
  the domain home (for example, the path into the archive such as `config/wlsdeploy/dbWallets/rcu/keystore.jks`) or the
  absolute path to the key store file.
- `javax.net.ssl.keyStoreType`     - The key store type (JKS, PKCS12, or SSO).
- `javax.net.ssl.keyStorePassword` - The passphrase used to open the key store file, if required.

Depending on the type of database and the SSL connection type, you can provide the necessary information
with `RCUDbInfo` in the model.

### Examples
The following examples represent how to specify the `RCUDbInfo` parameters for connecting to an RCU database.

#### ATP database
ATP databases can use either ONE_WAY or TWO_WAY SSL.  See the [Access a database using SSL connections](#access-a-database-using-ssl-connections)
for more details on which fields are relevant for your ATP database configuration.

For example, to use the Oracle Autonomous Transaction Processing Cloud Database for a JRF domain, specify the following
information in the model:

```yaml
domainInfo:
    RCUDbInfo:
        oracle_database_connection_type : 'ATP'
        rcu_db_conn_string: <URL string, optional if using tnsnames.ora>
        rcu_prefix : DEV
        rcu_admin_user : admin # only required when you specify the `-run_rcu` flag
        rcu_admin_password: <database admin password> # only required when you specify the `-run_rcu` flag
        rcu_schema_password : <RCU schema password>
        oracle.net.tns_admin: <optional path to the wallet directory containing the tnsnames.ora file>
        tns.alias : <alias of ATP db in the tnsnames.ora file>
        javax.net.ssl.keyStore: <archive path or absolute path to the identity key store if using mTLS>
        javax.net.ssl.keyStoreType: <the identity key store type (JKS, SSO, or PKCS12) if using mTLS>
        javax.net.ssl.keyStorePassword : <the identity key store password when generating the wallet from Oracle Cloud Console if using mTLS and not using an SSO wallet as the key store>
        javax.net.ssl.trustStore: <archive path or absolute path to the trust key store>
        javax.net.ssl.trustStoreType: <the trust key store type (JKS, SSO, or PKCS12)>
        javax.net.ssl.trustStorePassword : <the trust key store password when generating the wallet from Oracle Cloud Console if not using an SSO wallet as the trust key store>
```

The database wallet downloaded from the ATP database can be included in the archive file as a named entry (example uses
`rcu` as that name) under the`dbWallets` archive structure, either as a ZIP file:

`wlsdeploy/dbWallets/rcu/Walletxyz.zip`

or as the unzipped contents:

- `wlsdeploy/dbWallets/rcu/cwallet.sso`
- `wlsdeploy/dbWallets/rcu/ewallet.p12`
- `wlsdeploy/dbWallets/rcu/ewallet.pem`
- `wlsdeploy/dbWallets/rcu/keystore.jks`
- `wlsdeploy/dbWallets/rcu/ojdbc.properties`
- `wlsdeploy/dbWallets/rcu/sqlnet.ora`
- `wlsdeploy/dbWallets/rcu/tnsnames.ora`
- `wlsdeploy/dbWallets/rcu/truststore.jks`

At runtime, WDT will extract the files (if they are in a ZIP file) to `$DOMAIN_HOME/wlsdeploy/dbWallets/rcu/` so that they can be
referenced directly from the model using the normal relative path.  For example:

#### Oracle database using an SSL connection
Other Oracle databases can use either ONE_WAY or TWO_WAY SSL.  See the [Access a database using SSL connections](#access-a-database-using-ssl-connections)
for more details on which fields are relevant for your database configuration.

For an Oracle SSL database with TWO_WAY SSL enabled, with an `SSO` wallet, use the following example:
```yaml
domainInfo:
    RCUDbInfo:
      oracle_database_connection_type : 'SSL'
      rcu_db_conn_string: <URL string, optional if using tnsnames.ora>
      rcu_prefix : DEV
      rcu_admin_password: <required with -run_rcu flag>
      rcu_schema_password: <required>
      oracle.net.tns_admin: <optional path to the wallet directory containing the tnsnames.ora file>
      tns.alias: <alias of ssl db in the tnsnames.ora file>
      javax.net.ssl.keyStore: <path to the SSO wallet with the identity certificate; for example, config/wlsdeploy/dbWallets/rcu/cwallet.sso>
      javax.net.ssl.keyStoreType: SSO
      javax.net,ssl.trustStore: <path to the SSO wallet with the trust CA certificate; for example, config/wlsdeploy/dbWallets/rcu/cwallet.sso>
      javax.net.ssl.trustStoreType: SSO
```

For an Oracle SSL database with ONE_WAY SSL enabled, with an `SSO` wallet, use the following example:

```yaml
domainInfo:
    RCUDbInfo:
      databaseType : 'SSL'
      rcu_prefix : DEV
      rcu_db_conn_string: <URL string, optional if using tnsnames.ora>
      rcu_admin_password: <required with -run_rcu flag>
      rcu_schema_password: <required>
      oracle.net.tns_admin: <optional path to the wallet directory containing the tnsnames.ora file>
      tns.alias: <alias of ssl db in the tnsnames.ora file>
      javax.net,ssl.trustStore: <path to the SSO wallet with the trust CA certificate; for example, config/wlsdeploy/dbWallets/rcu/cwallet.sso>
      javax.net.ssl.trustStoreType: SSO
```

#### SSL database using Oracle PKI PKCS12 wallets

For an Oracle SSL database with TW0_WAY SSL enabled, with an Oracle PKI `PKCS12` wallet, use the following example:
```yaml
domainInfo:
    RCUDbInfo:
      databaseType : 'SSL'
      rcu_db_conn_string: <URL string, optional if using tnsnames.ora>
      rcu_prefix : DEV
      rcu_admin_password: <required with -run_rcu flag>
      rcu_schema_password: <required>
      oracle.net.tns_admin: <optional path to the wallet directory containing the tnsnames.ora file>
      tns.alias: <alias of ssl db in the tnsnames.ora file>
      javax.net.ssl.keyStore: <path to the PKCS12 keystore with the identity certificate; for example, config/wlsdeploy/dbWallets/rcu/ewallet.p12>
      javax.net.ssl.keyStoreType: PKCS12
      javax.net.ssl.keyStorePassword: <keystore password>
      javax.net.ssl.trustStore: <path to the PKCS12 keystore with the trust CA certificate; for example, config/wlsdeploy/dbWallets/rcu/ewallet.p12>
      javax.net.ssl.trustStoreType: PKCS12
      javax.net.ssl.trustStorePassword: <truststore password>

```
For an Oracle SSL database with ONE_WAY SSL enabled, with a `PKCS12` wallet, use the following example:
```yaml
domainInfo:
    RCUDbInfo:
      databaseType : 'SSL'
      rcu_db_conn_string: <URL string, optional if using tnsnames.ora>
      rcu_prefix : DEV
      rcu_admin_password: <required with -run_rcu flag>
      rcu_schema_password: <required>
      oracle.net.tns_admin: <optional path to the wallet directory containing the tnsnames.ora file>
      tns.alias: <alias of ssl db in the tnsnames.ora file>
      javax.net.ssl.trustStore: <truststore found in the unzipped wallet; for example, config/wlsdeploy/dbWallets/rcu/ewallet.p12>
      javax.net.ssl.trustStoreType: PKCS12
      javax.net.ssl.trustStorePassword: <password of the truststore>

```
When using an Oracle PKI-generated PKCS12 wallet, you must include the Oracle PKI provider to access your wallet.  Add the Oracle PKI provider to your Java `java.security` file. For more information, see Section 2.2.4 "How can Oracle wallets be used in Java" in [SSL with Oracle JDBC Thin Driver](https://www.oracle.com/technetwork/topics/wp-oracle-jdbc-thin-ssl-130128.pdf).

### Access a database without using a wallet

For a typical database, use the following example:

```yaml
domainInfo:
    RCUDbInfo:
        rcu_prefix : DEV
        # Optional rcu_admin_user for creating RCU schema if -run_rcu flag is specified. Default user is SYS if not specified.
        # This user must have SYSDBA privilege and this is the equivalent of -dbUser in the RCU utility.
        rcu_admin_user: superuser
        rcu_admin_password : <required with -run_rcu flag>
        rcu_schema_password : <rcu schema password>
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

Include your XML files in your archive file using the location `wlsdeploy/custom/rcu/config`. Then include this relative location in the `RCUDbInfo` section of the model.

```yaml
domainInfo:
    RCUDbInfo:
        compInfoXMLLocation: config/wlsdeploy/custom/rcu/config/MyComponentInfo.xml
        storageXMLLocation: config/wlsdeploy/custom/rcu/config/MyStorage.xml
```

### Advanced JRF database use cases

In the following examples of the JRF data source sparse model, you can use it to further customize the JRF domain template data sources.

#### Default template data source

For example, if you have created RCU schemas with different passwords for different schemas.  You can use a sparse model to create a domain with different passwords for different FMW data sources.

```yaml
domainInfo:
  RCUDbInfo:
    rcu_prefix : -- FIX ME --
    rcu_schema_password : -- FIX ME --
    rcu_db_conn_string : -- FIX ME --
resources:
  JDBCSystemResource:
    LocalSvcTblDataSource:
      JdbcResource:
        JDBCDriverParams:
          PasswordEncrypted: --FIX ME--
    opss-data-source:
      JdbcResource:
        JDBCDriverParams:
          PasswordEncrypted: --FIX ME--
    opss-audit-viewDS:
      JdbcResource:
        JDBCDriverParams:
          PasswordEncrypted: --FIX ME--
    opss-audit-DBDS:
      JdbcResource:
        JDBCDriverParams:
          PasswordEncrypted: --FIX ME--
    mds-owsm:
      JdbcResource:
        JDBCDriverParams:
          PasswordEncrypted: --FIX ME--   
```

This is a sparse model of the FMW data sources discovered from a FMW domain.  You can use any part of it to update your domain.  

```yaml

...

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
