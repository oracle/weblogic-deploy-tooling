## Specifying RCU connection information in the model

During creating or updating a domain, there is new section `RCUDbInfo` in the model, under the `domainInfo` section, for specifying RCU database connection information without using the command-line arguments `-rcu_db` and `-rcu_prefix`. Use this to support a database where the connection string is more complex and requires extra options.

For example, in order to use the Oracle Autonomous Transaction Processing Cloud Database for the JRF domain, specify the following information in the model:

```yaml
domainInfo:
    RCUDbInfo:
        useATP : true
        rcu_prefix : DEV
        rcu_admin_password: <database admin password is required only when you specify -run_rcu flag, will be prompted
         if not specified>
        rcu_schema_password : <RCU schema password, user will be prompted if not specified>
        atp.admin.user : admin
        tns.alias : dbatp_tp
        javax.net.ssl.keyStorePassword : <atp wallet password>
        javax.net.ssl.trustStorePassword : <atp wallet password>
        oracle.net.tns_admin: <optional: unzipped wallet root directory, if the wallet.zip is not included in the archive>
```           
The database wallet can be included in the archive file under `atpwallet` zipentry structure

`atpwallet/Walletxyz.zip`

or by specifying the unzipped root directory of the ATP wallet zip file in `oracle.net.tns_admin`.
     
Using the Create Domain Tool with the `-run_rcu` flag will create the RCU schemas against the Oracle Autonomous Transaction Processing Cloud Database and configure the datasources in the JRF domain to use the database.  For example:

    weblogic-deploy/bin/createDomain.sh -oracle_home /u01/wls12213 -domain_type JRF -domain_home /u01/data/domains/demodomain -archive_file DemoDomain.zip -run_rcu 

For a non-ATP database, use the following example:

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
        rcu_db_conn_string : 'dbhost:1521/pdborcl'
```        
RCU `-variables` option of the repository creation utility can now be included in the `RCUDbInfo` section with the key `rcu_variables`:

```yaml
domainInfo:
    RCUDbInfo:
        rcu_variables : 'xxxx'
```    

**Note: Prior to release 0.23, the useATP flag only accepts values of 0, 1, 'true' or 'false'.**

When creating a domain using WDT and the -run_rcu option, you can specify your extended XML files in the RCUDbInfo section. 

This correlates to the `createRepository` and `dropRepository` command line arguments `RCU -compInfoXMLLocation <file path> -storageXMLLocation <file path>`

Include your XML files in your archive file using location `wlsdeploy/rcu/config`. Then include this relative location in the RCUDbInfo section of the model.

```yaml
domainInfo:
    RCUDbInfo:
        compInfoXMLLocation: 'wlsdeploy/rcu/config/MyComponentInfo.xml'
        storageXMLLocation: 'wlsdeploy/rcu/config/MyStorage.xml'
```
