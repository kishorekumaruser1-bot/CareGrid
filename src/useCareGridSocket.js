import { useEffect, useRef, useState } from 'react';

const WS_URL = 'ws://localhost:8000/ws';
const RECONNECT_DELAY_MS = 3000;

/* ============================================================
   REQUIRED FIELDS
   These match the example payload given in the integration spec.
   They are used ONLY to validate that incoming data has the shape
   the UI expects — nothing here calculates or invents a value.
   If the real backend contract differs, update these lists (and
   mapBackendPayload below) to match it exactly.
   ============================================================ */
const REQUIRED_PATIENT_FIELDS = [
  'patient_id',
  'rank',
  'severity',
  'survival_probability',
  'waiting_minutes',
  'composite_score',
  'status',
];

const REQUIRED_BED_FIELDS = ['total_beds', 'occupied_beds', 'available_beds'];

function isValidPatient(obj) {
  return (
    obj &&
    typeof obj === 'object' &&
    REQUIRED_PATIENT_FIELDS.every((field) => field in obj)
  );
}

function isValidBedCapacity(obj) {
  return (
    obj &&
    typeof obj === 'object' &&
    REQUIRED_BED_FIELDS.every((field) => field in obj)
  );
}

function isValidSimulationStatus(value) {
  // The backend contract for this field isn't confirmed yet. We only
  // accept a plain string so we never render "[object Object]" or
  // similar if the shape turns out to differ — if it's not a string,
  // we simply don't surface it rather than guessing at its shape.
  return typeof value === 'string' && value.trim().length > 0;
}

/* ============================================================
   PAYLOAD MAPPING — SINGLE ISOLATED ENTRY POINT
   ------------------------------------------------------------
   >>> THIS IS THE ONE FUNCTION TO EDIT ONCE THE REAL BACKEND <<<
   >>> WEBSOCKET MESSAGE SCHEMA IS CONFIRMED.                 <<<

   The exact shape of FastAPI's messages hasn't been provided yet,
   so this function stays defensive: it recognizes a couple of
   conventional shapes (a bare patient array, or an object with
   queue/bed_capacity keys) and otherwise logs and does nothing.

   It never fabricates a field. If a message doesn't match a
   recognized shape, or a patient/bed object is missing required
   fields, the update is dropped and the last valid state is kept.

   Return shape:
   { patientQueue: Array|null, bedCapacity: Object|null, simulationStatus: string|null }
   (null on any means "no update for this part of state")
   ============================================================ */
function mapBackendPayload(raw) {
  let patientQueue = null;
  let bedCapacity = null;
  let simulationStatus = null;

  if (Array.isArray(raw)) {
    // Shape: backend sends the queue as a bare array.
    if (raw.every(isValidPatient)) {
      patientQueue = raw;
    } else {
      console.warn('[CareGrid WS] Received patient array with invalid/missing fields:', raw);
    }
    return { patientQueue, bedCapacity, simulationStatus };
  }

  if (raw && typeof raw === 'object') {
    // Shape: backend sends an envelope object. Try common key names.
    const queueCandidate = raw.patient_queue ?? raw.patientQueue ?? raw.queue ?? raw.patients;
    const bedCandidate = raw.bed_capacity ?? raw.bedCapacity ?? raw.beds;
    // Optional: only present if/when the backend starts sending it.
    // Not required for Step 5 to function — the panel falls back to
    // its own request-lifecycle state when this is absent.
    const simCandidate = raw.simulation_status ?? raw.simulationStatus;

    if (queueCandidate !== undefined) {
      if (Array.isArray(queueCandidate) && queueCandidate.every(isValidPatient)) {
        patientQueue = queueCandidate;
      } else {
        console.warn('[CareGrid WS] Queue field present but invalid shape:', queueCandidate);
      }
    }

    if (bedCandidate !== undefined) {
      if (isValidBedCapacity(bedCandidate)) {
        bedCapacity = bedCandidate;
      } else {
        console.warn('[CareGrid WS] Bed capacity field present but invalid shape:', bedCandidate);
      }
    }

    if (simCandidate !== undefined) {
      if (isValidSimulationStatus(simCandidate)) {
        simulationStatus = simCandidate;
      } else {
        console.warn('[CareGrid WS] Simulation status field present but invalid shape:', simCandidate);
      }
    }

    if (queueCandidate === undefined && bedCandidate === undefined && simCandidate === undefined) {
      console.warn(
        '[CareGrid WS] Unrecognized message shape — update mapBackendPayload() with the real backend schema:',
        raw
      );
    }

    return { patientQueue, bedCapacity, simulationStatus };
  }

  console.warn('[CareGrid WS] Message was not an object or array, ignoring:', raw);
  return { patientQueue, bedCapacity, simulationStatus };
}

/**
 * useCareGridSocket
 * Connects to the FastAPI backend WebSocket and exposes the latest
 * backend-provided state. Does not calculate, sort, or invent any
 * clinical data — it only parses, validates, and stores what the
 * backend sends.
 */
export function useCareGridSocket() {
  const [patientQueue, setPatientQueue] = useState([]);
  const [bedCapacity, setBedCapacity] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  // Backend-provided simulation status string, if/when the backend sends
  // one over this same socket. Null until (unless) that happens — the
  // simulation panel does not depend on this to function.
  const [simulationStatus, setSimulationStatus] = useState(null);

  const socketRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const shouldReconnectRef = useRef(true);

  useEffect(() => {
    shouldReconnectRef.current = true;

    function connect() {
      setConnectionStatus((prev) => (prev === 'connected' ? prev : 'connecting'));

      const socket = new WebSocket(WS_URL);
      socketRef.current = socket;

      socket.onopen = () => {
        setConnectionStatus('connected');
      };

      socket.onmessage = (event) => {
        let parsed;
        try {
          parsed = JSON.parse(event.data);
        } catch (err) {
          console.error('[CareGrid WS] Failed to parse message as JSON:', event.data, err);
          return; // keep last valid state
        }

        const {
          patientQueue: newQueue,
          bedCapacity: newBeds,
          simulationStatus: newSimStatus,
        } = mapBackendPayload(parsed);

        if (newQueue !== null) {
          setPatientQueue(newQueue);
        }
        if (newBeds !== null) {
          setBedCapacity(newBeds);
        }
        if (newSimStatus !== null) {
          setSimulationStatus(newSimStatus);
        }
      };

      socket.onerror = (err) => {
        console.error('[CareGrid WS] WebSocket error:', err);
      };

      socket.onclose = () => {
        socketRef.current = null;

        if (!shouldReconnectRef.current) {
          setConnectionStatus('disconnected');
          return;
        }

        setConnectionStatus('reconnecting');
        reconnectTimerRef.current = setTimeout(connect, RECONNECT_DELAY_MS);
      };
    }

    connect();

    return () => {
      // Prevent reconnect attempts and duplicate sockets on unmount.
      shouldReconnectRef.current = false;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, []);

  return { patientQueue, bedCapacity, connectionStatus, simulationStatus };
}