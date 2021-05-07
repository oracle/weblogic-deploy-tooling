---
title: "Build WebLogic Deploy Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 4
---

### Prerequisites

You will need the following software installed in your local build environment:

* Oracle WebLogic Server installation version 12.2.1 and later
* JDK version 8
* Maven 3 and later

#### Specify the WLST location

Execution of the unit tests requires a WebLogic Server installation, because the tests must be run within WLST.

The WLST directory can be specified in one of two ways:

- Specify the `-Dunit-test-wlst-dir=<wlst-directory>` on the `mvn` command line.

- Create a file `.mvn/maven.config` file in the project directory, containing a single line with the `-Dunit-test-wlst-dir=<wlst-directory>` value. The `.mvn` directory contains a `maven.config-template` file that can be copied and used as a starting point.

In these cases, `<wlst-directory>` refers to the fully-qualified path to the WLST script (`wlst.sh` or `wlst.cmd`).

If you are using an IDE for development and building, creating a `maven-config` file will allow some Maven tasks to be performed within the IDE.

#### Build commands

If you are making changes to the project, you can build the project using this command line:

  `$ mvn -Dunit-test-wlst-dir=<wlst-directory> clean install`

This will build the entire project and run the unit tests. Omit the `-Dunit-test-wlst-dir=` argument if you have created a `maven.config` file, as described above.

Another option for specifying the WLST directory is to set the environment variable WLST_DIR.  It is not necessary to use both, and
the -D setting will take precedence.

If you are not making changes and are only interested in building the latest version, then you can skip the unit tests, using this command line:

  `$ mvn -DskipTests clean install`

The resulting installer ZIP file built is under the `WLSDEPLOY_HOME/installer/target` directory.
