/**
 * ==========================================================================
 * SLIPSTREAM ORACLE - DataHub & Predictions Module
 * Handles dynamic discovery of 2026 Grand Prix predictions via manifest.json,
 * rendering interactive Grand Prix tabs, Podium telemetry, classification
 * leaderboards, full Final_Data.csv inspection, and raw CSV exports.
 * ==========================================================================
 */

// Active State
let predictionManifest = null;
let activeGrandPrix = null;
let activePredictionsData = [];
let activeRawCsvText = '';
let currentSortColumn = 'PredictedPosition';
let currentSortAsc = true;
let currentViewMode = 'leaderboard';
let detectedPredictionsBase = '../predictions/2026';
let fullCsvHeaders = [];
let isDataHubInitialized = false;

/* ==========================================================================
   CIRCUIT & ROUND METADATA
   ========================================================================== */
const CIRCUIT_INFO = {
  "Austrian_Grand_Prix": {
    circuit: "Red Bull Ring",
    location: "Spielberg, Austria",
    length: "4.318 km",
    laps: 71,
    type: "High-Altitude Power & Traction Circuit",
    roundDefault: "Round 08"
  },
  "Azerbaijan_Grand_Prix": {
    circuit: "Baku City Circuit",
    location: "Baku, Azerbaijan",
    length: "6.003 km",
    laps: 51,
    type: "High-Speed Street Circuit",
    roundDefault: "Round 15"
  },
  "Belgian_Grand_Prix": {
    circuit: "Circuit de Spa-Francorchamps",
    location: "Stavelot, Belgium",
    length: "7.004 km",
    laps: 44,
    type: "High-Downforce Elevation Circuit",
    roundDefault: "Round 10"
  },
  "British_Grand_Prix": {
    circuit: "Silverstone Circuit",
    location: "Northamptonshire, UK",
    length: "5.891 km",
    laps: 52,
    type: "Ultra High-Speed Aero Circuit",
    roundDefault: "Round 09"
  },
  "Dutch_Grand_Prix": {
    circuit: "Circuit Zandvoort",
    location: "Zandvoort, Netherlands",
    length: "4.259 km",
    laps: 72,
    type: "Banked Corners & Dune Technical",
    roundDefault: "Round 12"
  },
  "Hungarian_Grand_Prix": {
    circuit: "Hungaroring",
    location: "Mogyoród, Hungary",
    length: "4.381 km",
    laps: 70,
    type: "Twisty High-Downforce Circuit",
    roundDefault: "Round 11"
  },
  "Italian_Grand_Prix": {
    circuit: "Autodromo Nazionale Monza",
    location: "Monza, Italy",
    length: "5.793 km",
    laps: 53,
    type: "Temple of Speed Low-Downforce",
    roundDefault: "Round 13"
  },
  "Spanish_Grand_Prix": {
    circuit: "Circuit de Barcelona-Catalunya",
    location: "Montmeló, Spain",
    length: "4.657 km",
    laps: 66,
    type: "Aerodynamic Benchmark Circuit",
    roundDefault: "Round 14"
  }
};

/* ==========================================================================
   MANIFEST & DATA CANDIDATE PATHS
   ========================================================================== */
/**
 * Look into candidate paths for 2026 manifest.json.
 * Notice: ../../predictions/2026/manifest.json is tried first as requested.
 */
const MANIFEST_CANDIDATE_PATHS = [
  '../../predictions/2026/manifest.json',
  '../predictions/2026/manifest.json',
  'predictions/2026/manifest.json',
  '/predictions/2026/manifest.json'
];

/**
 * Embedded fallback manifest for 2026 season.
 * Ensures 100% offline & local file:// protocol compatibility.
 */
const EMBEDDED_MANIFEST = {
  "season": 2026,
  "races": [
    {
      "name": "Austrian Grand Prix",
      "slug": "Austrian_Grand_Prix",
      "data": "Austrian_Grand_Prix/Final_Data.csv"
    },
    {
      "name": "Azerbaijan Grand Prix",
      "slug": "Azerbaijan_Grand_Prix",
      "data": "Azerbaijan_Grand_Prix/Final_Data.csv"
    },
    {
      "name": "Belgian Grand Prix",
      "slug": "Belgian_Grand_Prix",
      "data": "Belgian_Grand_Prix/Final_Data.csv"
    },
    {
      "name": "British Grand Prix",
      "slug": "British_Grand_Prix",
      "data": "British_Grand_Prix/Final_Data.csv"
    },
    {
      "name": "Dutch Grand Prix",
      "slug": "Dutch_Grand_Prix",
      "data": "Dutch_Grand_Prix/Final_Data.csv"
    },
    {
      "name": "Hungarian Grand Prix",
      "slug": "Hungarian_Grand_Prix",
      "data": "Hungarian_Grand_Prix/Final_Data.csv"
    },
    {
      "name": "Italian Grand Prix",
      "slug": "Italian_Grand_Prix",
      "data": "Italian_Grand_Prix/Final_Data.csv"
    },
    {
      "name": "Spanish Grand Prix",
      "slug": "Spanish_Grand_Prix",
      "data": "Spanish_Grand_Prix/Final_Data.csv"
    }
  ]
};

/**
 * Embedded fallback Final_Data.csv datasets for all 8 Grand Prix rounds.
 * Guarantees zero blank screens even under strict browser CORS policies.
 */
const FALLBACK_PREDICTION_CSVS = {
  "Austrian_Grand_Prix": "PredictedPosition,Year,RoundNumber,Race,Driver,Team,QualiPosition,GridPosition,AvgFinishLast3,AvgFinishLast5,AvgGridLast3,AvgGridLast5,AvgPointsLast3,AvgPointsLast5,TargetFinish,PredictedFinish,Error\n1,2026,8,Austrian_Grand_Prix,RUS,Mercedes,1.0,1.0,6.0,4.8,2.67,3.0,6.0,8.4,1.0,2.86,1.8599999999999999\n2,2026,8,Austrian_Grand_Prix,LEC,Ferrari,2.0,2.0,9.0,6.8,7.33,5.8,4.0,6.2,8.0,3.19,4.8100000000000005\n3,2026,8,Austrian_Grand_Prix,VER,Red Bull Racing,5.0,5.0,4.0,5.2,4.33,5.2,9.0,8.2,2.0,4.69,2.6900000000000004\n4,2026,8,Austrian_Grand_Prix,HAM,Ferrari,3.0,3.0,1.67,3.4,3.33,4.4,20.33,15.4,5.0,4.72,0.28000000000000025\n5,2026,8,Austrian_Grand_Prix,PIA,McLaren,7.0,7.0,7.0,5.2,6.0,5.6,6.67,10.6,4.0,4.99,0.9900000000000002\n6,2026,8,Austrian_Grand_Prix,NOR,McLaren,6.0,6.0,3.33,3.75,5.0,4.8,5.0,8.6,7.0,5.36,1.6399999999999997\n7,2026,8,Austrian_Grand_Prix,HAD,Red Bull Racing,8.0,8.0,5.0,7.0,6.0,9.6,10.0,6.0,6.0,6.89,0.8899999999999997\n8,2026,8,Austrian_Grand_Prix,ANT,Mercedes,4.0,4.0,6.0,4.0,2.0,1.6,16.67,20.0,3.0,7.14,4.14\n9,2026,8,Austrian_Grand_Prix,LAW,Racing Bulls,9.0,9.0,7.0,7.4,10.0,11.0,6.0,4.0,9.0,7.52,1.4800000000000004\n10,2026,8,Austrian_Grand_Prix,GAS,Alpine,11.0,11.0,6.0,6.2,12.33,10.6,8.33,6.2,13.0,8.77,4.23\n11,2026,8,Austrian_Grand_Prix,LIN,Racing Bulls,10.0,10.0,10.0,11.2,11.67,12.2,2.67,1.6,10.0,9.89,0.10999999999999943\n12,2026,8,Austrian_Grand_Prix,BOR,Audi,12.0,12.0,11.67,12.0,13.67,14.2,0.0,0.0,11.0,10.8,0.1999999999999993\n13,2026,8,Austrian_Grand_Prix,HUL,Audi,14.0,14.0,12.0,11.75,11.0,11.2,0.0,0.0,12.0,11.15,0.8499999999999996\n14,2026,8,Austrian_Grand_Prix,OCO,Haas F1 Team,15.0,15.0,12.0,11.8,17.0,15.4,0.67,0.6,16.0,11.65,4.35\n15,2026,8,Austrian_Grand_Prix,BEA,Haas F1 Team,13.0,13.0,12.67,10.0,16.67,16.0,0.33,0.2,14.0,11.67,2.33\n16,2026,8,Austrian_Grand_Prix,SAI,Williams,17.0,17.0,12.33,12.2,14.33,14.4,0.67,0.8,20.0,11.79,8.21\n17,2026,8,Austrian_Grand_Prix,COL,Alpine,16.0,16.0,10.0,10.6,12.33,12.0,3.0,3.0,15.0,11.96,3.039999999999999\n18,2026,8,Austrian_Grand_Prix,ALB,Williams,18.0,18.0,12.67,12.5,15.67,15.8,1.33,1.0,17.0,13.58,3.42\n19,2026,8,Austrian_Grand_Prix,PER,Cadillac,19.0,19.0,15.0,15.4,19.0,19.2,0.0,0.0,21.0,14.05,6.949999999999999\n20,2026,8,Austrian_Grand_Prix,ALO,Aston Martin,21.0,21.0,14.33,14.33,20.67,20.0,0.33,0.2,18.0,14.31,3.6899999999999995\n21,2026,8,Austrian_Grand_Prix,STR,Aston Martin,22.0,22.0,16.0,16.0,21.67,21.0,0.0,0.0,19.0,14.35,4.65\n22,2026,8,Austrian_Grand_Prix,BOT,Cadillac,20.0,20.0,17.67,16.5,20.33,20.0,0.0,0.0,22.0,14.47,7.529999999999999",
  "Azerbaijan_Grand_Prix": "PredictedPosition,Year,RoundNumber,Race,Driver,Team,QualiPosition,GridPosition,AvgFinishLast3,AvgFinishLast5,AvgGridLast3,AvgGridLast5,AvgPointsLast3,AvgPointsLast5,PositionsGainedLastRace,FinishStdLast5,TargetFinish,PredictedFinish,RaceStatus,Error\n1,2026,15,Azerbaijan_Grand_Prix,RUS,Mercedes,1.0,1.0,3.33,3.8,3.33,3.8,14.33,9.8,1.0,1.94,1.0,2.24,1,1.2400000000000002\n2,2026,15,Azerbaijan_Grand_Prix,LEC,Ferrari,2.0,2.0,4.33,3.2,4.67,4.0,7.33,10.4,1.0,1.47,4.0,3.34,4,0.6600000000000001\n3,2026,15,Azerbaijan_Grand_Prix,PIA,McLaren,3.0,3.0,6.33,7.0,5.67,5.2,7.33,6.4,-1.0,2.28,13.0,4.37,13,8.629999999999999\n4,2026,15,Azerbaijan_Grand_Prix,NOR,McLaren,5.0,5.0,2.67,3.2,3.33,4.8,17.33,16.6,-2.0,2.23,,4.51,R,\n5,2026,15,Azerbaijan_Grand_Prix,HAD,Red Bull Racing,4.0,4.0,5.67,5.8,11.33,9.6,8.67,8.4,2.0,0.4,3.0,5.94,3,2.9400000000000004\n6,2026,15,Azerbaijan_Grand_Prix,HAM,Ferrari,6.0,6.0,5.0,4.4,4.33,4.6,6.67,8.4,-2.0,1.02,6.0,6.18,6,0.17999999999999972\n7,2026,15,Azerbaijan_Grand_Prix,VER,Red Bull Racing,8.0,8.0,2.33,6.0,5.0,4.2,11.0,13.2,1.0,7.01,2.0,6.68,2,4.68\n8,2026,15,Azerbaijan_Grand_Prix,ANT,Mercedes,16.0,16.0,1.33,1.6,8.0,6.4,22.67,21.6,1.0,0.8,5.0,7.4,5,2.4000000000000004\n9,2026,15,Azerbaijan_Grand_Prix,GAS,Alpine,7.0,7.0,9.67,10.4,8.67,9.6,2.33,1.4,2.0,1.85,,8.12,R,\n10,2026,15,Azerbaijan_Grand_Prix,COL,Alpine,10.0,9.0,10.0,11.0,10.0,10.8,2.67,1.8,2.0,3.03,,9.32,R,\n11,2026,15,Azerbaijan_Grand_Prix,LAW,Racing Bulls,12.0,11.0,9.0,9.4,12.67,11.6,4.67,3.6,2.0,3.07,12.0,11.33,12,0.6699999999999999\n12,2026,15,Azerbaijan_Grand_Prix,SAI,Williams,9.0,14.0,15.67,16.0,16.67,17.4,0.0,0.0,0.0,1.67,10.0,11.57,10,1.5700000000000003\n13,2026,15,Azerbaijan_Grand_Prix,BEA,Haas F1 Team,11.0,10.0,16.67,15.2,17.67,16.8,0.0,0.0,6.0,2.32,9.0,12.2,9,3.1999999999999993\n14,2026,15,Azerbaijan_Grand_Prix,LIN,Racing Bulls,15.0,15.0,9.67,9.6,9.67,9.0,2.0,1.8,1.0,1.36,7.0,12.38,7,5.380000000000001\n15,2026,15,Azerbaijan_Grand_Prix,OCO,Haas F1 Team,14.0,13.0,14.33,14.6,14.0,14.6,0.0,0.0,2.0,2.24,8.0,13.17,8,5.17\n16,2026,15,Azerbaijan_Grand_Prix,ALB,Williams,13.0,12.0,16.33,16.2,17.33,17.2,0.0,0.0,1.0,0.98,,13.18,R,\n17,2026,15,Azerbaijan_Grand_Prix,BOR,Audi,17.0,17.0,12.33,11.2,10.33,10.6,0.0,0.8,-1.0,1.83,15.0,13.93,15,1.0700000000000003\n18,2026,15,Azerbaijan_Grand_Prix,HUL,Audi,18.0,18.0,10.0,10.4,12.0,11.6,1.67,1.4,1.0,1.85,11.0,14.05,11,3.0500000000000007\n19,2026,15,Azerbaijan_Grand_Prix,STR,Aston Martin,21.0,22.0,15.67,16.0,19.33,19.6,0.0,0.0,7.0,2.24,,16.22,R,\n20,2026,15,Azerbaijan_Grand_Prix,PER,Cadillac,20.0,19.0,15.67,15.2,19.0,19.4,0.0,0.0,-1.0,1.47,14.0,16.24,14,2.2399999999999984\n21,2026,15,Azerbaijan_Grand_Prix,ALO,Aston Martin,19.0,21.0,13.33,15.4,18.67,18.8,0.67,0.4,0.0,3.61,,16.27,R,\n22,2026,15,Azerbaijan_Grand_Prix,BOT,Cadillac,22.0,20.0,18.33,17.4,18.67,18.8,0.0,0.0,1.0,1.2,16.0,16.57,16,0.5700000000000003",
  "Belgian_Grand_Prix": "PredictedPosition,Year,RoundNumber,Race,Driver,Team,QualiPosition,GridPosition,AvgFinishLast3,AvgFinishLast5,AvgGridLast3,AvgGridLast5,AvgPointsLast3,AvgPointsLast5,TargetFinish,PredictedFinish,Error\n1,2026,10,Belgian_Grand_Prix,RUS,Mercedes,3.0,3.0,1.67,4.2,2.0,2.6,20.33,12.2,22.0,5.34,16.66\n2,2026,10,Belgian_Grand_Prix,VER,Red Bull Racing,2.0,2.0,8.67,6.8,5.67,5.0,10.0,9.0,3.0,5.41,2.41\n3,2026,10,Belgian_Grand_Prix,LEC,Ferrari,4.0,4.0,8.0,7.2,4.67,5.2,9.67,8.2,2.0,5.47,3.4699999999999998\n4,2026,10,Belgian_Grand_Prix,PIA,McLaren,6.0,6.0,6.67,7.2,7.33,6.6,7.33,6.4,5.0,6.87,1.87\n5,2026,10,Belgian_Grand_Prix,HAM,Ferrari,5.0,5.0,3.0,2.6,2.67,3.2,16.67,17.2,4.0,7.52,3.5199999999999996\n6,2026,10,Belgian_Grand_Prix,ANT,Mercedes,1.0,1.0,11.33,7.2,2.67,2.2,5.0,13.0,1.0,7.63,6.63\n7,2026,10,Belgian_Grand_Prix,LIN,Racing Bulls,7.0,7.0,8.67,9.4,10.0,10.8,3.0,3.0,9.0,7.7,1.2999999999999998\n8,2026,10,Belgian_Grand_Prix,LAW,Racing Bulls,9.0,9.0,7.67,7.2,9.0,9.8,4.67,5.6,12.0,7.99,4.01\n9,2026,10,Belgian_Grand_Prix,BOR,Audi,8.0,8.0,10.0,10.8,11.67,12.8,1.33,0.8,8.0,9.01,1.0099999999999998\n10,2026,10,Belgian_Grand_Prix,GAS,Alpine,10.0,10.0,10.0,8.2,13.33,12.6,2.33,5.2,11.0,9.24,1.7599999999999998\n11,2026,10,Belgian_Grand_Prix,HUL,Audi,12.0,12.0,12.33,11.8,11.67,11.8,0.0,0.0,13.0,10.38,2.619999999999999\n12,2026,10,Belgian_Grand_Prix,NOR,McLaren,13.0,13.0,4.67,4.2,5.33,5.4,11.0,6.6,7.0,10.53,3.5299999999999994\n13,2026,10,Belgian_Grand_Prix,HAD,Red Bull Racing,21.0,21.0,5.67,5.2,6.33,6.2,8.67,9.6,6.0,11.09,5.09\n14,2026,10,Belgian_Grand_Prix,COL,Alpine,11.0,11.0,11.33,10.8,16.0,14.4,1.0,2.2,10.0,11.36,1.3599999999999994\n15,2026,10,Belgian_Grand_Prix,BEA,Haas F1 Team,15.0,15.0,14.33,12.8,13.67,15.2,0.0,0.2,14.0,11.87,2.130000000000001\n16,2026,10,Belgian_Grand_Prix,SAI,Williams,14.0,14.0,15.0,12.6,15.67,14.8,0.0,0.4,16.0,12.89,3.1099999999999994\n17,2026,10,Belgian_Grand_Prix,PER,Cadillac,19.0,19.0,14.33,15.2,19.33,19.2,0.0,0.0,21.0,14.72,6.279999999999999\n18,2026,10,Belgian_Grand_Prix,OCO,Haas F1 Team,17.0,17.0,14.0,13.0,16.33,16.6,0.0,0.4,17.0,14.81,2.1899999999999995\n19,2026,10,Belgian_Grand_Prix,STR,Aston Martin,20.0,20.0,17.0,17.0,21.67,21.8,0.0,0.0,20.0,14.82,5.18\n20,2026,10,Belgian_Grand_Prix,ALB,Williams,16.0,16.0,11.67,13.4,17.33,16.2,0.0,0.8,15.0,14.89,0.10999999999999943\n21,2026,10,Belgian_Grand_Prix,BOT,Cadillac,18.0,18.0,16.67,16.4,19.33,19.8,0.0,0.0,18.0,15.45,2.5500000000000007\n22,2026,10,Belgian_Grand_Prix,ALO,Aston Martin,22.0,22.0,15.33,15.8,21.33,20.8,0.0,0.2,19.0,15.86,3.1400000000000006",
  "British_Grand_Prix": "PredictedPosition,Year,RoundNumber,Race,Driver,Team,QualiPosition,GridPosition,AvgFinishLast3,AvgFinishLast5,AvgGridLast3,AvgGridLast5,AvgPointsLast3,AvgPointsLast5,TargetFinish,PredictedFinish,Error\n1,2026,9,British_Grand_Prix,ANT,Mercedes,1.0,1.0,6.67,4.4,2.67,2.2,13.33,18.0,16.0,2.72,13.28\n2,2026,9,British_Grand_Prix,RUS,Mercedes,4.0,4.0,5.0,4.6,2.67,2.8,14.33,11.0,2.0,3.53,1.5299999999999998\n3,2026,9,British_Grand_Prix,NOR,McLaren,6.0,6.0,4.0,4.4,6.0,5.0,7.0,7.8,4.0,4.12,0.1200000000000001\n4,2026,9,British_Grand_Prix,HAM,Ferrari,3.0,3.0,2.67,3.2,2.67,3.8,17.67,15.8,3.0,4.25,1.25\n5,2026,9,British_Grand_Prix,VER,Red Bull Racing,7.0,7.0,3.0,4.4,4.0,4.0,10.0,11.0,20.0,4.37,15.629999999999999\n6,2026,9,British_Grand_Prix,HAD,Red Bull Racing,5.0,5.0,5.33,6.6,6.33,9.6,9.33,7.6,5.0,4.55,0.4500000000000002\n7,2026,9,British_Grand_Prix,LEC,Ferrari,2.0,2.0,9.0,7.6,5.33,5.4,1.33,4.0,1.0,5.16,4.16\n8,2026,9,British_Grand_Prix,PIA,McLaren,8.0,8.0,4.67,5.6,7.0,6.4,10.67,9.4,11.0,6.14,4.86\n9,2026,9,British_Grand_Prix,LAW,Racing Bulls,10.0,10.0,7.67,7.8,9.0,10.0,4.67,4.0,6.0,8.91,2.91\n10,2026,9,British_Grand_Prix,LIN,Racing Bulls,9.0,9.0,8.67,10.8,12.0,12.2,3.0,1.8,7.0,8.92,1.92\n11,2026,9,British_Grand_Prix,SAI,Williams,15.0,15.0,12.33,12.2,15.0,14.6,0.0,0.8,12.0,10.53,1.4700000000000006\n12,2026,9,British_Grand_Prix,BOR,Audi,11.0,11.0,11.0,11.6,13.33,14.8,0.0,0.0,8.0,11.04,3.039999999999999\n13,2026,9,British_Grand_Prix,GAS,Alpine,12.0,12.0,7.67,7.6,11.33,11.4,7.0,5.0,10.0,11.11,1.1099999999999994\n14,2026,9,British_Grand_Prix,HUL,Audi,13.0,13.0,12.33,11.8,12.0,11.4,0.0,0.0,22.0,11.22,10.78\n15,2026,9,British_Grand_Prix,BEA,Haas F1 Team,14.0,14.0,13.67,11.4,15.67,15.0,0.0,0.2,13.0,11.57,1.4299999999999997\n16,2026,9,British_Grand_Prix,ALB,Williams,16.0,16.0,11.67,13.4,15.67,16.0,1.33,1.0,21.0,13.5,7.5\n17,2026,9,British_Grand_Prix,COL,Alpine,19.0,19.0,13.0,10.4,14.33,12.2,0.33,3.0,9.0,14.17,5.17\n18,2026,9,British_Grand_Prix,PER,Cadillac,20.0,20.0,15.0,15.4,18.67,19.2,0.0,0.0,15.0,14.51,0.4900000000000002\n19,2026,9,British_Grand_Prix,STR,Aston Martin,21.0,21.0,16.0,16.0,21.67,21.0,0.0,0.0,19.0,14.75,4.25\n20,2026,9,British_Grand_Prix,OCO,Haas F1 Team,17.0,17.0,12.67,13.0,16.33,16.0,0.67,0.4,14.0,14.79,0.7899999999999991\n21,2026,9,British_Grand_Prix,BOT,Cadillac,18.0,18.0,17.67,16.5,20.0,20.0,0.0,0.0,17.0,15.04,1.9600000000000009\n22,2026,9,British_Grand_Prix,ALO,Aston Martin,22.0,22.0,14.33,15.25,21.33,20.0,0.33,0.2,18.0,15.75,2.25",
  "Dutch_Grand_Prix": "PredictedPosition,Year,RoundNumber,Race,Driver,Team,QualiPosition,GridPosition,AvgFinishLast3,AvgFinishLast5,AvgGridLast3,AvgGridLast5,AvgPointsLast3,AvgPointsLast5,TargetFinish,PredictedFinish,RaceStatus,Error\n1,2026,12,Dutch_Grand_Prix,NOR,McLaren,1.0,1.0,4.0,4.4,6.67,6.0,14.33,12.8,1.0,2.17,1,1.17\n2,2026,12,Dutch_Grand_Prix,RUS,Mercedes,2.0,2.0,3.33,4.8,4.33,3.0,8.0,13.4,3.0,2.76,3,0.2400000000000002\n3,2026,12,Dutch_Grand_Prix,ANT,Mercedes,3.0,3.0,6.33,7.6,3.0,3.2,13.33,11.0,2.0,3.51,2,1.5099999999999998\n4,2026,12,Dutch_Grand_Prix,HAM,Ferrari,5.0,5.0,4.0,3.6,4.33,3.6,12.33,14.4,4.0,3.93,4,0.06999999999999984\n5,2026,12,Dutch_Grand_Prix,PIA,McLaren,4.0,4.0,6.67,6.0,5.67,6.2,3.33,6.4,6.0,4.19,6,1.8099999999999996\n6,2026,12,Dutch_Grand_Prix,LEC,Ferrari,6.0,6.0,2.33,6.0,2.67,4.0,18.33,11.8,5.0,6.57,5,1.5700000000000003\n7,2026,12,Dutch_Grand_Prix,LAW,Red Bull Racing,8.0,8.0,8.67,8.6,10.0,9.4,4.0,3.6,7.0,7.81,7,0.8099999999999996\n8,2026,12,Dutch_Grand_Prix,LIN,Racing Bulls,10.0,10.0,8.67,9.0,8.33,9.2,3.0,2.4,12.0,8.92,12,3.08\n9,2026,12,Dutch_Grand_Prix,BOR,Audi,9.0,9.0,9.0,9.8,11.0,11.4,2.67,1.6,13.0,9.06,13,3.9399999999999995\n10,2026,12,Dutch_Grand_Prix,VER,Red Bull Racing,7.0,7.0,8.33,6.2,4.33,4.6,11.0,12.6,,9.12,R,\n11,2026,12,Dutch_Grand_Prix,TSU,Racing Bulls,12.0,12.0,12.0,12.8,15.0,14.4,0.33,0.2,11.0,10.6,11,0.40000000000000036\n12,2026,12,Dutch_Grand_Prix,GAS,Alpine,11.0,11.0,11.0,10.6,12.33,12.4,0.33,1.4,10.0,10.72,10,0.7200000000000006\n13,2026,12,Dutch_Grand_Prix,HUL,Audi,13.0,13.0,11.33,11.8,11.33,11.4,0.67,0.4,8.0,12.03,8,4.029999999999999\n14,2026,12,Dutch_Grand_Prix,COL,Alpine,14.0,14.0,11.33,11.8,14.33,14.4,1.0,0.8,14.0,12.22,14,1.7799999999999994\n15,2026,12,Dutch_Grand_Prix,STR,Aston Martin,19.0,19.0,15.67,16.0,20.67,21.0,0.0,0.0,,14.72,R,\n16,2026,12,Dutch_Grand_Prix,ALB,Williams,16.0,16.0,16.33,13.4,16.67,17.2,0.0,0.0,17.0,14.78,17,2.2200000000000006\n17,2026,12,Dutch_Grand_Prix,OCO,Haas F1 Team,15.0,15.0,15.33,15.0,16.0,16.0,0.0,0.0,,15.12,R,\n18,2026,12,Dutch_Grand_Prix,SAI,Williams,17.0,17.0,17.0,15.8,17.0,16.8,0.0,0.0,16.0,15.37,16,0.6300000000000008\n19,2026,12,Dutch_Grand_Prix,PER,Cadillac,22.0,22.0,14.33,15.2,20.0,19.6,0.0,0.0,15.0,15.49,15,0.4900000000000002\n20,2026,12,Dutch_Grand_Prix,BOT,Cadillac,21.0,21.0,16.67,17.4,18.67,19.2,0.0,0.0,,15.68,R,\n21,2026,12,Dutch_Grand_Prix,ALO,Aston Martin,18.0,18.0,17.0,15.8,19.67,20.4,0.0,0.0,9.0,15.78,9,6.779999999999999\n22,2026,12,Dutch_Grand_Prix,BEA,Haas F1 Team,20.0,20.0,15.0,15.2,14.67,14.4,0.0,0.0,,16.87,R,",
  "Hungarian_Grand_Prix": "PredictedPosition,Year,RoundNumber,Race,Driver,Team,QualiPosition,GridPosition,AvgFinishLast3,AvgFinishLast5,AvgGridLast3,AvgGridLast5,AvgPointsLast3,AvgPointsLast5,TargetFinish,PredictedFinish,RaceStatus,Error\n1,2026,11,Hungarian_Grand_Prix,LEC,Ferrari,2.0,2.0,3.67,6.0,2.67,4.4,15.67,9.4,4.0,1.69,4,2.31\n2,2026,11,Hungarian_Grand_Prix,VER,Red Bull Racing,4.0,4.0,8.33,6.4,4.67,4.2,11.0,9.0,2.0,3.02,2,1.02\n3,2026,11,Hungarian_Grand_Prix,NOR,McLaren,1.0,1.0,6.0,4.6,8.33,7.4,8.0,7.8,1.0,3.13,1,2.13\n4,2026,11,Hungarian_Grand_Prix,PIA,McLaren,3.0,3.0,6.67,6.0,7.0,7.0,7.33,8.4,,3.31,R,\n5,2026,11,Hungarian_Grand_Prix,HAM,Ferrari,5.0,5.0,4.0,3.0,3.67,3.2,12.33,16.0,5.0,4.18,5,0.8200000000000003\n6,2026,11,Hungarian_Grand_Prix,HAD,Red Bull Racing,8.0,8.0,5.67,5.4,11.33,9.0,8.67,9.2,6.0,7.26,6,1.2599999999999998\n7,2026,11,Hungarian_Grand_Prix,LIN,Racing Bulls,9.0,9.0,8.67,8.4,8.67,10.4,3.0,3.4,10.0,8.15,10,1.8499999999999996\n8,2026,11,Hungarian_Grand_Prix,RUS,Mercedes,6.0,6.0,1.67,4.2,2.67,3.0,14.33,12.2,7.0,8.9,7,1.9000000000000004\n9,2026,11,Hungarian_Grand_Prix,HUL,Audi,10.0,10.0,12.67,12.2,12.67,12.0,0.0,0.0,9.0,8.98,9,0.019999999999999574\n10,2026,11,Hungarian_Grand_Prix,ANT,Mercedes,7.0,7.0,6.33,7.2,2.0,2.0,13.33,13.0,3.0,9.7,3,6.699999999999999\n11,2026,11,Hungarian_Grand_Prix,BOR,Audi,14.0,14.0,9.0,9.8,10.33,11.8,2.67,1.6,11.0,9.81,11,1.1899999999999995\n12,2026,11,Hungarian_Grand_Prix,LAW,Racing Bulls,11.0,11.0,9.0,8.2,9.33,9.2,3.33,4.4,8.0,9.86,8,1.8599999999999994\n13,2026,11,Hungarian_Grand_Prix,GAS,Alpine,12.0,12.0,11.33,8.8,12.0,11.8,0.33,4.4,12.0,10.05,12,1.9499999999999993\n14,2026,11,Hungarian_Grand_Prix,COL,Alpine,13.0,13.0,11.33,11.6,15.33,14.6,1.0,0.8,15.0,12.2,15,2.8000000000000007\n15,2026,11,Hungarian_Grand_Prix,BEA,Haas F1 Team,17.0,17.0,13.33,13.4,13.33,14.8,0.0,0.0,19.0,13.06,19,5.9399999999999995\n16,2026,11,Hungarian_Grand_Prix,OCO,Haas F1 Team,15.0,15.0,15.33,13.6,16.0,16.4,0.0,0.4,16.0,14.4,16,1.5999999999999996\n17,2026,11,Hungarian_Grand_Prix,ALO,Aston Martin,16.0,16.0,18.33,16.0,21.33,21.4,0.0,0.2,14.0,14.85,14,0.8499999999999996\n18,2026,11,Hungarian_Grand_Prix,SAI,Williams,18.0,18.0,15.0,14.0,16.67,15.6,0.0,0.0,18.0,15.35,18,2.6500000000000004\n19,2026,11,Hungarian_Grand_Prix,PER,Cadillac,22.0,22.0,14.33,15.2,19.0,18.8,0.0,0.0,,15.4,R,\n20,2026,11,Hungarian_Grand_Prix,STR,Aston Martin,20.0,20.0,17.0,17.0,21.33,21.4,0.0,0.0,13.0,15.81,13,2.8100000000000005\n21,2026,11,Hungarian_Grand_Prix,ALB,Williams,19.0,19.0,13.33,14.0,16.33,15.6,0.0,0.8,17.0,17.13,17,0.129999999999999\n22,2026,11,Hungarian_Grand_Prix,BOT,Cadillac,21.0,21.0,16.67,17.4,18.33,19.0,0.0,0.0,,17.7,R,",
  "Italian_Grand_Prix": "PredictedPosition,Year,RoundNumber,Race,Driver,Team,QualiPosition,GridPosition,AvgFinishLast3,AvgFinishLast5,AvgGridLast3,AvgGridLast5,AvgPointsLast3,AvgPointsLast5,PositionsGainedLastRace,FinishStdLast5,TargetFinish,PredictedFinish,RaceStatus,Error\n1,2026,13,Italian_Grand_Prix,RUS,Mercedes,2.0,2.0,4.0,3.0,3.67,3.2,7.0,12.8,-1.0,2.1,2.0,2.85,2,0.8500000000000001\n2,2026,13,Italian_Grand_Prix,VER,Red Bull Racing,5.0,5.0,8.33,6.2,4.33,5.0,11.0,10.2,2.0,6.94,3.0,3.74,3,0.7400000000000002\n3,2026,13,Italian_Grand_Prix,LEC,Ferrari,3.0,3.0,3.67,4.0,4.0,3.2,13.33,13.8,1.0,2.45,,4.13,R,\n4,2026,13,Italian_Grand_Prix,HAM,Ferrari,4.0,4.0,4.33,4.2,5.0,4.2,11.33,11.8,1.0,0.75,6.0,4.51,6,1.4900000000000002\n5,2026,13,Italian_Grand_Prix,PIA,McLaren,6.0,6.0,7.33,6.2,4.33,5.6,6.0,6.0,-2.0,2.48,5.0,4.54,5,0.45999999999999996\n6,2026,13,Italian_Grand_Prix,GAS,Alpine,1.0,1.0,11.0,11.2,11.0,11.8,0.33,0.4,1.0,1.17,7.0,5.99,7,1.0099999999999998\n7,2026,13,Italian_Grand_Prix,NOR,McLaren,8.0,8.0,3.0,4.0,5.0,5.4,18.67,14.8,0.0,2.68,4.0,6.68,4,2.6799999999999997\n8,2026,13,Italian_Grand_Prix,COL,Alpine,7.0,7.0,13.0,12.6,12.67,14.6,0.33,0.6,0.0,2.58,9.0,6.84,9,2.16\n9,2026,13,Italian_Grand_Prix,LIN,Racing Bulls,9.0,9.0,10.33,9.6,8.67,9.0,1.0,2.0,-2.0,1.62,8.0,10.67,8,2.67\n10,2026,13,Italian_Grand_Prix,BEA,Haas F1 Team,11.0,11.0,15.0,15.2,17.0,15.4,0.0,0.0,-2.0,2.48,15.0,11.09,15,3.91\n11,2026,13,Italian_Grand_Prix,BOR,Audi,10.0,10.0,10.67,10.2,10.33,10.8,1.33,1.6,-4.0,1.94,11.0,11.19,11,0.1899999999999995\n12,2026,13,Italian_Grand_Prix,HUL,Audi,12.0,12.0,10.0,11.0,11.67,12.2,2.0,1.2,5.0,2.1,12.0,11.22,12,0.7799999999999994\n13,2026,13,Italian_Grand_Prix,LAW,Red Bull Racing,22.0,22.0,9.0,8.4,9.33,9.4,3.33,4.0,1.0,2.06,14.0,12.25,14,1.75\n14,2026,13,Italian_Grand_Prix,ANT,Mercedes,19.0,19.0,2.0,4.8,3.67,3.2,19.33,14.6,1.0,5.15,1.0,12.43,1,11.43\n15,2026,13,Italian_Grand_Prix,TSU,Racing Bulls,15.0,15.0,11.0,11.0,12.0,12.0,0.0,0.0,1.0,0.0,10.0,12.79,10,2.789999999999999\n16,2026,13,Italian_Grand_Prix,OCO,Haas F1 Team,14.0,14.0,15.33,15.0,15.33,15.6,0.0,0.0,-1.0,1.67,16.0,12.89,16,3.1099999999999994\n17,2026,13,Italian_Grand_Prix,SAI,Williams,13.0,13.0,16.67,15.8,18.0,17.0,0.0,0.0,1.0,2.04,13.0,13.03,13,0.02999999999999936\n18,2026,13,Italian_Grand_Prix,STR,Aston Martin,18.0,18.0,15.67,16.0,19.67,20.6,0.0,0.0,7.0,2.24,,14.7,R,\n19,2026,13,Italian_Grand_Prix,BOT,Cadillac,16.0,16.0,16.67,17.4,19.67,19.4,0.0,0.0,-1.0,1.2,19.0,14.81,19,4.1899999999999995\n20,2026,13,Italian_Grand_Prix,ALB,Williams,20.0,20.0,16.33,14.8,16.67,16.8,0.0,0.0,-1.0,3.49,17.0,15.58,17,1.42\n21,2026,13,Italian_Grand_Prix,PER,Cadillac,17.0,17.0,14.33,14.8,20.67,20.2,0.0,0.0,7.0,0.75,18.0,15.65,18,2.3499999999999996\n22,2026,13,Italian_Grand_Prix,ALO,Aston Martin,21.0,21.0,14.0,15.6,18.67,19.6,0.67,0.4,9.0,3.72,,15.74,R,",
  "Spanish_Grand_Prix": "PredictedPosition,Year,RoundNumber,Race,Driver,Team,QualiPosition,GridPosition,AvgFinishLast3,AvgFinishLast5,AvgGridLast3,AvgGridLast5,AvgPointsLast3,AvgPointsLast5,PositionsGainedLastRace,FinishStdLast5,TargetFinish,PredictedFinish,RaceStatus,Error\n1,2026,14,Spanish_Grand_Prix,NOR,McLaren,1.0,1.0,2.0,3.4,3.33,5.8,20.67,16.0,4.0,2.24,3.0,2.08,3,0.9199999999999999\n2,2026,14,Spanish_Grand_Prix,ANT,Mercedes,2.0,2.0,2.0,4.4,9.67,6.2,19.33,16.6,18.0,5.35,1.0,2.94,1,1.94\n3,2026,14,Spanish_Grand_Prix,VER,Red Bull Racing,3.0,3.0,2.67,6.0,5.33,5.0,11.0,9.6,2.0,7.01,2.0,3.75,2,1.75\n4,2026,14,Spanish_Grand_Prix,HAM,Ferrari,4.0,4.0,5.0,4.4,4.67,4.4,10.0,11.4,-2.0,1.02,,3.99,R,\n5,2026,14,Spanish_Grand_Prix,LEC,Ferrari,5.0,5.0,3.67,4.0,3.67,3.4,7.33,13.0,1.0,2.45,4.0,4.29,4,0.29000000000000004\n6,2026,14,Spanish_Grand_Prix,RUS,Mercedes,6.0,6.0,4.0,3.0,3.33,3.4,13.0,11.4,0.0,2.1,5.0,4.93,5,0.07000000000000028\n7,2026,14,Spanish_Grand_Prix,PIA,McLaren,7.0,7.0,5.33,6.2,4.33,5.4,6.0,5.6,1.0,2.48,8.0,7.23,8,0.7699999999999996\n8,2026,14,Spanish_Grand_Prix,LAW,Red Bull Racing,8.0,8.0,9.67,9.4,13.67,12.0,3.33,3.6,8.0,3.07,6.0,8.82,6,2.8200000000000003\n9,2026,14,Spanish_Grand_Prix,COL,Alpine,9.0,9.0,12.67,11.4,11.33,12.8,0.67,1.0,-2.0,2.58,7.0,10.16,7,3.16\n10,2026,14,Spanish_Grand_Prix,LIN,Racing Bulls,10.0,10.0,10.0,9.2,9.33,8.8,1.67,2.6,1.0,1.72,9.0,10.65,9,1.6500000000000004\n11,2026,14,Spanish_Grand_Prix,HUL,Audi,11.0,11.0,9.67,10.8,11.67,11.8,2.0,1.2,0.0,1.94,10.0,11.08,10,1.08\n12,2026,14,Spanish_Grand_Prix,BOR,Audi,12.0,12.0,11.67,10.2,11.0,10.4,0.0,1.6,-1.0,1.94,13.0,11.51,13,1.4900000000000002\n13,2026,14,Spanish_Grand_Prix,GAS,Alpine,14.0,14.0,9.67,10.0,8.0,9.8,2.33,1.6,-6.0,1.67,12.0,12.19,12,0.1899999999999995\n14,2026,14,Spanish_Grand_Prix,TSU,Racing Bulls,15.0,15.0,10.5,10.5,13.5,13.5,0.5,0.5,5.0,0.5,14.0,12.28,14,1.7200000000000006\n15,2026,14,Spanish_Grand_Prix,OCO,Haas F1 Team,13.0,13.0,16.33,15.6,14.67,15.4,0.0,0.0,-2.0,1.36,11.0,12.83,11,1.83\n16,2026,14,Spanish_Grand_Prix,ALB,Williams,16.0,16.0,17.0,16.6,18.33,17.2,0.0,0.0,3.0,0.8,15.0,15.48,15,0.4800000000000004\n17,2026,14,Spanish_Grand_Prix,PER,Cadillac,19.0,19.0,15.67,15.2,20.33,19.8,0.0,0.0,-1.0,1.47,,15.78,R,\n18,2026,14,Spanish_Grand_Prix,ALO,Aston Martin,18.0,18.0,14.0,15.6,18.33,19.6,0.67,0.4,9.0,3.72,17.0,16.0,17,1.0\n19,2026,14,Spanish_Grand_Prix,STR,Aston Martin,21.0,21.0,15.67,16.0,19.0,19.8,0.0,0.0,7.0,2.24,,16.14,R,\n20,2026,14,Spanish_Grand_Prix,SAI,Williams,17.0,20.0,15.67,16.0,16.0,16.2,0.0,0.0,0.0,1.67,,16.21,R,\n21,2026,14,Spanish_Grand_Prix,BOT,Cadillac,20.0,20.0,17.67,17.4,19.33,18.6,0.0,0.0,-3.0,1.2,18.0,16.36,18,1.6400000000000006\n22,2026,14,Spanish_Grand_Prix,BEA,Haas F1 Team,,,16.0,14.8,16.0,15.0,0.0,0.0,-4.0,2.32,16.0,,16,"
};

/* ==========================================================================
   DATAHUB INITIALIZATION
   ========================================================================== */

/**
 * Initializes DataHub Tab.
 * Discovers Grand Prix from manifest.json, lists GP tabs, and renders the active GP.
 */
async function initDataHubTab() {
  const dataHubContainer = 
    document.getElementById('datahub-content-container') ||
    document.getElementById('tab-datahub') ||
    document.querySelector('.datahub-section');

  if (!dataHubContainer) {
    console.warn('[Slipstream Oracle] DataHub container not found in DOM.');
    return;
  }

  // Setup view mode buttons and clipboard copy handlers once
  if (!isDataHubInitialized) {
    initDataHubViewControls();
    isDataHubInitialized = true;
  }

  // Load Grand Prix races from manifest.json
  const races = await getAvailableGrandPrix();

  if (!races || races.length === 0) {
    console.error('[Slipstream Oracle] No Grand Prix datasets found in manifest.');
    showPredictionLoadError(null, new Error('No Grand Prix datasets registered in manifest.json.'));
    return;
  }

  // Render GP tabs neatly in DataHub tab
  renderGrandPrixTabs(races);

  // If no GP is currently selected, pick default: prefer Azerbaijan or first GP
  if (!activeGrandPrix) {
    activeGrandPrix = races.find(r => r.slug === 'Azerbaijan_Grand_Prix') || races[0];
  }

  // Select and load the active Grand Prix
  await selectGrandPrix(activeGrandPrix);
}

/**
 * Sets up View Mode switcher (Leaderboard vs All CSV Columns vs Raw CSV)
 */
function initDataHubViewControls() {
  document.querySelectorAll('.datahub-view-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const mode = btn.getAttribute('data-view-mode');
      if (mode) switchDataHubView(mode);
    });
  });

  const copyBtn = document.getElementById('copy-raw-csv-btn');
  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      if (activeRawCsvText) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(activeRawCsvText).then(() => {
            const original = copyBtn.textContent;
            copyBtn.textContent = 'Copied!';
            setTimeout(() => { copyBtn.textContent = original; }, 2000);
          }).catch(() => fallbackCopy(activeRawCsvText, copyBtn));
        } else {
          fallbackCopy(activeRawCsvText, copyBtn);
        }
      }
    });
  }
}

function fallbackCopy(text, btn) {
  try {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = 'Copy CSV'; }, 2000);
  } catch (e) {
    console.warn('Copy failed:', e);
  }
}

/**
 * Switches the subview display within DataHub
 */
function switchDataHubView(mode) {
  currentViewMode = mode;
  document.querySelectorAll('.datahub-view-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-view-mode') === mode);
  });

  const views = {
    leaderboard: document.getElementById('subview-leaderboard'),
    fullcsv: document.getElementById('subview-fullcsv'),
    raw: document.getElementById('subview-raw')
  };

  Object.entries(views).forEach(([key, el]) => {
    if (el) {
      el.style.display = key === mode ? 'block' : 'none';
      if (key === mode) {
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    }
  });
}

/* ==========================================================================
   MANIFEST DETECTION & LOADING
   ========================================================================== */

/**
 * Loads prediction manifest.json by checking candidate paths starting with
 * ../../predictions/2026/manifest.json.
 */
async function loadPredictionManifest() {
  if (predictionManifest) {
    return predictionManifest;
  }

  console.log('[Slipstream Oracle] Detecting manifest.json across candidate paths...');

  for (const candidatePath of MANIFEST_CANDIDATE_PATHS) {
    try {
      console.log(`[Slipstream Oracle] Checking manifest candidate: ${candidatePath}`);
      const response = await fetch(candidatePath, { cache: 'no-cache' });
      if (response.ok) {
        const json = await response.json();
        if (json && Array.isArray(json.races) && json.races.length > 0) {
          predictionManifest = json;
          // Extract base directory
          detectedPredictionsBase = candidatePath.substring(0, candidatePath.lastIndexOf('/'));
          console.log(`[Slipstream Oracle] Manifest detected at ${candidatePath}. Base: ${detectedPredictionsBase}`);
          return predictionManifest;
        }
      }
    } catch (err) {
      // Continue checking next candidate path
    }
  }

  console.warn('[Slipstream Oracle] External fetch failed or restricted. Utilizing embedded 2026 manifest.');
  predictionManifest = EMBEDDED_MANIFEST;
  detectedPredictionsBase = '../predictions/2026';
  return predictionManifest;
}

/**
 * Returns available Grand Prix list from manifest
 */
async function getAvailableGrandPrix() {
  const manifest = await loadPredictionManifest();
  return manifest ? manifest.races || [] : [];
}

/* ==========================================================================
   GRAND PRIX TABS RENDERING
   ========================================================================== */

/**
 * Helper to determine round code (e.g. R08, R15)
 */
function getRoundCode(race, index) {
  if (CIRCUIT_INFO[race.slug] && CIRCUIT_INFO[race.slug].roundDefault) {
    const match = CIRCUIT_INFO[race.slug].roundDefault.match(/\d+/);
    if (match) return `R${match[0].padStart(2, '0')}`;
  }
  return `R${String(index + 1).padStart(2, '0')}`;
}

/**
 * Renders the Grand Prix selection tabs neatly in the DataHub tab.
 */
function renderGrandPrixTabs(races) {
  const container = document.getElementById('gp-tabs-container');
  const countBadge = document.getElementById('gp-count-badge');
  if (!container) return;

  if (countBadge) {
    countBadge.textContent = `${races.length} RACES DETECTED`;
  }

  container.innerHTML = races.map((race, index) => {
    const isActive = activeGrandPrix && activeGrandPrix.slug === race.slug;
    const cleanName = race.name || race.slug.replace(/_/g, ' ');
    const roundCode = getRoundCode(race, index);

    return `
      <button 
        type="button" 
        class="gp-tab-btn ${isActive ? 'active' : ''}" 
        data-gp-slug="${race.slug}"
        role="tab"
        aria-selected="${isActive ? 'true' : 'false'}"
        title="View telemetry for ${cleanName}"
      >
        <span class="gp-tab-round-badge">${roundCode}</span>
        <span class="gp-tab-name">${cleanName}</span>
        ${isActive ? '<span class="gp-tab-status-led"></span>' : ''}
      </button>
    `;
  }).join('');

  // Attach event handlers
  container.querySelectorAll('.gp-tab-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const slug = btn.getAttribute('data-gp-slug');
      const selected = races.find(r => r.slug === slug);
      if (selected) {
        await selectGrandPrix(selected);
      }
    });
  });
}

/**
 * Selects a Grand Prix tab and loads its Final_Data.csv
 */
async function selectGrandPrix(race) {
  if (!race) return;
  activeGrandPrix = race;

  // Immediately update tab active classes
  const container = document.getElementById('gp-tabs-container');
  if (container) {
    container.querySelectorAll('.gp-tab-btn').forEach(btn => {
      const isCurrent = btn.getAttribute('data-gp-slug') === race.slug;
      btn.classList.toggle('active', isCurrent);
      btn.setAttribute('aria-selected', isCurrent ? 'true' : 'false');
      const led = btn.querySelector('.gp-tab-status-led');
      if (isCurrent && !led) {
        btn.insertAdjacentHTML('beforeend', '<span class="gp-tab-status-led"></span>');
      } else if (!isCurrent && led) {
        led.remove();
      }
    });
  }

  // Load and render race predictions
  await loadGrandPrixPredictions(race);
}

/* ==========================================================================
   GRAND PRIX DATA LOADING (Final_Data.csv)
   ========================================================================== */

/**
 * Loads and parses Final_Data.csv for the given Grand Prix.
 */
async function loadGrandPrixPredictions(race) {
  const relativeDataPath = race.data || `${race.slug}/Final_Data.csv`;

  // Candidate URLs to fetch Final_Data.csv
  const candidateCsvPaths = [
    `${detectedPredictionsBase}/${relativeDataPath}`,
    `../../predictions/2026/${relativeDataPath}`,
    `../predictions/2026/${relativeDataPath}`,
    `predictions/2026/${relativeDataPath}`,
    `/predictions/2026/${relativeDataPath}`
  ];

  let csvContent = null;
  let loadedUrl = '';

  for (const path of candidateCsvPaths) {
    try {
      const response = await fetch(path, { cache: 'no-cache' });
      if (response.ok) {
        const text = await response.text();
        if (text && text.trim().length > 0) {
          csvContent = text;
          loadedUrl = path;
          console.log(`[Slipstream Oracle] Loaded Final_Data.csv from ${path}`);
          break;
        }
      }
    } catch (err) {
      // Continue to next candidate
    }
  }

  // Fallback to embedded raw CSV text
  if (!csvContent && FALLBACK_PREDICTION_CSVS[race.slug]) {
    csvContent = FALLBACK_PREDICTION_CSVS[race.slug];
    loadedUrl = `embedded:${race.slug}/Final_Data.csv`;
    console.log(`[Slipstream Oracle] Using embedded Final_Data.csv for ${race.slug}`);
  }

  if (!csvContent) {
    console.error(`[Slipstream Oracle] Failed to load Final_Data.csv for ${race.name}`);
    activePredictionsData = [];
    activeRawCsvText = '';
    showPredictionLoadError(race, new Error(`Could not load Final_Data.csv for ${race.name}`));
    renderDataHubView();
    return;
  }

  activeRawCsvText = csvContent;
  activePredictionsData = parseCSV(csvContent);

  // Extract all column headers from raw CSV
  const firstLine = csvContent.trim().split(/\r?\n/)[0];
  if (firstLine) {
    fullCsvHeaders = firstLine.split(',').map(h => h.trim().replace(/^"|"$/g, ''));
  }

  // Ensure drivers metadata is loaded
  if (typeof allDriversData === 'undefined' || !allDriversData || Object.keys(allDriversData).length === 0) {
    if (typeof loadDriversMetadata === 'function') {
      allDriversData = await loadDriversMetadata();
    }
  }

  // Render all views with newly loaded Final_Data.csv
  renderGrandPrixCard(race, activePredictionsData);
  renderDataHubView();
  renderFullCsvTable(activePredictionsData);
  renderRawCsvView(activeRawCsvText, race);
  updateBadges(race, activePredictionsData);
}

/**
 * Updates status badges in telemetry table header
 */
function updateBadges(race, data) {
  const statusBadge = document.getElementById('dataset-status-badge');
  const classifiedBadge = document.getElementById('grid-classified-badge');

  if (statusBadge) {
    statusBadge.textContent = 'FINAL_DATA.CSV PARSED';
    statusBadge.className = 'tech-badge green';
  }
  if (classifiedBadge) {
    classifiedBadge.textContent = `${data.length || 22} CARS CLASSIFIED`;
  }
}

/* ==========================================================================
   GRAND PRIX CARD BANNER
   ========================================================================== */

/**
 * Renders the primary Grand Prix selection card banner.
 */
function renderGrandPrixCard(race = null, data = []) {
  const container = document.getElementById('gp-banner-container');
  if (!container) return;

  const currentRace = race || activeGrandPrix;
  const rawGpName = currentRace?.slug || 'Azerbaijan_Grand_Prix';
  const cleanGpName = currentRace?.name || rawGpName.replace(/_/g, ' ');

  // Look up circuit metadata
  const circuitMeta = CIRCUIT_INFO[rawGpName] || {
    circuit: "Formula 1 Grand Prix Circuit",
    location: "Championship Round",
    type: "Championship Grand Prix",
    roundDefault: data[0]?.RoundNumber ? `Round ${data[0].RoundNumber}` : "2026 Championship"
  };

  // Determine round number from data if available
  const roundNum = data[0]?.RoundNumber ? `Round ${String(data[0].RoundNumber).padStart(2, '0')}` : circuitMeta.roundDefault;

  // Determine predicted winner
  const winner = data.find(d => Number(d.PredictedPosition) === 1);
  const winnerText = winner ? `${winner.Driver} (${winner.Team})` : '--';

  container.innerHTML = `
    <div class="gp-selection-card">
      <div class="gp-meta-details">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.35rem;">
          <span class="tech-badge red">${roundNum} // 2026</span>
          <span class="tech-badge" style="font-family: var(--font-mono);">${circuitMeta.location}</span>
        </div>
        <h3>${cleanGpName}</h3>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.25rem;">
          ${circuitMeta.circuit} &bull; ${circuitMeta.length || 'FIA Grade 1'} &bull; ${circuitMeta.type}
        </p>
      </div>

      <div class="gp-stats-row">
        <div class="gp-stat-item">
          <span class="gp-stat-title">Dataset Status</span>
          <span class="gp-stat-val" style="color: var(--telemetry-green); font-size: 0.95rem;">
            <span class="beacon-led" style="display:inline-block; margin-right:4px;"></span>
            Final_Data.csv Verified
          </span>
        </div>

        <div class="gp-stat-item">
          <span class="gp-stat-title">Grid Size</span>
          <span class="gp-stat-val">
            ${data.length || 22} Drivers
          </span>
        </div>

        <div class="gp-stat-item">
          <span class="gp-stat-title">P1 Forecast</span>
          <span class="gp-stat-val" style="color: var(--telemetry-gold); font-size: 0.95rem;">
            ${winnerText}
          </span>
        </div>

        <div class="gp-stat-item">
          <span class="gp-stat-title">Inference Engine</span>
          <span class="gp-stat-val" style="color: var(--telemetry-cyan); font-size: 0.95rem;">
            Random Forest (RF-REG-26)
          </span>
        </div>
      </div>
    </div>
  `;
}

/* ==========================================================================
   PODIUM & TELEMETRY RENDERING
   ========================================================================== */

/**
 * Renders both the Predicted Podium, Actual Race Podium, and Full Telemetry Table.
 */
function renderDataHubView() {
  renderPodiumStage();
  renderActualPodiumStage();
  renderTelemetryTable();
}

/**
 * Renders top 3 predicted finishers from active Final_Data.csv
 */
function renderPodiumStage() {
  const container = document.getElementById('podium-stage-container');
  if (!container) return;

  if (!activePredictionsData || activePredictionsData.length < 3) {
    container.innerHTML = '';
    return;
  }

  const sorted = [...activePredictionsData].sort(
    (a, b) => Number(a.PredictedPosition) - Number(b.PredictedPosition)
  );

  const p1 = sorted[0];
  const p2 = sorted[1];
  const p3 = sorted[2];

  const p1Driver = resolveDriver(p1.Driver, allDriversData);
  const p2Driver = resolveDriver(p2.Driver, allDriversData);
  const p3Driver = resolveDriver(p3.Driver, allDriversData);

  container.innerHTML = `
    <div class="podium-header-bar">
      <h3 class="podium-stage-title predicted-stage-title">
        Predicted Podium Telemetry // ${activeGrandPrix?.name || 'Grand Prix'}
      </h3>
      <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
        <span class="tech-badge cyan">ML ENSEMBLE FORECAST</span>
        <span class="tech-badge" style="font-family: var(--font-mono);">PREDICTEDFINISH SCORE</span>
      </div>
    </div>

    <div class="podium-grid">
      <!-- P2 Runner-Up -->
      <div class="podium-card p2">
        <div class="podium-badge">P2 PREDICTED</div>
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
        <div class="podium-score-pill">
          Model Score: ${Number(p2.PredictedFinish).toFixed(2)}
        </div>
        <div style="margin-top: 0.6rem;">
          ${renderDeltaBadge(p2.GridPosition, p2.PredictedPosition)}
        </div>
      </div>

      <!-- P1 Winner -->
      <div class="podium-card p1">
        <div class="podium-badge">P1 WINNER // PREDICTED</div>
        <div class="podium-headshot-wrap" style="height: 220px;">
          <img
            src="${normalizeHeadshotUrl(p1Driver.headshot)}"
            alt="${p1Driver.name}"
            class="podium-headshot"
            onerror="handleImageFallback(this, '${p1Driver.headshot}')"
          />
        </div>
        <h4 class="podium-driver-name" style="font-size: 1.55rem;">${p1Driver.name}</h4>
        <div class="podium-driver-team" style="color: var(--telemetry-gold);">
          ${p1.Team} #${p1Driver.number}
        </div>
        <div class="podium-score-pill" style="border: 1px solid var(--telemetry-gold); color: var(--telemetry-gold);">
          Model Score: ${Number(p1.PredictedFinish).toFixed(2)}
        </div>
        <div style="margin-top: 0.6rem;">
          ${renderDeltaBadge(p1.GridPosition, p1.PredictedPosition)}
        </div>
      </div>

      <!-- P3 Third Place -->
      <div class="podium-card p3">
        <div class="podium-badge">P3 PREDICTED</div>
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
        <div class="podium-score-pill">
          Model Score: ${Number(p3.PredictedFinish).toFixed(2)}
        </div>
        <div style="margin-top: 0.6rem;">
          ${renderDeltaBadge(p3.GridPosition, p3.PredictedPosition)}
        </div>
      </div>
    </div>
  `;
}

/**
 * Renders the Actual Podium Stage (Official FIA race results)
 * based on TargetFinish in Final_Data.csv.
 */
function renderActualPodiumStage() {
  const container = document.getElementById('actual-podium-stage-container');
  if (!container) return;

  if (!activePredictionsData || activePredictionsData.length === 0) {
    container.innerHTML = '';
    return;
  }

  // Filter rows with valid TargetFinish and sort ascending (1, 2, 3)
  const actualSorted = [...activePredictionsData]
    .filter(r => r.TargetFinish !== undefined && r.TargetFinish !== null && r.TargetFinish !== '' && !Number.isNaN(Number(r.TargetFinish)))
    .sort((a, b) => Number(a.TargetFinish) - Number(b.TargetFinish));

  if (actualSorted.length < 3) {
    container.innerHTML = '';
    return;
  }

  const p1 = actualSorted[0];
  const p2 = actualSorted[1];
  const p3 = actualSorted[2];

  const p1Driver = resolveDriver(p1.Driver, allDriversData);
  const p2Driver = resolveDriver(p2.Driver, allDriversData);
  const p3Driver = resolveDriver(p3.Driver, allDriversData);

  function getComparisonPill(row, targetPos) {
    const predPos = Number(row.PredictedPosition);
    const score = Number(row.PredictedFinish).toFixed(2);
    if (predPos === targetPos) {
      return `
        <div class="podium-comparison-pill hit">
          <span>&check; Exact Model Match (P${predPos} &bull; Score: ${score})</span>
        </div>
      `;
    }
    const diff = Math.abs(predPos - targetPos);
    return `
      <div class="podium-comparison-pill">
        <span>Predicted: P${predPos} (Score: ${score} &bull; &Delta;${diff})</span>
      </div>
    `;
  }

  container.innerHTML = `
    <div class="podium-header-bar">
      <h3 class="podium-stage-title actual-stage-title">
        Official Race Podium // Actual Results // ${activeGrandPrix?.name || 'Grand Prix'}
      </h3>
      <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
        <span class="tech-badge gold">OFFICIAL FIA CLASSIFICATION</span>
        <span class="tech-badge" style="font-family: var(--font-mono);">EMPIRICAL TARGETFINISH</span>
      </div>
    </div>

    <div class="podium-grid">
      <!-- Actual P2 -->
      <div class="podium-card actual-p2">
        <div class="podium-badge">P2 OFFICIAL</div>
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
        <div class="actual-result-pill">
          Official Finish: P2
        </div>
        <div style="margin-top: 0.6rem;">
          ${renderDeltaBadge(p2.GridPosition, p2.TargetFinish)}
        </div>
        ${getComparisonPill(p2, 2)}
      </div>

      <!-- Actual P1 Winner -->
      <div class="podium-card actual-p1">
        <div class="podium-badge" style="background: linear-gradient(135deg, #FFB800 0%, #D48800 100%); color: #000;">
          P1 OFFICIAL WINNER
        </div>
        <div class="podium-headshot-wrap" style="height: 220px;">
          <img
            src="${normalizeHeadshotUrl(p1Driver.headshot)}"
            alt="${p1Driver.name}"
            class="podium-headshot"
            onerror="handleImageFallback(this, '${p1Driver.headshot}')"
          />
        </div>
        <h4 class="podium-driver-name" style="font-size: 1.55rem;">${p1Driver.name}</h4>
        <div class="podium-driver-team" style="color: var(--telemetry-gold);">
          ${p1.Team} #${p1Driver.number}
        </div>
        <div class="actual-result-pill" style="border: 1px solid var(--telemetry-gold); color: var(--telemetry-gold); background: rgba(255, 184, 0, 0.12);">
          Official Finish: P1 WINNER
        </div>
        <div style="margin-top: 0.6rem;">
          ${renderDeltaBadge(p1.GridPosition, p1.TargetFinish)}
        </div>
        ${getComparisonPill(p1, 1)}
      </div>

      <!-- Actual P3 -->
      <div class="podium-card actual-p3">
        <div class="podium-badge">P3 OFFICIAL</div>
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
        <div class="actual-result-pill">
          Official Finish: P3
        </div>
        <div style="margin-top: 0.6rem;">
          ${renderDeltaBadge(p3.GridPosition, p3.TargetFinish)}
        </div>
        ${getComparisonPill(p3, 3)}
      </div>
    </div>
  `;
}

/**
 * Calculates position change between starting grid and predicted finish rank.
 */
function renderDeltaBadge(gridPos, predPos) {
  const grid = Number(gridPos);
  const prediction = Number(predPos);
  const delta = grid - prediction;

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

/**
 * Renders the full prediction classification table.
 */
function renderTelemetryTable() {
  const tableBody = document.getElementById('telemetry-table-body');
  if (!tableBody) return;

  if (!activePredictionsData || activePredictionsData.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center; padding:2rem; color:var(--text-muted);">
          No prediction data available for this Grand Prix.
        </td>
      </tr>
    `;
    return;
  }

  const data = [...activePredictionsData];

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
            <span class="team-color-indicator" style="background-color:${teamColor};"></span>
            <span>${row.Team}</span>
          </div>
        </td>

        <td style="font-family:var(--font-mono);">${row.GridPosition}</td>

        <td style="font-family:var(--font-mono);">${row.QualiPosition}</td>

        <td class="score-cell">${Number(row.PredictedFinish).toFixed(2)}</td>

        <td>
          ${renderDeltaBadge(row.GridPosition, row.PredictedPosition)}
        </td>
      </tr>
    `;
  }).join('');
}

/* ==========================================================================
   FULL FINAL_DATA.CSV VIEW (ALL COLUMNS)
   ========================================================================== */

/**
 * Renders every single column from Final_Data.csv in a rich tabular format.
 */
function renderFullCsvTable(data) {
  const thead = document.getElementById('full-csv-thead');
  const tbody = document.getElementById('full-csv-tbody');
  if (!thead || !tbody) return;

  if (!data || data.length === 0) {
    thead.innerHTML = '';
    tbody.innerHTML = `<tr><td style="padding:2rem; text-align:center; color:var(--text-muted);">No data available</td></tr>`;
    return;
  }

  // Use parsed keys or raw headers
  const columns = fullCsvHeaders.length > 0 ? fullCsvHeaders : Object.keys(data[0]);

  // Render Table Head
  thead.innerHTML = `
    <tr>
      ${columns.map(col => `
        <th style="cursor: pointer; white-space: nowrap;" onclick="sortFullCsvTable('${col}')" title="Click to sort by ${col}">
          ${col} &#x25B4;&#x25BE;
        </th>
      `).join('')}
    </tr>
  `;

  // Render Table Body
  tbody.innerHTML = data.map(row => {
    const teamColor = getTeamColor(row.Team);
    return `
      <tr>
        ${columns.map((col, idx) => {
          const val = row[col] !== undefined ? row[col] : '';
          const isNumeric = typeof val === 'number';
          const isPos = col === 'PredictedPosition';
          const isScore = col === 'PredictedFinish';
          const isDriver = col === 'Driver';

          let cellStyle = '';
          if (isNumeric) cellStyle += 'font-family:var(--font-mono);';
          if (isPos) cellStyle += `border-left: 3px solid ${teamColor}; font-weight:700;`;
          if (isScore) cellStyle += 'color:var(--telemetry-cyan); font-weight:700;';
          if (isDriver) cellStyle += 'font-weight:600; color:#FFF;';

          return `<td style="${cellStyle}">${val}</td>`;
        }).join('')}
      </tr>
    `;
  }).join('');
}

/**
 * Sorts the complete CSV table
 */
function sortFullCsvTable(column) {
  if (currentSortColumn === column) {
    currentSortAsc = !currentSortAsc;
  } else {
    currentSortColumn = column;
    currentSortAsc = true;
  }

  activePredictionsData.sort((a, b) => {
    let valA = a[column];
    let valB = b[column];

    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();

    if (valA < valB) return currentSortAsc ? -1 : 1;
    if (valA > valB) return currentSortAsc ? 1 : -1;
    return 0;
  });

  renderFullCsvTable(activePredictionsData);
}

/* ==========================================================================
   RAW CSV CODE VIEW
   ========================================================================== */

/**
 * Renders the raw CSV text view with copy helper
 */
function renderRawCsvView(rawText, race) {
  const codeEl = document.getElementById('raw-csv-code');
  const pathEl = document.getElementById('raw-csv-path');
  if (pathEl) {
    pathEl.textContent = `predictions/2026/${race?.data || race?.slug + '/Final_Data.csv'}`;
  }
  if (codeEl) {
    codeEl.textContent = rawText || 'No CSV text available.';
  }
}

/* ==========================================================================
   ERROR STATE
   ========================================================================== */

function showPredictionLoadError(race, error) {
  const container = document.getElementById('gp-banner-container');
  if (!container) return;

  container.innerHTML = `
    <div
      class="prediction-error"
      style="
        margin: 1.5rem 0;
        padding: 1.5rem;
        border: 1px solid rgba(225, 6, 0, 0.45);
        border-radius: 12px;
        background: rgba(225, 6, 0, 0.08);
      "
    >
      <div style="display:flex; align-items:center; gap:0.5rem; color:#FF5A54; font-family:var(--font-race); font-size:1.1rem; font-weight:700;">
        <span>&#9888;</span>
        <span>Telemetry Dataset Error</span>
      </div>
      <p style="color: var(--text-muted); margin-top: 0.4rem; font-size:0.9rem;">
        Could not load prediction dataset for <strong>${race?.name || 'Grand Prix'}</strong>.
      </p>
      <code style="display:block; margin-top:0.6rem; font-size:0.8rem; color:var(--text-technical); word-break:break-all;">
        ${error?.message || 'Unknown network or parse error'}
      </code>
    </div>
  `;
}

/* ==========================================================================
   CSV PARSER (Fallback & Robust Parsing)
   ========================================================================== */

/**
 * Handles CSV parsing with quotes and type coercion.
 */
function parseCSV(text) {
  if (!text || typeof text !== 'string') return [];

  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) return [];

  const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
  const rows = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const values = [];
    let insideQuote = false;
    let entry = '';

    for (let j = 0; j < line.length; j++) {
      const char = line[j];
      if (char === '"' || char === "'") {
        insideQuote = !insideQuote;
      } else if (char === ',' && !insideQuote) {
        values.push(entry.trim().replace(/^"|"$/g, ''));
        entry = '';
      } else {
        entry += char;
      }
    }
    values.push(entry.trim().replace(/^"|"$/g, ''));

    if (values.length === headers.length) {
      const rowObj = {};
      headers.forEach((h, idx) => {
        let val = values[idx];
        if (['QualiPosition', 'GridPosition', 'PredictedPosition', 'TargetFinish', 'Year', 'RoundNumber'].includes(h)) {
          const num = parseInt(val, 10);
          rowObj[h] = Number.isNaN(num) ? val : num;
        } else if (['PredictedFinish', 'AvgFinishLast3', 'AvgFinishLast5', 'AvgGridLast3', 'AvgGridLast5', 'AvgPointsLast3', 'AvgPointsLast5', 'Error'].includes(h)) {
          const flt = parseFloat(val);
          rowObj[h] = Number.isNaN(flt) ? val : flt;
        } else {
          rowObj[h] = val;
        }
      });
      rows.push(rowObj);
    }
  }

  return rows;
}

/* ==========================================================================
   TABLE SORT CONTROLS
   ========================================================================== */

function sortPredictionTable(column) {
  if (currentSortColumn === column) {
    currentSortAsc = !currentSortAsc;
  } else {
    currentSortColumn = column;
    currentSortAsc = true;
  }
  renderTelemetryTable();
}

/* ==========================================================================
   DEBUG HELPERS
   ========================================================================== */

async function debugPredictionPaths() {
  console.log('Manifest paths:', MANIFEST_CANDIDATE_PATHS);
  const manifest = await loadPredictionManifest();
  console.log('Manifest loaded:', manifest);
  console.log('Active GP:', activeGrandPrix);
  console.log('Rows loaded:', activePredictionsData.length);
}
