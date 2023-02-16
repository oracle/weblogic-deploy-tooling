---
title: "Install WDT"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 1
---

#### Download and install the software

The WebLogic Deploy Tooling project repository is located at [`https://github.com/oracle/weblogic-deploy-tooling`](https://github.com/oracle/weblogic-deploy-tooling).  
You can download binary distributions of the `weblogic-deploy.zip` installer from the [GitHub Releases page](https://github.com/oracle/weblogic-deploy-tooling/releases).  

1. To install the software, simply unzip the `weblogic-deploy.zip` installer on a machine that has the desired versions of WebLogic Server installed.  
1. After being unzipped, the software is ready to use, just set the `JAVA_HOME` environment variable to point to a Java 7 or higher JDK  and the shell scripts are ready to run.

#### Supported WLS versions

The following table specifies the supported WebLogic Server versions, along with the JDK versions, that must be used to run the WDT tool. You must set the `JAVA_HOME` environment variable to specify a JDK version different from the system default version.

 To create a domain with the proper JDK (particularly if the `JAVA_HOME` is different from the one which will be used by the target domain), set the domain `JavaHome` attribute in the domain model.

{{% notice note %}} The Encryption Model Tool used to encrypt and decrypt clear-text passwords in the model and variable files, requires WDT to run with a minimum JDK version of 1.8.
{{% /notice %}}

  | WebLogic Server Version | Tool JDK Version |
  |--------------------------|-------------------|
  | 10.3.6                   | 1.7               |
  | 12.1.1                   | 1.7, 1.8          |
  | 12.1.2 <sup>[1]</sup><sup>[2]</sup>         | 1.7, 1.8          |
  | 12.1.3                   | 1.7, 1.8          |
  | 12.2.1 <sup>[3]</sup>               | 1.8               |
  | 12.2.1.1 <sup>[4]</sup>             | 1.8               |
  | 12.2.1.2                 | 1.8               |
  | 12.2.1.3                 | 1.8               |
  | 12.2.1.4 <sup>[5]</sup>  | 1.8               |
  | 14.1.1                   | 1.8, 1.11         |    

***1*** First release dynamic clusters are supported  
***2*** First release Coherence clusters are supported  
***3*** First release WLS roles are supported  
***4*** First release multitenancy is supported  
***5*** Last release multitenancy is supported
