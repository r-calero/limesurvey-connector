# 3. `validation.pattern` is translated to `re`

Date: 2026-09-30
Status: accepted (revised the same day: translation replaced plain rejection)

## Context

The contract defines `validation.pattern` as ECMAScript regular expression source without flags. The reference validator checks that it compiles with `RegExp` and that a text `defaultValue` matches it, anchored as Angular does. This service never evaluates patterns against user answers, but a front end may validate the same document with the TypeScript package, so both sides must agree on what a pattern means.

The contract keeps a single ECMAScript pattern. A second, Python-specific field would be rejected by the strict TypeScript schema and could drift from the original.

## Decision

- Use the standard `re` module; no ECMAScript engine dependency.
- `survey_structure/patterns.py` parses the ECMAScript source (non-Unicode grammar with Annex B) and emits an equivalent Python expression: named groups and references, back-references to groups that did not participate, forward references, legacy octal and control escapes, identity escapes, class ranges and literal dashes, `\s`, `\S`, `\B`, `.`, `$`, literal braces, and surrogate pairs.
- Matching runs on UTF-16 code units (`utf16_units`), as ECMAScript does without the `u` flag.
- A pattern Python cannot match identically is rejected. Today that is variable-width look-behind, a back-reference inside a repeated group that also contains the referenced capture, and group names with `$`.
- `to_python_pattern` and `test_pattern` expose the translation to library users.

## Consequences

- Every accepted pattern is valid ECMAScript with the same meaning, so a front end never receives a document the TypeScript validator rejects because of its pattern.
- 2,774 of 2,812 reference pattern and value combinations match exactly; the remaining 38 belong to the two rejected patterns in that battery. Rejected and translated constructs are listed in `conformance/known-divergences.json` and covered by tests.

## Update 2026-10-15 (SurveyStructure 2.1.0)

The contract renamed the field to `responseValidation.responseFormatPattern`, added `patternFlags` (`i`, `m`, `s`) and a `pattern-match` condition, and now tests the pattern as written: Angular's anchoring is gone, so a pattern matches anywhere unless it uses `^` and `$`.

- `test_pattern(source, value, flags)` searches instead of matching the whole value.
- `s` makes `.` match any code unit; `m` makes `^` and `$` recognize `\n`, `\r`, `\u2028` and `\u2029`, as ECMAScript does, rather than Python's `\n` only.
- `i` follows ECMAScript's `Canonicalize` without the `u` flag: a unit matches when its simple uppercase form is the same, and a non-ASCII character never matches an ASCII one (`ſ` is not `s`, the Kelvin sign is not `k`). Literals and classes are expanded to the units that share that form; `re.IGNORECASE` is not used.
- A back-reference under `i` is rejected: ECMAScript compares it by canonical case and Python compares it exactly.
- 20,608 pattern, flag and value combinations generated with Node agree, except the 9 back-references under `i` listed in `known-divergences.json`.
