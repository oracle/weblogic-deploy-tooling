## The Update Domain Tool

The Update Domain Tool uses a model, the archive, and WLST to update the configuration of an existing WebLogic Server domain, and to deploy applications and resources into the domain in either WLST online or offline mode.  The update tool will add or re-configure elements from the `topology` section of the model, and deploy applications and resources from the `resources` and `appDeployments` sections, as described in the Deploy Applications Tool.

The Update Domain Tool will only add or update elements in the specified model. It will not attempt to remove any missing elements that were present in a previous model.

Running the Update Domain Tool in WLST offline mode is very similar to running the Create Domain Tool; simply provide the domain location and archive file, and separate model and variable files, if needed.  For example:

    weblogic-deploy\bin\updateDomain.cmd -oracle_home c:\wls12213 -domain_type WLS -domain_home domains\DemoDomain -archive_file DemoDomain.zip -model_file DemoDomain.yaml -variable_file DemoDomain.properties

In WLST online mode, simply add the information on how to connect to the WebLogic Server Administration Server, for example:

    weblogic-deploy\bin\updateDomain.cmd -oracle_home c:\wls12213 -domain_type WLS -domain_home domains\DemoDomain -archive_file DemoDomain.zip -model_file DemoDomain.yaml -variable_file DemoDomain.properties -admin_url t3://127.0.0.1:7001 -admin_user weblogic

As usual, the tool will prompt for the password (it can also be supplied by piping it to standard input of the tool).

Unlike the Create Domain Tool, the full domain home directory is specified, rather than the domain's parent directory, because the domain has already been established.

The Update Domain Tool will not attempt to recreate or add schemas for the RCU database, for domain types that use RCU.

When running the tool in WLST online mode, the update operation may require server restarts or a domain restart to pick up the changes.  The update operation can also encounter situations where it cannot complete its operation until the domain is restarted.  To communicate these conditions to scripts that may be calling the Update Domain Tool, the shell scripts have three special, non-zero exit codes to communicate these states:

- `101` - The domain needs to be restarted and the Update Domain Tool needs to be re-invoked with the same arguments.
- `102` - The servers impacted by the update operation need to be restarted, in a rolling fashion, starting with the Administration Server, if applicable.
- `103` - The entire domain needs to be restarted.

### Using Multiple Models

The Update Domain Tool supports the use of multiple models, as described in [Using Multiple Models](../README.md#using-multiple-models).
