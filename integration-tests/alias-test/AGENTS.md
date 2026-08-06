# Alias Test Guidance

## Alias Test Verify

Run from `integration-tests/alias-test/verify`.

### Resolve the WebLogic Version First

`wls_version` must be the exact canonical version used by the generated alias-test files; Maven accepts only a four- to six-component version number. Do not first invoke Maven with an abbreviated release name such as `26.1` to discover the required format.

Before running the verifier, look up the requested release in the repository's generation pipeline configuration. For development releases, inspect `integration-tests/alias-test/Jenkinsfile.generate-development` (for example, it maps `26.1` to `26.1.0.0.0`). Use that exact value for `-Dwls_version` and for the report filenames. If the requested release is not listed there, obtain its canonical value from the applicable generation/verify pipeline configuration or ask the requester; do not infer the number of trailing components.

For an initial verification run, install WDT and use generated-file download:

`mvn -B verify -DskipTests=true -Dalias-test-skipITs=false -Dalias_test_tenancy=<oci_namespace> -Dalias_test_oci_profile=<oci_profile> -Dwls_version=<version>`

This ensures that `target/weblogic-deploy` exists before verification.  For follow-up runs in the same workspace, after that runtime has been installed, add `-Dskip-wdt-install=true` to avoid reinstalling it.

Do not pass `-Dskip-generated-file-download=true` unless explicitly asked to verify existing local `target` files.

If `WKT_TENANCY` or `WKT_DEFAULT_OCI_PROFILE` are unset, discover a working local OCI profile without printing config contents:

`awk '/^\[.*\]$/ { print }' ~/.oci/config`

Then test likely profiles with:

`oci os ns get --profile <profile> --query data --raw-output`

Use the returned namespace as `alias_test_tenancy` and the profile name as `alias_test_oci_profile`.

Maven may need approval/escalation because `oci-maven-plugin` writes under `~/.m2/caches/kordamp`.

After the run, summarize `target/reportOnline-<version>.txt` and `target/reportOffline-<version>.txt`.

## Confirming Verification Completion

Do not treat the presence, timestamp, or contents of `target/reportOnline-<version>.txt` or `target/reportOffline-<version>.txt` as proof that the current verification run is complete; a prior run can leave stale reports and the current verifier writes reports before its final result is known.

Wait for the `mvn ... verify` command to exit and use its final exit status as the pass/fail result. On success, also confirm that both completion markers exist:

`target/verify-status/doVerifyOnline`

`target/verify-status/doVerifyOffline`

The final `verifyVerification.sh` phase checks these markers and returns a nonzero status when either verification failed. Use the reports only after this completion check, to summarize diagnostics.

## Alias Curly-Brace Values

When fixing alias verify failures, remember that alias string fields can use curly-brace mode substitutions:

`${offline_value:online_value}`

Examples:

- `get_method: "${LSA:GET}"` means offline uses `LSA`, online uses `GET`.
- `wlst_name: "CandidateMachine${:s}"` means offline uses `CandidateMachine`, online uses `CandidateMachines`.
- `${__NULL__:value}` means offline resolves to `null`, online resolves to `value`.

Use this for small offline/online value differences in fields like `wlst_name`, `default_value`, `get_method`, `set_method`, `wlst_type`, and paths. Do not use curly braces in `wlst_mode`; split alias entries if mode availability or version ranges differ.
