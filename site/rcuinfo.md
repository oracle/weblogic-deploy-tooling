## Specifying RCU connection information in the model

During creating or updating a domain, there is new section `RCUDbInfo` in the model, under the `domainInfo` section, for specifying RCU database connection information without using the command-line arguments `-rcu_db` and `-rcu_prefix`. Use this to support a database where the connection string is more complex and requires extra options.

For example, in order to use the Oracle Autonomous Transaction Processing Cloud Database for the JRF domain, specify the following information in the model:

```yaml
domainInfo:
    RCUDbInfo:
        useATP : true
        rcu_prefix : DEV
        rcu_schema_password : xxxxx
        rcu_admin_user : admin
        tns.alias : dbatp_tp
        javax.net.ssl.keyStorePassword : xxxx
        javax.net.ssl.trustStorePassword : xxxx
```           
The database wallet can be included in the archive file under `atpwallet` zipentry structure

`atpwallet/Walletxyz.zip`
        
Using the Create Domain Tool with the `-run_rcu` flag will create the RCU schemas against the Oracle Autonomous Transaction Processing Cloud Database and configure the datasources in the JRF domain to use the database.  For example:

    weblogic-deploy/bin/updateDomain.sh -oracle_home /u01/wls12213 -domain_type JRF -domain_home /u01/data/domains/demodomain -archive_file DemoDomain.zip -run_rcu 

For a non-ATP database, use the following example:

```yaml
domainInfo:
    RCUDbInfo:
        rcu_prefix : DEV
        rcu_schema_password : xxxxx
        rcu_admin_password : xxxx
        rcu_db_conn_string : 'dbhost:1521/pdborcl'
```        
RCU `-variables` option of the repository creation utility can now be included in the `RCUDbInfo` section with the key `rcu_variables`:

```yaml
domainInfo:
    RCUDbInfo:
        rcu_variables : 'xxxx'
```    

**Note: Prior to release 0.23, the useATP flag only accepts values of 0, 1, 'true' or 'false'.**
