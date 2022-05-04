---
title: "Encrypt Model Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 5
description: "Encrypts the passwords in a model (or its variable file) using a user-provided passphrase."
---


{{% notice note %}} To meet Oracle's security standards, the encryption algorithms require JDK 8 to run.
{{% /notice %}}

Models contain WebLogic Server domain configuration.  Certain types of resources and other configurations require passwords; for example, a JDBC data source requires the password for the user establishing the database connection.  When creating or configuring a resource that requires a password, that password must be specified either in the model directly or in the variable file.  Clear-text passwords are not conducive to storing configurations as source, so the Encrypt Model Tool gives the model author the ability to encrypt the passwords in the model and variable file using passphrase-based, reversible encryption.  When using a tool with a model containing encrypted passwords, the encryption passphrase must be provided, so that the tool can decrypt the password in memory to set the necessary WebLogic Server configuration (which supports its own encryption mechanism based on a domain-specific key).  While there is no requirement to use the WebLogic Deploy Tooling encryption mechanism, it is highly recommended because storing clear-text passwords on disk is never a good idea.

The Create, Update and Deploy tools can take a set of models. The Encrypt model will encrypt a set of models. Each model is encrypted using the same passphrase and written back to its original location.

{{% notice note %}} WebLogic Deploy Tooling also supports the use of domain-encrypted passwords directly in the model. The Encrypt Model Tool should not be used in tandem with this method.
{{% /notice %}}

Start with the following example model:

```yaml
domainInfo:
    AdminUserName: weblogic
    AdminPassword: welcome1
    ServerStartMode: prod
topology:
    Name: DemoDomain
    AdminServerName: AdminServer
    Cluster:
        mycluster:
    Server:
        AdminServer:
            ListenAddress: 192.168.1.50
            ListenPort: 7001
            Machine: machine1
        m1:
            ListenAddress: 192.168.1.50
            ListenPort: 8001
            Cluster: mycluster
            Machine: machine1
        m2:
            ListenAddress: 192.168.1.51
            ListenPort: 8001
            Cluster: mycluster
            Machine: machine2
    Machine:
        machine1:
            NodeManager:
                ListenAddress: 192.168.1.50
                ListenPort: 5556
        machine2:
            NodeManager:
                ListenAddress: 192.168.1.51
                ListenPort: 5556
    SecurityConfiguration:
        NodeManagerUsername: weblogic
        NodeManagerPasswordEncrypted: welcome1
    RestfulManagementServices:
        Enabled: true
    Security:
        Group:
            FriscoGroup:
                Description: The WLS Deploy development group
        User:
            Robert:
                Password: welcome1
                GroupMemberOf: [ Administrators, FriscoGroup ]
            Derek:
                Password: welcome1
                GroupMemberOf: 'Administrators, FriscoGroup'
            Richard:
                Password: welcome1
                GroupMemberOf: [ FriscoGroup ]
            Carolyn:
                Password: welcome1
                GroupMemberOf: FriscoGroup
            Mike:
                Password: welcome1
                GroupMemberOf: FriscoGroup
            Johnny:
                Password: welcome1
                GroupMemberOf: FriscoGroup
            Gopi:
                Password: welcome1
                GroupMemberOf: FriscoGroup
```

To run the Encrypt Model Tool on the model, run the following command:

    $ weblogic-deploy\bin\encryptModel.cmd -oracle_home c:\wls12213 -model_file UnencryptedDemoDomain.yaml

The tool will prompt for the encryption passphrase twice and then encrypt any passwords it finds in the model, skipping any password fields that have variable values, to produce a result that looks like the following model. You can bypass the stdin prompt with two other options. Store the passphrase in an environment variable, and use the environment variable name with command-line option `-passphrase_env`. Another option is to create a file containing the passphrase value. Pass this filename using the command-line option `-passphrase_file`.

```yaml
domainInfo:
    AdminUserName: weblogic
    AdminPassword: '{AES}a0dacEQ4Q2JnTmI4VHp5NjIzVHNPRFg5ZjRiVDJ4NzU6T1M0SGYwM2xBeHdRdHFWVTpWZEh6bkd4NzZSQT0='
    ServerStartMode: prod
topology:
    Name: DemoDomain
    AdminServerName: AdminServer
    Cluster:
        mycluster:
    Server:
        AdminServer:
            ListenAddress: 192.168.1.50
            ListenPort: 7001
            Machine: machine1
        m1:
            ListenAddress: 192.168.1.50
            ListenPort: 8001
            Cluster: mycluster
            Machine: machine1
        m2:
            ListenAddress: 192.168.1.51
            ListenPort: 8001
            Cluster: mycluster
            Machine: machine2
    Machine:
        machine1:
            NodeManager:
                ListenAddress: 192.168.1.50
                ListenPort: 5556
        machine2:
            NodeManager:
                ListenAddress: 192.168.1.51
                ListenPort: 5556
    SecurityConfiguration:
        NodeManagerUsername: weblogic
        NodeManagerPasswordEncrypted: '{AES}WndJQWNySWpoY0VEbFpmR2V1RFhvamVFdGwzandtaFU6L1d4V0dPRFpsaXJIUkl2djpQdUdLaTloR1IxTT0='
    RestfulManagementServices:
        Enabled: true
    Security:
        Group:
            FriscoGroup:
                Description: The WebLogic Deploy development group
        User:
            Robert:
                Password: '{AES}VFIzVmdwcWNLeHBPaWhyRy82VER6WFV6aHRPbGcwMjQ6bS90OGVSTnJxWTIvZjkrRjpjSzBQUHlOWWpWTT0='
                GroupMemberOf: [ Administrators, FriscoGroup ]
            Derek:
                Password: '{AES}R1BTM21ZSkxpdTNIZjNqcTlsSC9PeHV4aXJoT3kxazM6M1dLOXBLeCtlc1lsVDUrWjo5VitHZUxCcjZnOD0='
                GroupMemberOf: 'Administrators, FriscoGroup'
            Richard:
                Password: '{AES}Y3FkQmRIRGhjZEtlRjVkVVdLQU1Eb09LWDIzMlhUWVo6MjllVExsMmNmNzJzZDFjaTpNcVNDbUs2cnRFRT0='
                GroupMemberOf: [ FriscoGroup ]
            Carolyn:
                Password: '{AES}cW8wczJqZXJZOHVsTGNOTmlqTGpuZGFoSkY2ME5WbTk6c0VaWGs1ME5pemlKdC9wajpFaTJPRS9ZQlcvND0='
                GroupMemberOf: FriscoGroup
            Mike:
                Password: '{AES}cnF6Z3JOVWcvc0czN3JVb1g5T2FidmRsSU51anJCa0Y6UlBsNVFsOFlXU29xUlY1aDp3VWZWYU5VOVRkMD0='
                GroupMemberOf: FriscoGroup
            Johnny:
                Password: '{AES}UWJ5Y25Ma2RHTkNMVTZ1RnlhRkNaTUxXaXV4SjBjaWg6citwTDQvelN1aUlPdnZaSDpCMEdSWGg2ZlVJUT0='
                GroupMemberOf: FriscoGroup
            Gopi:
                Password: '{AES}MWJGcnhtZlNyWXVrU1VXMVFxZFEvQThoS1hPN2FQdDc6MmRPaUF2Y1FCQ3VIK3MydDpZaFR5clBrN1FjOD0='
                GroupMemberOf: FriscoGroup
```

If the model stores passwords in the variables file, like the following model:

```yaml
resources:
    JDBCSystemResource:
        Generic1:
            Target: mycluster
            JdbcResource:
              JDBCDataSourceParams:
                  JNDIName: [ jdbc/generic1 ]
                  GlobalTransactionsProtocol: TwoPhaseCommit
              JDBCDriverParams:
                  DriverName: oracle.jdbc.xa.client.OracleXADataSource
                  URL: 'jdbc:oracle:thin:@//@@PROP:db.url@@'
                  PasswordEncrypted: '@@PROP:db.password@@'
                  Properties:
                      user:
                          Value: '@@PROP:db.user@@'
                      oracle.net.CONNECT_TIMEOUT:
                          Value: 5000
                      oracle.jdbc.ReadTimeout:
                          Value: 30000
              JDBCConnectionPoolParams:
                  InitialCapacity: 3
                  MaxCapacity: 15
                  TestTableName: SQL ISVALID
                  TestConnectionsOnReserve: true
    MailSession:
        MyMailSession:
            JNDIName: mail/MyMailSession
            Target: mycluster
            SessionUsername: john.smith@example.com
            SessionPasswordEncrypted: '@@PROP:mymailsession.password@@'
            Properties:
                mail.store.protocol: imap
                mail.imap.port: 993
                mail.imap.ssl.enable: true
                mail.imap.starttls.enable: true
                mail.imap.host: imap.example.com
                mail.impa.auth: true
                mail.transport.protocol: smtp
                mail.smtp.starttls.enable: true
                mail.smtp.port: 465
                mail.smtp.ssl.enable: true
                mail.smtp.auth: true
                mail.smtp.host: smtp.example.com
```

Run the Encrypt Model Tool and pass both the model and variable files, like this:

    $ weblogic-deploy\bin\encryptModel.cmd -oracle_home c:\wls12213 -model_file UnencryptedDemoDomain.yaml -variable_file UnencryptedDemoDomain.properties

The variable file will now look something like the following:

    #Variables updated after encryption
    #Thu Feb 01 19:12:57 CST 2018
    db.user=rpatrick
    db.url=mydb.example.com:1539/PDBORCL
    db.password={AES}czFXMkNFWNG9jNTNYd0hRL2R1anBnb0hDUlp4K1liQWFBdVM4UTlvMnE0NU1aMUZ5UVhiK25oaWFBc2lIQ20\=
    mymailsession.password={AES}RW9nRnUzcE41WGNMdnEzNDdRQVVNWm1LMGhidkFBVXg6OUN3aXcyci82cmh3cnpNQTpmY2UycUp5YWl4UT0\=

### Parameter table for `encryptModel`
| Parameter | Definition | Default |
| ---- | ---- | ---- |
| `-manual` | Run without a model and get an encrypted value for a single password. |    |
| `-model_file` | The location of the model file or a set of model files. |    |
| `-oracle_home` | Home directory of the Oracle WebLogic installation. Required if the `ORACLE_HOME` environment variable is not set. |    |
| `-passphrase_env` | An alternative to entering the encryption passphrase at a prompt. The value is an environment variable name that WDT will use to retrieve the passphrase. |    |
| `-passphrase_file` | An alternative to entering the encryption passphrase at a prompt. The value is a the name of a file with a string value which WDT will read to retrieve the passphrase. |    |
| `-variable_file` | The location and name of the property file containing the variable values for all variables used in the model(s). |    |
