---
title: "Building CRD schemas"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 4
description: "How to build the CRD schemas"
---

The structure of the `kubernetes` section of the [WDT model]({{% relref "/concepts/model.md" %}}) is described by schemas based on the Custom Resource Definitions (CRDs) for this product. This is different from other sections of the model that use the [alias framework]({{% relref "/developer/alias-definitions.md" %}}) to describe their structures.

These schemas are used during model validation to check that folder and attribute names are valid. The [Model Help Tool]({{% relref "/userguide/tools/model_help.md" %}}) uses them to list the contents of folders and details about their attributes.

CRDs corresponding to the `kubernetes` section of the model are contained in the [WebLogic Kubernetes Operator](https://oracle.github.io/weblogic-kubernetes-operator/) (WKO) project. CRDs from this project are merged together to form self-contained OpenAPI schemas.

You will need to regenerate the CRD schemas when there are changes to CRDs in the corresponding projects.

### Building the schemas

The tool that builds the CRD schemas is contained in the
[WDT project repository](https://github.com/oracle/weblogic-deploy-tooling), in the module `tools/crd-schema`. You can run the tool from the command line, or from within an IDE.

#### Running from the command line

You will need to build the runnable JAR file using Maven:
```bash
$ mvn -f <project-dir>/tools/crd-schema/pom.xml clean install
```
Next, run the JAR file:
```bash
$ java -jar <project-dir>/tools/crd-schema/target/crd-schema.jar
```
This will write the generated schema files to the current directory.

#### Running from an IDE

If your IDE supports running Java programs directly, you can run the Java class `oracle.weblogic.deploy.crdschema.SchemaGenerator`.

In IntelliJ IDEA, right-click on the `SchemaGenerator` source file, and select `Run SchemaGenerator.main()`.

This will write the generated schema files to the target directory `<project-dir>/tools/crd-schema/target/crd`.

#### Importing the new schemas

Copy the generated files to the `<project-dir>/core/src/main/resources/oracle/weblogic/deploy/crds` directory. Confirm that any changes appear correctly when using the [Model Help Tool]({{% relref "/userguide/tools/model_help.md" %}}) before checking in the schemas.
