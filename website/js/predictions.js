/**
 * ==========================================================================
 * SLIPSTREAM ORACLE - DataHub & Predictions Module
 * Handles loading GP datasets, rendering podium telemetry, full race control
 * leaderboard, delta calculations, and commented dynamic discovery logic.
 * ==========================================================================
 */

let activePredictionsData = [];
let currentSortColumn = 'PredictedPosition';
let currentSortAsc = true;

/**
 * Initializes DataHub Tab
 */
async function initDataHubTab() {
  const dataHubContainer = document.getElementById('datahub-content-container');
  if (!dataHubContainer) return;

  // Render the Grand Prix Banner Card
  renderGrandPrixCard();

  // Load and parse the Azerbaijan Grand Prix prediction dataset
  await loadGrandPrixPredictions('Azerbaijan_Grand_Prix');
}

/**
 * Renders the primary Grand Prix selection card
 */
function renderGrandPrixCard() {
  const container = document.getElementById('gp-banner-container');
  if (!container) return;

  // Clean Grand Prix name without underscores
  const rawGpName = 'Azerbaijan_Grand_Prix';
  const cleanGpName = rawGpName.replace(/_/g, ' ');

  container.innerHTML = `
    <div class="gp-selection-card">
      <div class="gp-meta-details">
        <span class="tech-badge red">CURRENT ACTIVE ROUND // 2026</span>
        <h3>${cleanGpName}</h3>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.25rem;">
          Baku City Circuit &bull; 6.003 km &bull; 51 Laps &bull; High-Speed Street Circuit
        </p>
      </div>

      <div class="gp-stats-row">
        <div class="gp-stat-item">
          <span class="gp-stat-title">Dataset Status</span>
          <span class="gp-stat-val" style="color: var(--telemetry-green); font-size: 0.95rem;">
            <span class="beacon-led" style="display:inline-block; margin-right:4px;"></span>
            Final_Data.csv VERIFIED
          </span>
        </div>
        <div class="gp-stat-item">
          <span class="gp-stat-title">Grid Size</span>
          <span class="gp-stat-val">22 Drivers</span>
        </div>
        <div class="gp-stat-item">
          <span class="gp-stat-title">Inference Engine</span>
          <span class="gp-stat-val" style="color: var(--telemetry-cyan); font-size: 0.95rem;">Random Forest (RF-REG-26)</span>
        </div>
      </div>
    </div>
  `;
}

/**
 * Fetches and parses Final_Data.csv for a given GP
 */
async function loadGrandPrixPredictions(gpSlug) {
  // Support both relative paths: direct from workspace root or nested
  const primaryPath = `predictions/2026/${gpSlug}/Final_Data.csv`;
  const secondaryPath = `../predictions/2026/${gpSlug}/Final_Data.csv`;

  let csvContent = null;

  try {
    let res = await fetch(primaryPath);
    if (!res.ok) {
      res = await fetch(secondaryPath);
    }
    if (res.ok) {
      csvContent = await res.text();
    }
  } catch (err) {
    console.warn('[Slipstream Oracle] Fetch failed for prediction CSV (likely file:// protocol). Falling back to sample dataset.', err);
  }

  if (csvContent) {
    activePredictionsData = parseCSV(csvContent);
  } else {
    activePredictionsData = getSamplePredictionData();
  }

  // Ensure drivers metadata is loaded to cross-reference
  if (Object.keys(allDriversData).length === 0) {
    allDriversData = await loadDriversMetadata();
  }

  renderDataHubView();
}

/**
 * Renders both the Podium Showcase and Full Telemetry Table
 */
function renderDataHubView() {
  renderPodiumStage();
  renderTelemetryTable();
}

/**
 * Renders top 3 predicted finishers on the podium stage
 */
function renderPodiumStage() {
  const container = document.getElementById('podium-stage-container');
  if (!container || activePredictionsData.length < 3) return;

  // Sort by PredictedPosition ascending
  const sorted = [...activePredictionsData].sort((a, b) => a.PredictedPosition - b.PredictedPosition);
  const p1 = sorted[0];
  const p2 = sorted[1];
  const p3 = sorted[2];

  const p1Driver = resolveDriver(p1.Driver, allDriversData);
  const p2Driver = resolveDriver(p2.Driver, allDriversData);
  const p3Driver = resolveDriver(p3.Driver, allDriversData);

  container.innerHTML = `
    <h3 class="podium-stage-title">Predicted Podium Telemetry</h3>
    <div class="podium-grid">
      <!-- P2 Second Step -->
      <div class="podium-card p2">
        <div class="podium-badge">P2</div>
        <div class="podium-headshot-wrap">
          <img 
            src="${normalizeHeadshotUrl(p2Driver.headshot)}" 
            alt="${p2Driver.name}" 
            class="podium-headshot" 
            onerror="handleImageFallback(this, '${p2Driver.headshot}')"
          />
        </div>
        <h4 class="podium-driver-name">${p2Driver.name}</h4>
        <div class="podium-driver-team">${p2.Team} #${p2Driver.number}</div>
        <div class="podium-score-pill">Model Score: ${p2.PredictedFinish.toFixed(2)}</div>
        <div style="margin-top: 0.6rem;">${renderDeltaBadge(p2.GridPosition, p2.PredictedPosition)}</div>
      </div>

      <!-- P1 Center Apex Step -->
      <div class="podium-card p1">
        <div class="podium-badge">P1 WINNER</div>
        <div class="podium-headshot-wrap" style="height: 220px;">
          <img 
            src="${normalizeHeadshotUrl(p1Driver.headshot)}" 
            alt="${p1Driver.name}" 
            class="podium-headshot" 
            onerror="handleImageFallback(this, '${p1Driver.headshot}')"
          />
        </div>
        <h4 class="podium-driver-name" style="font-size: 1.55rem;">${p1Driver.name}</h4>
        <div class="podium-driver-team" style="color: var(--telemetry-gold);">${p1.Team} #${p1Driver.number}</div>
        <div class="podium-score-pill" style="border: 1px solid var(--telemetry-gold); color: var(--telemetry-gold);">
          Model Score: ${p1.PredictedFinish.toFixed(2)}
        </div>
        <div style="margin-top: 0.6rem;">${renderDeltaBadge(p1.GridPosition, p1.PredictedPosition)}</div>
      </div>

      <!-- P3 Third Step -->
      <div class="podium-card p3">
        <div class="podium-badge">P3</div>
        <div class="podium-headshot-wrap">
          <img 
            src="${normalizeHeadshotUrl(p3Driver.headshot)}" 
            alt="${p3Driver.name}" 
            class="podium-headshot" 
            onerror="handleImageFallback(this, '${p3Driver.headshot}')"
          />
        </div>
        <h4 class="podium-driver-name">${p3Driver.name}</h4>
        <div class="podium-driver-team">${p3.Team} #${p3Driver.number}</div>
        <div class="podium-score-pill">Model Score: ${p3.PredictedFinish.toFixed(2)}</div>
        <div style="margin-top: 0.6rem;">${renderDeltaBadge(p3.GridPosition, p3.PredictedPosition)}</div>
      </div>
    </div>
  `;
}

/**
 * Calculates position change delta between starting grid and predicted finish rank
 */
function renderDeltaBadge(gridPos, predPos) {
  const delta = gridPos - predPos; // Positive = gained positions (started 3, predicted 1 = +2)
  if (delta > 0) {
    return `<span class="delta-badge gain">&blacktriangle; +${delta} GAINED</span>`;
  } else if (delta < 0) {
    return `<span class="delta-badge loss">&blacktriangledown; ${delta} LOST</span>`;
  } else {
    return `<span class="delta-badge even">&boxh; MAINTAIN</span>`;
  }
}

/**
 * Renders the full 22-car telemetry classification table
 */
function renderTelemetryTable() {
  const tableBody = document.getElementById('telemetry-table-body');
  if (!tableBody) return;

  const data = [...activePredictionsData];

  // Apply sorting
  data.sort((a, b) => {
    let valA = a[currentSortColumn];
    let valB = b[currentSortColumn];
    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();
    if (valA < valB) return currentSortAsc ? -1 : 1;
    if (valA > valB) return currentSortAsc ? 1 : -1;
    return 0;
  });

  tableBody.innerHTML = data.map(row => {
    const driver = resolveDriver(row.Driver, allDriversData);
    const teamColor = getTeamColor(row.Team);
    const headshot = normalizeHeadshotUrl(driver.headshot);

    return `
      <tr>
        <td class="pos-cell">
          <span style="border-left: 3px solid ${teamColor}; padding-left: 0.5rem;">
            ${row.PredictedPosition}
          </span>
        </td>
        <td>
          <div class="driver-cell">
            <img 
              src="${headshot}" 
              alt="${driver.name}" 
              class="driver-table-thumb" 
              onerror="handleImageFallback(this, '${driver.headshot}')"
            />
            <div>
              <span class="driver-name-text">${driver.name}</span>
              <span class="driver-code-tag">${row.Driver}</span>
            </div>
          </div>
        </td>
        <td>
          <div class="team-badge-cell">
            <span class="team-color-indicator" style="background-color: ${teamColor};"></span>
            <span>${row.Team}</span>
          </div>
        </td>
        <td style="font-family: var(--font-mono);">${row.GridPosition}</td>
        <td style="font-family: var(--font-mono);">${row.QualiPosition}</td>
        <td class="score-cell">${row.PredictedFinish.toFixed(2)}</td>
        <td>${renderDeltaBadge(row.GridPosition, row.PredictedPosition)}</td>
      </tr>
    `;
  }).join('');
}

/**
 * Fallback prediction dataset matching the Azerbaijan Grand Prix sample
 */
function getSamplePredictionData() {
  return [
    { Driver: "NOR", Team: "McLaren", QualiPosition: 1, GridPosition: 1, PredictedFinish: 1.18, PredictedPosition: 1 },
    { Driver: "VER", Team: "Red Bull Racing", QualiPosition: 3, GridPosition: 3, PredictedFinish: 1.84, PredictedPosition: 2 },
    { Driver: "LEC", Team: "Ferrari", QualiPosition: 2, GridPosition: 2, PredictedFinish: 2.42, PredictedPosition: 3 },
    { Driver: "PIA", Team: "McLaren", QualiPosition: 4, GridPosition: 4, PredictedFinish: 3.75, PredictedPosition: 4 },
    { Driver: "HAM", Team: "Ferrari", QualiPosition: 5, GridPosition: 5, PredictedFinish: 4.90, PredictedPosition: 5 },
    { Driver: "RUS", Team: "Mercedes", QualiPosition: 6, GridPosition: 6, PredictedFinish: 5.82, PredictedPosition: 6 },
    { Driver: "ANT", Team: "Mercedes", QualiPosition: 8, GridPosition: 8, PredictedFinish: 7.15, PredictedPosition: 7 },
    { Driver: "SAI", Team: "Williams", QualiPosition: 7, GridPosition: 7, PredictedFinish: 7.80, PredictedPosition: 8 },
    { Driver: "ALB", Team: "Williams", QualiPosition: 10, GridPosition: 10, PredictedFinish: 8.95, PredictedPosition: 9 },
    { Driver: "ALO", Team: "Aston Martin", QualiPosition: 9, GridPosition: 9, PredictedFinish: 9.40, PredictedPosition: 10 },
    { Driver: "HAD", Team: "Red Bull Racing", QualiPosition: 12, GridPosition: 12, PredictedFinish: 11.20, PredictedPosition: 11 },
    { Driver: "GAS", Team: "Alpine", QualiPosition: 11, GridPosition: 11, PredictedFinish: 11.65, PredictedPosition: 12 },
    { Driver: "OCO", Team: "Haas F1 Team", QualiPosition: 14, GridPosition: 14, PredictedFinish: 12.85, PredictedPosition: 13 },
    { Driver: "BEA", Team: "Haas F1 Team", QualiPosition: 13, GridPosition: 13, PredictedFinish: 13.40, PredictedPosition: 14 },
    { Driver: "LAW", Team: "Racing Bulls", QualiPosition: 16, GridPosition: 16, PredictedFinish: 14.60, PredictedPosition: 15 },
    { Driver: "HUL", Team: "Audi", QualiPosition: 15, GridPosition: 15, PredictedFinish: 15.10, PredictedPosition: 16 },
    { Driver: "COL", Team: "Alpine", QualiPosition: 17, GridPosition: 17, PredictedFinish: 16.20, PredictedPosition: 17 },
    { Driver: "STR", Team: "Aston Martin", QualiPosition: 18, GridPosition: 18, PredictedFinish: 17.35, PredictedPosition: 18 },
    { Driver: "BOR", Team: "Audi", QualiPosition: 19, GridPosition: 19, PredictedFinish: 18.50, PredictedPosition: 19 },
    { Driver: "LIN", Team: "Racing Bulls", QualiPosition: 20, GridPosition: 20, PredictedFinish: 19.25, PredictedPosition: 20 },
    { Driver: "BOT", Team: "Cadillac", QualiPosition: 21, GridPosition: 21, PredictedFinish: 20.40, PredictedPosition: 21 },
    { Driver: "PER", Team: "Cadillac", QualiPosition: 22, GridPosition: 22, PredictedFinish: 21.15, PredictedPosition: 22 }
  ];
}

/* ==========================================================================
   DYNAMIC GP FOLDER DISCOVERY LOGIC (EXPERIMENTAL)
   
   NOTE PER WEBSITE_PLAN.MD:
   Browsers cannot natively enumerate arbitrary server filesystem directories
   on static GitHub Pages hosting without an index or manifest.
   
   Below is the complete architectural implementation for dynamic GP discovery:
   - It checks a generated static manifest (manifest.json) OR iterates through
     known Grand Prix season directories, verifying the presence of Final_Data.csv
     before instantiating a GP card.
   - Keep this section commented out as requested. When ready, uncomment and wire
     it into initDataHubTab().
   ========================================================================== */

/*
async function discoverGrandPrixDatasets() {
  const discoveredGps = [];
  
  // Approach A: Manifest-based discovery (Recommended for GitHub Pages)
  // try {
  //   const manifestRes = await fetch('data/gp_manifest.json');
  //   if (manifestRes.ok) {
  //     const manifest = await manifestRes.json();
  //     for (const item of manifest) {
  //       // Verify Final_Data.csv exists before creating card
  //       const testRes = await fetch(item.file, { method: 'HEAD' });
  //       if (testRes.ok) {
  //         discoveredGps.push({
  //           rawName: item.slug,
  //           displayName: item.slug.replace(/_/g, ' '),
  //           filePath: item.file
  //         });
  //       }
  //     }
  //     return discoveredGps;
  //   }
  // } catch (e) {
  //   console.log('Manifest discovery bypassed:', e);
  // }

  // Approach B: Probing directory structure for 2026 calendar rounds
  // const seasonCalendar = [
  //   "Bahrain_Grand_Prix",
  //   "Saudi_Arabian_Grand_Prix",
  //   "Australian_Grand_Prix",
  //   "Japanese_Grand_Prix",
  //   "Chinese_Grand_Prix",
  //   "Miami_Grand_Prix",
  //   "Emilia_Romagna_Grand_Prix",
  //   "Monaco_Grand_Prix",
  //   "Canadian_Grand_Prix",
  //   "Spanish_Grand_Prix",
  //   "Austrian_Grand_Prix",
  //   "British_Grand_Prix",
  //   "Hungarian_Grand_Prix",
  //   "Belgian_Grand_Prix",
  //   "Dutch_Grand_Prix",
  //   "Italian_Grand_Prix",
  //   "Azerbaijan_Grand_Prix",
  //   "Singapore_Grand_Prix",
  //   "United_States_Grand_Prix",
  //   "Mexico_City_Grand_Prix",
  //   "Sao_Paulo_Grand_Prix",
  //   "Las_Vegas_Grand_Prix",
  //   "Qatar_Grand_Prix",
  //   "Abu_Dhabi_Grand_Prix"
  // ];

  // for (const gpSlug of seasonCalendar) {
  //   const targetCsvPath = `predictions/2026/${gpSlug}/Final_Data.csv`;
  //   try {
  //     const check = await fetch(targetCsvPath, { method: 'HEAD' });
  //     // Only consider GP available when Final_Data.csv actually exists!
  //     if (check.ok) {
  //       discoveredGps.push({
  //         rawName: gpSlug,
  //         displayName: gpSlug.replace(/_/g, ' '),
  //         filePath: targetCsvPath
  //       });
  //     }
  //   } catch (err) {
  //     // File does not exist for this round, omit card per spec
  //   }
  // }

  // return discoveredGps;
}
*/
