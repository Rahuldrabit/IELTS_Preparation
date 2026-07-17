/**
 * PcmProcessor — AudioWorkletProcessor running on the audio rendering thread.
 *
 * Processes 128-frame blocks from the microphone input:
 *   - Computes RMS energy (for live waveform + silence detection)
 *   - Computes Zero Crossing Rate (voiced/unvoiced distinction)
 *   - Posts metrics to the main thread every ~50ms (6 blocks × 128 frames @ 16kHz)
 *
 * The processor never buffers audio itself — the main thread handles blob assembly
 * via a parallel MediaRecorder on the same stream.
 */
class PcmProcessor extends AudioWorkletProcessor {
  constructor() {
    super()
    this._frameCount = 0
  }

  process(inputs) {
    const input = inputs[0]
    if (!input || !input[0]) return true

    const samples = input[0]  // Float32Array, 128 frames

    // ── RMS energy ──────────────────────────────────
    let sumSq = 0
    for (let i = 0; i < samples.length; i++) {
      sumSq += samples[i] * samples[i]
    }
    const rms = Math.sqrt(sumSq / samples.length)

    // ── Zero Crossing Rate ───────────────────────────
    let crossings = 0
    for (let i = 1; i < samples.length; i++) {
      if ((samples[i] >= 0) !== (samples[i - 1] >= 0)) crossings++
    }
    const zcr = crossings / samples.length

    this._frameCount++

    // Post every ~6 blocks ≈ 48ms at 16kHz
    if (this._frameCount % 6 === 0) {
      this.port.postMessage({ type: 'metrics', rms, zcr })
    }

    return true   // keep processor alive
  }
}

registerProcessor('pcm-processor', PcmProcessor)
