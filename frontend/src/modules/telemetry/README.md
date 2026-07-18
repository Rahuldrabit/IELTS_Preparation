# Cognitive Telemetry Engine (CTE)

A self-contained, research-grade subsystem for tracking eye gaze, mouse behavior, scroll patterns, and attention during IELTS reading and listening practice.

---

## Overview

The CTE captures real-time behavioral data from the user's webcam (iris tracking via MediaPipe FaceMesh), mouse, scroll, and focus events. It aggregates this into compact analytics summaries and uploads them to the backend for AI-driven coaching.

**Key principle:** Only aggregated summaries are sent to the backend — never raw gaze data. This achieves ~100x data reduction while preserving all diagnostic value.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (Main Thread)                                       │
│                                                             │
│  React Page Component                                       │
│       │                                                     │
│       ▼                                                     │
│  useTelemetry() ─── Master Lifecycle Hook                   │
│       │                                                     │
│       ├── ReadingTracker / ListeningTracker (orchestrator)  │
│       │       ├── CameraManager (webcam stream)             │
│       │       ├── FaceMeshProcessor (landmark extraction)   │
│       │       ├── GazeEstimator (iris → screen coords)      │
│       │       ├── FixationDetector (I-DT algorithm)         │
│       │       ├── RegressionDetector (backward saccades)    │
│       │       ├── AOIMapper (gaze → DOM hit-testing)        │
│       │       ├── MouseTracker (throttled tracking)         │
│       │       ├── ScrollTracker (IntersectionObserver)      │
│       │       └── FocusTracker (Page Visibility API)        │
│       │                                                     │
│       ├── ReadingAnalytics (per-second aggregation)         │
│       ├── IndexedDBStore (offline buffer)                   │
│       └── TelemetryUploader (batched POST every 2s)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                        │
              POST /api/telemetry/upload (every 2s)
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                            │
│                                                             │
│  /api/telemetry/session/start                               │
│  /api/telemetry/upload                                      │
│  /api/telemetry/event                                       │
│  /api/telemetry/report/{session_id}                         │
│  /api/telemetry/profile/{user_id}                           │
│       │                                                     │
│       ▼                                                     │
│  PostgreSQL                                                 │
│    telemetry_sessions                                       │
│    telemetry_summaries                                      │
│    attention_scores                                         │
│    question_behavior                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Structure

```
frontend/src/modules/telemetry/
├── index.ts                    # Public API barrel
├── types.ts                    # All type definitions (IEmitter, ILifecycle, ITracker, events, config)
│
├── core/
│   ├── Emitter.ts             # Generic type-safe event emitter (base for all subsystems)
│   └── index.ts
│
├── camera/
│   ├── CameraManager.ts      # Webcam access, permission flow, rAF frame loop
│   ├── FaceMesh.ts           # MediaPipe FaceLandmarker (lazy-loaded), EAR blink detection
│   ├── Calibration.ts        # 9-point polynomial regression, localStorage persistence
│   └── index.ts
│
├── gaze/
│   ├── GazeEstimator.ts      # Iris → screen coordinate via calibration matrix + EMA smoothing
│   ├── FixationDetector.ts   # I-DT (dispersion-threshold) fixation identification
│   ├── RegressionDetector.ts # Backward saccade detection with reading direction config
│   ├── AOIMapper.ts          # DOM scanning (data-cte-*), spatial hit-testing, ResizeObserver
│   └── index.ts
│
├── trackers/
│   ├── MouseTracker.ts       # Throttled position, click, text selection tracking
│   ├── ScrollTracker.ts      # Direction, velocity, paragraph enter/exit via IntersectionObserver
│   ├── FocusTracker.ts       # Tab visibility, blur/focus, focus ratio computation
│   ├── ReadingTracker.ts     # Orchestrates ALL reading subsystems into unified event stream
│   ├── ListeningTracker.ts   # Audio-synced gaze with distractor attraction tracking
│   └── index.ts
│
├── analytics/
│   ├── ReadingAnalytics.ts   # Accumulator → periodic summary (fixations, regressions, speed)
│   ├── AttentionScore.ts     # Pure function: weighted composite score (0-100)
│   └── index.ts
│
├── storage/
│   ├── IndexedDBStore.ts     # Offline-first event buffer with in-memory fallback
│   ├── TelemetryUploader.ts  # Batched upload, exponential backoff, sendBeacon on unload
│   └── index.ts
│
├── workers/
│   ├── telemetry.worker.ts   # Web Worker: MediaPipe processing off main thread
│   └── WorkerBridge.ts       # Typed main↔worker communication, ImageBitmap zero-copy
│
├── hooks/
│   ├── useTelemetry.ts       # Master lifecycle: start/stop/config, wires everything together
│   ├── useCalibration.ts     # 9-point calibration flow state management
│   ├── useGaze.ts            # Real-time gaze point subscription (throttled state)
│   ├── useGazeDebug.ts       # Rolling trail + fixation buffer for debug overlay
│   └── index.ts
│
└── components/
    ├── CalibrationOverlay.tsx # Full-screen 9-point calibration with Framer Motion animations
    ├── GazeDebugOverlay.tsx   # Canvas: gaze dot + trail + fixation heatmap + stats badge
    ├── CameraPermission.tsx   # Permission request/denied/error UX states
    └── index.ts
```

---

## Features

### Camera Pipeline
- **Permission handling:** Graceful denied/error states with user guidance
- **MediaPipe FaceMesh:** 478-landmark face detection, lazy-loaded from CDN
- **Blink detection:** Eye Aspect Ratio (EAR) algorithm, configurable threshold
- **Head pose:** Pitch/yaw/roll extraction from transformation matrix
- **Web Worker offloading:** FaceMesh runs in separate thread (zero React blocking)

### 9-Point Calibration
- **Grid generation:** Configurable NxN with edge padding
- **Sample collection:** 30 frames per point, averaged for noise reduction
- **Polynomial regression:** 2nd-degree least-squares fitting (Gaussian elimination)
- **Persistence:** Stored in localStorage, invalidated on screen size change
- **Accuracy scoring:** MSE-based confidence metric

### Gaze Estimation
- **Iris averaging:** Both irises combined for stability
- **EMA smoothing:** Configurable alpha (reduces jitter without lag)
- **Confidence scoring:** Composite of eye openness + head pose stability
- **Viewport clamping:** Gaze never escapes screen bounds
- **Strategy pattern:** Pluggable ICalibrationProvider

### Fixation Detection (I-DT Algorithm)
- **Sliding window:** Expands until dispersion exceeds threshold
- **Manhattan dispersion:** (maxX - minX) + (maxY - minY)
- **Configurable:** minDuration (150ms), maxDispersion (30px)
- **AOI integration:** Each fixation annotated with word/paragraph/question

### Regression Detection
- **Backward saccades:** LTR/RTL reading direction aware
- **Cross-line detection:** Upward jumps (re-reading earlier paragraphs)
- **Minimum distance filter:** Ignores micro-movements
- **Paragraph correlation:** From/to paragraph IDs for comprehension analysis

### Area of Interest (AOI) Mapping
- **DOM conventions:** `data-cte-paragraph`, `data-cte-word`, `data-cte-question`, `data-cte-option`
- **Auto-scanning:** Discovers AOIs from DOM on start and resize/scroll
- **Priority system:** word > sentence > paragraph > question > option
- **Fuzzy hit padding:** Configurable padding around AOI rects

### Mouse & Scroll Tracking
- **Throttled mouse:** Configurable interval (default 50ms), AOI-aware clicks
- **Text selection:** Captures selected text with paragraph context
- **Scroll velocity:** Computed from delta between events
- **Paragraph visibility:** IntersectionObserver tracks enter/exit + dwell time

### Focus Tracking
- **Page Visibility API:** Detects tab switches
- **Window blur/focus:** Catches alt-tab and window changes
- **Time accounting:** Total focused vs unfocused time, focus ratio
- **Gaze invalidation:** Skips processing when user is away

### Analytics Aggregation
- **Per-interval summaries:** Compact metrics every 1-2 seconds
- **Metrics computed:**
  - Paragraph time distribution
  - Fixation count & average duration
  - Regression count
  - Skip rate (words not fixated / total words)
  - Blink rate (blinks/minute)
  - Reading speed (WPM estimate from forward saccade distance)
- **Attention score:** Weighted composite (focus ratio, fixation stability, regression penalty, blink normality, speed consistency)

### Storage & Upload
- **IndexedDB buffer:** Survives page refreshes and network drops
- **In-memory fallback:** Works when IndexedDB unavailable
- **Batched upload:** Every 2 seconds, max 100 events per batch
- **Retry with backoff:** Exponential (1s, 2s, 4s) up to 3 attempts
- **Offline awareness:** Pauses uploads when navigator.onLine is false
- **sendBeacon:** Last-resort flush on page unload

### Listening Telemetry
- **Audio sync:** Gaze events correlated with audio playback position
- **Choice tracking:** Gaze duration per answer option
- **Distractor attraction:** Detects when user gazes at wrong choices during keywords

---

## Backend API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/telemetry/session/start` | Create a telemetry session |
| POST | `/api/telemetry/upload` | Receive batched summaries (every 2s) |
| POST | `/api/telemetry/event` | Critical single event (session_end) |
| GET | `/api/telemetry/report/{session_id}` | Aggregated session analysis |
| GET | `/api/telemetry/profile/{user_id}` | Cross-session behavioral profile |

### Database Tables

| Table | Purpose |
|-------|---------|
| `telemetry_sessions` | One per reading/listening attempt |
| `telemetry_summaries` | Aggregated metrics per 2-second interval |
| `attention_scores` | Computed composite scores (post-session) |
| `question_behavior` | Per-question behavioral data |

---

## Usage

### Basic Integration (Reading Page)

```tsx
import { useTelemetry, useGaze, useGazeDebug, GazeDebugOverlay, CameraPermission } from '@/modules/telemetry'

function ReadingPage({ sessionId, passage }) {
  const { start, stop, status, tracker, error } = useTelemetry({
    skill: 'reading',
    sessionId,
    totalWords: passage.wordCount,
    config: { debugOverlay: process.env.NODE_ENV === 'development' }
  })

  const { trail, fixations, regressionCount } = useGazeDebug({
    tracker: tracker as ReadingTracker,
    enabled: status === 'active',
  })

  return (
    <>
      {status === 'idle' && (
        <CameraPermission
          status="idle"
          error={null}
          onRequestPermission={start}
          onSkip={() => start()} // starts without gaze
        />
      )}

      {/* Reading passage with data-cte-* attributes */}
      <div data-cte-paragraph="A">
        {passage.paragraphs[0].split(' ').map((word, i) => (
          <span key={i} data-cte-word={i}>{word} </span>
        ))}
      </div>

      {/* Debug overlay (dev only) */}
      <GazeDebugOverlay
        trail={trail}
        fixations={fixations}
        regressionCount={regressionCount}
        visible={status === 'active'}
      />
    </>
  )
}
```

### DOM Conventions

Add these data attributes to make elements trackable:

```html
<div data-cte-paragraph="A">...</div>
<span data-cte-word="42">ecosystem</span>
<div data-cte-question="7">...</div>
<div data-cte-option="7-2">Choice B</div>
```

---

## Engineering Principles

| Principle | Implementation |
|-----------|---------------|
| **Interface Segregation** | Small contracts: `IEmitter`, `ILifecycle`, `ITracker`, `IAOIResolver`, `ICalibrationProvider` |
| **Composition over Inheritance** | `ReadingTracker` composes 10 subsystems, no deep class hierarchies |
| **Strategy Pattern** | Pluggable calibration provider, AOI resolver |
| **Open/Closed** | All subsystems configurable without source modification |
| **Single Responsibility** | Each file does one thing, each class has one reason to change |
| **Dependency Inversion** | Hooks depend on interfaces, not concrete implementations |
| **Event-Driven** | Typed pub/sub via `Emitter<T>` — loose coupling between subsystems |
| **Offline-First** | IndexedDB buffer + retry ensures no data loss |
| **Zero-Copy Transfer** | `ImageBitmap` transfer to Web Worker avoids serialization |

---

## Configuration

All defaults in `types.ts → DEFAULT_CONFIG`:

```typescript
{
  gazeEnabled: true,        // Enable eye tracking
  mouseEnabled: true,       // Enable mouse tracking
  scrollEnabled: true,      // Enable scroll tracking
  focusEnabled: true,       // Enable focus tracking
  uploadIntervalMs: 2000,   // Upload batch interval
  debugOverlay: false,      // Show debug visualization
  fixationThresholdMs: 150, // Minimum fixation duration
  fixationDispersionPx: 30, // Max fixation dispersion
  gazeSamplingRate: 30,     // Target gaze FPS
  maxBufferSize: 500,       // IndexedDB max events
  uploadRetryAttempts: 3,   // Retry count before drop
}
```

---

## Dependencies

- `@mediapipe/tasks-vision` — FaceLandmarker for eye tracking
- `framer-motion` — Calibration overlay animations (already in project)
- `lucide-react` — Icons for CameraPermission (already in project)

---

## Future Roadmap (Sprint 2-5)

- [ ] Word-level gaze mapping with confidence scores
- [ ] Listening distractor attraction index
- [ ] Visual search path reconstruction (replay)
- [ ] Gemma 4 behavioral analysis prompts
- [ ] Personalized coaching from telemetry patterns
- [ ] Research-grade analytics export (CSV/JSON)
- [ ] Hardware eye tracker support (Tobii SDK)
- [ ] Metacognition agent (self-awareness coaching)
