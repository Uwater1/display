/**
 * Day-Stat Viewer
 * Navigation for day-trading statistics PNG images with descriptions
 */

(function () {
    'use strict';

    // Day trading statistics data with descriptions
    const stats = [
        {
            filename: "high_dist.png",
            title: "High Bar Distribution",
            description: "Shows at which 5-minute bar the day's high typically occurs. Helps identify when the highest price of the day is most likely to be reached."
        },
        {
            filename: "low_dist.png",
            title: "Low Bar Distribution",
            description: "Shows at which 5-minute bar the day's low typically occurs. Helps identify when the lowest price of the day is most likely to be reached."
        },
        {
            filename: "extremes_dist.png",
            title: "Extremes Distribution",
            description: "Combined view of when daily highs and lows occur, showing the distribution of extreme price points throughout the trading day."
        },
        {
            filename: "high_low_sequence.png",
            title: "High-Low Sequence",
            description: "Analyzes whether the daily high or low comes first. Understanding this pattern can help with entry and exit timing strategies."
        },
        {
            filename: "gap_dist.png",
            title: "Gap Distribution",
            description: "Distribution of opening gaps (difference between previous close and current open). Shows how often gaps of various sizes occur."
        },
        {
            filename: "gap_categories.png",
            title: "Gap Categories",
            description: "Categorizes opening gaps into buckets (small, medium, large) and shows their frequency and typical behavior patterns."
        },
        {
            filename: "first_hour.png",
            title: "First Hour Analysis",
            description: "Compares the first hour of trading (12 bars) vs the rest of the day. The first hour often sets the tone for daily price action."
        },
        {
            filename: "close_loc.png",
            title: "Close Location",
            description: "Where price closes relative to the day's range. Shows whether closes tend to be near highs, lows, or middle of the range."
        },
        {
            filename: "time_buckets.png",
            title: "Time Bucket Analysis",
            description: "Breaks the trading day into time periods and analyzes performance characteristics during each period."
        },
        {
            filename: "common_bars.png",
            title: "Common Bar Patterns",
            description: "Identifies the most common bar patterns and their frequency throughout the trading session."
        },
        {
            filename: "qqq_daytrading_stats.png",
            title: "QQQ Day Trading Summary",
            description: "Comprehensive summary of all QQQ intraday statistics and patterns for day trading analysis."
        }
    ];

    let currentIndex = 0;

    // DOM Elements
    const elements = {
        statDisplay: document.getElementById('stat-display'),
        statDescription: document.getElementById('stat-description'),
        prevBtn: document.getElementById('prev-btn'),
        nextBtn: document.getElementById('next-btn'),
        statCounter: document.getElementById('stat-counter'),
        statTitle: document.getElementById('stat-title')
    };

    /**
     * Get initial index from URL
     */
    function getInitialIndex() {
        const urlParams = new URLSearchParams(window.location.search);
        const indexParam = urlParams.get('i');
        if (indexParam !== null) {
            const parsedIndex = parseInt(indexParam, 10);
            if (!isNaN(parsedIndex) && parsedIndex >= 0 && parsedIndex < stats.length) {
                return parsedIndex;
            }
        }
        return 0;
    }

    /**
     * Update URL with current index
     */
    function updateURL(index) {
        const newURL = `${window.location.pathname}?i=${index}`;
        history.replaceState({ index: index }, '', newURL);
    }

    /**
     * Update navigation UI
     */
    function updateNavigationUI() {
        const stat = stats[currentIndex];
        elements.statCounter.textContent = `${currentIndex + 1} of ${stats.length}`;
        elements.statTitle.textContent = stat.title;
        elements.prevBtn.disabled = currentIndex === 0;
        elements.nextBtn.disabled = currentIndex === stats.length - 1;
    }

    /**
     * Render current statistic
     */
    function renderStat() {
        const stat = stats[currentIndex];

        elements.statDisplay.style.opacity = '0';

        setTimeout(() => {
            elements.statDisplay.innerHTML = '';

            const img = document.createElement('img');
            img.src = 'data/daystat/' + stat.filename;
            img.alt = stat.title;
            img.className = 'chart-image daystat-image';
            img.onload = () => {
                elements.statDisplay.style.opacity = '1';
            };
            img.onerror = () => {
                elements.statDisplay.innerHTML = '<div class="error">Failed to load image</div>';
                elements.statDisplay.style.opacity = '1';
            };
            elements.statDisplay.appendChild(img);

            // Update description
            elements.statDescription.textContent = stat.description;
        }, 150);
    }

    /**
     * Navigate to previous
     */
    function goToPrevious() {
        if (currentIndex > 0) {
            currentIndex--;
            updateURL(currentIndex);
            renderStat();
            updateNavigationUI();
        }
    }

    /**
     * Navigate to next
     */
    function goToNext() {
        if (currentIndex < stats.length - 1) {
            currentIndex++;
            updateURL(currentIndex);
            renderStat();
            updateNavigationUI();
        }
    }

    /**
     * Handle keyboard navigation
     */
    function handleKeyboardNavigation(event) {
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
                if (currentIndex !== 0) {
                    currentIndex = 0;
                    updateURL(currentIndex);
                    renderStat();
                    updateNavigationUI();
                }
                break;
            case 'End':
                event.preventDefault();
                if (currentIndex !== stats.length - 1) {
                    currentIndex = stats.length - 1;
                    updateURL(currentIndex);
                    renderStat();
                    updateNavigationUI();
                }
                break;
        }
    }

    /**
     * Initialize
     */
    function init() {
        currentIndex = getInitialIndex();
        updateURL(currentIndex);

        elements.prevBtn.addEventListener('click', goToPrevious);
        elements.nextBtn.addEventListener('click', goToNext);
        document.addEventListener('keydown', handleKeyboardNavigation);

        renderStat();
        updateNavigationUI();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
