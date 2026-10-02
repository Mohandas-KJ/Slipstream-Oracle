/**
 * ==========================================================================
 * SLIPSTREAM ORACLE - Main Application Controller
 * Handles tab navigation, video player resilience, telemetry clock,
 * mobile drawer, and lifecycle initialization.
 * ==========================================================================
 */

const VALID_TABS = ['home', 'drivers', 'models', 'datahub', 'about'];
let activeTab = 'home';
let tabsInitialized = {
  home: true,
  drivers: false,
  models: false,
  datahub: false,
  about: false
};

document.addEventListener('DOMContentLoaded', () => {
  initTelemetryClock();
  initNavigation();
  initVideoPlayer();
  initHashRouting();
  initTableSorting();
});

/**
 * Initializes tab switching and event listeners
 */
function initNavigation() {
  const tabButtons = document.querySelectorAll('.nav-tab-btn');
  const mobileToggle = document.getElementById('mobile-nav-toggle');
  const navTabsContainer = document.getElementById('nav-tabs-container');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      if (targetTab && VALID_TABS.includes(targetTab)) {
        switchTab(targetTab);
        window.location.hash = targetTab;
        
        // Close mobile nav drawer if open
        if (navTabsContainer) {
          navTabsContainer.classList.remove('mobile-open');
        }
      }
    });
  });

  // Mobile drawer toggle
  if (mobileToggle && navTabsContainer) {
    mobileToggle.addEventListener('click', () => {
      navTabsContainer.classList.toggle('mobile-open');
    });
  }

  // Handle CTA buttons that jump between tabs
  document.querySelectorAll('[data-jump-tab]').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      const jumpTarget = el.getAttribute('data-jump-tab');
      if (jumpTarget && VALID_TABS.includes(jumpTarget)) {
        switchTab(jumpTarget);
        window.location.hash = jumpTarget;
      }
    });
  });
}

/**
 * Switches the active tab view with smooth transitions
 */
function switchTab(tabId) {
  if (!VALID_TABS.includes(tabId)) tabId = 'home';
  activeTab = tabId;

  // Update navigation buttons
  document.querySelectorAll('.nav-tab-btn').forEach(btn => {
    const isTarget = btn.getAttribute('data-tab') === tabId;
    btn.classList.toggle('active', isTarget);
    btn.setAttribute('aria-selected', isTarget ? 'true' : 'false');
  });

  // Update tab panes
  document.querySelectorAll('.tab-pane').forEach(pane => {
    const isTarget = pane.id === `tab-${tabId}`;
    pane.classList.toggle('active', isTarget);
  });

  // Scroll to top of window smoothly
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Lazy-initialize tab content on first view
  if (!tabsInitialized[tabId]) {
    tabsInitialized[tabId] = true;
    if (tabId === 'drivers') {
      initDriversTab();
    } else if (tabId === 'datahub') {
      initDataHubTab();
    }
  }
}

/**
 * Syncs tab state with URL hash
 */
function initHashRouting() {
  function handleHash() {
    const hash = window.location.hash.replace('#', '').toLowerCase();
    if (VALID_TABS.includes(hash)) {
      switchTab(hash);
    } else {
      switchTab('home');
    }
  }

  window.addEventListener('hashchange', handleHash);
  handleHash();
}

/**
 * Resilient background video playback controller
 */
function initVideoPlayer() {
  const video = document.getElementById('hero-bg-video');
  if (!video) return;

  // Guarantee muted state required by browser autoplay policies
  video.muted = true;
  video.defaultMuted = true;
  video.loop = true;
  video.playsInline = true;
  video.setAttribute('muted', '');
  video.setAttribute('playsinline', '');

  function attemptPlay() {
    video.muted = true;
    const playPromise = video.play();
    if (playPromise !== undefined) {
      playPromise.then(() => {
        video.style.opacity = '1';
      }).catch(err => {
        console.log('[Slipstream Oracle] Autoplay waiting for user gesture:', err.message);
      });
    }
  }

  // Attempt immediate playback
  attemptPlay();

  // Re-attempt when media is buffered and ready
  video.addEventListener('loadedmetadata', attemptPlay);
  video.addEventListener('loadeddata', attemptPlay);
  video.addEventListener('canplay', attemptPlay);
  video.addEventListener('canplaythrough', attemptPlay);

  // If autoplay is delayed by browser policy (e.g. file:// protocol), resume on first interaction
  const triggerEvents = ['pointerdown', 'touchstart', 'scroll', 'keydown', 'click'];
  function onUserGesture() {
    attemptPlay();
    triggerEvents.forEach(evt => window.removeEventListener(evt, onUserGesture));
  }
  triggerEvents.forEach(evt => window.addEventListener(evt, onUserGesture, { passive: true, once: true }));
}

/**
 * Pit-Wall UTC telemetry session clock
 */
function initTelemetryClock() {
  const clockEl = document.getElementById('pitwall-clock');
  if (!clockEl) return;

  function update() {
    const now = new Date();
    const hours = String(now.getUTCHours()).padStart(2, '0');
    const minutes = String(now.getUTCMinutes()).padStart(2, '0');
    const seconds = String(now.getUTCSeconds()).padStart(2, '0');
    clockEl.textContent = `${hours}:${minutes}:${seconds} UTC`;
  }

  update();
  setInterval(update, 1000);
}

/**
 * Telemetry table sort headers
 */
function initTableSorting() {
  document.querySelectorAll('[data-sort-col]').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.getAttribute('data-sort-col');
      if (currentSortColumn === col) {
        currentSortAsc = !currentSortAsc;
      } else {
        currentSortColumn = col;
        currentSortAsc = true;
      }
      renderTelemetryTable();
    });
  });
}
