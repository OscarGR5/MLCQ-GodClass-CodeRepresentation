#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo 'Source identity checks'
sha256sum --check event_b/evidence/SHA256SUMS
git diff --exit-code PRE_EVENT_B -- . ':!event_b'
echo 'Tracked files outside event_b match PRE_EVENT_B'

java -version 2>&1
javac -version
build_dir=$(mktemp -d)
trap 'rm -rf "$build_dir"' EXIT

echo 'Compile focused tests with javac --release 8 -encoding UTF-8 -Xlint:all'
javac --release 8 -encoding UTF-8 -Xlint:all -d "$build_dir" \
  m4/test/stubs/com/google/android/exoplayer2/C.java \
  m4/after/TimeUtil.java m4/test/TimeUtilTest.java \
  event_b/src/com/google/android/exoplayer2/util/PlaybackDurationFormatter.java \
  event_b/test/PlaybackDurationFormatterTest.java \
  event_b/test/stubs/org/apache/commons/lang/StringUtils.java \
  event_b/test/stubs/org/apache/commons/lang/builder/ToStringBuilder.java \
  event_b/test/stubs/com/alibaba/otter/canal/common/utils/CanalToStringStyle.java \
  event_b/before/canal/ClientIdentity.java \
  event_b/src/com/alibaba/otter/canal/protocol/ClientIdentityPropertiesStore.java \
  event_b/test/ClientIdentityPropertiesStoreTest.java

echo 'Run unchanged M4 regression'
java -cp "$build_dir" TimeUtilTest
echo 'Run Event B formatter tests'
java -cp "$build_dir" PlaybackDurationFormatterTest
echo 'Run Event B properties persistence tests (real temporary filesystem)'
java -cp "$build_dir" ClientIdentityPropertiesStoreTest
echo 'All verification commands exited 0'
