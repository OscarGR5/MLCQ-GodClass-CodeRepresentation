# M4: Move Method refactoring of ExoPlayer `C` (sample 3788627)

**Design problem** (from `rq2/inspection.md`, case 7): `C` is a non-instantiable constants holder
(164 constants) that also contains behaviour with unrelated reasons to change: time conversion
(`usToMs`, `msToUs`, L988–1001) and an Android audio-session service call
(`generateAudioSessionIdV21`, L1009–1013). This violates the Single Responsibility Principle,
localised to these 3 methods.

**Intervention:** Move Method with deprecated delegates.
- `TimeUtil` (new): `usToMs`, `msToUs`, with the logic copied unchanged.
- `AudioSessionUtil` (new): `generateAudioSessionIdV21`, with the logic copied unchanged.
- `C` keeps the 3 method signatures as one-line `@Deprecated` delegates, so existing callers still work.
- Two classes rather than one, so the two unrelated responsibilities aren't recombined; pure-Java
  time logic is now testable without Android.

## Input identity
- `before/C.java`: ExoPlayer `C.java` at commit `90cf56092dca07e8752f8f7e063a0b3b98313942`
  (amzn/exoplayer-amazon-port), 1,015 lines,
  SHA-256 `b35490557ab4af498f679853f973cb013128dbbb234f9877db4bcb8ad5409b2d`.

## Verification
1. **Structure:** `C_before_after.diff` shows one change block (L978–1015): only the 3 method
   bodies were replaced by delegates; all 164 constants and 18 annotation types are unchanged.
2. **Behaviour:** `test/TimeUtilTest.java` compares `TimeUtil` against the original logic
   (copied verbatim) on 12 inputs including edge cases and both sentinels:
   **all 26 checks passed** (`test/test_output.txt`).
3. **Observation:** the original `msToUs` overflows for very large inputs (e.g. `Long.MAX_VALUE` → -1000);
   the refactored version reproduces this exactly. A refactoring must preserve behaviour, so the
   overflow is noted, not fixed.

| | Before | After |
|---|---|---|
| Methods in `C` containing logic | 3 | 0 (3 one-line deprecated delegates) |
| Responsibilities in `C` | constants + time conversion + audio service | constants only (+ temporary delegates) |
| `C` → `Context` dependency | yes | only via the deprecated delegate (removed when delegates are removed) |
| Time conversion testable without Android | no | yes (`TimeUtil`) |

## How to re-run
    mkdir -p m4/test/out
    javac -d m4/test/out m4/test/stubs/com/google/android/exoplayer2/C.java m4/after/TimeUtil.java m4/test/TimeUtilTest.java
    java -cp m4/test/out TimeUtilTest

## Limitations
- `C.java` and `AudioSessionUtil.java` are not compiled: they need the Android SDK.
- `generateAudioSessionIdV21` is verified by reviewing the diff (the delegate forwards the same
  argument to the moved, unchanged method), not by running it.
- `test/stubs/.../C.java` is a test-only stub holding just the 2 constants `TimeUtil` needs,
  copied verbatim from `before/C.java` L48 and L54.
- The `C` → `AudioManager` dependency remains through ~15 constants; the refactoring removes the
  runtime service call from `C`, not all Android coupling.

## Detector prediction (written BEFORE checking)
 We predict the frozen metric SVM will still flag `C` as a God Class after this change,
because its 164 fields and around 900 LOC are unchanged which would mean the detector reacts to size, not to the mixed
responsibilities we fixed.

## AI use
Claude helped us drafted the step-by-step plan and code skeletons, and we  wrote the files, ran the
diff and the test, and checked results. Oscar's ChatGPT-assisted notes identified the candidate;
the team verified it against the code (rq2/inspection.md).
