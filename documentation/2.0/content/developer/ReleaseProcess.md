---
title: "WDT project release process"
date: 2019-02-23T17:19:24-05:00
draft: false
weight: 5
---

This document describes the process that should be followed to create a WebLogic Deploy Tooling (WDT) release.

### Prerequisites
- A local installation of WebLogic Server 12.2.1.x must be available.
- The person running the release process must have admin privileges on the [WebLogic Deploy Tooling GitHub repo](https://github.com/oracle/weblogic-deploy-tooling) because the release process pushes to the master branch directly.
- The person running the release process needs to create a GitHub Personal Access Token for the repository with (at least) the `repo:status`, `repo_deployment`, `public_repo`, and `security_events` privileges.
- The person running the release process needs a server added to their Maven `settings.xml` file, where the GitHub Personal Access Token is stored, as shown below.  Note that this token can either be stored in plain text or encrypted using [Maven password encryption](https://maven.apache.org/guides/mini/guide-encryption.html).

```xml
  <servers>
    <server>
      <id>github</id>
      <passphrase>store plain text or encrypted token here</passphrase>
    </server>
  </servers>
```

- If the machine from which the release process is being run requires a proxy server to access the Internet, the person running the release process needs an active proxy configured in their Maven `settings.xml` file.

```xml
  <proxies>
    <proxy>
      <active>true</active>
      <id>my-proxy</id>
      <protocol>http</protocol>
      <host>proxy server DNS name</host>
      <port>proxy server port</port>
      <nonProxyHosts>list of DNS names/patterns separated by |</nonProxyHosts>
    </proxy>
  </proxies>
```

### Software release process
The best practice is to write the release notes that will be published to GitHub prior to starting the steps below.

1. Set (and export) the environment variable `WLST_DIR` to `<WLS-install-dir>/oracle_common/common/bin`, replacing `<WLS-install-dir>` with the full path to the WLS 12.2.1.x installation directory.
2. In the `weblogic-deploy-tooling` project directory, create a file called `release.properties` with content similar to the example shown below.  Note that the example is configured to cut the 1.9.11 release.

```properties
tag=release-1.9.11
releaseVersion=1.9.11
developmentVersion=1.9.12-SNAPSHOT
```

3. In the `weblogic-deploy-tooling` project directory, run the `mvn -B release:prepare release:perform` command.  If your SSH private key has a passphrase, watch the build closely because it will prompt for your passphrase multiple times.  Failure to enter it in a timely manner may result in a failure.
4. If the build fails, run the `mvn -B release:rollback` command to undo it and start over from Step 2., after correcting the issue.
5. After the software has been released, move on to the GitHub Release Process.

### GitHub release process
Note that this process relies on the WDT installers being in your local Maven repository.  As such, it is critical for the same user to run these steps on the same machine as the steps from the previous section!

1. Save the release notes in the file `<wdt-project-directory>/target/ReleaseNotes.md`.
2. Run the command `mvn -f github-release.xml -DreleaseVersion=<release version number> verify` to create the draft GitHub Release.
3. Log into [GitHub](https://github.com/oracle/weblogic-deploy-tooling), go to the Releases page, review/edit the draft release, and then publish the release.
