/**
 * ==========================================================================
 * SLIPSTREAM ORACLE - Charts & Visual Telemetry
 * Lightweight vanilla SVG telemetry visualizers (no external chart libraries)
 * ==========================================================================
 */

/**
 * Generates an inline SVG telemetry gauge or delta bar
 */
function createDeltaSparkline(delta) {
  const width = 60;
  const height = 16;
  const zeroY = height / 2;
  
  let barColor = 'var(--text-muted)';
  let targetY = zeroY;

  if (delta > 0) {
    barColor = 'var(--telemetry-green)';
    targetY = 2;
  } else if (delta < 0) {
    barColor = 'var(--f1-red)';
    targetY = height - 2;
  }

  return `
    <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" style="vertical-align: middle;">
      <line x1="0" y1="${zeroY}" x2="${width}" y2="${zeroY}" stroke="rgba(255,255,255,0.15)" stroke-width="1" />
      <circle cx="${width / 2}" cy="${targetY}" r="3" fill="${barColor}" />
      <line x1="${width / 2}" y1="${zeroY}" x2="${width / 2}" y2="${targetY}" stroke="${barColor}" stroke-width="2" />
    </svg>
  `;
}
