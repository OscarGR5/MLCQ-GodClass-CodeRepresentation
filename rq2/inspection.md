# RQ2 inspection: first 10 Metric-vs-Token disagreements

**RQ2.** Do the disagreements correspond to genuinely different design responsibilities, and what refactoring decision follows from the code evidence?

**Goal:** for each of our 10 frozen disagreement cases, read the actual Java code and decide whether the class has a real design problem. This is the evidence for RQ2 and the source of our M4 design decision.

## The rule (frozen in M1)

- **Clear design problem:** the class does separate, unrelated jobs (different reasons to change), and you can point to the specific methods or fields that show it.
- **No clear problem:** the class does one coherent job, even if it's big.
- **Unclear:** not enough code or context to judge fairly.
- Size alone is NOT a problem. A detector flag or an AI summary alone is NOT evidence.

Cases are the first 10 Metric-vs-Token disagreements in `m2/disagreements.csv`, in sample_id order. Only the sampled lines are judged (cases 6 and 10 are nested classes).

## Summary

| # | sample_id | Class | Label | Metric | Token | Verdict | Inspected by | Checked by |
|---|---|---|---|---|---|---|---|---|
| 1 | 3705164 | `ClientIdentity` | 0 | 1 | 0 | No clear problem | Tudor | Oscar |
| 2 | 3717506 | `BundleListener` | 0 | 0 | 1 | No clear problem | Oscar | Tudor |
| 3 | 3727271 | `DruidPooledCallableStatement` | 1 | 1 | 0 | No clear problem | Tudor | Oscar |
| 4 | 3763661 | `SetOrderReferenceDetailsRequest` | 1 | 1 | 0 | No clear problem | Oscar | Tudor |
| 5 | 3772084 | `PrivateIonDatagram` | 0 | 0 | 1 | No clear problem | Tudor | Oscar |
| 6 | 3787706 | `Split` (nested) | 0 | 0 | 1 | No clear problem | Oscar | Tudor |
| 7 | 3788627 | `C` | 1 | 1 | 0 | **Clear design problem** | Tudor | Oscar |
| 8 | 3796929 | `MqttDTO` | 1 | 1 | 0 | No clear problem | Oscar | Tudor |
| 9 | 3804138 | `ZookeeperServerCnxnFactory` | 0 | 0 | 1 | No clear problem | Tudor | Oscar |
| 10 | 3817323 | `RowRange` (nested) | 0 | 0 | 1 | No clear problem | Oscar | Tudor |

All inspections and checks dated 05/11/2026.

---

## Case 1: 3705164, `ClientIdentity` (alibaba/canal, lines 14–105)

- **Link:** https://github.com/alibaba/canal/blob/08167c95c767fd3c9879584c0230820a8476a7a7/protocol/src/main/java/com/alibaba/otter/canal/protocol/ClientIdentity.java#L14-L105
- **Label:** 0 (not God Class) · **Metric:** 1 · **Token:** 0 · 10 methods / 4 fields / 75 LOC

**Responsibilities seen:** One, representing the identity of a Canal client, subscriber to a data destination. Supporting behaviour for that one concept is: construction, field access, a filter check, string formatting, and value equality.

**Code evidence:**
- Fields: `destination`, `clientId`, `filter` (lines 17–19) plus `serialVersionUID` (line 16)
- Constructors (lines 21–34): only set those three fields
- `hasFilter()` (lines 36–41): checks whether `filter` is non-blank
- Getters/setters (lines 45–67): one pair per field
- `toString()` (lines 69–71): formats the object for logging
- `equals()`/`hashCode()` (lines 73–103): compare `clientId` and `destination`
- Every method uses only the class's own fields; no calls to databases, network, files or UI

**Verdict:** No clear problem

**Reason:** All methods serve the one concept of representing a client's identity and work on the same 3 fields, so it has high cohesion and one reason to change. The 10 methods are mostly one-line accessors plus standard `equals`/`hashCode`, which probably explains the metric detector's flag (method count and branches) rather than any mixed responsibility.

**Inspected by:** Tudor, 05/11/2026 · **Checked by:** Oscar, 05/11/2026


---

## Case 2: 3717506, `BundleListener` (alibaba/atlas, interface, lines 24–32)

- **Link:** https://github.com/alibaba/atlas/blob/e8c7b3f1ff14b2a1df64321c6992b796cae7d732/atlas-core/src/main/java/org/osgi/framework/BundleListener.java#L24-L32
- **Label:** 0 · **Metric:** 0 · **Token:** 1 · 1 method / 0 fields / 9 LOC

**Responsibilities seen:** It defines one: receiving notifications when an OSGi bundle changes its lifecycle state.

**Code evidence:**
- `BundleListener extends EventListener` (line 24)
- Declares only one method, `bundleChanged(BundleEvent event)` (line 31)

**Verdict:** No clear problem

**Reason:** The interface has one cohesive responsibility and doesn't combine unrelated functionality. Its single method handles bundle lifecycle notifications. There's no evidence of excessive responsibilities or any reason to refactor it.

**Observations:** Our manual verdict agrees with the Metric-based prediction (0) but disagrees with the Token-based prediction (1). The interface declares only one lifecycle notification method, providing no evidence of multiple unrelated responsibilities.

**Inspected by:** Oscar, 05/11/2026 · **Checked by:** Tudor, 05/11/2026


---

## Case 3: 3727271, `DruidPooledCallableStatement` (alibaba/druid, lines 40–1089)

- **Link:** https://github.com/alibaba/druid/blob/768469fe4d1340efe1036453366a58c9ab7e30d1/src/main/java/com/alibaba/druid/pool/DruidPooledCallableStatement.java#L40-L1089
- **Label:** 1 (God Class) · **Metric:** 1 · **Token:** 0 · 116 methods / 1 field / 928 LOC

**Responsibilities seen:** A connection-pool wrapper around a JDBC `CallableStatement`. It passes every call on to the real statement, applies the pool's error handling and wraps returned `ResultSet`s so the pool can track them.

**Code evidence:**
- The JDBC interface (line 40) defines the ~100 methods
- The one own field (line 42), `stmt`, the wrapped real statement, is set in the constructor (lines 44–47)
- 89 of 98 methods, e.g. `registerOutParameter` (lines 54–60) and `wasNull` (lines 72–78), use one identical pattern: `try { stmt.X(..) } catch (Throwable t) { throw checkException(t); }`
- `getObject` appears 4 times (lines 199, 231, 682, 701), plus a private `wrapObject` (lines 208–219) which wraps a returned `ResultSet` in a `DruidPooledResultSet` and registers it with `addResultSetTrace`
- `getObject(.., Class<T>)` appears twice (lines 1070–1076) and throws `SQLFeatureNotSupportedException`
- `getCallableStatementRaw()` (lines 49–51) and `unwrap()` (lines 1079–1088) give access to the underlying statement
- No calls to other systems beyond the wrapped `stmt` and the pool's own helpers (`checkException`, `addResultSetTrace`)

**Verdict:** No clear problem

**Reason:** Every method serves one job, acting as a pooled wrapper around the wrapped `stmt`, and nothing calls other systems beyond the pool's own helpers, so there's no hidden second responsibility. The large size of the class is imposed by the JDBC `CallableStatement` interface, and the 4 `getObject` and `wrapObject` methods belong to that same job, since the pool must track the result sets it hands out.

**Observations:** Our verdict disagrees with the dataset label (1 = God Class), mainly due to the interface-driven size.

**Inspected by:** Tudor, 05/11/2026 · **Checked by:** Oscar, 05/11/2026


---

## Case 4: 3763661, `SetOrderReferenceDetailsRequest` (amzn/amazon-pay-sdk-java, lines 25–272)

- **Link:** https://github.com/amzn/amazon-pay-sdk-java/blob/5a3547d00c796aab8f0c8ac12e0310f7a5c4678a/src/com/amazon/pay/request/SetOrderReferenceDetailsRequest.java#L25-L272
- **Label:** 1 · **Metric:** 1 · **Token:** 0 · 20 methods / 10 fields / 224 LOC

**Responsibilities seen:** Represents the parameters required for an Amazon Pay SetOrderReferenceDetails request, including order information, seller details and payment authorization settings.

**Code evidence:**
- Lines 32–44: defines 10 fields related to the same payment request
- Lines 55–58: constructor initializes the order reference ID and amount
- Lines 68–152 and 244–247: setter methods configure request parameters and return the object to support method chaining
- Lines 158–234: getter methods retrieve the stored parameters
- Lines 257–270: `toString()` provides a string representation of the request

**Verdict:** No clear problem

**Reason:** Although the class contains many fields and methods, they all support the main responsibility of representing and configuring an Amazon Pay order-reference request. Most methods are simple getters and setters rather than unrelated operations. The class's size alone doesn't establish it as a God Class.

**Observations:** Our inspection disagrees with the Metric-based prediction and dataset label, both of which classify this as a God Class. Although the class contains multiple fields and methods, they all serve the same request-related responsibility. Our verdict agrees with the Token-based prediction.

**Inspected by:** Oscar, 05/11/2026 · **Checked by:** Tudor, 05/11/2026


---

## Case 5: 3772084, `PrivateIonDatagram` (amzn/ion-java, interface, lines 23–28)

- **Link:** https://github.com/amzn/ion-java/blob/a19302d1ebcc5e8ca41d19342581364f89d09c1a/src/software/amazon/ion/impl/PrivateIonDatagram.java#L23-L28
- **Label:** 0 · **Metric:** 0 · **Token:** 1 · 1 method / 0 fields / 6 LOC

**Responsibilities seen:** `PrivateIonDatagram` is a 6-line interface, so it's only responsible for declaring one extra operation, `appendTrailingSymbolTable`.

**Code evidence:**
- Line 23: `@Deprecated`
- Lines 24–25: `interface PrivateIonDatagram extends PrivateIonValue, IonDatagram` (combines two interfaces; doesn't inherit any fields or code)
- Line 27: 1 method, `void appendTrailingSymbolTable(SymbolTable symtab);`

**Verdict:** No clear problem

**Reason:** This interface only has a single method and doesn't inherit any fields or code through the two other interfaces it extends from.

**Observations:** The token model flagged this 6-line, one-method interface as a God Class (label 0, Metric 0), so its flag can't be explained by size or responsibilities. It's most likely reacting to vocabulary that's common in the project's larger classes, like Ion/symbol-table terms, rather than the structure.

**Inspected by:** Tudor, 05/11/2026 · **Checked by:** Oscar, 05/11/2026


---

## Case 6: 3787706, `Split` (nested class in TridentFastWordCount.java, alibaba/jstorm, lines 45–53)

- **Link:** https://github.com/alibaba/jstorm/blob/5d6cde22dbca7df3d6e6830bf94f98a6639ab559/example/sequence-split-merge/src/main/java/org/apache/storm/starter/trident/TridentFastWordCount.java#L45-L53
- **Label:** 0 · **Metric:** 0 · **Token:** 1 · 1 method / 0 fields / 9 LOC
- Judged only lines 45–53, not the whole file.

**Responsibilities seen:** Splits an input sentence into individual words and emits each word for further processing in the Trident topology.

**Code evidence:**
- Line 45: `Split extends BaseFunction`, defining it as a Trident processing function
- Lines 47–52: the single `execute()` method retrieves the input sentence using `tuple.getString(0)`, splits it using `sentence.split(" ")` and emits each word through `collector.emit(new Values(word))`
- The class has no fields and no additional methods

**Verdict:** No clear problem

**Reason:** The class has one responsibility only, which is splitting a sentence into words. All its operations contribute directly to this purpose. There are no unrelated responsibilities.

**Observations:** Our manual verdict agrees with the Metric-based prediction (0) but disagrees with the Token-based prediction (1). The sampled class has one method that splits sentences into words, with no evidence of unrelated responsibilities.

**Inspected by:** Oscar, 05/11/2026 · **Checked by:** Tudor, 05/11/2026


---

## Case 7: 3788627, `C` (amzn/exoplayer-amazon-port, lines 39–1015)

- **Link:** https://github.com/amzn/exoplayer-amazon-port/blob/90cf56092dca07e8752f8f7e063a0b3b98313942/library/core/src/main/java/com/google/android/exoplayer2/C.java#L39-L1015
- **Label:** 1 · **Metric:** 1 · **Token:** 0 · 3 methods / 164 fields / 908 LOC

**Responsibilities seen:** 3 responsibilities observed. The first is defining the library's shared constants (time sentinels, audio, video, network, track selection, playback), which is its intended job as a non-instantiable constants holder. The second is converting times between microseconds and milliseconds, and the third is generating an audio-session ID by calling an Android system service at runtime.

**Code evidence:**
- Lines 40–42: `public final class C` with a private constructor `private C() {}`, so it's designed as a non-instantiable constants holder
- Lines 48–979: `public static final` constants across many domains (`USAGE_` 16, `ENCODING_` 13, `STREAM_` 9, `TRACK_` 9, `NETWORK_` 9, `MSG_` 8, `COLOR_` 8, `AUDIOFOCUS_` 5)
- About 15 constants copy values from Android's `AudioManager` (e.g. lines 139, 246, 449), so `C` depends on `AudioManager` through its constants anyway
- Lines 988–990 `usToMs()` and lines 999–1001 `msToUs()`: executable time-conversion logic, with special handling for `TIME_UNSET` and `TIME_END_OF_SOURCE`
- Lines 1009–1013: `generateAudioSessionIdV21(Context)` takes an Android `Context` and calls `getSystemService(AUDIO_SERVICE).generateAudioSessionId()`. This is a live call to an Android system service and the only member that needs `Context`
- Corroboration: a later version of this repo (commit `ebceee0`, `library/common/.../C.java`, lines 1365–1390) marks all 3 methods `@Deprecated` and delegates them to `Util`

**Verdict:** Clear design problem

**Reason:** This class violates the Single Responsibility Principle, since the class has 3 groups with unrelated triggers: new codecs/stream types (constants), a time-sentinel bug via `usToMs()` and `msToUs()` (lines 988–1001), and an Android API change (lines 1009–1013), so behaviour is mixed into a class meant only to hold constants. The problem is centred on these 3 methods rather than the whole class.

**Observations:** The metric SVM's flag is likely driven by size: `C` has the most fields in the dataset (164) and 908 LOC (98th percentile), while its other five features look like a typical non-God class (3 methods, complexity 1). The actual responsibility problem sits in the 3 methods, which the features barely capture. Oscar's AI-assisted notes said the audio method couples `C` to Android; checking showed `C` already depends on `AudioManager` through its constants, so the method adds a `Context` dependency and a runtime service call rather than introducing Android coupling.

**Inspected by:** Tudor, 05/11/2026 · **Checked by:** Oscar, 05/11/2026
**AI used:** Yes. Oscar's ChatGPT-assisted notes proposed this case; Claude extracted the structure, computed the feature percentiles and drafted the evidence bullets; Tudor checked them against the code (and corrected the Android-coupling claim) and made the verdict.

---

## Case 8: 3796929, `MqttDTO` (apache/activemq-apollo, lines 31–109)

- **Link:** https://github.com/apache/activemq-apollo/blob/8e4b134b2a5d3576aa62cd8df9905a9fe2eba2d0/apollo-mqtt/src/main/java/org/apache/activemq/apollo/mqtt/dto/MqttDTO.java#L31-L109
- **Label:** 1 · **Metric:** 1 · **Token:** 0 · 2 methods / 10 fields / 64 LOC

**Responsibilities seen:** Represents MQTT protocol configuration settings, including message size limits, protocol filters, queue prefixes, and wildcard settings.

**Code evidence:**
- Lines 31–33: JAXB annotations define the class as an XML-mapped MQTT configuration object extending `ProtocolDTO`
- Lines 35–63: defines configuration fields, including `max_message_length`, `protocol_filters`, and wildcard settings
- Lines 65–93: `equals()` compares the configuration fields to determine object equality
- Lines 95–108: `hashCode()` generates a hash value from the configuration fields

**Verdict:** No clear problem

**Reason:** Although the class contains several configuration fields, they all relate to one responsibility: representing MQTT protocol settings. The `equals()` and `hashCode()` methods support this responsibility by defining equality for configuration objects.

**Observations:** Our manual inspection disagrees with the Metric-based prediction, which flags the class as a God Class. The fields and methods all support MQTT configuration, so we found no clear evidence of unrelated responsibilities.

**Inspected by:** Oscar, 05/11/2026 · **Checked by:** Tudor, 05/11/2026

---

## Case 9: 3804138, `ZookeeperServerCnxnFactory` (alibaba/jstorm, lines 29–84)

- **Link:** https://github.com/alibaba/jstorm/blob/5d6cde22dbca7df3d6e6830bf94f98a6639ab559/jstorm-core/src/main/java/backtype/storm/utils/ZookeeperServerCnxnFactory.java#L29-L84
- **Label:** 0 · **Metric:** 0 · **Token:** 1 · 2 methods / 3 fields / 50 LOC

**Responsibilities seen:** One responsibility seen: setting up a ZooKeeper server connection factory on a free port. It picks a port range (lines 35–43), creates the `NIOServerCnxnFactory` (lines 45–52), then tries different ports, skipping any already in use via `BindException` and aborting on any other IO error (lines 54–67), and exposes the chosen port and factory through two getters (lines 77–83).

**Code evidence:**
- Fields: `LOG`, `_port`, `_factory` (lines 30–32). Every method works on `_port` and `_factory`
- Constructor (lines 34–75) contains all the logic:
  - port range selection: default 2000–65535 or the exact given port (lines 35–43)
  - creates the `NIOServerCnxnFactory` instance; on failure, resets fields and throws (lines 45–52)
  - port search loop: tries each port and binds (lines 55–57), skips busy ports via `BindException` (line 60), aborts on other IO errors (lines 61–65)
  - no free port found: resets fields, logs an error and throws (lines 69–74)
- Two getters exposing the chosen port and factory (lines 77–83)
- External calls: ZooKeeper's `NIOServerCnxnFactory`, Java networking (`InetSocketAddress`) and logging only

**Verdict:** No clear problem

**Reason:** Using the reason-to-change test, every likely trigger (port range, ZooKeeper factory API, retry policy and error reporting) comes back to starting a ZooKeeper server factory on a free port, which is the only concern in this class. The constructor is long, but its four steps belong to that one task, so there's no unrelated responsibility to separate.

**Observations:** Only the token model flagged this small class (50 LOC, 2 methods) as a God Class, most likely due to its vocabulary (ZooKeeper, server, connection, factory) rather than its structure. Code-quality issues that aren't responsibility problems: the constructor does real network work (binding to ports), and the reset-and-throw code is repeated 3 times (lines 48–51, 62–65, 70–73).

**Inspected by:** Tudor, 05/11/2026 · **Checked by:** Oscar, 05/11/2026


---

## Case 10: 3817323, `RowRange` (nested class in Gatherer.java, apache/accumulo, lines 617–656)

- **Link:** https://github.com/apache/accumulo/blob/f896c98c2356a52dfa2235d2cc02ae556ab17909/core/src/main/java/org/apache/accumulo/core/summary/Gatherer.java#L617-L656
- **Label:** 0 · **Metric:** 0 · **Token:** 1 · 5 methods / 2 fields / 32 LOC
- Judged only lines 617–656, not the whole file.

**Responsibilities seen:** Represents a row range in Apache Accumulo, storing its start and end boundaries and providing methods to access and convert those boundaries.

**Code evidence:**
- Lines 617–619: defines the `RowRange` class with two fields, `startRow` and `endRow`
- Lines 621–634: constructors initialise the range from different representations
- Lines 636–642: `toRange()` and `toThrift()` convert the stored boundaries into other range representations
- Lines 644–649: getter methods provide access to the boundaries
- Lines 652–655: `toString()` produces a textual representation of the range

**Verdict:** No clear problem

**Reason:** The class has one cohesive responsibility, representing and converting row boundaries. Its fields and methods all support this purpose. There are no unrelated responsibilities or excessive complexity within the sampled class, so structural refactoring is not justified.

**Observations:** Our manual verdict disagrees with the Token-based prediction (1) and agrees with the Metric-based prediction (0). The sampled class only contains range-related data and operations, with no clear evidence of multiple unrelated responsibilities.

**Inspected by:** Oscar, 05/11/2026 · **Checked by:** Tudor, 05/11/2026


---

## Results

- **Verdict counts:** clear problem 1, no clear problem 9, unclear 0.
- **Label vs verdict:** of the 4 label-1 (God Class) cases (3, 4, 7, 8), only 1 showed a clear problem, case 7 (`C`). Cases 3, 4 and 8 were cohesive classes labelled God Class mainly for size (e.g. case 3, interface-driven). Of the 6 label-0 cases, 0 showed a clear problem, so those labels agree with our verdicts.
- **Which detector matched the code better:** Metric agreed with our verdict in 6 of 10 cases, Token in 4 of 10. Metric's 5 flags contained the only real problem (case 7) but also 4 false alarms (1, 3, 4, 8), which were mostly large or busy-looking classes. Token's 5 flags (2, 5, 6, 9, 10) were all small classes with no problem, and it also missed case 7. From what we've seen, Metric reacts to size and Token reacts to vocabulary, with neither really detecting mixed responsibilities.
- **M4 candidate: 3788627, `C` (ExoPlayer).** A non-instantiable constants holder (lines 40–42) holding 164 constants, which also contains behaviour with unrelated reasons to change: time conversion via `usToMs` and `msToUs` (lines 988–1001) and an Android audio-session service call (lines 1009–1013). The problem is localised to these 3 methods, and it's corroborated by a later upstream version that deprecates the 3 methods and delegates them to `Util`. Implemented and verified in `m4/` (see `m4/README.md`).
