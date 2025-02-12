+++
title = "Release 4.3.2"
date = 2024-01-09T18:27:38-05:00
weight = 66
pre = "<b> </b>"
+++


### Changes in Release 4.3.2
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1778 - Added preliminary support for using an enhanced offline `isSet()` method when determining whether to write
  computed fields to the model during offline discovery.  Once the enhancement is available in a 14.1.2 PSU, we will
  complete the support.

#### Bug Fixes
- #1773 - Reduced the logging level of a message about removing attributes from the model to reduce the
  amount of noise on stdout.
- #1775 - Fixed Discover Domain Tool handling of server keystore files when running with `-skip_archive`.
- #1776 - Fixed issues with the `ManagedExecutorServiceTemplate`, `ManagedScheduledExecutorServiceTemplate`, and
  `ManagedThreadFactoryTemplate` folders so that they can be used in models.
- #1777 - Fixed Create Domain Tool so write the domain's mode-related attributes upfront before the initial call
  to `writeDomain()` so that the dynamically computed fields are properly persisted in `config.xml`.

#### Known Issues
- SSH support requires a reasonably recent version of Bouncy Castle.  WDT picks up Bouncy Castle from WLST so, for example,
  the 12.2.1.4.0 GA release fails with the following error, as mentioned at https://github.com/hierynomus/sshj/issues/895.
  Applying a recent PSU should resolve the issue for 12.2.1.4 and 14.1.1.

  ```shell
  SEVERE Messages:
          1. WLSDPLY-20008: verifySSH argument processing failed: Failed to initialize SSH context: Failed to SSH connect to host myhost.oracle.com: no such algorithm: X25519 for provider BC
  ```

- SSH support for the Update Domain Tool and Deploy Apps Tool does not work when using an archive file and the remote 
  WebLogic Server is running on Windows using the optional, Windows-provided, OpenSSH component.  This is due to an
  issue with the SSHJ library WDT is using.  See https://github.com/hierynomus/sshj/issues/929 for more information.

See https://oracle.github.io/weblogic-deploy-tooling/userguide/limitations/limitations/ for the current set of known limitations.
