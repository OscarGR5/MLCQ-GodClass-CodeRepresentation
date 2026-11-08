# Event B audit and behavior contract

Recorded 2026-11-08 after read-only inspection, before implementation. This defines
the experiment's behavior, not a revision of the earlier prediction.

## Baseline and evidence

- `event-b` was created locally tracking `origin/event-b`. Its initial HEAD and
  peeled `PRE_EVENT_B` both equal `b590e1b574891af198e00e332ac290e0efcdf069`.
  No tracked changes existed. The only untracked entry was `.idea/`, explicitly
  authorized to remain untouched and excluded from staging.
- Read the local `../Event B/P35_Event_B_STUDENT.docx`, its connected Drive copy,
  `rq2/inspection.md`, `m4/README.md`, `m4/after/`, the M4 diff, regression test,
  stub and recorded output. The frozen Week 9 decision and executable evidence
  are present in the repository. The provided Google Doc's pre-execution Event B
  prediction was read without editing it. A shared tracker cell was not independently
  verified; this task requests append-ready response text, not a tracker edit.
- Case 3788627: label=1, Metric=1, Token=0; manually verified mixed responsibilities.
  Start from all three POST-M4 files, including C's deprecated delegates. Original
  ExoPlayer revision `90cf56092dca07e8752f8f7e063a0b3b98313942` was fetched read-only;
  its C.java matches `m4/before/C.java`, SHA-256
  `b35490557ab4af498f679853f973cb013128dbbb234f9877db4bcb8ad5409b2d`.
- Case 3705164: label=0, Metric=1, Token=0; manually verified cohesive identity object.
  Retrieved only the pinned Canal revision
  `08167c95c767fd3c9879584c0230820a8476a7a7`, path
  `protocol/src/main/java/com/alibaba/otter/canal/protocol/ClientIdentity.java`.
  Exact source: 2,575 bytes, SHA-256
  `552ad76e6de306a187b57f3a9009cfa4f0554f45fd546a78506a729e215b614b`.
  It imports Serializable, Commons Lang StringUtils and ToStringBuilder, and
  CanalToStringStyle. Equality deliberately excludes filter. No persistence exists.

## Build feasibility

This is a research snapshot repository, with no tracked Maven/Gradle build or
complete upstream Java/Android project. OpenJDK/javac 21.0.13 and Maven are available;
Gradle is not on PATH and no Android SDK is configured in ANDROID_HOME/ANDROID_SDK_ROOT.
The pinned ExoPlayer core build requests Java 8; Canal's pinned root pom requests
Java 7 and already manages Commons Lang 2.6. No upstream HEAD is substituted.

Use `javac --release 8` for focused tests (this JDK's minimum supported release),
real temporary filesystem operations for persistence, and the existing two-constant
C stub for formatter/TimeUtil tests. For the exact Canal snapshot, use explicit
test-only compile stubs for its three unrelated dependencies; those stubs throw
if their behavior is invoked. Do not claim validation of hasFilter/toString,
actual Android C or AudioSessionUtil compilation, upstream integration, or Java 7
bytecode compatibility. Re-run the unchanged M4 TimeUtilTest in a temporary output
directory outside m4/. These constraints do not prevent testing the new behaviors.

Graph verification tier: Verify. Project `mlcq-godclass-coderepresentation`, recorded
generation `2026-10-18T14:51:49Z`, fast index. Symbol lookup returned no matches for
C/TimeUtil/AudioSessionUtil/ClientIdentity and relevant methods. Coverage for all
eight inspected M4/RQ2 evidence paths was `freshness: not_tracked`; m4 scope had
zero recorded entries. Therefore conclusions rely on direct source/diff reads,
not absence of graph edges or a claim of complete graph coverage.

## Exact behavior fixed before implementation

### Playback duration

`PlaybackDurationFormatter.formatUs(long durationUs)` returns ASCII total minutes,
a colon, and exactly two seconds digits. Minutes are not padded or capped at 59.
Nonnegative fractional seconds truncate toward zero: 999,999 us -> `0:00`,
59,999,999 us -> `0:59`, 60,000,000 us -> `1:00`, 3,600,000,000 us -> `60:00`.
Zero is `0:00`. Both C.TIME_UNSET and C.TIME_END_OF_SOURCE return `--:--`, since
neither specifies a finite duration. Every other negative value throws
IllegalArgumentException. Long.MAX_VALUE must work without multiplication/overflow.
Output is independent of the default locale. No localization or hours format is added.

### Client identity properties

`ClientIdentityPropertiesStore.save(Path, ClientIdentity)` and `load(Path)` perform
round-trip persistence of destination, clientId and filter using Properties and Files.
The store lives beside the identity class and depends on its public accessors and
constructor; the identity never depends on the store.

- Property keys: `destination`, `clientId`, `filter`. Save writes clientId as decimal.
  All short values, including negative and boundary values, are supported.
- Null destination/filter are represented by absent keys; empty strings remain
  present and empty. Preserve whitespace, separators, backslashes, newlines and Unicode.
  Use standard Properties InputStream/OutputStream escaping (ISO-8859-1 plus Unicode
  escapes), not a custom file format. No trimming of string field values.
- Load requires clientId; missing, nonnumeric, whitespace-padded, or out-of-short-range
  values cause IOException. Malformed Properties Unicode escapes also cause IOException
  with the original cause. Missing destination/filter decode to null. Unknown keys are
  ignored; duplicate keys follow Properties' last-value behavior.
- Null Path or null identity arguments cause NullPointerException before file writes.
  Load returns a new identity; save does not mutate the supplied object.
- Save creates or replaces the named file, does not create parent directories, and
  removes obsolete keys on replacement. Streams close on success and failure.
  Filesystem errors propagate as IOException; no silent defaults or catch-and-continue.
  Atomic replacement, crash recovery, locking, concurrent mutation, permission policy,
  schema migration and byte-for-byte stable output are outside this single-file task.

## Alternatives and intended implementation

For each case, analyze adding the new behavior directly to the existing class
(C.formatUs; ClientIdentity.save/load) versus implementing a focused formatter/store.
The former needs fewer classes and is plausible for a small change, but places display
policy in C and filesystem/format/error policy in ClientIdentity. Choose two focused
components: one class per new responsibility, no interface hierarchy or framework.
Reuse the frozen M4 files in place and preserve the exact Canal file as a referenced
baseline, rather than duplicating production variants. Record measured file changes
separately from hypothetical future edits. Both direct alternatives could also confine
an internal policy change to one file; do not predict fewer files automatically.

The earlier hypotheses remain hypotheses until verification. Neither variant retunes
or retrains the detector or changes the original false-positive classification.
