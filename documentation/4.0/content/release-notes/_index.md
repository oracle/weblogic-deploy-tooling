+++
title = "Release Notes"
date = 2024-01-09T18:27:38-05:00
weight = 58
pre = "<b> </b>"
+++


### Changes in Release 4.4.0
- [Major New Features](#major-new-features)
- [Other Changes](#other-changes)
- [Bugs Fixes](#bug-fixes)
- [Known Issues](#known-issues)


#### Major New Features
None

#### Other Changes
- #1854 - Added the `merge.server-start-arguments` to the tool.properties file with a default of `true`.  Setting the
          value to `false` will disable the merging and simply replace any existing value to the model value.

#### Bug Fixes
- #1847 - Fixed a number of attributes to correct the alias setting for `uses_path_tokens` to give more accurate
          information for the upcoming WKT UI model editor.
- #1848, #1855 - Fixed a number of attributes that are delimited strings in WLST to allow the use of lists in the model.
- #1849 - Fixed the handling of the JMS `ForeignServer` `ConnectionURL` in the Create Domain and Update Domain Tools.
- #1850 - Fixed a number of attributes that are delimited strings with name-value pairs in WLST to allow the use of
          YAML dictionaries in the model.
- #1851 - Added the merging handler use in `ServerStart` `Arguments` processing to `SystemComponentStart` `Arguments`.

#### Known Issues
- SSH support requires a reasonably recent version of Bouncy Castle.  WDT picks up Bouncy Castle from WLST so, for example,
  the 12.2.1.4.0 GA release fails with the following error, as mentioned at https://github.com/hierynomus/sshj/issues/895.
  Applying a recent PSU should resolve the issue for 12.2.1.4 and 14.1.1.

  ```shell
  SEVERE Messages:
          1. WLSDPLY-20008: verifySSH argument processing failed: Failed to initialize SSH context: Failed to SSH connect to host myhost.oracle.com: no such algorithm: X25519 for provider BC
  ```
