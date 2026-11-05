package com.google.android.exoplayer2.util;

import com.google.android.exoplayer2.C;

/** Time-unit conversions. Moved from C (M4 refactoring). */
public final class TimeUtil {

  private TimeUtil() {}

  /** Microseconds to milliseconds, preserving C.TIME_UNSET and C.TIME_END_OF_SOURCE. */
  public static long usToMs(long timeUs) {
    return (timeUs == C.TIME_UNSET || timeUs == C.TIME_END_OF_SOURCE) ? timeUs : (timeUs / 1000);
  }

  /** Milliseconds to microseconds, preserving C.TIME_UNSET and C.TIME_END_OF_SOURCE. */
  public static long msToUs(long timeMs) {
    return (timeMs == C.TIME_UNSET || timeMs == C.TIME_END_OF_SOURCE) ? timeMs : (timeMs * 1000);
  }
}
