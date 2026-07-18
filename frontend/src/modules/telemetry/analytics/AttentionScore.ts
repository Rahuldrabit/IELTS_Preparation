/**
 * AttentionScore — composite focus/attention scoring from telemetry signals.
 *
 * Computes a 0-100 score based on multiple weighted factors:
 *   - Focus ratio (time on page vs away)
 *   - Fixation stability (low variance = focused)
 *   - Regression frequency (many regressions = struggling)
 *   - Blink rate (normal: 15-20/min, high = fatigue, very low = strain)
 *   - Reading speed consistency
 *
 * Design:
 *   - Pure function: given metrics, returns score
 *   - Configurable weights for different contexts
 *   - Stateless utility (no lifecycle, no emitter needed)
 *   - Can be used on frontend or backend
 */

export interface AttentionWeights {
  focusRatio: number
  fixationStability: number
  regressionPenalty: number
  blinkNormality: number
  speedConsistency: number
}

const DEFAULT_WEIGHTS: AttentionWeights = {
  focusRatio: 0.30,
  fixationStability: 0.25,
  regressionPenalty: 0.20,
  blinkNormality: 0.10,
  speedConsistency: 0.15,
}

export interface AttentionInput {
  /** Fraction of time focused on page (0-1) */
  focusRatio: number
  /** Average fixation duration in ms */
  avgFixationMs: number
  /** Standard deviation of fixation durations in ms */
  fixationStdDevMs: number
  /** Regressions per minute */
  regressionsPerMinute: number
  /** Blinks per minute */
  blinksPerMinute: number
  /** Coefficient of variation of reading speed across intervals */
  speedCV: number
}

export interface AttentionResult {
  /** Composite score 0-100 */
  overall: number
  /** Breakdown of each factor (0-100) */
  factors: {
    focusRatio: number
    fixationStability: number
    regressionPenalty: number
    blinkNormality: number
    speedConsistency: number
  }
}

/**
 * Compute attention score from telemetry metrics.
 * Pure function — no side effects, fully testable.
 */
export function computeAttentionScore(
  input: AttentionInput,
  weights: Partial<AttentionWeights> = {},
): AttentionResult {
  const w: AttentionWeights = { ...DEFAULT_WEIGHTS, ...weights }

  // Factor 1: Focus ratio (higher is better, linear)
  const f1 = clamp01(input.focusRatio) * 100

  // Factor 2: Fixation stability
  //   Ideal fixation: 200-350ms. Low std dev = stable reading.
  //   Score decreases as stdDev exceeds 100ms.
  const idealFixation = input.avgFixationMs >= 150 && input.avgFixationMs <= 400
  const fixationBase = idealFixation ? 80 : 50
  const stabilityPenalty = Math.min(50, input.fixationStdDevMs / 4) // Lose up to 50pts
  const f2 = clamp0100(fixationBase + 20 - stabilityPenalty)

  // Factor 3: Regression penalty
  //   0-2 regressions/min = excellent, 2-5 = normal, 5-10 = struggling, 10+ = severe
  const regScore = input.regressionsPerMinute <= 2 ? 100
    : input.regressionsPerMinute <= 5 ? 80
    : input.regressionsPerMinute <= 10 ? 50
    : Math.max(0, 100 - input.regressionsPerMinute * 5)
  const f3 = clamp0100(regScore)

  // Factor 4: Blink normality
  //   Normal: 15-20/min. Deviation penalized.
  const blinkDev = Math.abs(input.blinksPerMinute - 17.5) // midpoint of normal range
  const f4 = clamp0100(100 - blinkDev * 4)

  // Factor 5: Speed consistency
  //   Low CV (coefficient of variation) = consistent reading pace
  //   CV < 0.2 = excellent, CV > 0.6 = erratic
  const f5 = clamp0100(100 - input.speedCV * 150)

  // Weighted sum
  const overall = clamp0100(
    f1 * w.focusRatio +
    f2 * w.fixationStability +
    f3 * w.regressionPenalty +
    f4 * w.blinkNormality +
    f5 * w.speedConsistency
  )

  return {
    overall: Math.round(overall),
    factors: {
      focusRatio: Math.round(f1),
      fixationStability: Math.round(f2),
      regressionPenalty: Math.round(f3),
      blinkNormality: Math.round(f4),
      speedConsistency: Math.round(f5),
    },
  }
}

// ─────────────────────────────────────────────
//  Helpers
// ─────────────────────────────────────────────

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v))
}

function clamp0100(v: number): number {
  return Math.max(0, Math.min(100, v))
}

/**
 * Compute standard deviation from an array of numbers.
 * Utility for preparing AttentionInput.
 */
export function stdDev(values: number[]): number {
  if (values.length < 2) return 0
  const mean = values.reduce((a, b) => a + b, 0) / values.length
  const variance = values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / (values.length - 1)
  return Math.sqrt(variance)
}

/**
 * Compute coefficient of variation (stdDev / mean).
 * Returns 0 if mean is 0.
 */
export function coefficientOfVariation(values: number[]): number {
  if (values.length < 2) return 0
  const mean = values.reduce((a, b) => a + b, 0) / values.length
  if (mean === 0) return 0
  return stdDev(values) / mean
}
