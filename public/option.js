/**
 * Option Volatility Viewer
 * Navigation for VIX / implied-vs-historical volatility SVG charts
 */

(function () {
    'use strict';

    const stats = [
        {
            filename: "vix_vs_gspc_hv.svg",
            title: "VIX vs S&P 500 Historical Volatility",
            description: "Compares the CBOE VIX (implied volatility from S&P 500 options) against the 20-day realized historical volatility of the S&P 500 index. The persistent positive spread (IV > HV) reflects the well-known volatility risk premium."
        },
        {
            filename: "vix_vs_gspc_hv_zoom.svg",
            title: "VIX vs S&P 500 — Zoomed In (2021–Present)",
            description: "Zoomed-in view of VIX vs S&P 500 20-day historical volatility from 2021 onward. Shows recent volatility dynamics including the 2022 rate-hike selloff and the Aug 2024 VIX spike."
        },
        {
            filename: "vxn_vs_ndx_hv.svg",
            title: "VXN vs Nasdaq-100 Historical Volatility",
            description: "Compares the CBOE VXN (implied volatility from Nasdaq-100 options) against the 20-day realized historical volatility of the Nasdaq-100 index. The Nasdaq tends to exhibit higher volatility than the S&P 500, with a similar implied-over-realized premium."
        },
        {
            filename: "vxn_vs_ndx_hv_zoom.svg",
            title: "VXN vs Nasdaq-100 — Zoomed In (2021–Present)",
            description: "Zoomed-in view of VXN vs Nasdaq-100 20-day historical volatility from 2021 onward. Highlights the tech-driven volatility during the 2022 bear market and subsequent recovery."
        },
        {
            filename: "vxst_vs_gspc_hv.svg",
            title: "VXST (VIX9D) vs S&P 500 Historical Volatility",
            description: "Compares the CBOE 9-day VIX (VIX9D, successor to VXST) against the 9-day realized historical volatility of the S&P 500. The shorter window captures near-term volatility expectations and reacts more sharply to market events."
        },
        {
            filename: "vxst_vs_gspc_hv_zoom.svg",
            title: "VXST (VIX9D) vs S&P 500 — Zoomed In (2021–Present)",
            description: "Zoomed-in view of VIX9D vs S&P 500 9-day historical volatility from 2021 onward. The 9-day window reacts faster to market shocks, producing sharper spikes."
        }
    ];

    let currentIndex = 0;

    const elements = {
        statDisplay: document.getElementById('stat-display'),
        statDescription: document.getElementById('stat-description'),
        prevBtn: document.getElementById('prev-btn'),
        nextBtn: document.getElementById('next-btn'),
        statCounter: document.getElementById('stat-counter'),
        statTitle: document.getElementById('stat-title')
    };

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

    function updateURL(index) {
        const newURL = `${window.location.pathname}?i=${index}`;
        history.replaceState({ index: index }, '', newURL);
    }

    function updateNavigationUI() {
        const stat = stats[currentIndex];
        elements.statCounter.textContent = `${currentIndex + 1} of ${stats.length}`;
        elements.statTitle.textContent = stat.title;
        elements.prevBtn.disabled = currentIndex === 0;
        elements.nextBtn.disabled = currentIndex === stats.length - 1;
    }

    function renderStat() {
        const stat = stats[currentIndex];

        elements.statDisplay.style.opacity = '0';

        setTimeout(() => {
            elements.statDisplay.innerHTML = '';

            const img = document.createElement('img');
            img.src = 'data/option/' + stat.filename;
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

    function goToPrevious() {
        if (currentIndex > 0) {
            currentIndex--;
            updateURL(currentIndex);
            renderStat();
            updateNavigationUI();
        }
    }

    function goToNext() {
        if (currentIndex < stats.length - 1) {
            currentIndex++;
            updateURL(currentIndex);
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
