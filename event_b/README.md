# P35 Event B

**M4 is supported within this bounded source-level experiment.** Two focused
components implement the new responsibilities without changing the POST-M4
classes or the cohesive ClientIdentity model. All 129 checks passed. The evidence
supports keeping responsibilities separate; it does **not** establish fewer file
edits, lower total system coupling, or successful upstream integration.

## Frozen starting point

`PRE_EVENT_B` = `b590e1b574891af198e00e332ac290e0efcdf069`. The local tracking branch
`event-b` initially matched it exactly. `SmellDetection` is the default and PR target.
The only initial untracked entry, `.idea/`, was explicitly authorized to remain
untouched. No history, tags, M4/RQ2 evidence, labels, or models were changed.

Read the lecturer's [Event B brief](https://docs.google.com/document/d/1N4ZMvyUxSNoV7p142aAlbKRjGMbDNAud/edit)
and the unchanged [2026-11-08 pre-execution prediction](https://docs.google.com/document/d/1DkdifsOxD1jTiJZqT0Cowb8Ad-xbRlLSmUIwK0a5V_0/edit?tab=t.iwhmdspytf0b).
The audit and exact behavior contract were committed as `abccc8b` before source
implementation. See [AUDIT.md](AUDIT.md) for feasibility, graph coverage limitations,
edge cases, and the distinction between repository evidence and unverified tracker status.

| Case | Frozen classification and manual verdict | Event B input |
|---|---|---|
| ExoPlayer C, 3788627 | label=1, Metric=1, Token=0; verified responsibility problem | All of [m4/after](../m4/after), including TimeUtil, AudioSessionUtil and three deprecated delegates |
| Canal ClientIdentity, 3705164 | label=0, Metric=1, Token=0; cohesive, false positive | Exact [pinned source snapshot](before/canal/ClientIdentity.java), not current upstream HEAD |

Source origins are ExoPlayer [`90cf56092dca07e8752f8f7e063a0b3b98313942`](https://github.com/amzn/exoplayer-amazon-port/blob/90cf56092dca07e8752f8f7e063a0b3b98313942/library/core/src/main/java/com/google/android/exoplayer2/C.java)
and Canal [`08167c95c767fd3c9879584c0230820a8476a7a7`](https://github.com/alibaba/canal/blob/08167c95c767fd3c9879584c0230820a8476a7a7/protocol/src/main/java/com/alibaba/otter/canal/protocol/ClientIdentity.java).
The original ExoPlayer file was retrieved and matched the frozen M4-before hash.
The Canal snapshot is 2,575 bytes, SHA-256
`552ad76e6de306a187b57f3a9009cfa4f0554f45fd546a78506a729e215b614b`.
[SHA256SUMS](evidence/SHA256SUMS) records both original sources and POST-M4 files.
Original classifications remain unchanged. The detector was neither run nor retuned.

## Pressure, hypothesis and alternatives

**C: display a playback duration in minutes:seconds from microseconds.** The
prerecorded hypothesis was that adding presentation policy to C creates another
reason to change; a separate formatter may isolate it at the cost of one class.

| Response | Production change for this responsibility | Main trade-off |
|---|---|---|
| No additional structural change, analyzed | Add C.formatUs to POST-M4 C: 1 existing class edited, 0 new | Fewer classes and one familiar entry point; mixes display policy with constants and compatibility delegates |
| Decomposition, implemented | Add PlaybackDurationFormatter: 0 existing classes edited, 1 new | Keeps display policy outside C and conversions; adds a class and a dependency on C's sentinel contract |

The [formatter](src/com/google/android/exoplayer2/util/PlaybackDurationFormatter.java)
returns ASCII total minutes and two seconds digits, truncates fractional seconds,
returns `--:--` for either sentinel, and rejects all other negatives. It handles
Long.MAX_VALUE without multiplication. At an hour it returns `60:00`, not an hours
format. It divides microseconds directly into display seconds, rather than adding
a presentation method to TimeUtil or routing through deprecated C conversion APIs.
There is no new C delegate because this new API has no existing callers to preserve.

**ClientIdentity: persist destination, clientId and filter in a .properties file.**
The prerecorded hypothesis was that putting save/load on the identity couples its
representation to filesystem, format and error policy; a store may isolate these
details at the cost of a class and explicit field mapping.

| Response | Production change for this responsibility | Main trade-off |
|---|---|---|
| No additional structural change, analyzed | Add save/load to ClientIdentity: 1 existing class edited, 0 new | Mapping stays next to fields; identity gains filesystem, Properties, resource and error handling responsibilities |
| Decomposition, implemented | Add ClientIdentityPropertiesStore: 0 existing classes edited, 1 new | Identity remains cohesive and unchanged; store depends on its accessors/constructor and must track field changes |

The [store](src/com/alibaba/otter/canal/protocol/ClientIdentityPropertiesStore.java)
uses only standard Java APIs. Missing destination/filter keys mean null; empty
values remain empty. Standard Properties stream escaping preserves Unicode,
whitespace, newlines, separators and backslashes. clientId is a required decimal
short. Missing/invalid/out-of-range IDs and malformed Unicode escapes produce
IOException; parse failures retain their cause. Properties applies its own syntax
rules before parsing values, including stripping unescaped leading whitespace.
Null arguments cause NullPointerException. Filesystem failures propagate, streams
close with try-with-resources, and save creates/replaces a file without making
parent directories. Replacement is deliberately non-atomic.

## Measured before/after and dependencies

The post-response design is an **overlay**: the three frozen `m4/after` files plus
the exact Canal snapshot and the two new classes in `src/`. There are no copied or
edited alternatives masquerading as independent production implementations.

| Production unit | Before | After | Measured edit / new explicit imports |
|---|---|---|---|
| C | POST-M4 constants and deprecated delegates; 17 imports | Identical bytes | 0 / 0 |
| TimeUtil | Unit conversion; 1 import | Identical bytes | 0 / 0 |
| AudioSessionUtil | Android service access; 3 imports | Identical bytes | 0 / 0 |
| ClientIdentity | Pinned identity model; 4 imports, no file I/O | Identical source | 0 semantic edits; 1 baseline artifact newly stored / 0 |
| PlaybackDurationFormatter | Absent | New presentation class | 1 added file/class / C |
| ClientIdentityPropertiesStore | Absent | New persistence class | 1 added file/class / IOException, InputStream, OutputStream, Files, Path, Objects, Properties |

There are **2 new behavior classes, 0 edits to existing behavior classes**, plus
1 newly archived original source. The 8 new explicit import declarations are
listed in [imports.txt](evidence/imports.txt); import counts are not a CBO score or
an exhaustive runtime dependency metric. No new third-party production dependency
is introduced. A [small production patch](evidence/new_responsibilities.diff)
contains only the two added behavior classes.

Dependency direction is new display caller -> formatter -> C sentinel constants;
new persistence caller -> store -> ClientIdentity accessors/constructor and JDK
I/O/Properties. C does not depend on the formatter; ClientIdentity does not depend
on the store. Existing C -> TimeUtil/AudioSessionUtil compatibility delegates,
TimeUtil -> C sentinels, and C's Android constant/Context dependencies remain.
The formatter adds a source dependency on C even though primitive sentinel constants
may be inlined. It does not make the real C Android-independent.

Both additions increase the system's classes and dependency edges. Decomposition
keeps the **existing classes'** reasons to change and imports unchanged; it does
not remove the new dependencies from the system. No production caller migration
is measured because complete upstream applications are absent; the test harnesses
are the callers exercised here.

## Expected future change spread, not measured edits

These examples assume unchanged public method signatures. Test and caller updates
depend on the new requirements; they are not counted as observed changes.

| Future pressure | Direct alternative, hypothetical | Chosen decomposition, hypothetical |
|---|---|---|
| Change seconds rounding or display layout | Edit C and formatter expectations | Edit formatter and its expectations; C/TimeUtil unchanged |
| Change properties keys or file error policy | Edit ClientIdentity and persistence expectations | Edit store and persistence expectations; identity unchanged |
| Add another persisted identity field | Edit identity/mapping in one class, plus tests/callers | Edit identity **and** store mapping, plus tests/callers; potentially greater file spread |
| Change sentinel meanings or identity public API | Dependent callers may need edits | Formatter/store and their callers may also need edits; isolation is not guaranteed |

A policy change can touch **one production file in either option**. Neither the
future spread table nor the unimplemented direct alternatives are experimental
measurements. No time saved, merge-conflict reduction or maintainer outcome was measured.

## Verification results

Run from the repository root; build output and runtime files use temporary
directories, leaving m4 and the original snapshot unchanged:

```bash
bash event_b/verify.sh
git diff --exit-code PRE_EVENT_B -- . ':!event_b'
git diff --check PRE_EVENT_B
```

[Recorded output](evidence/test_output.txt): all commands exited **0** on OpenJDK
21.0.13, compiling with `--release 8 -encoding UTF-8 -Xlint:all`.

| Harness | Exact outcome | Coverage |
|---|---|---|
| Unchanged M4 TimeUtilTest | 26/26 checks passed | Original conversions, both sentinels, preserved overflow at extreme inputs |
| PlaybackDurationFormatterTest | 21/21 checks passed | Subsecond/second/minute/hour boundaries, large durations, Long.MAX_VALUE, both sentinels, other negatives, ASCII under Arabic default locale |
| ClientIdentityPropertiesStoreTest | 82/82 checks passed | Real file round-trips checking all 3 fields separately, short extremes, null vs empty, escaping/Unicode, nonmutation, overwrite, missing keys, parse causes, null args and filesystem errors |

The persistence harness demonstrates that baseline equals ignores filter, then
checks filter explicitly after loading. It also tests duplicate/unknown keys and
successful reuse after malformed input. The compiler emitted 3 options warnings
about the obsolete Java 8 source/target level; there were no source warnings.

## Accepted trade-offs, limitations and M4 conclusion

1. **C:** accept one extra formatter class and a dependency on C's sentinel contract
   to keep presentation changes out of constants and conversion code. Do not grow
   it into a general utility dumping ground. Separate display policy is useful
   here, but a one-file edit benefit over the direct alternative is not established.
2. **ClientIdentity:** accept one store class and duplicated field knowledge to keep
   I/O, serialization and error handling out of a cohesive identity model. Adding
   fields can require edits in both files. The simple overwrite can leave a partial
   file on write failure; atomic persistence would require a separate requirement.

Only the two-constant M4 C **stub**, not real Android C or AudioSessionUtil, was
compiled. Canal's exact source was compiled against three labeled **test-only**
stubs for its preexisting Commons Lang/Canal formatting dependencies. StringUtils
and ToStringBuilder throw if invoked; hasFilter/toString behavior was not validated.
There was no Android/full upstream build, integration test, Java 7 bytecode check,
permissions matrix, crash/atomicity test, performance study or concurrent access
test. The new store uses Java 7 APIs/syntax, but the available javac supports
release 8 as its oldest target. Properties comments include a timestamp, so
semantic round-trip, not deterministic bytes, is the contract.

The result **supports** M4's Move Method decision: the new presentation pressure
fits a focused component without undoing the split or changing deprecated APIs,
and all 26 original regression checks still pass. It also supports leaving the
original ClientIdentity cohesive, adding an adapter only for the new synthetic
pressure. That pressure cannot retroactively make its original detector flag
correct. The predictions about isolation are consistent with source evidence;
stronger claims about coupling reduction or measured future change spread remain
unproven. [Append-ready response and trade-offs](RESPONSE.md) are provided for the
Google Doc and shared tracker; neither earlier record was edited.
