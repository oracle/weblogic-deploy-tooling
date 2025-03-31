---
title: "Archive File"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 2
---


The archive file is used to deploy binaries and other file resources to the target domain. The archive is a ZIP file
with a specific directory structure.  Any file resources referenced in the model that are not already on the target
system must be stored in the correct location in the archive, and the model must reflect the path into the archive.

Note that file resources that already exist on the target system need not be included in the archive, provided that
the model specifies the correct location on the target system.

### Contents

- [Example](#example)
- [Archive structure](#archive-structure)
- [Using multiple archive files](#using-multiple-archive-files)

#### Example

This example shows an application with a `SourcePath` value referencing an EAR file resource contained in the archive.

```yaml
appDeployments:
    Application:
        simpleear:
            SourcePath: wlsdeploy/applications/simpleear.ear
            Target: my-cluster
            ModuleType: ear
```

The example shows the attribute `SourcePath` of the `simpleear` application with a value of
`wlsdeploy/applications/simpleear.ear`.  The prefix `wlsdeploy/` indicates that the resource is located in the archive
file in the specified location, and will be deployed to that directory in the domain, in this case
`<domain-home>/wlsdeploy/applications/simpleear.ear`.

### Archive structure

These are the paths within the archive that are used for different types of resources. You can create further
directory structures underneath some of these locations to organize the files and directories as you see fit.  The
[Archive Helper Tool]({{< relref "/userguide/tools/archive_helper.md" >}}) makes it easy to add, update, and remove entries from the archive file.  

#### Why are there two separate directory structures?

Starting in WDT 4.0, some types previously stored under the top-level `wlsdeploy` directory have been moved to the
`config/wlsdeploy` directory.  Anything stored in the archive under a location that begins with `config/wlsdeploy` will
end up inside the `$DOMAIN_HOME/config/wlsdeploy` directory.  This allows the files to benefit from standard WebLogic
Server behavior:

- The `pack` tool will include these files in the managed server template so that managed server directories created
  with the `unpack` tools will contain these files.
- On managed server startup, WebLogic Server will replicate any new/changed/removed files from the Administration
  Server to the managed server.

Because this file replication happens during managed server startup, that means placing very large files that are updated
under this location can slow down managed server startup times.  Most file types placed in this new `config/wlsdeploy` 
location are, by definition, small; for example, database wallets generally contain small text files like `tnsnames.ora`
and small binary files like `keystore.jks`.  The `custom` type is the only one that requires some thought and allows the
user to choose between the `config/wlsdeploy/custom` and `wlsdeploy/custom` locations.  

- The `config/wlsdeploy/custom` location allows the file or directory to be replicated to all managed servers.  This
  is ideal for situations like handling files that live outside an application or dynamically deploying custom security
  provider-related JAR files, which tend to be not be updated frequently.
- The `wlsdeploy/custom` location does not support replication of the contents.  This is ideal for storing large files
  that do not need to be included in `pack`-created templates or to be replicated to the managed servers, such as
  when deploying in Kubernetes with WebLogic Kubernetes Operator.

#### `config/wlsdeploy/coherence`
The root directory under which Coherence config files and/or empty directories for Coherence persistent stores.

#### `config/wlsdeploy/config`
The directory where a MIME mapping property file can be stored.

#### `config/wlsdeploy/custom`
This is the root directory where your custom files and directories can be stored and extracted from the archive. These
files are not collected by the Discover Domain Tool.   Every file resource under this directory is extracted during
`createDomain`, `updateDomain`, and `deployApps`.

Some custom files may belong in `wlsdeploy/custom`. To determine which location is preferable for your files, see [Why are there two separate directory structures?]({{< relref "#why-are-there-two-separate-directory-structures" >}}).

This location is particularly useful when handling files that live outside an application; for example, a property
file used to configure the application.  The general steps to make applications that use such files work when
provisioning them with WDT are:

1. Place the file in the required location inside the `config/wlsdeploy/custom` folder inside the archive; for example,
   `config/wlsdeploy/custom/com/mycompany/myapp/myapp-config.properties`.
2. Make sure the application is locating the file by `CLASSPATH`; for example, using
   `ClassLoader.getResourceAsStream("com/mycompany/myapp/myapp-config.properties")`.
3. Make sure that the server's CLASSPATH includes the `$DOMAIN_HOME/config/wlsdeploy/custom` directory.  One way to achieve
   this would be to add a `setUserOverrides.sh` that includes this directory in the `PRE_CLASSPATH` environment
   variable to the `wlsdeploy/domainBin` location in the archive file.  Don't forget to add `setUserOverrides.sh` to
   the `domainInfo/domainBin` of the model so that it gets extracted.

#### `config/wlsdeploy/dbWallets/<wallet-name>`

The directory where named database wallets can be stored for use with the Oracle database.  The `rcu` name is used as
the default location to store a wallet for RCU data sources.  The wallet placed into the archive can be either a ZIP
file or a set of one or more files.  If it is a ZIP file, that ZIP file will be expanded in place when running WDT
tools like the Create Domain or Update Domain tools.

#### `config/wlsdeploy/jms/foreignServer/<jms-foreign-server-name>`
The directory under which a JMS Foreign Server binding file is stored.

#### `config/wlsdeploy/nodeManager`
The root directory under which Node Manager keystore files are stored.

#### `config/wlsdeploy/scripts`
The root directory under which script files are stored. These can include JDBC create scripts and WLDF action scripts.

#### `config/wlsdeploy/servers/<server-name>`
The root directory under which server keystore files are stored. These are organized by server name, such as
`config/wlsdeploy/servers/AdminServer/mykey.jks`.

#### `config/wlsdeploy/serverTemplates/<server-template-name>`
The root directory under which server template keystore files are stored. These are organized by server template name, such as
`config/wlsdeploy/serverTemplates/myServerTemplate/mykey.jks`.

#### `wlsdeploy/applications`
The root directory under which applications and their deployment plans are stored. Applications can be stored in the
archive as EAR, WAR, or JAR files, or as an exploded directory at this location.

A sample expanded WAR application might have these entries:

```
wlsdeploy/applications/myApp/index.jsp
wlsdeploy/applications/myApp/META-INF/MANIFEST.MF
wlsdeploy/applications/myApp/WEB-INF/classes/MyClass.class
wlsdeploy/applications/myApp/WEB-INF/web.xml
wlsdeploy/applications/myApp/WEB-INF/weblogic.xml
```

#### `wlsdeploy/classpathLibraries`
The root directory under which JARs/directories used for server classpaths are stored. Every file resource under this
directory is extracted, even those not referenced in the model.

#### `wlsdeploy/custom`
This is the root directory where your custom files and directories can be stored and extracted from the archive. These
files are not collected by the Discover Domain Tool.   Every file resource under this directory is extracted during
`createDomain`, `updateDomain`, and `deployApps`.

Some custom files may belong in `config/wlsdeploy/custom`. To determine which location is preferable for your files, see [Why are there two separate directory structures?]({{< relref "#why-are-there-two-separate-directory-structures" >}}).

#### `wlsdeploy/domainBin`
The root directory under which `$DOMAIN_HOME/bin` scripts are stored. Only scripts referenced in the
`domainInfo/domainBin` section of the model are extracted, as shown in the example.

```yaml
    domainInfo:
        domainBin:
           - wlsdeploy/domainBin/setUserOverrides.sh
```

#### `wlsdeploy/domainLibraries`
The root directory under which `$DOMAIN_HOME/lib` libraries are stored.  Domain libraries must be
stored as JAR files. Only libraries referenced in the `domainInfo/domainLibraries` section of the model are extracted,
as shown in the example.

```yaml
    domainInfo:
        domainLibraries:
           - wlsdeploy/domainLibraries/myLibrary.jar
```

#### `wlsdeploy/opsswallet`
The directory where a wallet can be stored for use with Oracle Platform Security Services. The wallet placed into the
archive can be either a ZIP file or a set of one or more files.  If it is a ZIP file, that ZIP file will be expanded
in place when running WDT tools like the Create Domain or Update Domain tools.

#### `wlsdeploy/security/saml2`
The directory under which SAML2 partner data initialization files can be stored for use with the SAML2 Identity Asserter.
These files can include `saml2idppartner.properties` and `saml2sppartner.properties`, and any XML metadata files they reference.

If these files exist in the domain's `$DOMAIN_HOME/security` directory, then the Discover Domain Tool will add them to
the archive.  However, the Discover Domain Tool will never try to export the SAML2 partner data or generate the
properties files needed to load the exported SAML2 partner data into WebLogic Server.

Both the Create Domain and Update Domain Tools will extract these files from the archive and place them into the target
domain's `$DOMAIN_HOME/security` directory, if they exist in the archive.  No model references are required.

Note that server will not load the SAML2 partner data files if a corresponding `<filename>.initialized` file is present
in the domain's `$DOMAIN_HOME/security` directory. This indicates that existing data files have already
been processed. To force the server to reload a SAML2 partner data file, remove the corresponding `<filename>.initialized`
file, and restart the server to reinitialize the SAML2 partner data.

Note that this functionality is only present starting in the October 2023 PSUs for WebLogic Server 12.2.1.4 and 14.1.1,
and future versions of WebLogic Server.

#### `wlsdeploy/security/xacmlPolicies`
The directory under which XACML Authorizer policies can be stored when defining policies directly in XACML.  The name of the
policy file should match the name of the policy in the model.  For example, the following model entry requires that the
XACML policy file be stored in the archive at `wlsdeploy/security/xacmlPolicies/MyQueueSendPolicy.xml`.

```yqml
MyQueueSendPolicy:
    ResourceID: 'type=<jms>, application=MyJmsModule, destinationType=queue, resource=MyQueue, action=send'
    XacmlDocument: wlsdeploy/security/xacmlPolicies/MyQueueSendPolicy.xml
    XacmlStatus: 3
```

#### `wlsdeploy/security/xacmlRoles`
The directory under which XACML Role Mapper role definitions can be stored when defining role directly in XACML.  The name
of the role file should match the name of the role in the model.  For example, the following model entry requires that the
XACML role definition file be stored in the archive at `wlsdeploy/security/xacmlRoles/users.xml`.

```yqml
users:
    XacmlDocument: wlsdeploy/security/xacmlRoles/users.xml
    XacmlStatus: 3
```

#### `wlsdeploy/sharedLibraries`
The root directory under which shared libraries and their deployment plans are stored. Shared libraries can be stored
in the archive as EAR, WAR, or JAR files, or as an exploded directory at this location.

#### `wlsdeploy/stores`
The root directory under which empty directories must exist for `FileStore` elements in the model.

#### `wlsdeploy/structuredApplications`
The root directory under which "structured" applications are stored; the WebLogic Server documentation refers to them as
[application installation directories](https://docs.oracle.com/en/middleware/standalone/weblogic-server/14.1.1.0/depgd/deployunits.html#GUID-B5DA7628-5900-43C3-9290-8D17E151EDD4).
Applications inside the specified directory structure can be stored in the archive as EAR or WAR files, or as an
exploded directory.

A sample "structured" application might have these entries:

```
wlsdeploy/structuredApplications/myApp/app/webapp.war
wlsdeploy/structuredApplications/myApp/plan/plan.xml
wlsdeploy/structuredApplications/myApp/plan/WEB-INF/weblogic.xml
wlsdeploy/structuredApplications/myApp/plan/AppFileOverrides/updated.properties
```

#### `wlsdeploy/wrcExtension`
The directory into which the WebLogic Remote Console extension WAR file (i.e., `console-rest-ext-6.0.war`) is stored.
Create Domain, Update Domain, and Deploy Applications tools place any file in this directory into the
`$DOMAIN_HOME/management-services-ext/` directory. **NOTE**: The Deploy Applications Tool is deprecated in WDT 4.0.0.

### Using multiple archive files

The Create Domain, Update Domain, Deploy Applications, and Validate Model Tools allow the specification of multiple
archive files on the command line. For example:

    $ weblogic-deploy\bin\createDomain.cmd -archive_file one.zip,two.zip,three.zip ...

File resources can be present in any of these archives. Resources in each archive will supersede resources found
in previous archives.

When the model references a resource that is present in multiple archives, the latest in the list takes precedence.
For example, if the model references `wlsdeploy/applications/myapp.ear`, and that resource is present in archives
`one.zip` and `two.zip`, the resource in `two.zip` will be used.

Resources that are extracted without being referenced directly are extracted from the archives in the order specified
in the `archive_file` argument. For example, if `one.zip` and `two.zip` have resources under
`wlsdeploy/classpathLibraries`, the resources in `one.zip` will be extracted to
`<domain-home>/wlsdeploy/classpathLibraries`, then the resources of `two.zip` will be extracted to the same location,
overwriting any overlapping files.
