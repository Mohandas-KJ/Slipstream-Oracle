/**
 * ==========================================================================
 * SLIPSTREAM ORACLE - Drivers Module
 * Renders the 22 Formula 1 driver cards with team styling, hip-crop cutouts,
 * interactive constructor filtering, and search.
 * ==========================================================================
 */

let allDriversData = {};
let activeConstructorFilter = 'ALL';
let currentSearchTerm = '';

/**
 * Initializes the Drivers tab
 */
async function initDriversTab() {
  const container = document.getElementById('drivers-grid-container');
  if (!container) return;

  // Load driver metadata
  allDriversData = await loadDriversMetadata();

  // Populate constructor filter pills
  initConstructorFilters();

  // Bind search input
  const searchInput = document.getElementById('driver-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      currentSearchTerm = e.target.value.toLowerCase().trim();
      renderDriversGrid();
    });
  }

  // Initial render
  renderDriversGrid();
}

/**
 * Creates constructor filter buttons dynamically based on present teams
 */
function initConstructorFilters() {
  const filterWrap = document.getElementById('constructor-filter-wrap');
  if (!filterWrap) return;

  const teams = new Set();
  Object.values(allDriversData).forEach(d => {
    if (d.team) teams.add(d.team);
  });

  const teamList = ['ALL', ...Array.from(teams).sort()];
  filterWrap.innerHTML = '';

  teamList.forEach(team => {
    const btn = document.createElement('button');
    btn.className = `team-pill-btn ${team === activeConstructorFilter ? 'active' : ''}`;
    btn.textContent = team;
    btn.setAttribute('type', 'button');
    btn.addEventListener('click', () => {
      activeConstructorFilter = team;
      document.querySelectorAll('.team-pill-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderDriversGrid();
    });
    filterWrap.appendChild(btn);
  });
}

/**
 * Renders the driver cards based on current filter & search
 */
function renderDriversGrid() {
  const container = document.getElementById('drivers-grid-container');
  if (!container) return;

  const driverEntries = Object.entries(allDriversData);

  const filtered = driverEntries.filter(([code, driver]) => {
    const matchesTeam = activeConstructorFilter === 'ALL' || driver.team === activeConstructorFilter;
    const matchesSearch = !currentSearchTerm || 
      driver.name.toLowerCase().includes(currentSearchTerm) ||
      code.toLowerCase().includes(currentSearchTerm) ||
      String(driver.number).includes(currentSearchTerm) ||
      driver.team.toLowerCase().includes(currentSearchTerm);
    return matchesTeam && matchesSearch;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 1rem; color: var(--text-muted);">
        <p style="font-family: var(--font-race); font-size: 1.25rem; text-transform: uppercase;">No Drivers Found</p>
        <p style="font-size: 0.9rem; margin-top: 0.5rem;">Try adjusting your search criteria or constructor filter.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(([code, driver]) => {
    const teamColor = getTeamColor(driver.team);
    const headshotSrc = normalizeHeadshotUrl(driver.headshot);

    return `
      <article class="driver-card" style="--card-team-color: ${teamColor};" data-driver-code="${code}">
        <div class="driver-card-team-stripe"></div>
        <div class="driver-card-number-watermark">${driver.number}</div>
        
        <div class="driver-card-image-wrap">
          <img 
            src="${headshotSrc}" 
            alt="${driver.name} - ${driver.team}" 
            class="driver-card-image"
            loading="lazy"
            onload="this.style.opacity=1"
            onerror="handleImageFallback(this, '${driver.headshot}')"
          />
        </div>

        <div class="driver-card-body">
          <div class="driver-card-meta">
            <span class="driver-card-team">
              <span class="team-color-indicator"></span>
              ${driver.team}
            </span>
            <span class="driver-card-number-badge">#${driver.number}</span>
          </div>
          
          <h3 class="driver-card-name">${driver.name}</h3>
          <p class="driver-card-desc">${driver.description}</p>
        </div>
      </article>
    `;
  }).join('');
}
