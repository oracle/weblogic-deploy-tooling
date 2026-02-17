+++
title = "Release Notes"
date = 2024-01-09T18:27:38-05:00
weight = 56
pre = "<b> </b>"
+++


### Changes in Release 4.4.2
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1857 - Changed the Archive Helper Tool's help output to suppress displaying the non-public commands used to
  facilitate integration with the WebLogic Kubernetes Toolkit UI 2.0 so that it can handle archive files larger than 2 GB.

#### Bug Fixes
- #1859 - Fixed version ranges for NovellAuthenticator, IPlanetAuthenticator, and OracleVirtualDirectoryAuthenticator,
  which were removed in in 14.1.2.
- #1861 - Fixed version ranges for OracleUnifiedDirectoryAuthenticator, SAMLIdentityAsserterV2, VirtualUserAuthenticator,
  SAMLCredentialMapperV2 to properly represent the WebLogic Server versions where they exist.
- #1862 - Fixed Discover Domain Tool command-line validation to fail `-discover_security_provider_data` argument in
  offline mode.
- #1863 - Fixed handling of `OptionalFeature` folders across discovery and provisioning.

#### Known Issues
- SSH support requires a reasonably recent version of Bouncy Castle.  WDT picks up Bouncy Castle from WLST so, for example,
  the 12.2.1.4.0 GA release fails with the following error, as mentioned at https://github.com/hierynomus/sshj/issues/895.
  Applying a recent PSU should resolve the issue for 12.2.1.4 and 14.1.1.

  ```shell
  SEVERE Messages:
          1. WLSDPLY-20008: verifySSH argument processing failed: Failed to initialize SSH context: Failed to SSH connect to host myhost.oracle.com: no such algorithm: X25519 for provider BC
  ```
