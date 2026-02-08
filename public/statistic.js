/**
 * Statistics Viewer
 * Navigation for statistical PNG images with descriptions
 */

(function () {
    'use strict';

    // Statistics data with descriptions
    const stats = [
        {
            filename: "extended_stats_correlation.png",
            title: "Correlation Analysis",
            description: "Shows the correlation between different market indices and assets, helping identify relationships and potential diversification opportunities."
        },
        {
            filename: "extended_stats_qqq_pattern.png",
            title: "QQQ Pattern Analysis",
            description: "Analyzes historical patterns in QQQ (Nasdaq-100 ETF) movements, revealing recurring trends and seasonal behaviors."
        },
        {
            filename: "extended_stats_sell_in_may.png",
            title: "Sell in May Analysis",
            description: "Examines the 'Sell in May and Go Away' market adage, comparing performance during May-October vs November-April periods."
        },
        {
            filename: "extended_stats_volatility.png",
            title: "Volatility Analysis",
            description: "Displays volatility patterns across different time periods, helping understand market risk and uncertainty levels."
        },
        {
            filename: "monthly_analysis_IVV.png",
            title: "IVV Monthly Analysis",
            description: "Monthly performance breakdown of iShares S&P 500 ETF (IVV), showing average returns and patterns by month."
        },
        {
            filename: "monthly_analysis_QQQM.png",
            title: "QQQM Monthly Analysis",
            description: "Monthly performance breakdown of Invesco Nasdaq-100 ETF (QQQM), identifying seasonal trends in tech-heavy index."
        },
        {
            filename: "monthly_analysis_VUG.png",
            title: "VUG Monthly Analysis",
            description: "Monthly performance breakdown of Vanguard Growth ETF (VUG), analyzing growth stock performance by month."
        },
        {
            filename: "strategy_comparison_IVV.png",
            title: "IVV Strategy Comparison",
            description: "Compares different trading strategies applied to IVV, evaluating buy-and-hold vs timing approaches."
        },
        {
            filename: "strategy_comparison_QQQM.png",
            title: "QQQM Strategy Comparison",
            description: "Compares different trading strategies applied to QQQM, showing performance of various market timing methods."
        },
        {
            filename: "strategy_comparison_VUG.png",
            title: "VUG Strategy Comparison",
            description: "Compares different trading strategies applied to VUG, analyzing timing vs holding strategies for growth stocks."
        },
        {
            filename: "weekday_analysis_IVV.png",
            title: "IVV Weekday Analysis",
            description: "Analyzes IVV performance by day of week, revealing if certain weekdays tend to have better or worse returns."
        },
        {
            filename: "weekday_analysis_QQQM.png",
            title: "QQQM Weekday Analysis",
            description: "Analyzes QQQM performance by day of week, identifying day-of-week effects in tech sector performance."
        },
        {
            filename: "weekday_analysis_VUG.png",
            title: "VUG Weekday Analysis",
            description: "Analyzes VUG performance by day of week, examining if growth stocks exhibit weekday patterns."
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
            img.src = 'data/stats/' + stat.filename;
            img.alt = stat.title;
            img.className = 'chart-image stat-image';
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
