/**
 * Financial Charts Viewer
 * Main application JavaScript for GitHub Pages chart viewer
 */

(function() {
    'use strict';

    // State
    let charts = [];
    let currentIndex = 0;

    // DOM Elements
    const elements = {
        chartDisplay: document.getElementById('chart-display'),
        prevBtn: document.getElementById('prev-btn'),
        nextBtn: document.getElementById('next-btn'),
        chartCounter: document.getElementById('chart-counter'),
        chartDate: document.getElementById('chart-date'),
        chartChange: document.getElementById('chart-change')
    };

    /**
     * Get the initial chart index from URL query parameter
     * Defaults to the first chart if not specified or invalid
     */
    function getInitialIndex() {
        const urlParams = new URLSearchParams(window.location.search);
        const indexParam = urlParams.get('i');

        if (indexParam !== null) {
            const parsedIndex = parseInt(indexParam, 10);
            if (!isNaN(parsedIndex) && parsedIndex >= 0 && parsedIndex < charts.length) {
                return parsedIndex;
            }
        }

        // Default to first chart
        return 0;
    }

    /**
     * Update the URL with the current chart index
     * @param {number} index - The chart index to set in URL
     */
    function updateURL(index) {
        const newURL = `${window.location.pathname}?i=${index}`;
        history.replaceState({ index: index }, '', newURL);
    }

    /**
     * Update the navigation UI with current chart information
     */
    function updateNavigationUI() {
        const chart = charts[currentIndex];

        // Update counter (1-based index for display)
        elements.chartCounter.textContent = `Chart ${currentIndex + 1} of ${charts.length}`;

        // Update date
        elements.chartDate.textContent = chart.date || '--';

        // Update change percentage
        elements.chartChange.textContent = chart.change || '--';
        // Style the change based on positive/negative value
        if (chart.change) {
            const isPositive = chart.change.startsWith('+');
            const isNegative = chart.change.startsWith('-');
            elements.chartChange.classList.remove('positive', 'negative');
            if (isPositive) {
                elements.chartChange.classList.add('positive');
            } else if (isNegative) {
                elements.chartChange.classList.add('negative');
            }
        } else {
            elements.chartChange.classList.remove('positive', 'negative');
        }

        // Update button states
        elements.prevBtn.disabled = currentIndex === 0;
        elements.nextBtn.disabled = currentIndex === charts.length - 1;
    }

    /**
     * Render the current chart with smooth transition
     */
    function renderChart() {
        const chart = charts[currentIndex];

        // Add transition class for smooth animation
        elements.chartDisplay.classList.add('transitioning');

        // Fade out
        elements.chartDisplay.style.opacity = '0';

        setTimeout(() => {
            // Clear and render new chart
            elements.chartDisplay.innerHTML = '';

            if (chart.filename) {
                const img = document.createElement('img');
                img.src = 'data/chart/' + encodeURIComponent(chart.filename);
                img.alt = `Chart for ${chart.date}`;
                img.className = 'chart-image';
                img.onload = () => {
                    // Fade in after image loads
                    elements.chartDisplay.style.opacity = '1';
                    elements.chartDisplay.classList.remove('transitioning');
                };
                img.onerror = () => {
                    elements.chartDisplay.innerHTML = '<div class="error">Failed to load chart</div>';
                    elements.chartDisplay.style.opacity = '1';
                    elements.chartDisplay.classList.remove('transitioning');
                };
                elements.chartDisplay.appendChild(img);
            } else {
                elements.chartDisplay.innerHTML = '<div class="error">No chart data available</div>';
                elements.chartDisplay.style.opacity = '1';
                elements.chartDisplay.classList.remove('transitioning');
            }
        }, 150);
    }

    /**
     * Navigate to the previous chart
     */
    function goToPrevious() {
        if (currentIndex > 0) {
            currentIndex--;
            updateURL(currentIndex);
            renderChart();
            updateNavigationUI();
        }
    }

    /**
     * Navigate to the next chart
     */
    function goToNext() {
        if (currentIndex < charts.length - 1) {
            currentIndex++;
            updateURL(currentIndex);
            renderChart();
            updateNavigationUI();
        }
    }

    /**
     * Navigate to a specific chart index
     * @param {number} index - The target chart index
     */
    function goToChart(index) {
        if (index >= 0 && index < charts.length && index !== currentIndex) {
            currentIndex = index;
            updateURL(currentIndex);
            renderChart();
            updateNavigationUI();
        }
    }

    /**
     * Handle keyboard navigation
     * @param {KeyboardEvent} event - The keyboard event
     */
    function handleKeyboardNavigation(event) {
        // Ignore if user is typing in an input
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }

        switch (event.key) {
            case 'ArrowLeft':
            case 'a':
            case 'A':
                event.preventDefault();
                goToPrevious();
                break;
            case 'ArrowRight':
            case 'd':
            case 'D':
                event.preventDefault();
                goToNext();
                break;
            case 'Home':
                event.preventDefault();
                goToChart(0);
                break;
            case 'End':
                event.preventDefault();
                goToChart(charts.length - 1);
                break;
        }
    }

    /**
     * Handle browser back/forward navigation
     * @param {PopStateEvent} event - The popstate event
     */
    function handlePopState(event) {
        if (event.state && typeof event.state.index === 'number') {
            const newIndex = event.state.index;
            if (newIndex >= 0 && newIndex < charts.length) {
                currentIndex = newIndex;
                renderChart();
                updateNavigationUI();
            }
        }
    }

    /**
     * Initialize the application
     */
    async function init() {
        try {
            // Fetch charts data
            const response = await fetch('charts.json');
            if (!response.ok) {
                throw new Error(`Failed to fetch charts: ${response.status}`);
            }

            charts = await response.json();

            if (!Array.isArray(charts) || charts.length === 0) {
                throw new Error('No charts available');
            }

            // Get initial index from URL or default to first chart
            currentIndex = getInitialIndex();

            // Update URL to match current state
            updateURL(currentIndex);

            // Set up event listeners
            elements.prevBtn.addEventListener('click', goToPrevious);
            elements.nextBtn.addEventListener('click', goToNext);
            document.addEventListener('keydown', handleKeyboardNavigation);
            window.addEventListener('popstate', handlePopState);

            // Initial render
            renderChart();
            updateNavigationUI();

        } catch (error) {
            console.error('Failed to initialize chart viewer:', error);
            elements.chartDisplay.innerHTML = `<div class="error">Error loading charts: ${error.message}</div>`;
        }
    }

    // Start the application when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
