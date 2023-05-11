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

1. Set (and export) the following environment variables:

    - `WLST_DIR` - set to `$MW_HOME/oracle_common/common/bin`, where `$MW_HOME` is the path to a WLS 12.2.1.x or newer installation directory.
    - `WDT_SCM_REPO_URL` - set to the browsable URL to the project (e.g., `https://github.com/oracle/weblogic-deploy-tooling`)
    - `WDT_SCM_REPO_CONN` - set to the clonable URL for the project (e.g., `git@github.com:oracle/weblogic-deploy-tooling.git`)

2. In the `weblogic-deploy-tooling` project directory, run the `mvn -B release:prepare release:perform` command.

   - If the next development version is changing the major or minor version, override the default `developmentVersion` 
     property on the command line.  For example,  
     `mvn -B -DdevelopmentVersion=3.2.0-SNAPSHOT release:prepare release:perform`.
   - If your SSH private key has a passphrase, watch the build closely because it will prompt for your passphrase multiple times.
     Failure to enter it in a timely manner may result in a failure.

3. If the build fails, run the `mvn -B release:rollback` command to undo it and start over from Step 2., after correcting the issue. 
4. After the software has been released, move on to the GitHub Release Process.

### GitHub release process
Note that this process relies on the WDT installers being in your local Maven repository.  As such, it is critical for
the same user to run these steps on the same machine as the steps from the previous section!

1. Save the release notes in the file `<wdt-project-directory>/target/ReleaseNotes.md`.
2. Run the command `mvn -f github-release.xml -DreleaseVersion=<release version number> verify` to create the draft GitHub Release.
3. Log into [GitHub](https://github.com/oracle/weblogic-deploy-tooling), go to the Releases page, review/edit the draft release, and then publish the release.
