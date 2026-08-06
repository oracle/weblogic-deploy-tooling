# Alias Metadata Editing Guidance

This guidance applies to the alias metadata in `category_modules`.

## Work From the Requested Report Scope

- Treat errors, warnings, and informational findings as separate scopes. Change only the finding classes the user requested.
- Map each reported WLST/WDT location to the actual folder in the metadata. The root location `/` maps to `Domain.json`, but other report locations do not always map directly to a same-named JSON file.
- Search by both location and attribute name. The same attribute can occur in several category modules; change every reported location and no unreported locations.
- Treat the WLS value in a default-mismatch error as the expected value, but preserve its exact case and JSON type. In particular, the string `"None"` is different from JSON `null`, even though verifier output can make them look similar.
- Ask the user when the correct MBean owner, mode, version, type, or value cannot be established from the report and authoritative local sources. Do not guess.

## Preserve Version History

- Preserve every older alias entry. Do not delete, merge, or consolidate historical entries unless the user explicitly requests it.
- For a behavior change beginning with WLS 26.1.0.0.0, use the alias boundary `26.1`.
- When the current entry is open-ended, change only its upper bound to `26.1`, then add a copied entry with version `[26.1,)` on the next physical line.
- Keep every field other than `version` and the field being corrected unchanged. This includes `wlst_mode`, `wlst_name`, `wlst_path`, `wlst_type`, access settings, methods, and special metadata.
- If an entry for `[26.1,)` already exists, update that entry instead of adding a duplicate.
- Ensure ranges do not overlap for either offline or online mode. A range split must be contiguous at the boundary, with exactly one applicable entry for each affected mode and version.

For example, when offline changed from `null` to `disabled` at 26.1 while online remained `disabled`:

```json
"Example": [
    {"version": "[14.1.2,26.1)", "wlst_mode": "both", "wlst_name": "Example", "wlst_path": "WP001", "default_value": "${__NULL__:disabled}", "wlst_type": "string" },
    {"version": "[26.1,)",       "wlst_mode": "both", "wlst_name": "Example", "wlst_path": "WP001", "default_value": "disabled",             "wlst_type": "string" }
]
```

## Handle Offline and Online Values Deliberately

- Curly-brace values have the form `${offline_value:online_value}`.
- Use `__NULL__` when one side must resolve to null; for example, `${__NULL__:disabled}` means offline `null` and online `disabled`.
- Use JSON `null` when the value is null in every applicable mode. Do not use the string `"null"`.
- An entry with `"wlst_mode": "both"` applies to both offline and online verification. Do not add a second online entry when the existing versioned entry already uses `both`.
- Use separate `offline` and `online` entries when mode availability or version ranges differ. Do not use curly braces in `wlst_mode`.
- Curly-brace substitutions may be used for small mode-specific differences in fields such as `default_value`, `wlst_name`, `wlst_type`, methods, and paths.

## Add Missing Attributes Carefully

- Confirm the owning MBean, introduction version, mode availability, WLST name, WLST path, type, and defaults before adding an attribute.
- Prefer authoritative local WLS sources such as the MBean interface, BeanInfo, generated MBean implementation, and WLST behavior. Use adjacent alias entries only to establish formatting and structural conventions, not to invent metadata.
- Add an attribute at the version where WLS introduced it. For an attribute introduced in 26.1.0.0.0, use `[26.1,)`.
- Use `wlst_mode: "both"` only when the attribute exists in both modes. An offline-only folder or attribute must not acquire invented online metadata.
- Match the surrounding attribute ordering, alignment, `wlst_path`, and object layout.
- If offline and online reports both identify the same missing attribute and its metadata is identical in both modes, add one `both` entry rather than two overlapping entries.

## Preserve File Style and Scope

- Put every newly added version entry on its own physical line.
- Preserve the surrounding indentation, spacing, alignment, ordering, commas, and line endings. Do not reformat the whole file.
- Preserve the original copyright start year and update its ending year when editing a metadata file.
- Do not perform broad search-and-replace operations for repeated attribute names.
- Do not change warnings, informational findings, or adjacent metadata unless they are explicitly in scope.
- Honor task-specific source-control restrictions. If Git operations are prohibited, do not use Git even for inspection.

## Validate the Result

- Parse every edited JSON file with `jq empty`.
- Check edited files for tabs and trailing whitespace.
- Audit the requested findings one by one. Confirm the number of corrected attributes equals the requested error count, each target resolves exactly once for the requested version and mode, and each split predecessor ends at the new boundary.
- From the repository root, run the alias content and syntax tests without invoking the normal Maven lifecycle:

```text
mvn -B -pl core resources:resources
mvn -B -pl core process-test-resources wlst-test:test@python-tests
```

- When the required WLS and OCI artifacts are available, rerun the relevant offline or online integration verification as described in `integration-tests/alias-test/AGENTS.md`.
