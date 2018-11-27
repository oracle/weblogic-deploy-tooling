Example Image with a WLS Domain
===============================
This Dockerfile extends the Oracle WebLogic Server image by creating a sample WLS 12.2.1.3 domain and cluster. Utility scripts are copied into the image, enabling users to plug Node Manager automatically into the Administration Server running on another container.

The Dockerfile uses the `createDomain` script from the Oracle WebLogic Deploy Tooling (WDT) to create the domain from a text-based model file. More information about WDT is available in the README file for the WDT project in GitHub:

`https://github.com/oracle/weblogic-deploy-tooling`

### WDT Model File and Archive

This sample includes a basic WDT model, `simple-topology.yaml`, that describes the intended configuration of the domain within the Docker image. WDT models can be created and modified using a text editor, following the format and rule described in the README file for the WDT project in GitHub.

Another option is to use the WDT `discoverDomain` tool to create a model. This process is also described in the WDT project's README file. A user can use the tool to analyze an existing domain, and create a model based on its configuration. The user may choose to customize the model before using it to create a new Docker image.

The sample model file includes variable tokens that are replaced with values from the provided 'simple-topology.properties'. The properties files can be created and modified using a text editor. The property file must contain the values that the Dockerfile sets as ENV variables to expose ports
 and run a server in a docker container.
 
The admin server credentials in the sample model contain file tokens that reference special property files. A special property file must contain only one property value pair. The sample includes the credentials secrets property files in the properties/docker_build directory. The files can be created and modified using a text editor; one file must contain the admin password and one file must contain the admin user. See the README file for more information on using property and file tokens in the WDT model.

Domain creation may require the deployment of applications and libraries. This is accomplished by creating a ZIP archive with a specific structure, then referencing those items in the model. This sample creates and deploys a simple ZIP archive containing a small application WAR. That archive is built in the sample directory prior to creating the Docker image.

When the WDT `discoverDomain` tool is used on an existing domain, a ZIP archive is created containing any necessary applications and libraries. The corresponding configuration for those applications and libraries is added to the model.

### How to Build and Run

**NOTE:** The image is based on a WebLogic Server image in the docker-images project: `oracle/weblogic:12.2.1.3-developer`. Build that image to your local repository before building this sample.

The WebLogic Deploy Tool installer is required to build this image. Add `weblogic-deploy.zip` to the sample directory.

    $ wget https://github.com/oracle/weblogic-deploy-tooling/releases/download/weblogic-deploy-tooling-0.11/weblogic-deploy.zip

This sample deploys a simple, one-page web application contained in a ZIP archive. This archive needs to be built (one time only) before building the Docker image.

    $ ./build-archive.sh

To build this sample, run:

    $ docker build \
          --build-arg WDT_MODEL=simple-topology.yaml \
          --build-arg WDT_ARCHIVE=archive.zip \
          --build-arg WDT_VARIABLE=simple-topology.properties \
          --force-rm=true \
          -t 12213-domain-wdt .

This will use the model, variable and archive files in the sample directory.

The Admin Server and each Managed Server are run in containers from this build image. The admin server credentials, required for running the admin server or a managed server, are provided in a properties file. This sample contains a credentials properties file in the properties/docker_run directory, which can be mounted into a volume on the container image. It is the responsibility of the user to mange the properties file in this mounted container volume.

To start the containerized Administration Server, run:

    $ docker run -d --name wlsadmin --hostname wlsadmin -p 7001:7001 -v <sample-directory>/properties/docker_run:/u01/oracle/properties 12213-domain-wdt

To start a containerized Managed Server (ms-1) to self-register with the Administration Server above, run:

    $ docker run -d --name ms-1 --link wlsadmin:wlsadmin -p 9001:9001 -v <sample-directory>/properties/docker_run:/u01/oracle/properties -e MS_NAME=ms-1 12213-domain-wdt startManagedServer.sh

To start an additional Managed Server (in this example ms-2), run:

    $ docker run -d --name ms-2 --link wlsadmin:wlsadmin -p 9002:9001 -v <sample-directory>/properties/docker_run/:/u01/oracle/properties -e MS_NAME=ms-2 12213-domain-wdt startManagedServer.sh

The above scenario from this sample will give you a WebLogic domain with a dynamic cluster set up on a single host environment.

You may create more containerized Managed Servers by calling the `docker` command above for `startManagedServer.sh` as long you link properly with the Administration Server. For an example of a multihost environment, see the sample `1221-multihost`.

# Copyright
Copyright (c) 2018 Oracle and/or its affiliates. All rights reserved.
