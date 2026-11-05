import com.google.android.exoplayer2.C;
import com.google.android.exoplayer2.util.TimeUtil;

/**
 * Characterisation test for the M4 Move Method refactoring.
 * Compares the new TimeUtil against the ORIGINAL C.usToMs / C.msToUs logic,
 * copied verbatim from m4/before/C.java (L988-1001).
 */
public class TimeUtilTest {

  // ORIGINAL logic, copied verbatim from m4/before/C.java L988-1001 (the "before" oracle)
  static long originalUsToMs(long timeUs) {
    return (timeUs == C.TIME_UNSET || timeUs == C.TIME_END_OF_SOURCE) ? timeUs : (timeUs / 1000);
  }

  static long originalMsToUs(long timeMs) {
    return (timeMs == C.TIME_UNSET || timeMs == C.TIME_END_OF_SOURCE) ? timeMs : (timeMs * 1000);
  }

  public static void main(String[] args) {
    long[] inputs = {0, 1, 999, 1000, 1001, -1, -1000, 123_456_789L,
        Long.MAX_VALUE, Long.MIN_VALUE + 2, C.TIME_UNSET, C.TIME_END_OF_SOURCE};
    int checks = 0;
    for (long x : inputs) {
      check("usToMs(" + x + ")", originalUsToMs(x), TimeUtil.usToMs(x));
      check("msToUs(" + x + ")", originalMsToUs(x), TimeUtil.msToUs(x));
      checks += 2;
    }
    // the two special sentinel values must pass through unchanged
    check("usToMs(TIME_UNSET)", C.TIME_UNSET, TimeUtil.usToMs(C.TIME_UNSET));
    check("msToUs(TIME_END_OF_SOURCE)", C.TIME_END_OF_SOURCE, TimeUtil.msToUs(C.TIME_END_OF_SOURCE));
    checks += 2;
    System.out.println("ALL " + checks + " CHECKS PASSED: TimeUtil behaves identically to the original C methods.");
  }

  static void check(String name, long expected, long actual) {
    if (expected != actual) {
      throw new AssertionError("FAIL " + name + ": expected " + expected + ", got " + actual);
    }
    System.out.println("ok  " + name + " = " + actual);
  }
}
