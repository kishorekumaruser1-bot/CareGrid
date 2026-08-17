import { useEffect, useState } from 'react';
import './App.css';
import { useCareGridSocket } from './useCareGridSocket';

/* ============================================================
   NOTE: Step 2's static TEMP_BED_DATA / TEMP_PATIENT_QUEUE have
   been removed. Data now comes exclusively from useCareGridSocket,
   which is the single source of truth for backend state.

   STEP 4: the old sticky "SelectedPatientPanel" placeholder (which
   just said "explanation will appear here") has been replaced by
   the Transparency Drawer below, which renders the real
   backend-provided explanation_string and related fields once the
   backend sends them. Selection is tracked by patient_id only, so
   the drawer always reads the live patient object out of
   patientQueue rather than holding its own stale copy.
   ============================================================ */

const STATUS_LABELS = {
  connected: '● Live',
  connecting: 'Connecting...',
  reconnecting: 'Reconnecting...',
  disconnected: 'Disconnected',
};

/* ============================================================
   STEP 5: SIMULATION ENDPOINTS
   ------------------------------------------------------------
   These are the endpoints given in the Step 5 backend contract.
   They are isolated here as the single place to change if the
   real FastAPI backend ends up using different paths — nothing
   below this constant should hardcode a URL.
   ============================================================ */
const SIMULATION_ENDPOINTS = {
  surge: 'http://localhost:8000/api/surge',
  fastForward: 'http://localhost:8000/api/fast-forward',
};

const SIMULATION_SPEEDS = [1, 5, 10];

function ConnectionIndicator({ status }) {
  const label = STATUS_LABELS[status] ?? 'Disconnected';
  return (
    <span className={`cg-connection cg-connection--${status}`}>{label}</span>
  );
}

function Header({ connectionStatus }) {
  return (
    <header className="cg-header">
      <div className="cg-header-titles">
        <h1 className="cg-title">
          CareGrid<span className="cg-title-dot">.</span>
        </h1>
        <p className="cg-subtitle">Intelligent ICU Bed Arbitration</p>
      </div>
      <div className="cg-header-right">
        <ConnectionIndicator status={connectionStatus} />
        <p className="cg-disclaimer">
          Decision support only — final allocation remains with clinician.
        </p>
      </div>
    </header>
  );
}

function BedCapacity({ bedCapacity }) {
  // NOTE: these three values are independent backend-provided fields,
  // not derived from each other or from patient data. Until the first
  // valid WebSocket message arrives, bedCapacity is null and we show
  // a neutral placeholder rather than fabricating numbers.
  const totalBeds = bedCapacity?.total_beds ?? '—';
  const occupiedBeds = bedCapacity?.occupied_beds ?? '—';
  const availableBeds = bedCapacity?.available_beds ?? '—';

  return (
    <section className="cg-bed-capacity" aria-label="ICU bed capacity">
      <div className="cg-stat-card">
        <span className="cg-stat-label">Total ICU Beds</span>
        <span className="cg-stat-value">{totalBeds}</span>
      </div>
      <div className="cg-stat-card cg-stat-card--occupied">
        <span className="cg-stat-label">Occupied</span>
        <span className="cg-stat-value">{occupiedBeds}</span>
      </div>
      <div className="cg-stat-card cg-stat-card--available">
        <span className="cg-stat-label">Available</span>
        <span className="cg-stat-value">{availableBeds}</span>
      </div>
    </section>
  );
}

function StatusBadge({ status }) {
  const key = (status || '').toLowerCase().replace(/\s+/g, '-');
  return <span className={`cg-status-badge cg-status-badge--${key}`}>{status}</span>;
}

function RankBadge({ rank }) {
  return (
    <span className="cg-rank-badge">
      <span className="cg-rank-badge-number">{rank}</span>
    </span>
  );
}

function PatientRow({ patient, isSelected, onSelect, onAdmit, onDischarge }) {
  return (
    <tr
      className={`cg-row${isSelected ? ' cg-row--selected' : ''}`}
      onClick={() => onSelect(patient.patient_id)}
      tabIndex={0}
      role="button"
      aria-pressed={isSelected}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') onSelect(patient.patient_id);
      }}
    >
      <td>
        <RankBadge rank={patient.rank} />
      </td>
      <td className="cg-mono">{patient.patient_id}</td>
      <td className="cg-mono">{patient.severity}</td>
      <td className="cg-mono">{(patient.survival_probability * 100).toFixed(0)}%</td>
      <td className="cg-mono">{patient.waiting_minutes} min</td>
      <td className="cg-mono cg-score">{patient.composite_score}</td>
      <td>
        <StatusBadge status={patient.status} />
      </td>
      <td className="cg-actions" onClick={(e) => e.stopPropagation()}>
        <button
          type="button"
          className="cg-btn cg-btn--admit"
          onClick={() => onAdmit(patient.patient_id)}
        >
          Admit to ICU
        </button>
        <button
          type="button"
          className="cg-btn cg-btn--discharge"
          onClick={() => onDischarge(patient.patient_id)}
        >
          Discharge
        </button>
      </td>
    </tr>
  );
}

function PriorityQueue({ patients, selectedPatientId, onSelect, onAdmit, onDischarge }) {
  return (
    <section className="cg-queue" aria-label="Live priority queue">
      <div className="cg-queue-heading">
        <h2>Live Priority Queue</h2>
        <span className="cg-queue-count">{patients.length} waiting</span>
      </div>
      <div className="cg-table-wrap">
        <table className="cg-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Patient ID</th>
              <th>Acuity / Severity</th>
              <th>Survival %</th>
              <th>Wait Time</th>
              <th>Composite Priority Score</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {patients.length === 0 ? (
              <tr>
                <td colSpan={8} className="cg-empty-row">
                  No queue data received from the backend yet.
                </td>
              </tr>
            ) : (
              patients.map((patient) => (
                <PatientRow
                  key={patient.patient_id}
                  patient={patient}
                  isSelected={selectedPatientId === patient.patient_id}
                  onSelect={onSelect}
                  onAdmit={onAdmit}
                  onDischarge={onDischarge}
                />
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/* ============================================================
   STEP 5: SIMULATION CONTROL PANEL
   ------------------------------------------------------------
   This panel only ever does two things:
     1. POST a command to the backend (surge / fast-forward).
     2. Reflect the lifecycle of that HTTP request (idle / loading /
        success / error) plus, if the backend broadcasts one, its
        own `simulation_status` string over the existing WebSocket.

   It NEVER touches patientQueue or bedCapacity directly. Any queue,
   ranking, or wait-time change the judge sees comes from the same
   useCareGridSocket state that already powers Steps 1–4 — this
   component doesn't receive setters for that state at all, so it
   has no way to mutate it even by accident.
   ============================================================ */

function deriveStatusLabel({ surgeState, speedState, speed, simulationStatus }) {
  // Backend-provided status always wins once it exists — we don't
  // second-guess it with locally-derived text.
  if (simulationStatus) return simulationStatus;

  if (surgeState === 'loading') return 'Emergency surge running';
  if (surgeState === 'error' || speedState === 'error') return 'Simulation error';
  if (speedState === 'loading') return `Fast-forward request sending — ${speed}×`;
  if (speedState === 'success' && speed !== 1) return `Fast-forward active — ${speed}×`;
  return 'Ready';
}

function SimulationControlPanel({ connectionStatus, simulationStatus }) {
  const [surgeState, setSurgeState] = useState('idle'); // idle | loading | success | error
  const [speed, setSpeed] = useState(1);
  const [speedState, setSpeedState] = useState('idle'); // idle | loading | success | error
  const [errorMessage, setErrorMessage] = useState('');

  const isConnected = connectionStatus === 'connected';

  async function handleSurgeClick() {
    if (surgeState === 'loading') return; // guard against double-clicks
    setSurgeState('loading');
    setErrorMessage('');

    try {
      const res = await fetch(SIMULATION_ENDPOINTS.surge, { method: 'POST' });
      if (!res.ok) {
        throw new Error(`Surge request failed with status ${res.status}`);
      }
      // Success here only confirms the backend accepted the command.
      // The actual queue/bed changes arrive later via the WebSocket.
      setSurgeState('success');
    } catch (err) {
      console.error('[CareGrid Sim] Emergency surge request failed:', err);
      setSurgeState('error');
      setErrorMessage('Unable to start simulation. Check that the backend is running.');
    }
  }

  async function handleSpeedSelect(nextSpeed) {
    if (speedState === 'loading') return;
    setSpeed(nextSpeed);
    setSpeedState('loading');
    setErrorMessage('');

    try {
      const res = await fetch(SIMULATION_ENDPOINTS.fastForward, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // NOTE: { speed } is the payload shape given in the Step 5 spec.
        // If the confirmed backend contract differs, this is the only
        // line that needs to change.
        body: JSON.stringify({ speed: nextSpeed }),
      });
      if (!res.ok) {
        throw new Error(`Fast-forward request failed with status ${res.status}`);
      }
      setSpeedState('success');
    } catch (err) {
      console.error('[CareGrid Sim] Fast-forward request failed:', err);
      setSpeedState('error');
      setErrorMessage('Unable to change simulation speed. Check that the backend is running.');
    }
  }

  const statusLabel = deriveStatusLabel({ surgeState, speedState, speed, simulationStatus });
  const hasError = surgeState === 'error' || speedState === 'error';

  return (
    <section className="cg-sim-panel" aria-label="Simulation and demonstration controls">
      <div className="cg-sim-heading">
        <div>
          <h2 className="cg-sim-title">Simulation Controls</h2>
          <p className="cg-sim-subtitle">Demonstration environment</p>
        </div>
        <span className={`cg-sim-status-pill${hasError ? ' cg-sim-status-pill--error' : ''}`}>
          {statusLabel}
        </span>
      </div>

      {!isConnected && (
        <p className="cg-sim-stale-note">
          Live connection unavailable — simulation results may not appear until it's restored.
        </p>
      )}

      <div className="cg-sim-body">
        <div className="cg-sim-group">
          <button
            type="button"
            className="cg-btn cg-btn--surge"
            onClick={handleSurgeClick}
            disabled={surgeState === 'loading'}
          >
            {surgeState === 'loading' ? 'Simulating...' : '🚨 Simulate Emergency Surge'}
          </button>
          {surgeState === 'success' && (
            <p className="cg-sim-feedback cg-sim-feedback--success">Emergency surge triggered</p>
          )}
          {surgeState === 'error' && (
            <p className="cg-sim-feedback cg-sim-feedback--error">Unable to start simulation</p>
          )}
        </div>

        <div className="cg-sim-group">
          <span className="cg-sim-group-label">Simulation Speed</span>
          <div className="cg-speed-buttons" role="group" aria-label="Simulation speed">
            {SIMULATION_SPEEDS.map((s) => (
              <button
                key={s}
                type="button"
                className={`cg-speed-btn${speed === s ? ' cg-speed-btn--active' : ''}`}
                onClick={() => handleSpeedSelect(s)}
                disabled={speedState === 'loading'}
                aria-pressed={speed === s}
              >
                {s}×
              </button>
            ))}
          </div>
          {speedState === 'error' && (
            <p className="cg-sim-feedback cg-sim-feedback--error">{errorMessage}</p>
          )}
        </div>
      </div>

      <p className="cg-sim-disclaimer">
        Simulation and priority-update commands only — decision support only, final allocation
        remains with clinician.
      </p>
    </section>
  );
}

/* ============================================================
   TRANSPARENCY DRAWER
   ------------------------------------------------------------
   Everything rendered here comes straight off the live patient
   object resolved from patientQueue by patient_id. Nothing in
   this component computes a score, a rank, or a reason — it only
   formats/visualizes fields the backend already sent.

   Optional fields (explanation_string, tie_break_used,
   tie_break_reason, score_difference, tie_break_threshold,
   ranking_history) are read defensively with `patient?.field`.
   If the backend hasn't started sending a given field yet, the
   corresponding UI section is simply omitted or shows an
   explicit "unavailable" state — never a fabricated value.
   ============================================================ */

function SurvivalBar({ value }) {
  // Pure visualization of the backend-supplied survival_probability.
  // Not a score contribution, not a weighted calculation.
  const pct = Math.max(0, Math.min(1, value ?? 0)) * 100;
  return (
    <div className="cg-metric-bar-track" aria-hidden="true">
      <div className="cg-metric-bar-fill" style={{ width: `${pct}%` }} />
    </div>
  );
}

function TieBreakSection({ patient }) {
  if (patient?.tie_break_used !== true) return null;

  return (
    <section className="cg-drawer-section cg-drawer-tiebreak">
      <h3 className="cg-drawer-section-title">Tie-Break Applied</h3>
      <p className="cg-drawer-tiebreak-reason">
        {patient.tie_break_reason || 'Backend flagged a tie-break but did not supply a reason string.'}
      </p>
      {(patient.score_difference !== undefined || patient.tie_break_threshold !== undefined) && (
        <div className="cg-drawer-tiebreak-meta">
          {patient.score_difference !== undefined && (
            <span>
              Score difference: <span className="cg-mono">{patient.score_difference}</span>
            </span>
          )}
          {patient.tie_break_threshold !== undefined && (
            <span>
              Threshold: <span className="cg-mono">{patient.tie_break_threshold}</span>
            </span>
          )}
        </div>
      )}
    </section>
  );
}

function RankingHistorySection({ patient }) {
  const history = patient?.ranking_history;
  const hasHistory = Array.isArray(history) && history.length > 0;

  return (
    <section className="cg-drawer-section">
      <h3 className="cg-drawer-section-title">Ranking History</h3>
      {hasHistory ? (
        <ul className="cg-drawer-history-list">
          {history.map((entry, i) => (
            <li key={i} className="cg-drawer-history-item">
              <span className="cg-mono cg-drawer-history-rank">
                {entry.rank !== undefined ? `#${entry.rank}` : JSON.stringify(entry)}
              </span>
              {entry.timestamp && <span className="cg-drawer-history-meta">{entry.timestamp}</span>}
              {entry.reason && <span className="cg-drawer-history-meta">{entry.reason}</span>}
            </li>
          ))}
        </ul>
      ) : (
        <p className="cg-drawer-placeholder">
          Ranking history not yet provided by the backend for this patient.
        </p>
      )}
    </section>
  );
}

function TransparencyDrawer({
  patient,
  patientExists,
  connectionStatus,
  onClose,
  onAdmit,
  onDischarge,
}) {
  // Escape key closes the drawer.
  useEffect(() => {
    function handleKey(e) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  const isLive = connectionStatus === 'connected';

  return (
    <>
      <div className="cg-drawer-backdrop" onClick={onClose} />
      <aside className="cg-drawer" aria-label="Transparency drawer" role="dialog" aria-modal="true">
        <div className="cg-drawer-topbar">
          {!isLive && (
            <div className="cg-drawer-stale-banner">
              Live connection unavailable — showing last received data.
            </div>
          )}
          <button type="button" className="cg-drawer-close" onClick={onClose} aria-label="Close drawer">
            ✕
          </button>
        </div>

        {!patientExists ? (
          <div className="cg-drawer-body cg-drawer-gone">
            <p className="cg-drawer-gone-text">Patient no longer in active queue.</p>
            <button type="button" className="cg-btn cg-btn--discharge" onClick={onClose}>
              Close
            </button>
          </div>
        ) : (
          <div className="cg-drawer-body">
            {/* 1 & 2. Patient ID + current rank */}
            <header className="cg-drawer-header">
              <p className="cg-drawer-eyebrow">Patient</p>
              <h2 className="cg-drawer-patient-id">{patient.patient_id}</h2>
              <div className="cg-drawer-header-row">
                <span className="cg-drawer-rank">Current Rank: #{patient.rank}</span>
                <StatusBadge status={patient.status} />
              </div>
            </header>

            {/* 3. Composite priority score */}
            <section className="cg-drawer-section cg-drawer-score-section">
              <h3 className="cg-drawer-section-title">Composite Priority Score</h3>
              <p className="cg-drawer-score-value cg-mono">{patient.composite_score}</p>
            </section>

            {/* 4. Score components (visualization only, no derived math) */}
            <section className="cg-drawer-section">
              <h3 className="cg-drawer-section-title">Score Components</h3>
              <div className="cg-drawer-metrics">
                <div className="cg-drawer-metric-card">
                  <span className="cg-drawer-metric-label">Severity</span>
                  <span className="cg-drawer-metric-value cg-mono">{patient.severity}</span>
                </div>
                <div className="cg-drawer-metric-card">
                  <span className="cg-drawer-metric-label">Survival Likelihood</span>
                  <span className="cg-drawer-metric-value cg-mono">
                    {(patient.survival_probability * 100).toFixed(0)}%
                  </span>
                  <SurvivalBar value={patient.survival_probability} />
                </div>
                <div className="cg-drawer-metric-card">
                  <span className="cg-drawer-metric-label">Waiting Time</span>
                  <span className="cg-drawer-metric-value cg-mono">{patient.waiting_minutes} min</span>
                </div>
              </div>
            </section>

            {/* 5. Why this rank — the core transparency feature */}
            <section className="cg-drawer-section cg-drawer-explanation-section">
              <h3 className="cg-drawer-section-title">Why This Rank?</h3>
              <blockquote className="cg-drawer-explanation">
                {patient.explanation_string && patient.explanation_string.trim().length > 0
                  ? patient.explanation_string
                  : 'Explanation unavailable from backend.'}
              </blockquote>
            </section>

            {/* 6. Tie-break, only if backend evidences one */}
            <TieBreakSection patient={patient} />

            {/* 7. Ranking history, only if backend supplies it */}
            <RankingHistorySection patient={patient} />

            {/* 8. Clinician actions — same handlers as the table row */}
            <section className="cg-drawer-section cg-drawer-actions-section">
              <h3 className="cg-drawer-section-title">Clinician Actions</h3>
              <div className="cg-actions cg-drawer-actions">
                <button
                  type="button"
                  className="cg-btn cg-btn--admit"
                  onClick={() => onAdmit(patient.patient_id)}
                >
                  Admit to ICU
                </button>
                <button
                  type="button"
                  className="cg-btn cg-btn--discharge"
                  onClick={() => onDischarge(patient.patient_id)}
                >
                  Discharge
                </button>
              </div>
            </section>
          </div>
        )}
      </aside>
    </>
  );
}

export default function App() {
  // Single source of truth for backend state. Connects on mount, closes
  // cleanly on unmount, and never sorts/calculates data on the frontend —
  // see useCareGridSocket.js for the WebSocket + payload-mapping logic.
  const { patientQueue, bedCapacity, connectionStatus, simulationStatus } = useCareGridSocket();

  // Selection is tracked by ID only, never by copying the patient object.
  // The drawer resolves the live object from patientQueue on every render,
  // so WebSocket updates (or a patient dropping out of the queue) are
  // reflected immediately without any stale local copy.
  const [selectedPatientId, setSelectedPatientId] = useState(null);

  const selectedPatient = selectedPatientId
    ? patientQueue.find((p) => p.patient_id === selectedPatientId) ?? null
    : null;
  const drawerOpen = selectedPatientId !== null;
  const selectedPatientExists = selectedPatient !== null;

  // Placeholder handlers. These intentionally do nothing beyond logging —
  // no fake success state, no optimistic UI. The WebSocket above is for
  // receiving state only; wiring these to real POST endpoints is a
  // separate future step once that backend contract exists.
  function handleAdmit(patientId) {
    console.log('handleAdmit called for', patientId, '— not yet connected to backend');
  }

  function handleDischarge(patientId) {
    console.log('handleDischarge called for', patientId, '— not yet connected to backend');
  }

  return (
    <div className="cg-app">
      <Header connectionStatus={connectionStatus} />
      <main className="cg-main">
        <div className="cg-main-primary">
          <BedCapacity bedCapacity={bedCapacity} />
          <SimulationControlPanel
            connectionStatus={connectionStatus}
            simulationStatus={simulationStatus}
          />
          <PriorityQueue
            patients={patientQueue}
            selectedPatientId={selectedPatientId}
            onSelect={setSelectedPatientId}
            onAdmit={handleAdmit}
            onDischarge={handleDischarge}
          />
        </div>
      </main>

      {drawerOpen && (
        <TransparencyDrawer
          patient={selectedPatient}
          patientExists={selectedPatientExists}
          connectionStatus={connectionStatus}
          onClose={() => setSelectedPatientId(null)}
          onAdmit={handleAdmit}
          onDischarge={handleDischarge}
        />
      )}
    </div>
  );
}