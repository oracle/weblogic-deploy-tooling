+++
title = "Release 4.2.0"
date = 2024-01-09T18:27:38-05:00
weight = 70
pre = "<b> </b>"
+++


### Changes in Release 4.2.0
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1682 - Added support for discovering built-in security provider data in online mode.  This includes
  DefaultAuthenticator users and groups, XACMLAuthorizer policies, XACMLRoleMapper roles, and DefaultCredentialMapper
  user/password credential mappings. As with other discovery features, default values are filtered out and will not
  appear in the model.  By default, discovering users and credential mappings require the use of WDT encryption so that
  no clear text passwords are stored in the model or variable files.
- #1682 - Normalized XACMLRoleMapper role handling by removing the previous discovery of XACMLRoleMapper roles (that was
  not working with newer versions of WebLogic anyway) and removing version limitations during provisioning.
- #1682 - Deprecated the `-use_encryption` command-line argument and replaced it with `-passphrase_prompt` to make the
  purpose of the argument clearer.
- #1682 - Relaxed the JDK 8 requirement to use WDT encryption.  Later versions of JDK 7 have the necessary algorithm
  support so now WDT determines at startup whether the underlying JDK supports WDT encryption or not.
- #1682 - Used the values of the `-admin_user` and provided password to populate the `domainInfo:/AdminUserName` and
  `domainInfo:/AdminPassword` fields when discovering security provider data.
- #1688 - Enhanced variable tokenization support to include passwords in discovered security provider data. 
- #1689 - Added the ability to discover the OPSS wallet when running in online mode.
- #1693 - Changed the `wko`, `wko-dii` (deprecated), and `wko-pv` target values to refer to the latest versions instead
  of WebLogic Kubernetes Operator 3 versions.  Added `wko3`, `wko3-dii`, and `wko3-pv` to accommodate users that still
  require the ability to use these older versions.
- #1697 - Added support for the Prepare Model Tool to preserve any one-way hashed passwords in the model. 
- #1700 - Added support for storing XACML policy and role definitions that could not be converted to their original
  policy and role expressions as XACML files in the archive file.

#### Bug Fixes
- #1687 - Fixed a problem with the Discover Domain Tool not properly handling Data Source user names with spaces with
  older versions of WebLogic Server.
- #1690 - Fixed a problem with determining the default security realm name that caused it to always be `myrealm`.
- #1692 - Fixed a misleading error message when the model points to an application outside of the archive file that
  does not exist.
- #1695 - Fixed an issue where the WebLogic Kubernetes Operator `domain.yaml` was including a placeholder for the
  `domainHome` attribute in all cases so that the WebLogic Image Tool could populate it when creating the image.
  This was occurring even in use cases where the WebLogic Image Tool did not have this information.  WDT no longer does
  this and will only include the `domainHome` in the case where the user has specified it on the command line,
  or in the `kubernetes` section of the model.
- #1698 - Fixed issues with the new messages related to the security provider data discovery features.
- #1701 - Moved the TestSummaryHandler logging class out of the installer since it is only meant for supporting unit tests.
- #1702 - Fixed a bug in deployment plan discovery for exploded applications.
- #1703 - Fixed a bug in discovery of `domainBin` scripts.
- #1705 - Added missing validation for the `WLSUserPasswordCredentialMappings` section.
- #1706 - Fixed a validation bug that was causing lax validation to fail when archive entries were missing.
- #1707 - Fixed a bug in the handling of the `ActiveContextHandlerEntry` attribute of an `Auditor` security provider.

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
