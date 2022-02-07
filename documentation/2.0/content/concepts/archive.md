---
title: "Archive File"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 2
---


The archive file is used to deploy binaries and other file resources to the target domain. The archive is a ZIP file with a specific directory structure.  Any file resources referenced in the model that are not already on the target system must be stored in the correct location in the archive, and the model must reflect the path into the archive. The model itself can also be stored inside the archive, if desired.

Note that file resources that already exist on the target system need not be included in the archive, provided that the model specifies the correct location on the target system.

### Contents

- [Example](#example)
- [Archive structure](#archive-structure)
- [Using multiple archive files](#using-multiple-archive-files)

#### Example

This example shows an application with a `SourcePath` value referencing an EAR file resource contained in the archive.

```yaml
appDeployments:
    Application:
        simpleear :
            SourcePath: wlsdeploy/applications/simpleear.ear
            Target: my-cluster
            ModuleType: ear
```

The example above shows the attribute `SourcePath` of the `simpleear` application with a value of `wlsdeploy/applications/simpleear.ear`.  The prefix `wlsdeploy/` indicates that the resource is located in the archive file in the specified location, and will be deployed to that directory in the domain, in this case `<domain-home>/wlsdeploy/applications/simpleear.ear`.

### Archive structure

These are the paths within the archive that are used for different types of resources. Users can create further directory structures underneath these locations to organize the files and directories as they see fit.  

#### `atpwallet`

The directory where a wallet can be stored for use with Oracle Autonomous Transaction Processing Cloud Database. The file resource name is not specified in the model, and is assumed to be a single ZIP file in the archive at this location.  

#### `model`
The directory where the model is optionally located. Only one model file, either in YAML or JSON, is allowed, and it must have the appropriate YAML or JSON file extension.

#### `opsswallet`

The directory where a wallet can be stored for use with Oracle Platform Security Services. The file resource name is not specified in the model, and is assumed to be a single ZIP file in the archive at this location.  

#### `wlsdeploy/applications`
The root directory under which applications are stored. Applications can be stored in the archive as EAR or WAR files, or expanded under this folder.

{{% notice note %}} Expanded application directories are supported after WebLogic Deploy Tooling release 1.6.2.
{{% /notice %}}

A sample expanded WAR application might have these entries:

```
wlsdeploy/applications/myApp/index.jsp
wlsdeploy/applications/myApp/META-INF/MANIFEST.MF
wlsdeploy/applications/myApp/WEB-INF/classes/MyClass.class
wlsdeploy/applications/myApp/WEB-INF/web.xml
wlsdeploy/applications/myApp/WEB-INF/weblogic.xml
```

#### `wlsdeploy/classpathLibraries`
The root directory under which JARs/directories used for server classpaths are stored. Every file resource under this directory is extracted, even those not referenced in the model.

#### `wlsdeploy/coherence`
The root directory under which empty directories must exist for Coherence persistent stores.

#### `wlsdeploy/custom`
This is the root directory where your custom files can be stored and extracted from the archive. These files are not collected by the Discover Domain Tool.
Every file resource under this directory is extracted during `createDomain` and `updateDomain`.

#### `wlsdeploy/domainBin`
The root directory under which `$DOMAIN_HOME/bin` scripts are stored. Only scripts referenced in the `domainInfo/domainBin` section of the model are extracted.

#### `wlsdeploy/domainLibraries`
The root directory under which `$DOMAIN_HOME/lib` libraries are stored. Only libraries referenced in the `domainInfo/domainLibraries` section of the model are extracted.

#### `wlsdeploy/nodeManager`
The root directory under which Node Manager file resources, such as keystore files, are stored.

#### `wlsdeploy/scripts`
The root directory under which scripts are stored. These can include JDBC create scripts, and WLDF action scripts.

#### `wlsdeploy/servers`
The root directory under which server files, such as keystore files, are stored. These are organized by server name, such as `wlsdeploy/server/my-server/mykey.jks`.

#### `wlsdeploy/sharedLibraries`
The root directory under which shared libraries are stored. These are stored as JAR files within the archive.

#### `wlsdeploy/stores`
The root directory under which empty directories must exist for `FileStore` elements in the model.

### Using multiple archive files

The Create Domain, Update Domain, Deploy Applications, and Validate Model Tools allow the specification of multiple archive files on the command line. For example:

    $ weblogic-deploy\bin\createDomain.cmd -archive_file one.zip,two.zip,three.zip ...

File resources can be present in any of these archives. Resources in each archive will supersede resources found in previous archives.

When the model references a resource that is present in multiple archives, the latest in the list takes precedence. For example, if the model references `wlsdeploy/applications/myapp.ear`, and that resource is present in archives `one.zip` and `two.zip`, the resource in `two.zip` will be used.

A similar rule applies for resources that have an assumed location, but are not specifically called out in the model. For example, if archive `two.zip` has a wallet in location `atpwallet/wallet2.zip`, and `three.zip` has a wallet in location `atpwallet/wallet3.zip`, the wallet `atpwallet/wallet3.zip` will be used.

Resources that are extracted without being referenced directly are extracted from the archives in the order specified in the `archive_file` argument. For example, if `one.zip` and `two.zip` have resources under `wlsdeploy/classpathLibraries`, the resources in `one.zip` will be extracted to `<domain-home>/wlsdeploy/classpathLibraries`, then the resources of `two.zip` will be extracted to the same location, overwriting any overlapping files.
