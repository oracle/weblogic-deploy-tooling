## Specifying RCU connection information in the model

During creation or updating a domain. There is new section RCUDbInfo in the model under domainInfo section for specifying RCU database connection information without using the command line options -rcu_database and -rcu_prefix.  This is created to support database where the connection string is more complicated and requires extra options.

For example, in order to use Oracle Autonomous Transaction Processing Cloud Database for the JRF domain, specify the following information in the model:

```yaml
domainInfo:
    RCUDbInfo:
        useATP : 1
        rcu_prefix : DEV
        rcu_schema_password : xxxxx
        rcu_admin_user : admin
        tns.alias : dbatp_tp
        javax.net.ssl.keyStorePassword : xxxx
        javax.net.ssl.trustStorePassword : xxxx
```           
The database wallet can be included in the archive file under atpwallet/ structure

atpwallet/Walletxyz.zip
        
Using createDomain tool with the -run_rcu flag will create the rcu schemas against the ATP database and configure the JRF domain
with the ATP database.  For example:

    weblogic-deploy/bin/updateDomain.sh -oracle_home /u01/wls12213 -domain_type JRF -domain_home /u01/data/domains/demodomain -archive_file DemoDomain.zip -run_rcu 

For non-ATP database, use the following example:

```yaml
domainInfo:
    RCUDbInfo:
        useATP : 0
        rcu_prefix : DEV
        rcu_schema_password : xxxxx
        rcu_admin_password : xxxx
        rcu_db_conn_string : 'dbhost:1521/pdborcl'
```        
Specifying RCU variables to the repository creation utility can now be included in the RCUDbInfo section with the key:

```yaml
domainInfo:
    RCUDbInfo:
        rcu_variables : 'xxxx'
```    
        
        
