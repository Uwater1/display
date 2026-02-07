/**
 * Financial Market Analysis App - V3
 */

(function() {
    'use strict';

    // State
    const state = {
        currentTicker: 'IVV',
        currentView: 'landing', // 'landing', 'stats', 'charts'
        charts: [],
        currentChartIndex: 0,
        statsManifest: null,
        preloadImages: []
    };

    // DOM Elements
    const elements = {
        appHeader: document.getElementById('app-header'),
        headerTitle: document.getElementById('header-title'),
        currentTickerDisplay: document.getElementById('current-ticker-display'),
        backBtn: document.getElementById('back-btn'),

        // Landing View
        landingView: document.getElementById('landing-view'),
        tickerBtns: document.querySelectorAll('.ticker-btn-large'),
        actionBtns: document.querySelectorAll('.action-btn'),

        // Stats View
        statsView: document.getElementById('stats-view'),
        statsContainer: document.getElementById('stats-container'),

        // Charts View
        chartsView: document.getElementById('charts-view'),
        dateSelector: document.getElementById('date-selector'),
        chartDisplay: document.getElementById('chart-display'),
        chartDate: document.getElementById('chart-date'),
        chartChange: document.getElementById('chart-change'),
        prevChartBtn: document.getElementById('prev-chart-btn'),
        nextChartBtn: document.getElementById('next-chart-btn'),
    };

    // --- Initialization ---

    function init() {
        setupEventListeners();
    }

    function setupEventListeners() {
        // Ticker Selection (Landing)
        elements.tickerBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const ticker = e.target.dataset.ticker;
                state.currentTicker = ticker;
                updateTickerButtons();
            });
        });

        // Action Buttons (Landing)
        elements.actionBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Find the button element even if span is clicked
                const targetBtn = e.target.closest('.action-btn');
                const targetView = targetBtn.dataset.target; // 'charts' or 'stats'

                if (targetView === 'charts') {
                    openChartsView();
                } else if (targetView === 'stats') {
                    openStatsView();
                }
            });
        });

        // Back Button
        elements.backBtn.addEventListener('click', () => {
            showView('landing');
            elements.appHeader.classList.add('hidden');
        });

        // Chart Navigation
        elements.dateSelector.addEventListener('change', (e) => {
            const index = parseInt(e.target.value, 10);
            if (!isNaN(index)) {
                renderDailyChart(index);
            }
        });

        elements.prevChartBtn.addEventListener('click', () => {
            if (state.currentChartIndex > 0) {
                renderDailyChart(state.currentChartIndex - 1);
            }
        });

        elements.nextChartBtn.addEventListener('click', () => {
            if (state.currentChartIndex < state.charts.length - 1) {
                renderDailyChart(state.currentChartIndex + 1);
            }
        });

        // Keyboard Navigation
        document.addEventListener('keydown', (e) => {
            if (state.currentView === 'charts') {
                if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') {
                    if (state.currentChartIndex > 0) renderDailyChart(state.currentChartIndex - 1);
                } else if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') {
                    if (state.currentChartIndex < state.charts.length - 1) renderDailyChart(state.currentChartIndex + 1);
                }
            }
        });
    }

    // --- View Management ---

    function showView(viewName) {
        state.currentView = viewName;

        // Hide all views
        elements.landingView.classList.remove('active');
        elements.statsView.classList.remove('active');
        elements.chartsView.classList.remove('active');

        // Show target view
        if (viewName === 'landing') {
            elements.landingView.classList.add('active');
        } else if (viewName === 'stats') {
            elements.statsView.classList.add('active');
            elements.appHeader.classList.remove('hidden');
            elements.headerTitle.textContent = 'Daily Statistics';
            elements.currentTickerDisplay.textContent = state.currentTicker;
        } else if (viewName === 'charts') {
            elements.chartsView.classList.add('active');
            elements.appHeader.classList.remove('hidden');
            elements.headerTitle.textContent = 'Historical Charts';
            elements.currentTickerDisplay.textContent = state.currentTicker;
        }
    }

    function updateTickerButtons() {
        elements.tickerBtns.forEach(btn => {
            if (btn.dataset.ticker === state.currentTicker) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }

    // --- Statistics View Logic ---

    async function openStatsView() {
        showView('stats');
        elements.statsContainer.innerHTML = '<div class="loading">Loading Statistics...</div>';

        try {
            const response = await fetch(`data/${state.currentTicker}/stats_manifest.json`);
            state.statsManifest = await response.json();
            renderStats();
        } catch (error) {
            console.error('Error loading stats manifest:', error);
            elements.statsContainer.innerHTML = '<div class="error">Failed to load statistics.</div>';
        }
    }

    function renderStats() {
        elements.statsContainer.innerHTML = '';

        if (!state.statsManifest || state.statsManifest.length === 0) {
            elements.statsContainer.innerHTML = '<div class="placeholder">No statistics available.</div>';
            return;
        }

        state.statsManifest.forEach(item => {
            const card = document.createElement('div');
            card.className = 'stat-card';

            const img = document.createElement('img');
            img.src = item.image;
            img.alt = item.title;
            img.className = 'stat-image';
            img.loading = 'lazy';

            const content = document.createElement('div');
            content.className = 'stat-content';

            const title = document.createElement('h3');
            title.textContent = item.title;

            const desc = document.createElement('p');
            desc.textContent = item.description;

            content.appendChild(title);
            content.appendChild(desc);

            card.appendChild(img);
            card.appendChild(content);

            elements.statsContainer.appendChild(card);
        });
    }

    // --- Historical Charts View Logic ---

    async function openChartsView() {
        showView('charts');

        // Load charts list if needed (or if ticker changed)
        // Ideally we cache this, but for simplicity we reload
        try {
            const response = await fetch(`data/charts_${state.currentTicker}.json`);
            state.charts = await response.json();

            state.currentChartIndex = 0;
            populateDateSelector();
            renderDailyChart(0);
        } catch (error) {
            console.error('Error loading charts list:', error);
            elements.chartDisplay.innerHTML = '<div class="error">Failed to load charts list.</div>';
        }
    }

    function populateDateSelector() {
        elements.dateSelector.innerHTML = '';
        state.charts.forEach((chart, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = `${chart.date} (${chart.weekday}) - ${chart.change}`;
            elements.dateSelector.appendChild(option);
        });
    }

    function renderDailyChart(index) {
        if (!state.charts || state.charts.length === 0) {
            elements.chartDisplay.innerHTML = '<div class="placeholder">No charts available</div>';
            return;
        }

        state.currentChartIndex = index;
        const chart = state.charts[index];

        // Update UI Controls
        elements.dateSelector.value = index;
        elements.chartDate.textContent = `${chart.date} (${chart.weekday})`;
        elements.chartChange.textContent = chart.change;
        elements.chartChange.className = chart.change.includes('+') ? 'pos' : 'neg';

        // Update Nav Button States
        if (index === 0) {
            elements.prevChartBtn.classList.add('disabled');
        } else {
            elements.prevChartBtn.classList.remove('disabled');
        }

        if (index === state.charts.length - 1) {
            elements.nextChartBtn.classList.add('disabled');
        } else {
            elements.nextChartBtn.classList.remove('disabled');
        }

        // Render SVG
        const imgPath = `data/${state.currentTicker}/charts/${chart.filename}`;

        // Preload next image for smoother navigation
        if (index < state.charts.length - 1) {
            const nextImg = new Image();
            nextImg.src = `data/${state.currentTicker}/charts/${state.charts[index+1].filename}`;
        }

        elements.chartDisplay.innerHTML = '<div class="loading">Loading...</div>';

        const img = new Image();
        img.onload = () => {
            elements.chartDisplay.innerHTML = '';
            elements.chartDisplay.appendChild(img);
        };
        img.onerror = () => {
            elements.chartDisplay.innerHTML = '<div class="error">Failed to load chart</div>';
        };
        img.src = imgPath;
        img.className = 'chart-svg-viewer';
    }

    // Initialize
    document.addEventListener('DOMContentLoaded', init);

})();
