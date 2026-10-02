/**
 * ==========================================================================
 * SLIPSTREAM ORACLE - Data Layer
 * Handles JSON/CSV fetching, normalization, schema resolution and fallbacks
 * ==========================================================================
 */

// Formula 1 Constructor Accent Color Mapping
const CONSTRUCTOR_COLORS = {
  "McLaren": "#FF8000",
  "Red Bull Racing": "#3671C6",
  "Ferrari": "#E8002D",
  "Mercedes": "#27F4D2",
  "Williams": "#64C4FF",
  "Aston Martin": "#229971",
  "Alpine": "#0093CC",
  "Haas F1 Team": "#B6BABD",
  "Haas": "#B6BABD",
  "Audi": "#F50537",
  "Racing Bulls": "#6692FF",
  "Cadillac": "#D4AF37"
};

/**
 * Returns team signature hex color or fallback
 */
function getTeamColor(teamName) {
  if (!teamName) return "#E10600";
  return CONSTRUCTOR_COLORS[teamName] || "#E10600";
}

/**
 * Normalizes headshot URLs to be bulletproof across Windows, Linux and GitHub Pages
 * Handles .AVIF vs .avif, underscores, and known disk filename aliases.
 */
function normalizeHeadshotUrl(url) {
  if (!url) return 'assets/Headshots/Lando_Norris.avif';
  
  let cleaned = url.trim();
  // Ensure relative path matches root location
  if (cleaned.startsWith('/')) {
    cleaned = cleaned.substring(1);
  }
  
  // Standardize extension to lowercase .avif
  cleaned = cleaned.replace(/\.AVIF$/i, '.avif');
  
  return cleaned;
}

/**
 * Set up image fallback logic for driver headshots
 */
function handleImageFallback(imgElement, originalSrc) {
  imgElement.onerror = function() {
    // Attempt alternate filename spellings
    if (this.src.includes('George_Russell.avif')) {
      this.src = this.src.replace('George_Russell.avif', 'George_Russel.avif');
      return;
    }
    if (this.src.includes('George_Russel.avif')) {
      this.src = this.src.replace('George_Russel.avif', 'George_Russell.avif');
      return;
    }
    if (this.src.includes('Pierre_Gasly.avif')) {
      this.src = this.src.replace('Pierre_Gasly.avif', 'Pierre Gasly.avif');
      return;
    }
    if (this.src.includes('Pierre%20Gasly.avif') || this.src.includes('Pierre Gasly.avif')) {
      this.src = this.src.replace(/Pierre(%20| )Gasly\.avif/, 'Pierre_Gasly.avif');
      return;
    }
    // Prevent infinite loop if fallback fails
    this.onerror = null;
  };
}

/**
 * Robust CSV parser that handles quotes, commas, and line endings
 */
function parseCSV(text) {
  if (!text || typeof text !== 'string') return [];
  
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) return [];

  const headers = lines[0].split(',').map(h => h.trim());
  const rows = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    // Handle commas inside quotes or standard split
    const values = [];
    let insideQuote = false;
    let entry = '';

    for (let char of line) {
      if (char === '"' || char === "'") {
        insideQuote = !insideQuote;
      } else if (char === ',' && !insideQuote) {
        values.push(entry.trim());
        entry = '';
      } else {
        entry += char;
      }
    }
    values.push(entry.trim());

    if (values.length === headers.length) {
      const rowObj = {};
      headers.forEach((h, idx) => {
        let val = values[idx];
        // Strip outer quotes if present
        if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
          val = val.slice(1, -1);
        }
        // Coerce numbers where applicable
        if (['QualiPosition', 'GridPosition', 'PredictedPosition'].includes(h)) {
          rowObj[h] = parseInt(val, 10) || 0;
        } else if (h === 'PredictedFinish') {
          rowObj[h] = parseFloat(val) || 0.0;
        } else {
          rowObj[h] = val;
        }
      });
      rows.push(rowObj);
    }
  }

  return rows;
}

/**
 * Loads driver metadata from assets/drivers.json
 */
async function loadDriversMetadata() {
  try {
    const response = await fetch('assets/drivers.json');
    if (!response.ok) {
      throw new Error(`Failed to load drivers.json: status ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (err) {
    console.warn('[Slipstream Oracle] Could not fetch drivers.json via HTTP (likely local file:// protocol). Using embedded metadata.', err);
    return getFallbackDriversMetadata();
  }
}

/**
 * Embedded fallback metadata matching assets/drivers.json for file:// protocol
 */
function getFallbackDriversMetadata() {
  return {
    "NOR": { "name": "Lando Norris", "number": 1, "team": "McLaren", "description": "British Formula 1 driver competing for McLaren, known for his qualifying pace, racecraft and consistency.", "headshot": "assets/Headshots/Lando_Norris.avif" },
    "PIA": { "name": "Oscar Piastri", "number": 81, "team": "McLaren", "description": "Australian Formula 1 driver competing for McLaren, recognized for his composed racecraft and strong technical approach.", "headshot": "assets/Headshots/Oscar_Piastri.avif" },
    "VER": { "name": "Max Verstappen", "number": 3, "team": "Red Bull Racing", "description": "Dutch Formula 1 driver competing for Red Bull Racing, renowned for his aggressive racecraft, pace and consistency.", "headshot": "assets/Headshots/Max_Verstappen.avif" },
    "HAD": { "name": "Isack Hadjar", "number": 6, "team": "Red Bull Racing", "description": "French Formula 1 driver competing for Red Bull Racing, bringing strong junior-category experience and developing racecraft.", "headshot": "assets/Headshots/Isack_Hadjar.avif" },
    "LEC": { "name": "Charles Leclerc", "number": 16, "team": "Ferrari", "description": "Monegasque Formula 1 driver competing for Ferrari, known for exceptional qualifying speed and precise car control.", "headshot": "assets/Headshots/Charles_Leclerc.avif" },
    "HAM": { "name": "Lewis Hamilton", "number": 44, "team": "Ferrari", "description": "British Formula 1 driver competing for Ferrari, a highly experienced competitor known for racecraft and qualifying ability.", "headshot": "assets/Headshots/Lewis_Hamilton.avif" },
    "RUS": { "name": "George Russell", "number": 63, "team": "Mercedes", "description": "British Formula 1 driver competing for Mercedes, known for his qualifying pace, consistency and technical feedback.", "headshot": "assets/Headshots/George_Russell.avif" },
    "ANT": { "name": "Kimi Antonelli", "number": 12, "team": "Mercedes", "description": "Italian Formula 1 driver competing for Mercedes, bringing strong junior-category results and developing Formula 1 experience.", "headshot": "assets/Headshots/Kimi_Antonelli.avif" },
    "ALB": { "name": "Alexander Albon", "number": 23, "team": "Williams", "description": "Thai-British Formula 1 driver competing for Williams, known for his adaptability, racecraft and technical understanding.", "headshot": "assets/Headshots/Alexander_Albon.avif" },
    "SAI": { "name": "Carlos Sainz", "number": 55, "team": "Williams", "description": "Spanish Formula 1 driver competing for Williams, recognized for his racecraft, consistency and strategic awareness.", "headshot": "assets/Headshots/Carlos_Sainz.avif" },
    "ALO": { "name": "Fernando Alonso", "number": 14, "team": "Aston Martin", "description": "Spanish Formula 1 driver competing for Aston Martin, renowned for his experience, racecraft and strategic ability.", "headshot": "assets/Headshots/Fernando_Alonso.avif" },
    "STR": { "name": "Lance Stroll", "number": 18, "team": "Aston Martin", "description": "Canadian Formula 1 driver competing for Aston Martin, with extensive experience across Formula 1 competition.", "headshot": "assets/Headshots/Lance_Stroll.avif" },
    "GAS": { "name": "Pierre Gasly", "number": 10, "team": "Alpine", "description": "French Formula 1 driver competing for Alpine, known for his speed, qualifying performances and race experience.", "headshot": "assets/Headshots/Pierre_Gasly.avif" },
    "COL": { "name": "Franco Colapinto", "number": 43, "team": "Alpine", "description": "Argentine Formula 1 driver competing for Alpine, bringing strong junior-category experience and developing Formula 1 racecraft.", "headshot": "assets/Headshots/Franco_Colapinto.avif" },
    "OCO": { "name": "Esteban Ocon", "number": 31, "team": "Haas F1 Team", "description": "French Formula 1 driver competing for Haas, bringing extensive Formula 1 experience and strong racecraft.", "headshot": "assets/Headshots/Esteban_Ocon.avif" },
    "BEA": { "name": "Oliver Bearman", "number": 87, "team": "Haas F1 Team", "description": "British Formula 1 driver competing for Haas, known for his junior-category success and developing Formula 1 experience.", "headshot": "assets/Headshots/Oliver_Bearman.avif" },
    "HUL": { "name": "Nico Hulkenberg", "number": 27, "team": "Audi", "description": "German Formula 1 driver competing for Audi, an experienced competitor known for his qualifying performances and racecraft.", "headshot": "assets/Headshots/Nico_Hulkenberg.avif" },
    "BOR": { "name": "Gabriel Bortoleto", "number": 5, "team": "Audi", "description": "Brazilian Formula 1 driver competing for Audi, bringing strong junior-category results and developing Formula 1 experience.", "headshot": "assets/Headshots/Gabriel_Bortoleto.avif" },
    "LAW": { "name": "Liam Lawson", "number": 30, "team": "Racing Bulls", "description": "New Zealand Formula 1 driver competing for Racing Bulls, known for his adaptability, racecraft and competitive junior-category background.", "headshot": "assets/Headshots/Liam_Lawson.avif" },
    "LIN": { "name": "Arvid Lindblad", "number": 41, "team": "Racing Bulls", "description": "British-Swedish Formula 1 driver competing for Racing Bulls, entering Formula 1 with a strong junior-category background.", "headshot": "assets/Headshots/Arvid_Lindblad.avif" },
    "PER": { "name": "Sergio Perez", "number": 11, "team": "Cadillac", "description": "Mexican Formula 1 driver competing for Cadillac, an experienced competitor known for tyre management, racecraft and strategic driving.", "headshot": "assets/Headshots/Sergio_Perez.avif" },
    "BOT": { "name": "Valtteri Bottas", "number": 77, "team": "Cadillac", "description": "Finnish Formula 1 driver competing for Cadillac, known for his qualifying pace, race experience and technical feedback.", "headshot": "assets/Headshots/Valtteri_Bottas.avif" }
  };
}

/**
 * Resolves a 3-letter driver code (e.g. 'VER') into its full metadata object
 */
function resolveDriver(code, driversMap) {
  if (!code) return null;
  const upperCode = code.toUpperCase().trim();
  if (driversMap && driversMap[upperCode]) {
    return {
      code: upperCode,
      ...driversMap[upperCode]
    };
  }
  // Fallback driver info
  return {
    code: upperCode,
    name: upperCode,
    number: "--",
    team: "Formula 1",
    description: "Competitor in the Formula 1 World Championship.",
    headshot: "assets/Headshots/Lando_Norris.avif"
  };
}
