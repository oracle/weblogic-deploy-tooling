---
title: "Extract Domain Resource Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 9
description: "Generates YAML resource files for use with the WebLogic Kubernetes Operator."
---


You can use the Extract Domain Resource Tool to create resource files for use with the WebLogic Kubernetes Operator. This allows the Kubernetes resource definitions to be generated from a model file.  This is especially
useful when making configuration changes to the domain that also need to be reflected in the resource file. For example,
adding a cluster to the domain only requires that it be added to the `topology` section of the WDT model, then a new
resource definition file can be generated that contains information pertaining to the new cluster to apply to Kubernetes.

By default, the resource file generated is pretty minimalistic and will always require editing.  For example, the Extract
Domain Resource Tool run against a simple model with only an Administration Server will generate something the looks
similar the one shown here.  Note that the `.spec.domainHome` attribute value was populated using the `-domain_home`
command-line argument.

```yaml
apiVersion: weblogic.oracle/v9
kind: Domain
metadata:
    name: mydomain
    namespace: mydomain
    labels:
        weblogic.domainUID: mydomain
spec:
    domainHome: /u01/domains/mydomain
    domainHomeSourceType: FromModel
    image: '{{{imageName}}}'
    # Add any credential secrets that are required to pull the image
    imagePullSecrets: []
    webLogicCredentialsSecret:
        name: mydomain-weblogic-credentials
    serverPod:
        env:
          - name: JAVA_OPTIONS
            value: -Dweblogic.StdoutDebugEnabled=false
          - name: USER_MEM_ARGS
            value: '-Djava.security.egd=file:/dev/./urandom -Xms64m -Xmx256m '
    configuration:
        introspectorJobActiveDeadlineSeconds: 900
        model:
            domainType: WLS
            modelHome: '{{{modelHome}}}'
            runtimeEncryptionSecret: mydomain-runtime-encryption-secret
```

To help make this tool more useful (and more automated), the model includes an optional, top-level `kubernetes` section that feeds into the generated domain resource.  Looking at the previous example output, you see
that the `.spec.image` and `.spec.configuration.model.modelHome` attributes are replaced with model values.

More information about the WebLogic Kubernetes Operator can be found [here](https://oracle.github.io/weblogic-kubernetes-operator).

Here is an example command line for the Extract Domain Resource Tool:

    $ weblogic-deploy/bin/extractDomainResource.sh -model_file /tmp/mymodel.yaml -variable_file /tmp/my.properties -output_dir /tmp/resource -target wko -oracle_home /tmp/oracle -domain_home /u01/mydomain 

For the simplest case, the Extract Domain Resource Tool will create resource files based on the templates corresponding
to the `target` argument, using information from the command line and the domain sections of the model. Information
about target types and templates can be found [Target environments]({{% relref "/userguide/target_env.md" %}}) page.

The value of the optional `-domain_home` argument will be applied to the corresponding field in the template output, if specified. As an alternative, the domain home value can be specified in the related section of the WDT model. 

Domain name and UID fields in the template will use the domain name in the topology section of the model, or the default `base_domain`. The cluster entries will be pulled from the topology section of the model; their replica counts will have been derived from the number of servers for each cluster.

The user is expected to fill in the image and secrets information identified by `--FIX ME--` in the resource output.

For more advanced configurations, including pre-populating the `--FIX ME--` values, the user can populate the related section of the WDT model, and those values will appear in the resulting custom resource definition (CRD) resource files. In this example the `kubernetes` section of the model overrides and adds some values to the CRD generated for WebLogic Kubernetes Operator.
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
This example uses `@@PROP:mySecret@@` to pull the value for `webLogicCredentialsSecret` from the variables file specified on the command line. This can be done with any of the values in the CRD sections of the model. More details about using model variables can be found [here]({{% relref "/concepts/model#simple-example" %}}).

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

The [Model Help Tool]({{% relref "/userguide/tools/model_help.md" %}}) can be used to determine the folders and attributes that can be used in the CRD sections of the model. For example, this command will list the folders and attributes in the `spec` folder in the `kubernetes` section:
```yaml
<wls-deploy-home>/bin/modelHelp.sh -oracle_home /tmp/oracle kubernetes:/spec
```

The content for the CRD sections is not generated when a model is discovered by the Discover Domain Tool.  

### Parameter table for `extractDomainResource`
| Parameter | Definition | Default |
| ---- | ---- | ---- |
| `-archive_file` | The path to the archive file.  This can also be specified as a comma-separated list of archive files.  The overlapping contents in each archive take precedence over previous archives in the list. |    |
| `-domain_home` | The domain home directory to be used in output files. This will override any value in the model. |    |
| `-model_file` | The location of the model file.  This can also be specified as a comma-separated list of model locations, where each successive model layers on top of the previous ones. |    |
| `-oracle_home` | Home directory of the Oracle WebLogic installation. Required if the `ORACLE_HOME` environment variable is not set. |    |
| `-output_dir` | The location for the target output files. |    |
| `-target` | The target output type. The default is `wko`. For more information about target types, see [Target Environments]({{% relref "userguide/target_env" %}}). |    |
| `-variable_file` | The location of the property file containing the values for variables used in the model. This can also be specified as a comma-separated list of property files, where each successive set of properties layers on top of the previous ones. |    |
