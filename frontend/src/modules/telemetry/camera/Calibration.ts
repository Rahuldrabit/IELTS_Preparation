/**
 * Calibration — 9-point polynomial regression for iris-to-screen mapping.
 *
 * Algorithm:
 *   1. Display 9 points in a grid pattern
 *   2. At each point, collect N iris samples (average removes jitter)
 *   3. Fit 2nd-degree polynomial via least-squares:
 *      screenX = a0 + a1*irisX + a2*irisY + a3*irisX² + a4*irisY²
 *      screenY = b0 + b1*irisX + b2*irisY + b3*irisX² + b4*irisY²
 *   4. Store CalibrationMatrix in localStorage for persistence
 *
 * Design:
 *   - Emitter pattern for UI updates
 *   - Pure math (no DOM dependencies) — testable
 *   - Serializable matrix for persistence/transfer
 *   - Configurable grid, samples per point, padding
 */

import { Emitter } from '../core/Emitter'
import type {
  CalibrationEventMap,
  CalibrationMatrix,
  CalibrationPoint,
  CalibrationState,
  ILifecycle,
  Point2D,
} from '../types'

export interface CalibrationConfig {
  /** Grid size (3 = 3x3 = 9 points) */
  gridSize: number
  /** Samples to collect per calibration point */
  samplesPerPoint: number
  /** Padding from screen edge (fraction 0-0.5) */
  edgePadding: number
  /** LocalStorage key for persisting matrix */
  storageKey: string
}

const DEFAULT_CAL_CONFIG: CalibrationConfig = {
  gridSize: 3,
  samplesPerPoint: 30,
  edgePadding: 0.1,
  storageKey: 'cte_calibration_matrix',
}

export class CalibrationSystem extends Emitter<CalibrationEventMap> implements ILifecycle {
  private config: CalibrationConfig
  private _state: CalibrationState
  private samples: Point2D[][] = [] // iris samples grouped by point
  private screenPoints: Point2D[] = []

  constructor(config: Partial<CalibrationConfig> = {}) {
    super()
    this.config = { ...DEFAULT_CAL_CONFIG, ...config }
    this._state = this.initialState()
  }

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  get state(): CalibrationState {
    return this._state
  }

  /** Get the calibration target points for the UI to render */
  getTargetPoints(): Point2D[] {
    return this.screenPoints
  }

  /** Get current target point the user should look at */
  getCurrentTarget(): Point2D | null {
    if (this._state.status !== 'calibrating' && this._state.status !== 'collecting') return null
    return this.screenPoints[this._state.currentPointIndex] ?? null
  }

  /** Begin calibration sequence */
  start(): void {
    this.screenPoints = this.generateGrid()
    this.samples = this.screenPoints.map(() => [])
    this.setState({
      ...this.initialState(),
      status: 'calibrating',
      totalPoints: this.screenPoints.length,
      samplesPerPoint: this.config.samplesPerPoint,
    })
  }

  /** Feed an iris sample for the current calibration point */
  addSample(irisX: number, irisY: number): void {
    if (this._state.status !== 'collecting') return

    const idx = this._state.currentPointIndex
    this.samples[idx].push({ x: irisX, y: irisY })

    this.setState({
      ...this._state,
      collectedSamples: this.samples[idx].length,
    })

    // Point complete?
    if (this.samples[idx].length >= this.config.samplesPerPoint) {
      const avgIris = this.average(this.samples[idx])
      const screenPt = this.screenPoints[idx]

      const calPoint: CalibrationPoint = {
        screenX: screenPt.x,
        screenY: screenPt.y,
        irisX: avgIris.x,
        irisY: avgIris.y,
        timestamp: Date.now(),
      }
      this.emit('pointComplete', { index: idx, point: calPoint })

      // Advance to next point or finish
      const nextIdx = idx + 1
      if (nextIdx >= this.screenPoints.length) {
        this.finalize()
      } else {
        this.setState({
          ...this._state,
          status: 'calibrating',
          currentPointIndex: nextIdx,
          collectedSamples: 0,
        })
      }
    }
  }

  /** Signal that user is ready to collect for current point (UI confirms gaze is on target) */
  beginCollection(): void {
    if (this._state.status !== 'calibrating') return
    this.setState({ ...this._state, status: 'collecting', collectedSamples: 0 })
  }

  stop(): void {
    this.setState(this.initialState())
    this.samples = []
  }

  destroy(): void {
    this.stop()
    this.removeAllListeners()
  }

  /** Load persisted calibration from localStorage */
  loadFromStorage(): CalibrationMatrix | null {
    try {
      const raw = localStorage.getItem(this.config.storageKey)
      if (!raw) return null
      const matrix: CalibrationMatrix = JSON.parse(raw)

      // Invalidate if screen size changed significantly
      if (
        Math.abs(matrix.screenWidth - window.innerWidth) > 100 ||
        Math.abs(matrix.screenHeight - window.innerHeight) > 100
      ) {
        localStorage.removeItem(this.config.storageKey)
        return null
      }

      this.setState({ ...this._state, status: 'complete', matrix, accuracy: 1 - matrix.mse / 100 })
      return matrix
    } catch {
      return null
    }
  }

  /** Persist current calibration to localStorage */
  saveToStorage(matrix: CalibrationMatrix): void {
    try {
      localStorage.setItem(this.config.storageKey, JSON.stringify(matrix))
    } catch {
      // Storage full or unavailable — non-critical
    }
  }

  // ─────────────────────────────────────────────
  //  Private — Grid Generation
  // ─────────────────────────────────────────────

  private generateGrid(): Point2D[] {
    const points: Point2D[] = []
    const pad = this.config.edgePadding
    const w = window.innerWidth
    const h = window.innerHeight
    const n = this.config.gridSize

    for (let row = 0; row < n; row++) {
      for (let col = 0; col < n; col++) {
        points.push({
          x: w * (pad + (col / (n - 1)) * (1 - 2 * pad)),
          y: h * (pad + (row / (n - 1)) * (1 - 2 * pad)),
        })
      }
    }
    return points
  }

  // ─────────────────────────────────────────────
  //  Private — Polynomial Fitting (Least Squares)
  // ─────────────────────────────────────────────

  private finalize(): void {
    try {
      const calPoints = this.buildCalibrationPoints()
      const matrix = this.fitPolynomial(calPoints)
      this.saveToStorage(matrix)
      this.setState({
        ...this._state,
        status: 'complete',
        matrix,
        accuracy: Math.max(0, 1 - matrix.mse / 100),
      })
      this.emit('complete', matrix)
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      this.setState({ ...this._state, status: 'failed' })
      this.emit('failed', error)
    }
  }

  private buildCalibrationPoints(): CalibrationPoint[] {
    return this.screenPoints.map((screen, i) => {
      const avg = this.average(this.samples[i])
      return {
        screenX: screen.x,
        screenY: screen.y,
        irisX: avg.x,
        irisY: avg.y,
        timestamp: Date.now(),
      }
    })
  }

  /**
   * Fit 2nd-degree polynomial via normal equations.
   * For each axis: solve A^T * A * c = A^T * b
   * where A = [1, ix, iy, ix², iy²] design matrix
   */
  private fitPolynomial(points: CalibrationPoint[]): CalibrationMatrix {
    const n = points.length
    // Build design matrix: each row = [1, ix, iy, ix², iy²]
    const A: number[][] = points.map((p) => [1, p.irisX, p.irisY, p.irisX ** 2, p.irisY ** 2])
    const bx: number[] = points.map((p) => p.screenX)
    const by: number[] = points.map((p) => p.screenY)

    const xCoeffs = this.solveNormalEquations(A, bx)
    const yCoeffs = this.solveNormalEquations(A, by)

    // Compute MSE
    let mse = 0
    for (let i = 0; i < n; i++) {
      const predX = this.polyEval(xCoeffs, points[i].irisX, points[i].irisY)
      const predY = this.polyEval(yCoeffs, points[i].irisX, points[i].irisY)
      mse += (predX - bx[i]) ** 2 + (predY - by[i]) ** 2
    }
    mse = Math.sqrt(mse / n)

    return {
      xCoeffs,
      yCoeffs,
      mse,
      calibratedAt: Date.now(),
      screenWidth: window.innerWidth,
      screenHeight: window.innerHeight,
    }
  }

  /** Evaluate polynomial: c0 + c1*x + c2*y + c3*x² + c4*y² */
  private polyEval(coeffs: number[], x: number, y: number): number {
    return coeffs[0] + coeffs[1] * x + coeffs[2] * y + coeffs[3] * x * x + coeffs[4] * y * y
  }

  /**
   * Solve A^T * A * c = A^T * b via Gaussian elimination.
   * A: m×n design matrix, b: m×1 target vector → returns n×1 coefficients.
   */
  private solveNormalEquations(A: number[][], b: number[]): number[] {
    const m = A.length
    const n = A[0].length

    // Compute A^T * A (n×n)
    const AtA: number[][] = Array.from({ length: n }, () => new Array(n).fill(0))
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        let sum = 0
        for (let k = 0; k < m; k++) sum += A[k][i] * A[k][j]
        AtA[i][j] = sum
      }
    }

    // Compute A^T * b (n×1)
    const Atb: number[] = new Array(n).fill(0)
    for (let i = 0; i < n; i++) {
      let sum = 0
      for (let k = 0; k < m; k++) sum += A[k][i] * b[k]
      Atb[i] = sum
    }

    // Gaussian elimination with partial pivoting
    return this.gaussianElimination(AtA, Atb)
  }

  private gaussianElimination(A: number[][], b: number[]): number[] {
    const n = A.length
    // Augmented matrix
    const aug: number[][] = A.map((row, i) => [...row, b[i]])

    for (let col = 0; col < n; col++) {
      // Partial pivoting
      let maxRow = col
      for (let row = col + 1; row < n; row++) {
        if (Math.abs(aug[row][col]) > Math.abs(aug[maxRow][col])) maxRow = row
      }
      [aug[col], aug[maxRow]] = [aug[maxRow], aug[col]]

      const pivot = aug[col][col]
      if (Math.abs(pivot) < 1e-10) continue // Singular — skip

      // Eliminate below
      for (let row = col + 1; row < n; row++) {
        const factor = aug[row][col] / pivot
        for (let j = col; j <= n; j++) {
          aug[row][j] -= factor * aug[col][j]
        }
      }
    }

    // Back substitution
    const x = new Array(n).fill(0)
    for (let i = n - 1; i >= 0; i--) {
      let sum = aug[i][n]
      for (let j = i + 1; j < n; j++) {
        sum -= aug[i][j] * x[j]
      }
      x[i] = Math.abs(aug[i][i]) > 1e-10 ? sum / aug[i][i] : 0
    }
    return x
  }

  // ─────────────────────────────────────────────
  //  Utilities
  // ─────────────────────────────────────────────

  private average(points: Point2D[]): Point2D {
    if (points.length === 0) return { x: 0, y: 0 }
    const sum = points.reduce((acc, p) => ({ x: acc.x + p.x, y: acc.y + p.y }), { x: 0, y: 0 })
    return { x: sum.x / points.length, y: sum.y / points.length }
  }

  private initialState(): CalibrationState {
    return {
      status: 'idle',
      currentPointIndex: 0,
      totalPoints: this.config.gridSize ** 2,
      collectedSamples: 0,
      samplesPerPoint: this.config.samplesPerPoint,
      matrix: null,
      accuracy: 0,
    }
  }

  private setState(state: CalibrationState): void {
    this._state = state
    this.emit('stateChange', state)
  }
}

// ─────────────────────────────────────────────
//  Static utility: evaluate calibration outside class
// ─────────────────────────────────────────────

/** Apply calibration matrix to iris coordinates → screen point */
export function applyCalibration(
  matrix: CalibrationMatrix,
  irisX: number,
  irisY: number,
): Point2D {
  const x = matrix.xCoeffs[0]
    + matrix.xCoeffs[1] * irisX
    + matrix.xCoeffs[2] * irisY
    + matrix.xCoeffs[3] * irisX * irisX
    + matrix.xCoeffs[4] * irisY * irisY

  const y = matrix.yCoeffs[0]
    + matrix.yCoeffs[1] * irisX
    + matrix.yCoeffs[2] * irisY
    + matrix.yCoeffs[3] * irisX * irisX
    + matrix.yCoeffs[4] * irisY * irisY

  return { x, y }
}
