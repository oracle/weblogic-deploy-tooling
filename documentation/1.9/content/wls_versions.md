## Supported WebLogic Server Versions
The following table specifies the supported WebLogic Server versions, along with the JDK versions, that must be used to run the WDT tool. You must set the `JAVA_HOME` environment variable to specify a JDK version different from the system default version.

 To create a domain with the proper JDK (particularly if the `JAVA_HOME` is different from the one which will be used by the target domain), set the domain `JavaHome` attribute in the domain model.

 Note that the WDT Encryption Model Tool used to encrypt and decrypt clear text passwords in the model and variable files, requires WDT to run with a minimum JDK version of 1.8.

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

