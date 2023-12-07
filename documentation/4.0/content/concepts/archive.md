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
Archive Helper Tool makes it easy to add, update, and remove entries from the archive file. 

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

#### `wlsdeploy/coherence`
The root directory under which Coherence config files and/or empty directories for Coherence persistent stores.

#### `wlsdeploy/config`
The directory where a MIME mapping property file can be stored.

#### `wlsdeploy/custom`
This is the root directory where your custom files and directories can be stored and extracted from the archive. These
files are not collected by the Discover Domain Tool.   Every file resource under this directory is extracted during
`createDomain` and `updateDomain`.

This location is particularly useful when handling files that live outside an application; for example, a property
file used to configure the application.  The general steps to make applications that use such files work when 
provisioning them with WDT are:

1. Place the file in the required location inside the `wlsdeploy/custom` folder inside the archive; for example,
   `wlsdeploy/custom/com/mycompany/myapp/myapp-config.properties`.
2. Make sure the application is locating the file by `CLASSPATH`; for example, using 
   `ClassLoader.getResourceAsStream("com/mycompany/myapp/myapp-config.properties")`.
3. Make sure that the server's CLASSPATH includes the `$DOMAIN_HOME/wlsdeploy/custom` directory.  One way to achieve
   this would be to add a `setUserOverrides.sh` that includes this directory in the `PRE_CLASSPATH` environment
   variable to the `wlsdeploy/domainBin` location in the archive file.  Don't forget to add `setUserOverrides.sh` to
   the `domainInfo/domainBin` of the model so that it gets extracted.

#### `wlsdeploy/dbWallets/<wallet-name>`

The directory where named database wallets can be stored for use with the Oracle database.  The `rcu` name is used as
the default location to store a wallet for RCU data sources.  The wallet placed into the archive can be either a ZIP
file or a set of one or more files.  If it is a ZIP file, that ZIP file will be expanded in place when running WDT
tools like the Create Domain or Update Domain tools.

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

#### `wlsdeploy/jms/foreignServer/<jms-foreign-server-name>`
The directory under which a JMS Foreign Server binding file is stored.

#### `wlsdeploy/nodeManager`
The root directory under which Node Manager keystore files are stored.

#### `wlsdeploy/opsswallet`
The directory where a wallet can be stored for use with Oracle Platform Security Services. The wallet placed into the
archive can be either a ZIP file or a set of one or more files.  If it is a ZIP file, that ZIP file will be expanded
in place when running WDT tools like the Create Domain or Update Domain tools.

#### `wlsdeploy/scripts`
The root directory under which script files are stored. These can include JDBC create scripts and WLDF action scripts.

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
and WebLogic Server 14.1.2 or newer.

#### `wlsdeploy/servers/<server-name>`
The root directory under which server keystore files are stored. These are organized by server name, such as 
`wlsdeploy/server/AdminServer/mykey.jks`.

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
`$DOMAIN_HOME/management-services-ext/` directory.

### Using multiple archive files

The Create Domain, Update Domain, Deploy Applications, and Validate Model Tools allow the specification of multiple
archive files on the command line. For example:

    $ weblogic-deploy\bin\createDomain.cmd -archive_file one.zip,two.zip,three.zip ...

File resources can be present in any of these archives. Resources in each archive will supersede resources found
in previous archives.

When the model references a resource that is present in multiple archives, the latest in the list takes precedence.
For example, if the model references `wlsdeploy/applications/myapp.ear`, and that resource is present in archives
`one.zip` and `two.zip`, the resource in `two.zip` will be used.

A similar rule applies for resources that have an assumed location, but are not specifically called out in the model.
For example, if archive `two.zip` has a wallet in location `atpwallet/wallet2.zip`, and `three.zip` has a wallet in
location `atpwallet/wallet3.zip`, the wallet `atpwallet/wallet3.zip` will be used.

Resources that are extracted without being referenced directly are extracted from the archives in the order specified
in the `archive_file` argument. For example, if `one.zip` and `two.zip` have resources under
`wlsdeploy/classpathLibraries`, the resources in `one.zip` will be extracted to
`<domain-home>/wlsdeploy/classpathLibraries`, then the resources of `two.zip` will be extracted to the same location,
overwriting any overlapping files.
