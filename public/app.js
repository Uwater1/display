/**
 * Financial Market Analysis App
 */

(function() {
    'use strict';

    // State
    const state = {
        currentTicker: 'IVV',
        currentView: 'stats',
        charts: [],
        currentChartIndex: 0,
        stats: null,
        chartInstances: {
            strategy: null,
            weekday: null,
            monthly: null
        }
    };

    // DOM Elements
    const elements = {
        tickerBtns: document.querySelectorAll('.ticker-btn'),
        viewBtns: document.querySelectorAll('.view-btn'),
        viewSections: document.querySelectorAll('.view-section'),

        // Stats View
        strategyChart: document.getElementById('strategyChart'),
        weekdayChart: document.getElementById('weekdayChart'),
        monthlyChart: document.getElementById('monthlyChart'),
        strategySummary: document.getElementById('strategy-summary'),

        // Charts View
        dateSelector: document.getElementById('date-selector'),
        chartDisplay: document.getElementById('chart-display'),
        prevBtn: document.getElementById('prev-btn'),
        nextBtn: document.getElementById('next-btn'),
        chartDate: document.getElementById('chart-date'),
        chartChange: document.getElementById('chart-change')
    };

    // --- Initialization ---

    async function init() {
        setupEventListeners();
        await loadData(state.currentTicker);
    }

    function setupEventListeners() {
        // Ticker Selection
        elements.tickerBtns.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const ticker = e.target.dataset.ticker;
                if (ticker !== state.currentTicker) {
                    updateActiveButton(elements.tickerBtns, e.target);
                    state.currentTicker = ticker;
                    await loadData(ticker);
                }
            });
        });

        // View Selection
        elements.viewBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const view = e.target.dataset.view;
                if (view !== state.currentView) {
                    updateActiveButton(elements.viewBtns, e.target);
                    switchView(view);
                }
            });
        });

        // Chart Navigation
        elements.dateSelector.addEventListener('change', (e) => {
            const index = parseInt(e.target.value, 10);
            if (!isNaN(index)) {
                renderDailyChart(index);
            }
        });

        elements.prevBtn.addEventListener('click', () => {
            if (state.currentChartIndex > 0) {
                renderDailyChart(state.currentChartIndex - 1);
            }
        });

        elements.nextBtn.addEventListener('click', () => {
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

    function updateActiveButton(group, target) {
        group.forEach(btn => btn.classList.remove('active'));
        target.classList.add('active');
    }

    function switchView(viewName) {
        state.currentView = viewName;
        elements.viewSections.forEach(section => {
            section.classList.remove('active');
            if (section.id === `${viewName}-view`) {
                section.classList.add('active');
            }
        });
    }

    // --- Data Loading ---

    async function loadData(ticker) {
        try {
            // Load Stats
            const statsRes = await fetch(`data/stats_${ticker}.json`);
            state.stats = await statsRes.json();

            // Load Charts List
            const chartsRes = await fetch(`data/charts_${ticker}.json`);
            state.charts = await chartsRes.json();

            // Reset Chart View
            state.currentChartIndex = 0;
            populateDateSelector();

            // Render Current View
            if (state.currentView === 'stats') {
                renderStats();
            } else {
                renderDailyChart(0);
            }

            // Always render stats charts to be ready when switching
            renderStats();

        } catch (error) {
            console.error('Error loading data:', error);
            alert('Failed to load data for ' + ticker);
        }
    }

    // --- Statistics Rendering ---

    function renderStats() {
        if (!state.stats) return;

        renderStrategyChart();
        renderWeekdayChart();
        renderMonthlyChart();
        renderStrategySummary();
    }

    function renderStrategySummary() {
        const s = state.stats.strategies;
        const intraReturn = (s.intraday.total_return * 100).toFixed(2);
        const overReturn = (s.overnight.total_return * 100).toFixed(2);

        elements.strategySummary.innerHTML = `
            <div class="summary-item">
                <span class="label">Intraday (9:30-16:00)</span>
                <span class="value ${s.intraday.total_return >= 0 ? 'pos' : 'neg'}">${intraReturn}%</span>
                <div class="sub-text">Win Rate: ${(s.intraday.win_rate * 100).toFixed(1)}%</div>
            </div>
            <div class="summary-item">
                <span class="label">Overnight (16:00-9:30)</span>
                <span class="value ${s.overnight.total_return >= 0 ? 'pos' : 'neg'}">${overReturn}%</span>
                <div class="sub-text">Win Rate: ${(s.overnight.win_rate * 100).toFixed(1)}%</div>
            </div>
        `;
    }

    function renderStrategyChart() {
        const ctx = elements.strategyChart.getContext('2d');
        const s = state.stats.strategies;

        if (state.chartInstances.strategy) {
            state.chartInstances.strategy.destroy();
        }

        state.chartInstances.strategy = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Intraday', 'Overnight'],
                datasets: [{
                    label: 'Total Return (%)',
                    data: [s.intraday.total_return * 100, s.overnight.total_return * 100],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(255, 99, 132, 0.7)'
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 99, 132, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#e0e0e0' },
                        grid: { color: '#333' }
                    },
                    x: {
                        ticks: { color: '#e0e0e0' },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    function renderWeekdayChart() {
        const ctx = elements.weekdayChart.getContext('2d');
        const data = state.stats.day_of_week;

        if (state.chartInstances.weekday) {
            state.chartInstances.weekday.destroy();
        }

        state.chartInstances.weekday = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.day.substring(0, 3)),
                datasets: [
                    {
                        label: 'Intraday Avg (%)',
                        data: data.map(d => d.intraday_avg * 100),
                        backgroundColor: 'rgba(54, 162, 235, 0.7)'
                    },
                    {
                        label: 'Overnight Avg (%)',
                        data: data.map(d => d.overnight_avg * 100),
                        backgroundColor: 'rgba(255, 99, 132, 0.7)'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        ticks: { color: '#e0e0e0' },
                        grid: { color: '#333' }
                    },
                    x: {
                        ticks: { color: '#e0e0e0' },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#e0e0e0' } }
                }
            }
        });
    }

    function renderMonthlyChart() {
        const ctx = elements.monthlyChart.getContext('2d');
        const data = state.stats.monthly;

        if (state.chartInstances.monthly) {
            state.chartInstances.monthly.destroy();
        }

        state.chartInstances.monthly = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.month.substring(0, 3)),
                datasets: [
                    {
                        label: 'Intraday Avg (%)',
                        data: data.map(d => d.intraday_avg * 100),
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: 'Overnight Avg (%)',
                        data: data.map(d => d.overnight_avg * 100),
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        ticks: { color: '#e0e0e0' },
                        grid: { color: '#333' }
                    },
                    x: {
                        ticks: { color: '#e0e0e0' },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#e0e0e0' } }
                }
            }
        });
    }

    // --- Daily Charts Rendering ---

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
        if (state.charts.length === 0) {
            elements.chartDisplay.innerHTML = '<div class="placeholder">No charts available</div>';
            return;
        }

        state.currentChartIndex = index;
        const chart = state.charts[index];

        // Update UI
        elements.dateSelector.value = index;
        elements.chartDate.textContent = `${chart.date} (${chart.weekday})`;
        elements.chartChange.textContent = chart.change;
        elements.chartChange.className = chart.change.includes('+') ? 'pos' : 'neg';

        elements.prevBtn.disabled = index === 0;
        elements.nextBtn.disabled = index === state.charts.length - 1;

        // Render SVG
        const imgPath = `data/${state.currentTicker}/charts/${chart.filename}`;

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
        img.className = 'chart-svg';
    }

    // Initialize
    document.addEventListener('DOMContentLoaded', init);

})();
