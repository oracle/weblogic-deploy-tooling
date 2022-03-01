---
title: "Project structure"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 1
---

This project is structured using the Standard Directory Layout for Maven projects, with two child modules, `core`, `alias-test`, `system-test`, and `installer`. In addition, there is a `documentation` directory containing project documentation.

The `core` module contains the main source code for the project. `core` includes Jython modules and Java classes, as well as typedef files, alias definitions, and the message bundle.

The `system-test` and `alias-test` modules contain test suites for verifying pull requests and nightly regression testing.

Alias definitions are discussed in more detail [here]({{< relref "/developer/alias-definitions.md" >}}).

The `installer` module builds the final installer ZIP file. `installer` includes the assembly definitions, start scripts for each tool for Linux and Windows platforms, and configurations for variable injection and logging.

Two installer files are built under the `WLSDEPLOY_HOME/installer/target` directory, one ZIP file for all platforms, and one `tar.gz` file for those that prefer the `tar.gz` format on UNIX systems.

There are detailed instructions for building the project [here]({{< relref "/developer/buildWDT.md" >}}).
