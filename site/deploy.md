## The Deploy Applications Tool

**NOTE: Work on the Deploy Applications Tool to bring it in line with the text below is still in progress.**

The Deploy Applications Tool uses a model, the archive, and WLST to deploy applications and resources into an existing WebLogic Server domain in either WLST online or offline mode.  When deploying applications and resources from a model, the deploy tool focuses primarily on the `resources` and `appDeployments` sections of the model.  There are exceptions for the `domainInfo` and `topology` sections, where those configuration elements are deemed to be "application-related."  For example, the servers' `ServerStart` folder has an `Arguments` and a `ClassPath` attribute that change the server environment (when started by the Node Manager) that applications may rely on to function properly.  Likewise, the `domainInfo` section contains a list of JAR files that are to be placed in `<DOMAIN_HOME>/lib` which are relevant to applications for a similar reason.

The Deploy Applications Tool will only add or update elements in the specified model. It will not attempt to remove any missing elements that were present in a previous model.

In WLST online mode, the tool tries to minimize the need to redeploy the applications and shared libraries, and the need to restart the server.  It does this in a few ways:

- If the model references an application or shared library that is already deployed, the tool compares the binaries to determine whether redeployment is required.  Redeployment of shared libraries is particularly expensive since all applications using the shared library must be redeployed--even if the application has not changed.
- It looks at the knowledge base to determine which attributes require restart when they are changed.  If an attribute requires restart, the tool compares the current and model values to make sure that they are different before trying to apply a change.

The goal is to make the tool both able to support iterative deployment and able to minimize service disruption while doing its work when working against a running domain.

Running the Deploy Applications Tool in WLST offline mode is very similar to running the Create Domain Tool; simply provide the domain location and archive file, and separate model and variable files, if needed.  For example:

    weblogic-deploy\bin\deployApps.cmd -oracle_home c:\wls12213 -domain_home domains\DemoDomain -archive_file DemoDomain.zip -model_file DemoDomain.yaml -variable_file DemoDomain.properties

In WLST online mode, simply replace the `-domain_home` argument with the information on how to connect to the WebLogic Server Administration Server, for example:

    weblogic-deploy\bin\deployApps.cmd -oracle_home c:\wls12213 -domain_home domains\DemoDomain -archive_file DemoDomain.zip -model_file DemoDomain.yaml -variable_file DemoDomain.properties -admin_url t3://127.0.0.1:7001 -admin_user weblogic

As usual, the tool will prompt for the password (it can also be supplied by piping it to standard input of the tool).

When running the tool in WLST online mode, the deploy operation may require server restarts or a domain restart to pick up the changes.  The deploy operation can also encounter situations where it cannot complete its operation until the domain is restarted.  To communicate these conditions to scripts that may be calling the Deploy Applications Tool, the shell scripts have three special, non-zero exit codes to communicate these states:

- `101` - The domain needs to be restarted and the Deploy Applications Tool needs to be re-invoked with the same arguments.
- `102` - The servers impacted by the deploy operation need to be restarted, in a rolling fashion, starting with the Administration Server, if applicable.
- `103` - The entire domain needs to be restarted.

### Using Multiple Models

The Deploy Applications Tool supports the use of multiple models, as described in [Using Multiple Models](../README.md#using-multiple-models).
