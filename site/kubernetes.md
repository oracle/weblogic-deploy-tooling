## Configuring Oracle WebLogic Server Kubernetes Operator

The Extract Domain Resource Tool can be used to create a domain resource file for use with the Oracle WebLogic Server Kubernetes Operator. This allows the domain configuration and the Kubernetes container configuration to be specified in a single model file.

The Extract Domain Resource Tool is available with WDT releases 1.7.0 and later.

More information about the Oracle WebLogic Server Kubernetes Operator can be found [here](https://github.com/oracle/weblogic-kubernetes-operator).

Here is an example command line for the Extract Domain Resource Tool:
```
<wls-deploy-home>/bin/extractDomainResource.sh -oracle_home /tmp/oracle	-domain_home /u01/mydomain -model_file /tmp/mymodel.yaml -domain_resource_file /tmp/operator/domain-resource.yaml
```

For the simplest case, the Extract Domain Resource Tool will create a sparse domain file. This is what is generated when there is not `kubernetes` section in the model, or that section is empty.
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

For this example, the user is expected to fill in the image and secrets information identified by `--FIX ME--` in the domain resource output. The value for `domainHome` was set from the command line. The `kind` and `name` were set to the domain name derived from the topology section of the model, or the default `base_domain`. The cluster entries are pulled from the topology section of the model, and their replica counts were derived from the number of servers for each cluster.

For more advanced configurations, the user can populate the `kubernetes` section of the WDT model, and those values will appear in the resulting domain resources file. This model section overrides and adds some values to the result.
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
            name: WEBLOGIC_CREDENTIALS_SECRET_NAME
        serverPod:
            env:
                USER_MEM_ARGS:
                    value: '-XX:+UseContainerSupport -Djava.security.egd=file:/dev/./urandom'
                JAVA_OPTIONS:
                    value: '-Dmydir=/home/me'
```

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

A full list of sections and variables supported by the Oracle WebLogic Server Kubernetes Operator is available [here](https://github.com/oracle/weblogic-kubernetes-operator/blob/master/docs/domains/Domain.md).

The Extract Domain Resource Tool supports a subset of these sections, including `metadata`, `serverPod`, and `spec`. 

The content in the `kubernetes` section is not generated when a model is discovered by the Discover Domain Tool.  
