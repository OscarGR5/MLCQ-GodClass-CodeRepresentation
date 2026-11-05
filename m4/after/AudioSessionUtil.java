package com.google.android.exoplayer2.util;

import android.annotation.TargetApi;
import android.content.Context;
import android.media.AudioManager;

/** Android audio-session access. Moved from C (M4 refactoring). */
public final class AudioSessionUtil {

  private AudioSessionUtil() {}

  /**
   * Returns a newly generated audio session identifier, or {@link AudioManager#ERROR} if an error
   * occurred in which case audio playback may fail.
   *
   * @see AudioManager#generateAudioSessionId()
   */
  @TargetApi(21)
  public static int generateAudioSessionIdV21(Context context) {
    return ((AudioManager) context.getSystemService(Context.AUDIO_SERVICE))
        .generateAudioSessionId();
  }
}
