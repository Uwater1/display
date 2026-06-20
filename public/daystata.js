/**
 * Day-Stat-A Viewer
 * Dynamic navigation for SSE 50, CSI 300, CSI 500, ChiNext, STAR 50, and CSI 800 statistics
 */

(function () {
    'use strict';

    // Standard list of plots for the 5 ETFs
    const standardPlots = [
        {
            filename: "gap_dist.png",
            title: "Opening Gap Distribution (High Precision)",
            description: "Shows a high-precision histogram and KDE of opening gaps, with detailed statistical metrics (mean, std dev, skewness, kurtosis, etc.)."
        },
        {
            filename: "gap_effect_intraday.png",
            title: "Intraday Gap Effect",
            description: "Traces the average cumulative price trajectory from 9:30 to 15:00 based on the size of the morning opening gap."
        },
        {
            filename: "gap_vs_return_scatter.png",
            title: "Gap Size vs. Intraday Return",
            description: "Scatter plot correlating morning opening gap size with subsequent open-to-close return, with trendline and correlation coefficient."
        },
        {
            filename: "gap_fill_analysis.png",
            title: "Gap Fill Rates & Time to Fill",
            description: "Shows fill probability for different gap sizes, and when gaps are typically filled during the trading session."
        },
        {
            filename: "yearly_return_dist.png",
            title: "Daily Return Distribution by Year",
            description: "Box plot of daily close-to-close returns grouped by Year, revealing historical volatility shifts."
        },
        {
            filename: "monthly_return_heatmap.png",
            title: "Monthly Return Heatmap",
            description: "A financial calendar heatmap showing performance for each month across all years."
        },
        {
            filename: "seasonality_analysis.png",
            title: "Seasonality Analysis",
            description: "Compares average daily returns by Day of Week (left) and Month of Year (right) with standard error bars."
        },
        {
            filename: "high_dist.png",
            title: "High Bar Distribution",
            description: "Shows at which 5-minute bar the day's high typically occurs, with cumulative distribution overlay."
        },
        {
            filename: "low_dist.png",
            title: "Low Bar Distribution",
            description: "Shows at which 5-minute bar the day's low typically occurs, with cumulative distribution overlay."
        },
        {
            filename: "extremes_dist.png",
            title: "Extremes Distribution",
            description: "Combined view of when daily highs and lows occur, tracing the first and second extreme timepoints."
        },
        {
            filename: "high_low_sequence.png",
            title: "High-Low Sequence",
            description: "Pie chart displaying whether the daily high or low is established first."
        },
        {
            filename: "close_loc.png",
            title: "Close Location in Range",
            description: "Where price closes relative to the day's range (0 = Low, 100 = High)."
        }
    ];

    // CSI 800 (from 800.csv) specific plots
    const csi800Plots = [
        {
            filename: "high_dist.png",
            title: "800 - High Bar Distribution",
            description: "Shows at which 5-minute bar the day's high typically occurs."
        },
        {
            filename: "low_dist.png",
            title: "800 - Low Bar Distribution",
            description: "Shows at which 5-minute bar the day's low typically occurs."
        },
        {
            filename: "extremes_dist.png",
            title: "800 - Extremes Distribution",
            description: "Combined view of when daily highs and lows occur."
        },
        {
            filename: "high_low_sequence.png",
            title: "800 - High-Low Sequence",
            description: "Analyzes whether the daily high or low comes first."
        },
        {
            filename: "gap_dist.png",
            title: "800 - Gap Distribution",
            description: "Distribution of opening gaps."
        },
        {
            filename: "gap_categories.png",
            title: "800 - Gap Categories",
            description: "Categorizes opening gaps into buckets."
        },
        {
            filename: "first_hour.png",
            title: "800 - First Hour Analysis",
            description: "Compares the first hour of trading vs the rest of the day."
        },
        {
            filename: "close_loc.png",
            title: "800 - Close Location",
            description: "Where price closes relative to the day's range."
        },
        {
            filename: "time_buckets.png",
            title: "800 - Time Bucket Analysis",
            description: "Breaks the trading day into time periods."
        },
        {
            filename: "common_bars.png",
            title: "800 - Common Bar Patterns",
            description: "Identifies the most common bar patterns."
        },
        // Liquidity Study (hs300_zz500_sum.csv)
        {
            filename: "../../liquidity/avg_volume_time.png",
            title: "Liquidity - Average Volume (Time of Day)",
            description: "Average Volume by Time of Day for HS300+ZZ500 Sum."
        },
        {
            filename: "../../liquidity/avg_range_time.png",
            title: "Liquidity - Average Range (Time of Day)",
            description: "Average Price Range (High-Low) by Time of Day for HS300+ZZ500 Sum."
        },
        {
            filename: "../../liquidity/price_impact_time.png",
            title: "Liquidity - Price Impact (Time of Day)",
            description: "Price Impact per Volume Unit (Liquidity Proxy) by Time of Day."
        },
        {
            filename: "../../liquidity/vol_pct_time.png",
            title: "Liquidity - Volume % (Time of Day)",
            description: "Percentage of Daily Volume by Time of Day for HS300+ZZ500 Sum."
        }
    ];

    // Map each asset ID to its prefix directory and list of plots
    const assets = {
        csi300: {
            prefix: "daystata/csi300/",
            name: "CSI 300",
            plots: standardPlots
        },
        csi500: {
            prefix: "daystata/csi500/",
            name: "CSI 500",
            plots: standardPlots
        },
        sse50: {
            prefix: "daystata/sse50/",
            name: "SSE 50",
            plots: standardPlots
        },
        chinext: {
            prefix: "daystata/chinext/",
            name: "ChiNext",
            plots: standardPlots
        },
        star50: {
            prefix: "daystata/star50/",
            name: "STAR 50",
            plots: standardPlots
        },
        csi800: {
            prefix: "daystata/csi800/",
            name: "CSI 800",
            plots: csi800Plots
        }
    };

    let currentAsset = 'csi300';
    let currentIndex = 0;
    let stats = [];

    // DOM Elements
    const elements = {
        statDisplay: document.getElementById('stat-display'),
        statDescription: document.getElementById('stat-description'),
        prevBtn: document.getElementById('prev-btn'),
        nextBtn: document.getElementById('next-btn'),
        statCounter: document.getElementById('stat-counter'),
        statTitle: document.getElementById('stat-title'),
        tabButtons: document.querySelectorAll('.tab-btn')
    };

    /**
     * Get active asset and index from URL
     */
    function parseURLParams() {
        const urlParams = new URLSearchParams(window.location.search);
        const assetParam = urlParams.get('a');
        const indexParam = urlParams.get('i');

        if (assetParam !== null && assets[assetParam]) {
            currentAsset = assetParam;
        } else {
            currentAsset = 'csi300';
        }

        stats = assets[currentAsset].plots;

        if (indexParam !== null) {
            const parsedIndex = parseInt(indexParam, 10);
            if (!isNaN(parsedIndex) && parsedIndex >= 0 && parsedIndex < stats.length) {
                currentIndex = parsedIndex;
                return;
            }
        }
        currentIndex = 0;
    }

    /**
     * Update URL parameters
     */
    function updateURL() {
        const newURL = `${window.location.pathname}?a=${currentAsset}&i=${currentIndex}`;
        history.replaceState({ asset: currentAsset, index: currentIndex }, '', newURL);
    }

    /**
     * Update navigation button states and label
     */
    function updateNavigationUI() {
        const stat = stats[currentIndex];
        elements.statCounter.textContent = `${currentIndex + 1} of ${stats.length}`;
        
        // Append current asset name to title
        const assetName = assets[currentAsset].name;
        elements.statTitle.textContent = `${assetName} - ${stat.title}`;
        
        elements.prevBtn.disabled = currentIndex === 0;
        elements.nextBtn.disabled = currentIndex === stats.length - 1;
    }

    /**
     * Render the chart image and description
     */
    function renderStat() {
        const stat = stats[currentIndex];
        const assetInfo = assets[currentAsset];

        elements.statDisplay.style.opacity = '0';

        setTimeout(() => {
            elements.statDisplay.innerHTML = '';

            const img = document.createElement('img');
            img.src = 'data/' + assetInfo.prefix + stat.filename;
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

            elements.statDescription.textContent = stat.description;
        }, 150);
    }

    /**
     * Switch asset when clicking a tab
     */
    function switchAsset(assetId) {
        if (!assets[assetId] || currentAsset === assetId) return;

        currentAsset = assetId;
        stats = assets[currentAsset].plots;
        currentIndex = 0;

        // Update active class on tab buttons
        elements.tabButtons.forEach(btn => {
            if (btn.getAttribute('data-asset') === assetId) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        updateURL();
        renderStat();
        updateNavigationUI();
    }

    function goToPrevious() {
        if (currentIndex > 0) {
            currentIndex--;
            updateURL();
            renderStat();
            updateNavigationUI();
        }
    }

    function goToNext() {
        if (currentIndex < stats.length - 1) {
            currentIndex++;
            updateURL();
            renderStat();
            updateNavigationUI();
        }
    }

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
                    updateURL();
                    renderStat();
                    updateNavigationUI();
                }
                break;
            case 'End':
                event.preventDefault();
                if (currentIndex !== stats.length - 1) {
                    currentIndex = stats.length - 1;
                    updateURL();
                    renderStat();
                    updateNavigationUI();
                }
                break;
        }
    }

    /**
     * Initialize viewer
     */
    function init() {
        parseURLParams();

        // Bind tab button click listeners
        elements.tabButtons = document.querySelectorAll('.tab-btn');
        elements.tabButtons.forEach(btn => {
            const assetId = btn.getAttribute('data-asset');
            // Set correct initial active class based on URL params
            if (assetId === currentAsset) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
            btn.addEventListener('click', () => switchAsset(assetId));
        });

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
