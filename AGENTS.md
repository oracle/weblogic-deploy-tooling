# WebLogic Deploy Tooling Guidance

## Build and WLST Python

- Build with JDK 17. Set `JAVA_HOME` to a JDK 17 installation and check `mvn -version` before running Maven; `core/pom.xml` enforces Java 17.
- The parent POM declares Jython 2.2.1, whose language baseline is CPython 2.2 syntax. Core Python code runs under WebLogic's WLST. Write code and tests for that baseline even if another installed WebLogic version has newer Jython. Jython and CPython do not have identical standard libraries, so validate library APIs in the target WLST runtime.
- Do not use Python 2.3+ or Python 3 syntax. In particular, the WLST 2.2.1 test runtime rejects conditional expressions (`a if condition else b`) and `with` statements; its library also lacks `tempfile.mkstemp` and `unittest.TestCase.assertTrue`. Use established patterns in nearby code and check new code with WLST tests.
- Bind a caught exception with `except SomeError, error:` rather than `except SomeError as error:`. To catch multiple types, use a tuple: `except (FirstError, SecondError), error:`. The `as` form was added in Python 2.6, and a comma without parentheses binds the exception instead of listing types.
- Core Python tests require WLST: set `WLST_DIR` or Maven's `unit-test-wlst-dir` property to the directory containing `wlst.sh` (or `wlst.cmd`). With JDK 17 and WLST configured, run `mvn -pl core test`. Maven's `-Dtest=...` selects Java tests; the WLST plugin still runs its Python suite.

## PyOrderedDict Portability and Review

- In WLST Python, avoid `.get()` and `.values()` on WDT's `oracle.weblogic.deploy.util.PyOrderedDict`, including variables that may contain model-loader dictionaries. Apply this rule across supported Jython versions even when a call works on the older test runtime.
- Use `dictionary_utils.get_element(mapping, key, default_value)` for lookups with a fallback, and `getValues()` for ordered values from a `PyOrderedDict`. Membership checks and indexing are also supported. Ordinary Python `dict`, Java `Properties`, and WLST helper methods named `get` are not affected by this restriction.
- Newer Jython can replace these Python-visible methods with Java Map adapters that dereference a null internal Java proxy. The dictionary and lookup arguments can all be valid. A Java override or guard may be bypassed; changing arguments or adding a guard inside the override does not fix that dispatch problem. Preserve internal Java `get()` calls used by `PyOrderedDict` indexing and `pop()`.
- During review, inspect changed `.get()` and `.values()` calls and trace their receiver types through callers and producers. Include related deployment, discovery, prepare-model, and credential-handling paths when model dictionaries flow through them; method names alone do not establish whether a call is affected.
- Regression tests for model-dictionary paths must exercise `PyOrderedDict` inputs, not only native Python dictionary literals. Validate relevant operations on a newer supported WLST runtime as well as the legacy baseline: passing the Jython 2.2.1 suite alone does not detect this adapter failure. For credential paths, verify explicit-key precedence, version-dependent behavior, and preservation of model values where the operation promises not to mutate them.

## Jira

- This repository's Jira issues use the `WDT` project at `https://jira.oraclecorp.com/jira/browse/WDT-<number>`.
- Submit changes through the OraHub repository `weblogic-cloud/weblogic-deploy-tooling` using OraHub merge requests. The GitHub repository `oracle/weblogic-deploy-tooling` receives propagated changes; do not open a GitHub pull request for this workspace's changes. Check `git remote -v` before publishing.
- For a WDT issue, read the live issue through the Jira/Atlassian connection before using its description, status, or comments as work instructions.
- If the local Jira MCP environment defaults `JIRA_PROJECTS_FILTER` to another project, use Jira search with `jql="key = WDT-<number>"` and `projects_filter="WDT"` for read-only WDT issue lookup. A direct `jira_get_issue` call may be restricted by the default filter. Keep Jira credentials out of repository files and tool output.
- The shared WebLogic Jira vetter and authoring guidance is written for `OWLS`. Check its project scope before applying it to WDT work.
