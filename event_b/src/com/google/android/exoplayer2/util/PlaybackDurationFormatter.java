package com.google.android.exoplayer2.util;

import com.google.android.exoplayer2.C;

/** Presentation of finite playback durations as total minutes and two-digit seconds. */
public final class PlaybackDurationFormatter {

  private PlaybackDurationFormatter() {}

  /**
   * Formats microseconds as ASCII m:ss, truncating fractional seconds.
   * Both time sentinels display as --:--; other negative inputs are invalid.
   * Minutes can exceed 59 and the result is independent of the default locale.
   *
   * @throws IllegalArgumentException if durationUs is negative and is not a time sentinel
   */
  public static String formatUs(long durationUs) {
    if (durationUs == C.TIME_UNSET || durationUs == C.TIME_END_OF_SOURCE) {
      return "--:--";
    }
    if (durationUs < 0) {
      throw new IllegalArgumentException("Duration must be nonnegative or a time sentinel");
    }
    long totalSeconds = durationUs / 1_000_000;
    long seconds = totalSeconds % 60;
    return (totalSeconds / 60) + ":" + (seconds < 10 ? "0" : "") + seconds;
  }
}
