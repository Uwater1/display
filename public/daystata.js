/**
 * Day-Stat-A Viewer
 * Navigation for 800.csv day-trading statistics and hs300_zz500_sum liquidity study
 */

(function () {
    'use strict';

    // Day trading stats A & Liquidity
    const stats = [
        // Day-Stat-A (800.csv)
        {
            filename: "daystata/high_dist.png",
            title: "800 - High Bar Distribution",
            description: "Shows at which 5-minute bar the day's high typically occurs."
        },
        {
            filename: "daystata/low_dist.png",
            title: "800 - Low Bar Distribution",
            description: "Shows at which 5-minute bar the day's low typically occurs."
        },
        {
            filename: "daystata/extremes_dist.png",
            title: "800 - Extremes Distribution",
            description: "Combined view of when daily highs and lows occur."
        },
        {
            filename: "daystata/high_low_sequence.png",
            title: "800 - High-Low Sequence",
            description: "Analyzes whether the daily high or low comes first."
        },
        {
            filename: "daystata/gap_dist.png",
            title: "800 - Gap Distribution",
            description: "Distribution of opening gaps."
        },
        {
            filename: "daystata/gap_categories.png",
            title: "800 - Gap Categories",
            description: "Categorizes opening gaps into buckets."
        },
        {
            filename: "daystata/first_hour.png",
            title: "800 - First Hour Analysis",
            description: "Compares the first hour of trading vs the rest of the day."
        },
        {
            filename: "daystata/close_loc.png",
            title: "800 - Close Location",
            description: "Where price closes relative to the day's range."
        },
        {
            filename: "daystata/time_buckets.png",
            title: "800 - Time Bucket Analysis",
            description: "Breaks the trading day into time periods."
        },
        {
            filename: "daystata/common_bars.png",
            title: "800 - Common Bar Patterns",
            description: "Identifies the most common bar patterns."
        },

        // Liquidity Study (hs300_zz500_sum.csv)
        {
            filename: "liquidity/avg_volume_time.png",
            title: "Liquidity - Average Volume (Time of Day)",
            description: "Average Volume by Time of Day for HS300+ZZ500 Sum."
        },
        {
            filename: "liquidity/avg_range_time.png",
            title: "Liquidity - Average Range (Time of Day)",
            description: "Average Price Range (High-Low) by Time of Day for HS300+ZZ500 Sum."
        },
        {
            filename: "liquidity/price_impact_time.png",
            title: "Liquidity - Price Impact (Time of Day)",
            description: "Price Impact per Volume Unit (Liquidity Proxy) by Time of Day."
        },
        {
            filename: "liquidity/vol_pct_time.png",
            title: "Liquidity - Volume % (Time of Day)",
            description: "Percentage of Daily Volume by Time of Day for HS300+ZZ500 Sum."
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
            img.src = 'data/' + stat.filename;
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
