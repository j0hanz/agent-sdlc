import { appendJsonl } from './io.mjs';

/**
 * Telemetry honors the `telemetry_enabled` plugin config, surfaced as an env
 * var. Defaults on; set AGENT_DEV_TELEMETRY=0 to silence.
 */
export function telemetryEnabled() {
  return process.env.AGENT_DEV_TELEMETRY !== '0';
}

/** Write a telemetry record (gated by config). Side effect only. */
export function writeTelemetry(record) {
  if (!telemetryEnabled()) return;
  appendJsonl('.claude/telemetry.log', { timestamp: new Date().toISOString(), ...record });
}
