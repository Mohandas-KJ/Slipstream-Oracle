/**
 * ==========================================================================
 * SLIPSTREAM ORACLE - DataHub & Predictions Module
 * Handles loading GP datasets, rendering podium telemetry, full race control
 * leaderboard, delta calculations, and manifest-based GP discovery.
 * ==========================================================================
 */

let activePredictionsData = [];
let currentSortColumn = 'PredictedPosition';
let currentSortAsc = true;
let predictionManifest = null;


/* ==========================================================================
   DATAHUB INITIALIZATION
   ========================================================================== */

/**
 * Initializes DataHub Tab
 */
async function initDataHubTab() {

  const dataHubContainer =
    document.getElementById('datahub-content-container');

  if (!dataHubContainer) return;

  renderGrandPrixCard();

  /*
   * Load the first GP from manifest.
   *
   * We do NOT hard-code the CSV filename here.
   * manifest.json decides which datasets exist.
   */
  const races = await getAvailableGrandPrix();

  if (races.length === 0) {
    console.error(
      '[Slipstream Oracle] No Grand Prix datasets found.'
    );

    activePredictionsData = [];

    renderDataHubView();

    return;
  }

  /*
   * Prefer Azerbaijan if it exists, otherwise use the first
   * GP available in manifest.json.
   */
  const defaultRace =
    races.find(
      race => race.slug === 'Azerbaijan_Grand_Prix'
    ) || races[0];

  renderGrandPrixCard(defaultRace);

  await loadGrandPrixPredictions(defaultRace.slug);
}


/* ==========================================================================
   GRAND PRIX BANNER
   ========================================================================== */

/**
 * Renders the primary Grand Prix selection card.
 */
function renderGrandPrixCard(race = null) {

  const container =
    document.getElementById('gp-banner-container');

  if (!container) return;

  const rawGpName =
    race?.slug || 'Azerbaijan_Grand_Prix';

  const cleanGpName =
    race?.name ||
    rawGpName.replace(/_/g, ' ');

  container.innerHTML = `

    <div class="gp-selection-card">

      <div class="gp-meta-details">

        <span class="tech-badge red">
          CURRENT ACTIVE ROUND // 2026
        </span>

        <h3>
          ${cleanGpName}
        </h3>

        <p
          style="
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 0.25rem;
          "
        >
          Prediction Dataset &bull;
          Slipstream Oracle
        </p>

      </div>


      <div class="gp-stats-row">

        <div class="gp-stat-item">

          <span class="gp-stat-title">
            Dataset Status
          </span>

          <span
            class="gp-stat-val"
            style="
              color: var(--telemetry-green);
              font-size: 0.95rem;
            "
          >

            <span
              class="beacon-led"
              style="
                display:inline-block;
                margin-right:4px;
              "
            ></span>

            Manifest Dataset
          </span>

        </div>


        <div class="gp-stat-item">

          <span class="gp-stat-title">
            Grid Size
          </span>

          <span class="gp-stat-val">
            ${activePredictionsData.length || '--'} Drivers
          </span>

        </div>


        <div class="gp-stat-item">

          <span class="gp-stat-title">
            Inference Engine
          </span>

          <span
            class="gp-stat-val"
            style="
              color: var(--telemetry-cyan);
              font-size: 0.95rem;
            "
          >
            Random Forest (RF-REG-26)
          </span>

        </div>

      </div>

    </div>
  `;
}


/* ==========================================================================
   PREDICTION DATA PATH
   ========================================================================== */

/*
 * IMPORTANT:
 *
 * The page is:
 *
 *     website/index.html
 *
 * The prediction data is:
 *
 *     predictions/2026/
 *
 * fetch() resolves relative URLs from the HTML document URL.
 *
 * Therefore:
 *
 *     ../predictions/2026
 *
 * is correct.
 *
 * DO NOT use:
 *
 *     ../../predictions/2026
 *
 * because that moves outside the repository root.
 *
 * ========================================================================== */

const PREDICTIONS_2026_BASE =
  '../predictions/2026';


/* ==========================================================================
   MANIFEST LOADING
   ========================================================================== */

/**
 * Loads the generated 2026 race manifest.
 *
 * Expected structure:
 *
 * {
 *   "season": 2026,
 *   "races": [
 *     {
 *       "name": "Azerbaijan Grand Prix",
 *       "slug": "Azerbaijan_Grand_Prix",
 *       "data": "Azerbaijan_Grand_Prix/Finaldata.csv"
 *     }
 *   ]
 * }
 */
async function loadPredictionManifest() {

  if (predictionManifest) {
    return predictionManifest;
  }

  const manifestUrl =
    `${PREDICTIONS_2026_BASE}/manifest.json`;

  console.log(
    '[Slipstream Oracle] Loading manifest:',
    manifestUrl
  );

  try {

    const response =
      await fetch(
        manifestUrl,
        {
          cache: 'no-cache'
        }
      );

    if (!response.ok) {

      throw new Error(
        `Manifest request failed: ${response.status} ${response.statusText}`
      );

    }


    predictionManifest =
      await response.json();


    if (
      !predictionManifest ||
      !Array.isArray(predictionManifest.races)
    ) {

      throw new Error(
        'Invalid manifest format. Expected a "races" array.'
      );

    }


    console.log(
      '[Slipstream Oracle] Manifest loaded:',
      predictionManifest
    );


    return predictionManifest;

  } catch (error) {

    console.error(
      '[Slipstream Oracle] Failed to load prediction manifest:',
      error
    );

    predictionManifest = null;

    return null;
  }
}


/* ==========================================================================
   GRAND PRIX DISCOVERY
   ========================================================================== */

/**
 * Returns all GP entries available in manifest.json.
 */
async function getAvailableGrandPrix() {

  const manifest =
    await loadPredictionManifest();

  if (!manifest) {
    return [];
  }

  return manifest.races || [];
}


/* ==========================================================================
   GRAND PRIX DATA LOADING
   ========================================================================== */

/**
 * Fetches and parses the prediction CSV for a given GP.
 *
 * The CSV filename/path comes entirely from manifest.json.
 */
async function loadGrandPrixPredictions(gpSlug) {

  const races =
    await getAvailableGrandPrix();


  const race =
    races.find(
      item => item.slug === gpSlug
    );


  if (!race) {

    console.error(
      `[Slipstream Oracle] GP "${gpSlug}" was not found in manifest.json.`
    );

    activePredictionsData = [];

    renderDataHubView();

    return;
  }


  if (!race.data) {

    console.error(
      `[Slipstream Oracle] No dataset path defined for "${race.name}".`
    );

    activePredictionsData = [];

    renderDataHubView();

    return;
  }


  /*
   * Construct the final CSV URL.
   *
   * Example:
   *
   * ../predictions/2026/Azerbaijan_Grand_Prix/Finaldata.csv
   */
  const csvUrl =
    new URL(
      `${PREDICTIONS_2026_BASE}/${race.data}`,
      window.location.href
    );


  console.log(
    '[Slipstream Oracle] Loading GP dataset:',
    csvUrl.href
  );


  try {

    const response =
      await fetch(
        csvUrl,
        {
          cache: 'no-cache'
        }
      );


    if (!response.ok) {

      throw new Error(
        `CSV request failed: ${response.status} ${response.statusText}`
      );

    }


    const csvContent =
      await response.text();


    if (!csvContent.trim()) {

      throw new Error(
        'CSV file is empty.'
      );

    }


    activePredictionsData =
      parseCSV(csvContent);


    if (
      !Array.isArray(activePredictionsData) ||
      activePredictionsData.length === 0
    ) {

      throw new Error(
        'CSV was loaded but produced no prediction rows.'
      );

    }


    console.log(
      `[Slipstream Oracle] Loaded ${race.name}: ${activePredictionsData.length} drivers`
    );


    /*
     * Update GP banner with actual loaded dataset.
     */
    renderGrandPrixCard(race);


  } catch (error) {

    console.error(
      `[Slipstream Oracle] Failed to load prediction data for ${race.name}:`,
      error
    );


    /*
     * DO NOT silently hide the problem with sample data.
     *
     * Empty DataHub previously made debugging difficult.
     *
     * If the CSV cannot be loaded, display the error state instead.
     */
    activePredictionsData = [];


    showPredictionLoadError(
      race,
      error
    );

  }


  /*
   * Load driver metadata if necessary.
   */
  if (
    typeof allDriversData === 'undefined' ||
    !allDriversData ||
    Object.keys(allDriversData).length === 0
  ) {

    if (typeof loadDriversMetadata === 'function') {

      allDriversData =
        await loadDriversMetadata();

    }

  }


  renderDataHubView();
}


/* ==========================================================================
   ERROR STATE
   ========================================================================== */

function showPredictionLoadError(
  race,
  error
) {

  const container =
    document.getElementById(
      'datahub-content-container'
    );

  if (!container) return;


  container.insertAdjacentHTML(
    'beforeend',
    `

      <div
        class="prediction-error"
        style="
          margin: 1rem 0;
          padding: 1rem;
          border: 1px solid rgba(255, 70, 70, 0.4);
          border-radius: 12px;
          background: rgba(255, 50, 50, 0.06);
        "
      >

        <strong>
          Prediction dataset could not be loaded.
        </strong>

        <p
          style="
            color: var(--text-muted);
            margin-top: 0.4rem;
          "
        >
          ${race?.name || 'Selected Grand Prix'}
        </p>

        <code
          style="
            display:block;
            margin-top:0.5rem;
            font-size:0.78rem;
            word-break:break-all;
          "
        >
          ${error?.message || 'Unknown error'}
        </code>

      </div>

    `
  );
}


/* ==========================================================================
   DATAHUB RENDERING
   ========================================================================== */

/**
 * Renders both the Podium Showcase and Full Telemetry Table.
 */
function renderDataHubView() {

  renderPodiumStage();

  renderTelemetryTable();
}


/* ==========================================================================
   PODIUM
   ========================================================================== */

/**
 * Renders top 3 predicted finishers.
 */
function renderPodiumStage() {

  const container =
    document.getElementById(
      'podium-stage-container'
    );


  if (!container) {
    return;
  }


  if (
    !activePredictionsData ||
    activePredictionsData.length < 3
  ) {

    container.innerHTML = '';

    return;
  }


  const sorted =
    [...activePredictionsData]
      .sort(
        (a, b) =>
          Number(a.PredictedPosition) -
          Number(b.PredictedPosition)
      );


  const p1 = sorted[0];
  const p2 = sorted[1];
  const p3 = sorted[2];


  const p1Driver =
    resolveDriver(
      p1.Driver,
      allDriversData
    );


  const p2Driver =
    resolveDriver(
      p2.Driver,
      allDriversData
    );


  const p3Driver =
    resolveDriver(
      p3.Driver,
      allDriversData
    );


  container.innerHTML = `

    <h3 class="podium-stage-title">
      Predicted Podium Telemetry
    </h3>

    <div class="podium-grid">


      <!-- P2 -->

      <div class="podium-card p2">

        <div class="podium-badge">
          P2
        </div>

        <div class="podium-headshot-wrap">

          <img
            src="${normalizeHeadshotUrl(p2Driver.headshot)}"
            alt="${p2Driver.name}"
            class="podium-headshot"
            onerror="handleImageFallback(this, '${p2Driver.headshot}')"
          />

        </div>

        <h4 class="podium-driver-name">
          ${p2Driver.name}
        </h4>

        <div class="podium-driver-team">
          ${p2.Team} #${p2Driver.number}
        </div>

        <div class="podium-score-pill">
          Model Score: ${Number(p2.PredictedFinish).toFixed(2)}
        </div>

        <div style="margin-top: 0.6rem;">
          ${renderDeltaBadge(
            p2.GridPosition,
            p2.PredictedPosition
          )}
        </div>

      </div>


      <!-- P1 -->

      <div class="podium-card p1">

        <div class="podium-badge">
          P1 WINNER
        </div>

        <div
          class="podium-headshot-wrap"
          style="height: 220px;"
        >

          <img
            src="${normalizeHeadshotUrl(p1Driver.headshot)}"
            alt="${p1Driver.name}"
            class="podium-headshot"
            onerror="handleImageFallback(this, '${p1Driver.headshot}')"
          />

        </div>

        <h4
          class="podium-driver-name"
          style="font-size: 1.55rem;"
        >
          ${p1Driver.name}
        </h4>

        <div
          class="podium-driver-team"
          style="color: var(--telemetry-gold);"
        >
          ${p1.Team} #${p1Driver.number}
        </div>

        <div
          class="podium-score-pill"
          style="
            border: 1px solid var(--telemetry-gold);
            color: var(--telemetry-gold);
          "
        >
          Model Score:
          ${Number(p1.PredictedFinish).toFixed(2)}
        </div>

        <div style="margin-top: 0.6rem;">
          ${renderDeltaBadge(
            p1.GridPosition,
            p1.PredictedPosition
          )}
        </div>

      </div>


      <!-- P3 -->

      <div class="podium-card p3">

        <div class="podium-badge">
          P3
        </div>

        <div class="podium-headshot-wrap">

          <img
            src="${normalizeHeadshotUrl(p3Driver.headshot)}"
            alt="${p3Driver.name}"
            class="podium-headshot"
            onerror="handleImageFallback(this, '${p3Driver.headshot}')"
          />

        </div>

        <h4 class="podium-driver-name">
          ${p3Driver.name}
        </h4>

        <div class="podium-driver-team">
          ${p3.Team} #${p3Driver.number}
        </div>

        <div class="podium-score-pill">
          Model Score:
          ${Number(p3.PredictedFinish).toFixed(2)}
        </div>

        <div style="margin-top: 0.6rem;">
          ${renderDeltaBadge(
            p3.GridPosition,
            p3.PredictedPosition
          )}
        </div>

      </div>

    </div>
  `;
}


/* ==========================================================================
   POSITION DELTA
   ========================================================================== */

/**
 * Calculates position change between starting grid
 * and predicted finish rank.
 */
function renderDeltaBadge(
  gridPos,
  predPos
) {

  const grid =
    Number(gridPos);

  const prediction =
    Number(predPos);

  const delta =
    grid - prediction;


  if (delta > 0) {

    return `
      <span class="delta-badge gain">
        &blacktriangle; +${delta} GAINED
      </span>
    `;

  }


  if (delta < 0) {

    return `
      <span class="delta-badge loss">
        &blacktriangledown; ${Math.abs(delta)} LOST
      </span>
    `;

  }


  return `
    <span class="delta-badge even">
      &boxh; MAINTAIN
    </span>
  `;
}


/* ==========================================================================
   TELEMETRY TABLE
   ========================================================================== */

/**
 * Renders the full prediction classification table.
 */
function renderTelemetryTable() {

  const tableBody =
    document.getElementById(
      'telemetry-table-body'
    );


  if (!tableBody) {
    return;
  }


  if (
    !activePredictionsData ||
    activePredictionsData.length === 0
  ) {

    tableBody.innerHTML = `
      <tr>
        <td
          colspan="7"
          style="
            text-align:center;
            padding:2rem;
            color:var(--text-muted);
          "
        >
          No prediction data available.
        </td>
      </tr>
    `;

    return;
  }


  const data =
    [...activePredictionsData];


  data.sort(
    (a, b) => {

      let valA =
        a[currentSortColumn];

      let valB =
        b[currentSortColumn];


      if (
        typeof valA === 'string'
      ) {

        valA =
          valA.toLowerCase();

      }


      if (
        typeof valB === 'string'
      ) {

        valB =
          valB.toLowerCase();

      }


      if (valA < valB) {

        return currentSortAsc
          ? -1
          : 1;

      }


      if (valA > valB) {

        return currentSortAsc
          ? 1
          : -1;

      }


      return 0;

    }
  );


  tableBody.innerHTML =
    data
      .map(
        row => {

          const driver =
            resolveDriver(
              row.Driver,
              allDriversData
            );


          const teamColor =
            getTeamColor(
              row.Team
            );


          const headshot =
            normalizeHeadshotUrl(
              driver.headshot
            );


          return `

            <tr>

              <td class="pos-cell">

                <span
                  style="
                    border-left: 3px solid ${teamColor};
                    padding-left: 0.5rem;
                  "
                >
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

                    <span class="driver-name-text">
                      ${driver.name}
                    </span>

                    <span class="driver-code-tag">
                      ${row.Driver}
                    </span>

                  </div>

                </div>

              </td>


              <td>

                <div class="team-badge-cell">

                  <span
                    class="team-color-indicator"
                    style="
                      background-color:${teamColor};
                    "
                  ></span>

                  <span>
                    ${row.Team}
                  </span>

                </div>

              </td>


              <td
                style="
                  font-family:var(--font-mono);
                "
              >
                ${row.GridPosition}
              </td>


              <td
                style="
                  font-family:var(--font-mono);
                "
              >
                ${row.QualiPosition}
              </td>


              <td class="score-cell">
                ${Number(row.PredictedFinish).toFixed(2)}
              </td>


              <td>
                ${renderDeltaBadge(
                  row.GridPosition,
                  row.PredictedPosition
                )}
              </td>

            </tr>

          `;

        }
      )
      .join('');
}


/* ==========================================================================
   CSV PARSER
   ========================================================================== */

/**
 * Simple CSV parser.
 *
 * Supports:
 * - comma-separated values
 * - quoted fields
 * - commas inside quoted fields
 */
function parseCSV(csvText) {

  const rows = [];

  let row = [];

  let field = '';

  let insideQuotes = false;


  for (
    let i = 0;
    i < csvText.length;
    i++
  ) {

    const char =
      csvText[i];

    const next =
      csvText[i + 1];


    if (
      char === '"' &&
      insideQuotes &&
      next === '"'
    ) {

      field += '"';

      i++;

      continue;
    }


    if (char === '"') {

      insideQuotes =
        !insideQuotes;

      continue;
    }


    if (
      char === ',' &&
      !insideQuotes
    ) {

      row.push(field.trim());

      field = '';

      continue;
    }


    if (
      (char === '\n' || char === '\r') &&
      !insideQuotes
    ) {

      if (
        char === '\r' &&
        next === '\n'
      ) {

        i++;

      }


      row.push(field.trim());

      field = '';


      if (
        row.some(
          value => value !== ''
        )
      ) {

        rows.push(row);

      }


      row = [];

      continue;
    }


    field += char;

  }


  if (field.length > 0 || row.length > 0) {

    row.push(
      field.trim()
    );

    if (
      row.some(
        value => value !== ''
      )
    ) {

      rows.push(row);

    }

  }


  if (rows.length < 2) {
    return [];
  }


  const headers =
    rows[0].map(
      header =>
        header.trim()
    );


  return rows
    .slice(1)
    .map(
      values => {

        const object = {};

        headers.forEach(
          (header, index) => {

            let value =
              values[index] ?? '';

            value =
              value.trim();


            /*
             * Convert numeric prediction fields.
             */
            if (
              [
                'PredictedPosition',
                'PredictedFinish',
                'GridPosition',
                'QualiPosition'
              ].includes(header)
            ) {

              const numericValue =
                Number(value);


              object[header] =
                Number.isNaN(numericValue)
                  ? value
                  : numericValue;

            } else {

              object[header] =
                value;

            }

          }
        );

        return object;

      }
    );
}


/* ==========================================================================
   OPTIONAL SORT CONTROLS
   ========================================================================== */

/**
 * Allows the HTML table headers to call:
 *
 * sortPredictionTable('PredictedPosition')
 */
function sortPredictionTable(
  column
) {

  if (
    currentSortColumn === column
  ) {

    currentSortAsc =
      !currentSortAsc;

  } else {

    currentSortColumn =
      column;

    currentSortAsc =
      true;

  }


  renderTelemetryTable();
}


/* ==========================================================================
   DEBUG HELPERS
   ========================================================================== */

/**
 * Useful from browser console:
 *
 * await debugPredictionPaths()
 */
async function debugPredictionPaths() {

  const manifestUrl =
    `${PREDICTIONS_2026_BASE}/manifest.json`;


  console.log(
    'Prediction base:',
    PREDICTIONS_2026_BASE
  );


  console.log(
    'Manifest URL:',
    new URL(
      manifestUrl,
      window.location.href
    ).href
  );


  const manifest =
    await loadPredictionManifest();


  console.log(
    'Manifest:',
    manifest
  );


  console.log(
    'Available GPs:',
    manifest?.races || []
  );

}


/* ==========================================================================
   END
   ========================================================================== */