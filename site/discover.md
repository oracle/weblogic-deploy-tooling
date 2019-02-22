## The Discover Domain Tool

The Discover Domain Tool provides a bootstrapping mechanism to creating a model and archive file by inspecting an existing domain and gathering configuration and binaries from it.  Note that the model file produced by the tool is not directly usable by the Create Domain Tool or the Deploy Applications Tool because the Discover Domain Tool does not discover the passwords from the existing domain.  Instead, it puts a `--FIX ME--` placeholder for passwords it finds.  Domain users are also not discoverable so the tool does not create the `AdminUserName` and `AdminPassword` fields in the `domainInfo` section, which are needed by the Create Domain Tool.  The idea of this tool is simply to provide a starting point where the user can edit the generated model and archive file to suit their needs for running one of the other tools.

To run the Discover Domain Tool, simply provide the domain location and the name of the archive file; a separate model file can also be provided to make editing the generated model easier.  For example:

    weblogic-deploy\bin\discoverDomain.cmd -oracle_home c:\wls12213 -domain_home domains\DemoDomain -archive_file DiscoveredDemoDomain.zip -model_file DiscoveredDemoDomain.yaml

When creating the archive, the tool will try to gather all binaries, scripts, and required directories referenced by the domain configuration with the following caveats.

1. Any binaries referenced from the `ORACLE_HOME` will not be gathered, as they are assumed to exist in any target domain to which model-driven operations will be applied.  Doing this is key to allowing the model to be WebLogic Server version independent.
2. In its current form, the Discover Domain Tool will only gather binaries and scripts that are accessible from the local machine.  Warnings will be generated for any binaries or scripts that cannot be found but the configuration for those binaries will still be collected, where possible.  It is the user's responsibility to add those missing files to the archive in the appropriate locations and edit the the model, as needed, to point to those files inside the archive using the relative path inside the archive (for example, `wlsdeploy/applications/myapp.ear`).
