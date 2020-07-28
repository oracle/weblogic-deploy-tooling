## Using WDT with Oracle WebLogic Server Kubernetes Operator

The Extract Domain Resource Tool can be used to create a domain resource file for use with the Oracle WebLogic Server Kubernetes Operator. This allows the domain configuration and the Kubernetes container configuration to be specified in a single model file.

This is especially useful when making configuration changes to the domain that also need to be reflected in the domain resource file. For example, adding a cluster to the domain only requires that it be added to the `topology` section of the WDT model, then a new domain resource file can be generated to apply to Kubernetes.

More information about the Oracle WebLogic Server Kubernetes Operator can be found [here](https://oracle.github.io/weblogic-kubernetes-operator).

NOTE: The Extract Domain Resource Tool is available with WDT releases 1.7.0 and later.

Here is an example command line for the Extract Domain Resource Tool:
```
<wls-deploy-home>/bin/extractDomainResource.sh -oracle_home /tmp/oracle -domain_home /u01/mydomain -model_file /tmp/mymodel.yaml -variable_file /tmp/my.properties -domain_resource_file /tmp/operator/domain-resource.yaml
```

For the simplest case, the Extract Domain Resource Tool will create a sparse domain file. This is what is generated when there is not a `kubernetes` section in the model, or that section is empty.
```yaml
apiVersion: weblogic.oracle/v6
kind: Domain
metadata:
    name: DemoDomain
spec:
    domainHome: /u01/mydomain
    image: '--FIX ME--'
    imagePullSecrets:
    -   name: '--FIX ME--'
    webLogicCredentialsSecret: '--FIX ME--'
    clusters:
    -   clusterName: mycluster
        replicas: 2
    -   clusterName: mycluster3
        replicas: 4
```

In this example, the value for `domainHome` was set as an input parameter to the extractDomainResource script from the command line. The `kind` and `name` were set to the domain name derived from the topology section of the model, or the default `base_domain`. The cluster entries are pulled from the topology section of the model, and their replica counts were derived from the number of servers for each cluster.

The user is expected to fill in the image and secrets information identified by `--FIX ME--` in the domain resource output.

For more advanced configurations, including pre-populating the `--FIX ME--` values, the user can populate the `kubernetes` section of the WDT model, and those values will appear in the resulting domain resources file. This model section overrides and adds some values to the result.
```yaml
kubernetes:
    metadata:
        name: myName
        namespace: myNamespace
    spec:
        image: 'my.repo/my-image:2.0'
        imagePullSecrets:
            WEBLOGIC_IMAGE_PULL_SECRET_NAME:
        webLogicCredentialsSecret:
            name: '@@PROP:mySecret@@'
        serverPod:
            env:
                USER_MEM_ARGS:
                    value: '-XX:+UseContainerSupport -Djava.security.egd=file:/dev/./urandom'
                JAVA_OPTIONS:
                    value: '-Dmydir=/home/me'
```
This example uses `@@PROP:mySecret@@` to pull the value for `webLogicCredentialsSecret` from the variables file specified on the command line. This can be done with any of the values in the `kubernetes` section of the model. More details about using model variables can be found [here](model.md#simple-example).

For this example, the resulting domain resource file would contain:
```yaml
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
    clusters:
    -   clusterName: mycluster
        replicas: 2
    -   clusterName: mycluster3
        replicas: 4
apiVersion: weblogic.oracle/v6
kind: Domain
```

The syntax of the `spec/serverPod/env` and other list sections in the WDT model are different from the syntax in the target file. The WDT tools do not recognize the hyphenated list syntax, so these elements are specified in a similar manner to other model lists.

If clusters are specified in the `kubernetes/spec` section of the model, those clusters will be configured in the domain resource file, and clusters from the `topology` section will be disregarded.

If the WDT model has a value of `Never` for `spec/imagePullPolicy`, the `imagePullSecrets` default value will not be added.

A full list of sections and variables supported by the Oracle WebLogic Server Kubernetes Operator is available [here](https://github.com/oracle/weblogic-kubernetes-operator/blob/master/docs/domains/Domain.md).

The Extract Domain Resource Tool supports a subset of these sections, including `metadata`, `serverPod`, and `spec`.

The [Model Help Tool](model_help.md) can be used to determine the folders and attributes that can be used in the `kubernetes` section of the model. For example, this command will list the folders and attributes in the `spec` folder:
```yaml
<wls-deploy-home>/bin/modelHelp.sh -oracle_home /tmp/oracle kubernetes:/spec
```

The content in the `kubernetes` section is not generated when a model is discovered by the Discover Domain Tool.  
