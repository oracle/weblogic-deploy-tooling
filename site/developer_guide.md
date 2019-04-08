# Developer Guide

## Table of Contents
- [PreRequisite](#prerequisite)
- [Project Structure](#project-structure)
- [Alias definition](#alias-definition)
- [Typedefs definition](#typedefs-definition)
- [Building WebLogic Deploy Tool](#building-weblogic-deploy-tool)

## PreRequisite

You will need the following software installed in your local build environment

1. Oracle WebLogic Server installation version 10.3.6 and above
2. JDK version 8
3. Maven 3 and above

## Project Structure

## Alias definition

## Typedefs definition

## Building WebLogic Deploy Tool

If you are making changes to the project, you can build the project by

  `mvn -Dunit-test-wlst-dir=<full path to the wlst.sh(cmd) directory> clean install`
  
This will build the entire project and run the unit test.

If you are not making changes and only interested in building the latest version, then you can 

  `mvn -Denforcer.skip -DskipTests clean install`
 
This will build the entire project without running any unit test.


