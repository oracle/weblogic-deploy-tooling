---
title: "Archive Helper Tool"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 12
description: "Helps you create and modify archive files."
---


With the Archive Helper Tool, you can display the contents of an archive file, add, update, extract, and remove files, as needed.

Use the Archive Helper Tool `-help` option to display its commands. Each command takes a subcommand, which may require one or more command-line options.

### `archiveHelper` commands
| Command | Description |
| ---- | ---- |
| `add` | Add items to the archive file. |
| `extract` | Extract items from the archive file. |
| `list` | List contents of the archive file. |
| `remove` | Remove items to the archive file. |

For each command, use the `-help` option for usage information about its subcommands.

For example, to display the subcommands of the `archiveHelper` `add` command:
```yaml
$ <wls-deploy-home>/bin/archiveHelper.sh add -help
```
This will result in the following output:
```yaml
Add items to the archive file.
Usage: archiveHelper add [-help] [COMMAND]

Command-line options:
      -help   Get help for the archiveHelper add command

Subcommands:
  application                     Add application to the archive file.
  applicationPlan                 Add application deployment plan to the archive file.
  classpathLibrary                Add classpath library to the archive file.
  coherenceConfig                 Add a Coherence config file to the archive file.
  coherencePersistenceDir         Add a Coherence persistence directory to the archive
                                    file.
  custom                          Add custom file/directory to the archive file.
  databaseWallet                  Add database wallet to the archive file.
  domainBinScript                 Add $DOMAIN_HOME/bin script to the archive file.
  domainLibrary                   Add $DOMAIN_HOME/lib library to the archive file.
  fileStore                       Add empty file store directory to the archive file.
  jmsForeignServer                Add a JMS Foreign Server binding file to the archive
                                    file.
  mimeMapping                     Add MIME mapping file to the archive file.
  nodeManagerKeystore             Add node manager keystore to the archive file.
  opssWallet                      Add OPSS wallet to the archive file.
  rcuWallet                       Add RCU database wallet to the archive file.
  saml2InitializationData         Add a SAML2 data initialization file to the archive
                                    file.
  script                          Add script to the archive file.
  serverKeystore                  Add a server keystore to the archive file.
  sharedLibrary                   Add shared library to the archive file.
  sharedLibraryPlan               Add shared library deployment plan to the archive
                                    file.
  structuredApplication           Add structured application installation directory to
                                    the archive file.
  weblogicRemoteConsoleExtension  Add the WebLogic Remote Console's Extension
                                    file to the archive file.
```
To display the command-line options for the `archiveHelper` `add application` subcommand:
```yaml
$ <wls-deploy-home>/bin/archiveHelper.sh add application -help
```
This will result in the following output:
```yaml
Add application to the archive file.
Usage: archiveHelper add application [-help] [-overwrite]
                                     -archive_file=<archive_file> -source=<path>

Command-line options:
      -archive_file=<archive_file>
                       Path to the archive file to use.
      -overwrite       Overwrite the existing entry in the archive file, if any
      -source=<path>   File system path to the application to add
      -help            Get help for the archiveHelper add application subcommand

Note: If using an Application Installation Directory, please see the
archiveHelper add structuredApplication command.
```
### Usage scenarios

- `list application`: List the applications in the archive file.
   ```yaml
   $ <wls-deploy-home>/bin/archiveHelper.sh list application -archive_file=C:\temp\archive-helper-test.zip
   ```

- `add application`: Update an existing application in the archive.
   ```yaml
   $ <wls-deploy-home>/bin/archiveHelper.sh add application -archive_file=C:\temp\archive-helper-test.zip -source=C:\temp\my-app.war -overwrite
   ```
   **NOTE**: Without the `-overwrite` option, the application gets added to the archive with a numerical suffix.
