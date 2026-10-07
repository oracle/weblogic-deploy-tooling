# WebLogic Deploy Tooling Guidance

## Build and WLST Python

- Build with JDK 17. Set `JAVA_HOME` to a JDK 17 installation and check `mvn -version` before running Maven; `core/pom.xml` enforces Java 17.
- The parent POM declares Jython 2.2.1, whose language baseline is CPython 2.2 syntax. Core Python code runs under WebLogic's WLST. Write code and tests for that baseline even if another installed WebLogic version has newer Jython. Jython and CPython do not have identical standard libraries, so validate library APIs in the target WLST runtime.
- Do not use Python 2.3+ or Python 3 syntax. In particular, the WLST 2.2.1 test runtime rejects conditional expressions (`a if condition else b`) and `with` statements; its library also lacks `tempfile.mkstemp` and `unittest.TestCase.assertTrue`. Use established patterns in nearby code and check new code with WLST tests.
- Bind a caught exception with `except SomeError, error:` rather than `except SomeError as error:`. To catch multiple types, use a tuple: `except (FirstError, SecondError), error:`. The `as` form was added in Python 2.6, and a comma without parentheses binds the exception instead of listing types.
- Core Python tests require WLST: set `WLST_DIR` or Maven's `unit-test-wlst-dir` property to the directory containing `wlst.sh` (or `wlst.cmd`). With JDK 17 and WLST configured, run `mvn -pl core test`. Maven's `-Dtest=...` selects Java tests; the WLST plugin still runs its Python suite.

## Jira

- This repository's Jira issues use the `WDT` project at `https://jira.oraclecorp.com/jira/browse/WDT-<number>`.
- Submit changes through the OraHub repository `weblogic-cloud/weblogic-deploy-tooling` using OraHub merge requests. The GitHub repository `oracle/weblogic-deploy-tooling` receives propagated changes; do not open a GitHub pull request for this workspace's changes. Check `git remote -v` before publishing.
- For a WDT issue, read the live issue through the Jira/Atlassian connection before using its description, status, or comments as work instructions.
- If the local Jira MCP environment defaults `JIRA_PROJECTS_FILTER` to another project, use Jira search with `jql="key = WDT-<number>"` and `projects_filter="WDT"` for read-only WDT issue lookup. A direct `jira_get_issue` call may be restricted by the default filter. Keep Jira credentials out of repository files and tool output.
- The shared WebLogic Jira vetter and authoring guidance is written for `OWLS`. Check its project scope before applying it to WDT work.
