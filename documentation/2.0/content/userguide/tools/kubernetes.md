---
title: "Extract Domain Resource Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 9
description: "Generates YAML resource files for use with the WebLogic Kubernetes Operator or Verrazzano."
---


#### Using WDT with WebLogic Kubernetes Operator

You can use the Extract Domain Resource Tool to create resource files for use with the WebLogic Kubernetes Operator or Verrazzano. This allows the domain configuration and the Kubernetes container configuration to be specified in a single model file.

This is especially useful when making configuration changes to the domain that also need to be reflected in the resource file. For example, adding a cluster to the domain only requires that it be added to the `topology` section of the WDT model, then a new resource file can be generated to apply to Kubernetes.

More information about the WebLogic Kubernetes Operator can be found [here](https://oracle.github.io/weblogic-kubernetes-operator).

More information about Verrazzano can be found [here](https://verrazzano.io/latest/docs/).

Here is an example command line for the Extract Domain Resource Tool:
```
$ <wls-deploy-home>/bin/extractDomainResource.sh -oracle_home /tmp/oracle -domain_home /u01/mydomain -model_file /tmp/mymodel.yaml -variable_file /tmp/my.properties -output_dir /tmp/resource -target wko
```

For the simplest case, the Extract Domain Resource Tool will create resource files based on the templates corresponding to the `target` argument, using information from the command line and the domain sections of the model. Information about target types and templates can be found [here]({{< relref "/userguide/target_env.md" >}}).

The value of the optional `-domain_home` argument will be applied in the template output. Domain name and UID fields in the template will use the domain name in the topology section of the model, or the default `base_domain`. The cluster entries will be pulled from the topology section of the model; their replica counts will have been derived from the number of servers for each cluster.

The user is expected to fill in the image and secrets information identified by `--FIX ME--` in the resource output.

For more advanced configurations, including pre-populating the `--FIX ME--` values, the user can populate the `kubernetes` section of the WDT model, and those values will appear in the resulting resource files. This model section overrides and adds some values to the result.
```yaml
kubernetes:
    metadata:
        name: myName
        namespace: myNamespace
    spec:
        image: 'my.repo/my-image:2.0'
        imagePullSecrets:
            -   name: WEBLOGIC_IMAGE_PULL_SECRET_NAME
        webLogicCredentialsSecret:
            name: '@@PROP:mySecret@@'
        configuration:
            model:
                domainType: 'WLS'
            secrets:
                -   secret1
                -   secret2
        serverPod:
            env:
                -   name: USER_MEM_ARGS
                    value: '-XX:+UseContainerSupport -Djava.security.egd=file:/dev/./urandom'
                -   name: JAVA_OPTIONS
                    value: '-Dmydir=/home/me'
```
This example uses `@@PROP:mySecret@@` to pull the value for `webLogicCredentialsSecret` from the variables file specified on the command line. This can be done with any of the values in the `kubernetes` section of the model. More details about using model variables can be found [here]({{< relref "/concepts/model#simple-example" >}}).

Using the `wko` target with this example, the resulting domain resource file would contain:
```yaml
apiVersion: weblogic.oracle/v8
kind: Domain
metadata:
    name: myName
    namespace: myNamespace
spec:
    image: 'my.repo/my-image:2.0'
    imagePullSecrets:
    -   name: WEBLOGIC_IMAGE_PULL_SECRET_NAME
    webLogicCredentialsSecret:
        name: WEBLOGIC_CREDENTIALS_SECRET_NAME
    serverPod:
        env:
        -   name: USER_MEM_ARGS
            value: '-XX:+UseContainerSupport -Djava.security.egd=file:/dev/./urandom'
        -   name: JAVA_OPTIONS
            value: '-Dmydir=/home/me'
    domainHome: /u01/mine/domain
    configuration:
        model:
            domainType: WLS
        secrets:
        -   secret1
        -   secret2
    clusters:
    -   clusterName: mycluster
        replicas: 2
    -   clusterName: mycluster3
        replicas: 4
```

If clusters are specified in the `kubernetes/spec` section of the model, those clusters will be combined with any clusters from the `topology` section of the model.

If the WDT model has a value of `Never` for `spec/imagePullPolicy`, the `imagePullSecrets` default value will not be added.

A full list of sections and variables supported by the WebLogic Kubernetes Operator is available [here](https://github.com/oracle/weblogic-kubernetes-operator/blob/main/documentation/domains/Domain.md). The Extract Domain Resource Tool supports a subset of these sections, including `metadata`, `serverPod`, and `spec`.

The [Model Help Tool]({{< relref "/userguide/tools/model_help.md" >}}) can be used to determine the folders and attributes that can be used in the `kubernetes` section of the model. For example, this command will list the folders and attributes in the `spec` folder:
```yaml
<wls-deploy-home>/bin/modelHelp.sh -oracle_home /tmp/oracle kubernetes:/spec
```

The content in the `kubernetes` section is not generated when a model is discovered by the Discover Domain Tool.  

### Parameter table for `extractResources`
| Parameter | Definition | Default |
| ---- | ---- | ---- |
| `-archive_file` | The path to the archive file.  If the `-model_file` argument is not specified, the model file in this archive will be used.  This can also be specified as a comma-separated list of archive files.  The overlapping contents in each archive take precedence over previous archives in the list. |    |
| `-domain_home` | The domain home directory to be used in output files. This will override any value in the model. |    |
| `-domain_resource_file` | The location of the extracted domain resource file. This is deprecated, use `-output_dir` to specify output location. |    |
| `-model_file` | The location of the model file.  This can also be specified as a comma-separated list of model locations, where each successive model layers on top of the previous ones. |    |
| `-oracle_home` | Home directory of the Oracle WebLogic installation. Required if the `ORACLE_HOME` environment variable is not set. |    |
| `-output_dir` | The location for the target output files. |    |
| `-target` | The target output type. The default is `wko`. |    |
| `-variable_file` | The location of the property file containing the values for variables used in the model. This can also be specified as a comma-separated list of property files, where each successive set of properties layers on top of the previous ones. |    |
