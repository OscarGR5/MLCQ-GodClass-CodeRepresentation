import com.google.android.exoplayer2.C;
import com.google.android.exoplayer2.util.PlaybackDurationFormatter;
import java.util.Locale;

/** Examples and boundaries fixed in AUDIT.md before implementation. */
public final class PlaybackDurationFormatterTest {
  private static int checks;

  public static void main(String[] args) {
    format("zero", 0, "0:00");
    format("one microsecond", 1, "0:00");
    format("last subsecond", 999_999, "0:00");
    format("one second", 1_000_000, "0:01");
    format("fractional second", 1_999_999, "0:01");
    format("single digit seconds", 9_000_000, "0:09");
    format("two digit seconds", 10_000_000, "0:10");
    format("before minute boundary", 59_999_999, "0:59");
    format("minute boundary", 60_000_000, "1:00");
    format("after minute boundary", 60_999_999, "1:00");
    format("minute and second", 61_000_000, "1:01");
    format("before hour boundary", 3_599_999_999L, "59:59");
    format("hour boundary uses total minutes", 3_600_000_000L, "60:00");
    format("beyond hour", 3_661_000_000L, "61:01");
    format("maximum long", Long.MAX_VALUE, "153722867280:54");
    format("unknown time", C.TIME_UNSET, "--:--");
    format("end of source", C.TIME_END_OF_SOURCE, "--:--");
    rejects(-1);
    rejects(-1_000_000);
    rejects(Long.MIN_VALUE + 2);
    Locale original = Locale.getDefault();
    try {
      Locale.setDefault(Locale.forLanguageTag("ar-EG"));
      format("ASCII under Arabic locale", 61_000_000, "1:01");
    } finally {
      Locale.setDefault(original);
    }
    System.out.println("ALL " + checks + " CHECKS PASSED: playback duration formatting.");
  }

  private static void format(String name, long input, String expected) {
    String actual = PlaybackDurationFormatter.formatUs(input);
    if (!expected.equals(actual)) {
      throw new AssertionError(name + ": expected " + expected + ", got " + actual);
    }
    checks++;
    System.out.println("ok  " + name + " = " + actual);
  }

  private static void rejects(long input) {
    try {
      PlaybackDurationFormatter.formatUs(input);
    } catch (IllegalArgumentException expected) {
      checks++;
      System.out.println("ok  rejected negative duration " + input);
      return;
    }
    throw new AssertionError("Accepted negative duration " + input);
  }
}
