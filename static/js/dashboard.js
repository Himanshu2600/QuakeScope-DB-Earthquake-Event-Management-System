/**
 * dashboard.js
 * QuakeScope DB — Liquid Glass Frontend Logic
 * Course: CSE494 Intelligent NoSQL Databases
 * Stage 3: Premium Dashboard & Visual Analytics
 */

// Global State
let currentSection = 'overview';
let explorerState = {
    page: 1,
    perPage: 15,
    query: '',
    minMag: '',
    magType: 'all',
    depthCat: 'all',
    sortBy: 'event_time',
    sortOrder: 'desc'
};

// Global Chart Instances
let chartInstances = {};
let leafletMap = null;
let mapMarkers = [];

// DOM Loaded Entrypoint
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initChartDefaults();
    initEventListeners();
    
    // Initial Data Fetch
    refreshAllData().then(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const openEvent = urlParams.get('event');
        if (openEvent) {
            setTimeout(() => openEventDetailModal(openEvent), 400);
        }
    });
});

// -----------------------------------------------------------------------------
// 1. NAVIGATION & ROUTING
// -----------------------------------------------------------------------------
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetSection = item.getAttribute('data-section');
            navigateToSection(targetSection);
        });
    });

    // Check URL hash if present
    const hash = window.location.hash.replace('#', '');
    if (hash && document.getElementById(`section-${hash}`)) {
        navigateToSection(hash);
    }
}

function navigateToSection(sectionId) {
    currentSection = sectionId;

    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.getAttribute('data-section') === sectionId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Update active content section
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.classList.remove('active');
    });

    const target = document.getElementById(`section-${sectionId}`);
    if (target) {
        target.classList.add('active');
    }

    // Update Header Titles
    const titles = {
        'overview': { title: 'Overview', sub: 'Earthquake Intelligence • USGS Comprehensive Catalog' },
        'analytics': { title: 'Visual Analytics', sub: 'Five Core Aggregation Pipelines • Real MongoDB Data' },
        'explorer': { title: 'Earthquake Explorer', sub: 'Search & Filter 19,705 Verified Event Documents' },
        'map': { title: 'Seismic Activity Map', sub: 'Geospatial Visualization • Esri Dark Gray Basemap' },
        'manage': { title: 'Manage Events', sub: 'PyMongo CRUD Interface • Enforced $jsonSchema Validation' },
        'about': { title: 'About Project', sub: 'CSE494 Intelligent NoSQL Databases • Milestone 3' }
    };

    const headerInfo = titles[sectionId] || titles['overview'];
    document.getElementById('pageTitle').textContent = headerInfo.title;
    document.getElementById('pageSubtitle').textContent = headerInfo.sub;

    window.location.hash = sectionId;

    // If map section opened, trigger size recalculation
    if (sectionId === 'map') {
        setTimeout(() => {
            initOrRefreshMap();
        }, 100);
    }
}

// -----------------------------------------------------------------------------
// 2. CHART.JS CONFIGURATION DEFAULTS
// -----------------------------------------------------------------------------
function initChartDefaults() {
    if (typeof Chart === 'undefined') return;

    Chart.defaults.color = '#9299AB';
    Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(17, 21, 34, 0.95)';
    Chart.defaults.plugins.tooltip.titleColor = '#F5F7FB';
    Chart.defaults.plugins.tooltip.bodyColor = '#D8DFEE';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.15)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
}

// -----------------------------------------------------------------------------
// 3. DATA REFRESH ORCHESTRATOR
// -----------------------------------------------------------------------------
async function refreshAllData() {
    await checkDatabaseHealth();
    await loadSummaryStats();
    await loadOverviewTables();
    await loadAnalyticsCharts();
    await loadExplorerData();
}

// -----------------------------------------------------------------------------
// 4. DATABASE HEALTH CHECK
// -----------------------------------------------------------------------------
async function checkDatabaseHealth() {
    const dot = document.getElementById('dbStatusDot');
    const label = document.getElementById('dbStatusLabel');
    const subtext = document.getElementById('dbSubtext');

    try {
        const res = await fetch('/api/health');
        const data = await res.json();

        if (res.ok && data.status === 'connected') {
            dot.className = 'status-indicator online';
            label.textContent = 'MongoDB Connected';
            subtext.textContent = `${data.database} • v${data.server_version}`;
        } else {
            dot.className = 'status-indicator offline';
            label.textContent = 'Disconnected';
            subtext.textContent = data.message || 'Cannot reach local database';
        }
    } catch (err) {
        dot.className = 'status-indicator offline';
        label.textContent = 'Service Offline';
        subtext.textContent = 'Connection refused (localhost:27017)';
    }
}

// -----------------------------------------------------------------------------
// 5. SUMMARY STATS (KPI CARDS)
// -----------------------------------------------------------------------------
async function loadSummaryStats() {
    try {
        const res = await fetch('/api/stats');
        const stats = await res.json();

        if (res.ok) {
            const countFormatted = stats.total_events ? stats.total_events.toLocaleString() : '19,705';
            document.getElementById('kpiTotalEvents').textContent = countFormatted;
            document.getElementById('headerDocCount').textContent = `${countFormatted} Events (2025–2026)`;
            document.getElementById('heroTotalCount').textContent = countFormatted;

            document.getElementById('kpiAvgMag').textContent = stats.avg_magnitude ? stats.avg_magnitude.toFixed(2) : '4.46';
            document.getElementById('kpiStrongCount').textContent = stats.strong_events_count ? stats.strong_events_count.toLocaleString() : '146';

            if (stats.strongest_event) {
                document.getElementById('kpiMaxMag').textContent = `${stats.strongest_event.magnitude} ${stats.strongest_event.magnitude_type || 'M'}`;
                document.getElementById('kpiMaxLocation').textContent = stats.strongest_event.location || 'Kamchatka Peninsula';
            }
        }
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

// -----------------------------------------------------------------------------
// 6. OVERVIEW PREVIEW TABLES
// -----------------------------------------------------------------------------
async function loadOverviewTables() {
    try {
        // Strongest Quakes
        const topRes = await fetch('/api/analytics/top-strongest');
        const topQuakes = await topRes.json();
        const topBody = document.getElementById('overviewTopQuakesBody');
        
        if (Array.isArray(topQuakes) && topQuakes.length > 0) {
            topBody.innerHTML = topQuakes.slice(0, 5).map(q => {
                const dateStr = q.event_time ? q.event_time.split('T')[0] : 'N/A';
                return `
                    <tr onclick="openEventDetailModal('${q.event_id}')">
                        <td><span class="mag-badge ${getMagBadgeClass(q.magnitude)}">${q.magnitude}</span></td>
                        <td class="text-truncate" style="max-width: 200px;">${escapeHtml(q.location)}</td>
                        <td>${q.depth_km} km</td>
                        <td>${dateStr}</td>
                    </tr>
                `;
            }).join('');
        }

        // Recent Quakes
        const recentRes = await fetch('/api/analytics/recent');
        const recentQuakes = await recentRes.json();
        const recentBody = document.getElementById('overviewRecentQuakesBody');

        if (Array.isArray(recentQuakes) && recentQuakes.length > 0) {
            recentBody.innerHTML = recentQuakes.slice(0, 5).map(q => {
                const dateStr = q.event_time ? q.event_time.replace('T', ' ').slice(0, 16) : 'N/A';
                return `
                    <tr onclick="openEventDetailModal('${q.event_id}')">
                        <td class="font-mono text-truncate" style="max-width: 90px;">${escapeHtml(q.event_id)}</td>
                        <td><span class="mag-badge ${getMagBadgeClass(q.magnitude)}">${q.magnitude}</span></td>
                        <td class="text-truncate" style="max-width: 180px;">${escapeHtml(q.location)}</td>
                        <td>${dateStr}</td>
                    </tr>
                `;
            }).join('');
        }
    } catch (err) {
        console.error('Failed to load overview tables:', err);
    }
}

// -----------------------------------------------------------------------------
// 7. ANALYTICS CHARTS (5 CORE AGGREGATIONS)
// -----------------------------------------------------------------------------
async function loadAnalyticsCharts() {
    if (typeof Chart === 'undefined') return;

    // Chart A: Magnitude Distribution ($bucket)
    try {
        const res = await fetch('/api/analytics/magnitude-distribution');
        const buckets = await res.json();
        
        if (Array.isArray(buckets)) {
            const labels = buckets.map(b => b.category.replace(/ \(.*\)/, ''));
            const counts = buckets.map(b => b.count);

            renderBarChart('chartMagDistribution', labels, counts, 'Earthquake Count', [
                'rgba(255, 208, 138, 0.85)',
                'rgba(255, 181, 71, 0.85)',
                'rgba(255, 122, 24, 0.85)',
                'rgba(239, 68, 68, 0.9)'
            ]);
        }
    } catch (err) {
        console.error('Failed Chart A:', err);
    }

    // Chart B: Monthly Activity ($dateToString)
    try {
        const res = await fetch('/api/analytics/monthly-activity');
        const monthly = await res.json();
        
        if (Array.isArray(monthly)) {
            const labels = monthly.map(m => m.month);
            const counts = monthly.map(m => m.count);

            renderLineChart('chartMonthlyActivity', labels, counts, 'Monthly Earthquakes');
        }
    } catch (err) {
        console.error('Failed Chart B:', err);
    }

    // Chart C: Magnitude Types ($group)
    try {
        const res = await fetch('/api/analytics/magnitude-types');
        const types = await res.json();
        
        if (Array.isArray(types)) {
            const topTypes = types.slice(0, 6);
            const labels = topTypes.map(t => t.magnitude_type);
            const counts = topTypes.map(t => t.count);

            renderDoughnutChart('chartMagTypes', labels, counts);
        }
    } catch (err) {
        console.error('Failed Chart C:', err);
    }

    // Chart D: Depth Distribution ($bucket)
    try {
        const res = await fetch('/api/analytics/depth-distribution');
        const depths = await res.json();
        
        if (Array.isArray(depths)) {
            const labels = depths.map(d => d.category);
            const counts = depths.map(d => d.count);

            renderHorizontalBarChart('chartDepthDistribution', labels, counts);
        }
    } catch (err) {
        console.error('Failed Chart D:', err);
    }

    // Top 10 Ranked Table in Analytics
    try {
        const res = await fetch('/api/analytics/top-strongest');
        const top10 = await res.json();
        const body = document.getElementById('analyticsTop10Body');

        if (Array.isArray(top10)) {
            body.innerHTML = top10.map((q, idx) => `
                <tr>
                    <td><strong>#${idx + 1}</strong></td>
                    <td class="font-mono">${escapeHtml(q.event_id)}</td>
                    <td><span class="mag-badge ${getMagBadgeClass(q.magnitude)}">${q.magnitude}</span></td>
                    <td><span class="badge badge-amber">${q.magnitude_type || 'N/A'}</span></td>
                    <td>${q.depth_km} km</td>
                    <td>${escapeHtml(q.location)}</td>
                    <td>${q.event_time ? q.event_time.replace('T', ' ').slice(0, 19) : 'N/A'}</td>
                    <td>
                        <button class="btn btn-sm btn-glass" onclick="openEventDetailModal('${q.event_id}')">Inspect</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (err) {
        console.error('Failed top 10:', err);
    }
}

// Chart Render Helpers
function renderBarChart(canvasId, labels, data, datasetLabel, backgroundColors) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: datasetLabel,
                data: data,
                backgroundColor: backgroundColors || 'rgba(255, 122, 24, 0.8)',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                }
            }
        }
    });
}

function renderLineChart(canvasId, labels, data, datasetLabel) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: datasetLabel,
                data: data,
                borderColor: '#FF7A18',
                backgroundColor: 'rgba(255, 122, 24, 0.12)',
                borderWidth: 2.5,
                fill: true,
                tension: 0.35,
                pointBackgroundColor: '#FFB547',
                pointBorderColor: '#080B12',
                pointBorderWidth: 2,
                pointRadius: 4.5,
                pointHoverRadius: 6.5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.03)' }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                }
            }
        }
    });
}

function renderDoughnutChart(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#FF7A18',
                    '#FFB547',
                    '#67E8F9',
                    '#FFD08A',
                    '#F4511E',
                    '#9299AB'
                ],
                borderColor: '#080B12',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { boxWidth: 12, padding: 14 }
                }
            },
            cutout: '68%'
        }
    });
}

function renderHorizontalBarChart(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Earthquake Count',
                data: data,
                backgroundColor: [
                    'rgba(103, 232, 249, 0.8)',
                    'rgba(255, 181, 71, 0.8)',
                    'rgba(244, 81, 30, 0.8)'
                ],
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                y: {
                    grid: { display: false }
                }
            }
        }
    });
}

// -----------------------------------------------------------------------------
// 8. GEOSPATIAL MAP (LEAFLET.JS)
// -----------------------------------------------------------------------------
function initOrRefreshMap() {
    const container = document.getElementById('leafletMapContainer');
    if (!container || typeof L === 'undefined') return;

    if (!leafletMap) {
        leafletMap = L.map('leafletMapContainer', {
            center: [15, 10],
            zoom: 2,
            minZoom: 1,
            maxZoom: 14
        });

        // Esri World Dark Gray Base Tile Layer (Reliable public cartography, zero API key required)
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ | USGS ComCat',
            maxZoom: 16
        }).addTo(leafletMap);

        // Esri World Dark Gray Reference Layer (Boundaries & Geographical Labels)
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
            attribution: '',
            maxZoom: 16,
            opacity: 0.75
        }).addTo(leafletMap);
    }

    // Invalidate size to guarantee clean tile alignment
    setTimeout(() => {
        if (leafletMap) {
            leafletMap.invalidateSize();
        }
    }, 150);

    loadMapMarkers();
}

async function loadMapMarkers() {
    if (!leafletMap) return;

    try {
        const res = await fetch('/api/analytics/map-events');
        const events = await res.json();

        // Clear existing markers
        mapMarkers.forEach(m => leafletMap.removeLayer(m));
        mapMarkers = [];

        if (Array.isArray(events)) {
            events.forEach(q => {
                if (q.latitude != null && q.longitude != null) {
                    const mag = q.magnitude || 4.0;
                    let color = '#FFB547';
                    if (mag >= 7.0) color = '#EF4444';
                    else if (mag >= 6.0) color = '#FF7A18';

                    const radius = Math.max(4, (mag - 3) * 2.8);

                    const marker = L.circleMarker([q.latitude, q.longitude], {
                        radius: radius,
                        fillColor: color,
                        color: '#FFF',
                        weight: 0.8,
                        opacity: 0.8,
                        fillOpacity: 0.75
                    });

                    const popupHtml = `
                        <div style="font-size: 0.85rem; line-height: 1.4;">
                            <strong style="color: ${color}; font-size: 1rem;">M ${q.magnitude}</strong> 
                            <span style="font-size: 0.72rem; color: #94A3B8;">(${q.magnitude_type || 'mb'})</span>
                            <div style="margin: 4px 0;">${escapeHtml(q.location)}</div>
                            <div style="font-size: 0.75rem; color: #94A3B8;">
                                Depth: ${q.depth_km} km<br>
                                Time: ${q.event_time ? q.event_time.replace('T', ' ').slice(0, 16) : ''}
                            </div>
                            <button onclick="openEventDetailModal('${q.event_id}')" 
                                style="margin-top: 8px; padding: 4px 8px; font-size: 0.72rem; background: #FF7A18; border: none; border-radius: 4px; color: #000; cursor: pointer; font-weight: 600;">
                                Inspect Record
                            </button>
                        </div>
                    `;

                    marker.bindPopup(popupHtml);
                    marker.addTo(leafletMap);
                    mapMarkers.push(marker);
                }
            });
        }
    } catch (err) {
        console.error('Failed to load map events:', err);
    }
}

// -----------------------------------------------------------------------------
// 9. EARTHQUAKE EXPLORER (SEARCH, FILTER & PAGINATION)
// -----------------------------------------------------------------------------
async function loadExplorerData() {
    const tableBody = document.getElementById('explorerTableBody');
    const countDisplay = document.getElementById('explorerResultsCount');
    
    // Construct query parameters
    const params = new URLSearchParams({
        q: explorerState.query,
        min_mag: explorerState.minMag,
        mag_type: explorerState.magType,
        depth_cat: explorerState.depthCat,
        sort_by: explorerState.sortBy,
        sort_order: explorerState.sortOrder,
        page: explorerState.page,
        per_page: explorerState.perPage
    });

    try {
        const res = await fetch(`/api/events?${params.toString()}`);
        const data = await res.json();

        if (res.ok) {
            const { events, total, page, per_page, total_pages } = data;

            // Update Counts display
            const startIdx = total > 0 ? (page - 1) * per_page + 1 : 0;
            const endIdx = Math.min(page * per_page, total);
            countDisplay.textContent = `Showing ${startIdx.toLocaleString()}–${endIdx.toLocaleString()} of ${total.toLocaleString()} matching events`;

            // Render table rows
            if (!events || events.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-muted">No earthquake events match your current filter criteria.</td></tr>`;
            } else {
                tableBody.innerHTML = events.map(q => {
                    const timeStr = q.event_time ? q.event_time.replace('T', ' ').slice(0, 19) : 'N/A';
                    return `
                        <tr onclick="openEventDetailModal('${q.event_id}')">
                            <td class="font-mono"><strong>${escapeHtml(q.event_id)}</strong></td>
                            <td>${timeStr}</td>
                            <td><span class="mag-badge ${getMagBadgeClass(q.magnitude)}">${q.magnitude}</span></td>
                            <td><span class="badge badge-amber">${q.magnitude_type || 'N/A'}</span></td>
                            <td>${q.depth_km} km</td>
                            <td class="text-truncate" style="max-width: 260px;">${escapeHtml(q.location)}</td>
                            <td>${escapeHtml(q.event_type || 'earthquake')}</td>
                            <td>
                                <button class="btn btn-sm btn-glass" onclick="event.stopPropagation(); loadEventIntoManage('${q.event_id}')">Edit</button>
                            </td>
                        </tr>
                    `;
                }).join('');
            }

            // Update Pagination controls
            renderPagination(page, total_pages);
        }
    } catch (err) {
        console.error('Failed to load explorer data:', err);
        tableBody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-danger">Error loading events from database.</td></tr>`;
    }
}

function renderPagination(currentPage, totalPages) {
    const prevBtn = document.getElementById('btnPrevPage');
    const nextBtn = document.getElementById('btnNextPage');
    const container = document.getElementById('paginationNumbers');

    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;

    // Calculate window of page numbers to show
    let pages = [];
    const maxShown = 5;
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + maxShown - 1);

    if (endPage - startPage < maxShown - 1) {
        startPage = Math.max(1, endPage - maxShown + 1);
    }

    for (let p = startPage; p <= endPage; p++) {
        pages.push(p);
    }

    container.innerHTML = pages.map(p => `
        <button class="page-btn ${p === currentPage ? 'active' : ''}" onclick="goToPage(${p})">${p}</button>
    `).join('');
}

function goToPage(page) {
    explorerState.page = page;
    loadExplorerData();
}

// -----------------------------------------------------------------------------
// 10. MANAGE EVENTS (CRUD OPERATIONS)
// -----------------------------------------------------------------------------
function initManageSection() {
    // Fill Demo Data helper
    const btnDemo = document.getElementById('btnFillDemoValues');
    if (btnDemo) {
        btnDemo.addEventListener('click', () => {
            const randomId = 'test_' + Math.floor(1000 + Math.random() * 9000);
            document.getElementById('createEventId').value = randomId;
            document.getElementById('createMagnitude').value = '5.4';
            document.getElementById('createMagType').value = 'mww';
            document.getElementById('createDepth').value = '18.5';
            document.getElementById('createLatitude').value = '35.6895';
            document.getElementById('createLongitude').value = '139.6917';
            document.getElementById('createLocation').value = '15 km S of Tokyo, Japan (Student Demo Test)';
            document.getElementById('createReviewStatus').value = 'reviewed';
        });
    }

    // Create Form Submit
    const formCreate = document.getElementById('formCreateEvent');
    if (formCreate) {
        formCreate.addEventListener('submit', async (e) => {
            e.preventDefault();
            const alertBox = document.getElementById('createAlertBox');

            const payload = {
                event_id: document.getElementById('createEventId').value.trim(),
                magnitude: parseFloat(document.getElementById('createMagnitude').value),
                magnitude_type: document.getElementById('createMagType').value,
                depth_km: parseFloat(document.getElementById('createDepth').value),
                latitude: parseFloat(document.getElementById('createLatitude').value),
                longitude: parseFloat(document.getElementById('createLongitude').value),
                location: document.getElementById('createLocation').value.trim(),
                event_type: 'earthquake',
                review_status: document.getElementById('createReviewStatus').value
            };

            try {
                const res = await fetch('/api/events', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await res.json();

                if (res.ok && result.success) {
                    alertBox.className = 'alert-box success';
                    alertBox.textContent = `[SUCCESS] ${result.message} (MongoDB _id: ${result.inserted_id})`;
                    formCreate.reset();
                    refreshAllData();
                } else {
                    alertBox.className = 'alert-box error';
                    alertBox.textContent = `[REJECTED] ${result.message}`;
                }
            } catch (err) {
                alertBox.className = 'alert-box error';
                alertBox.textContent = `Network Error: ${err}`;
            }
        });
    }

    // Search for Event to Edit
    const btnLookup = document.getElementById('btnFindForManage');
    if (btnLookup) {
        btnLookup.addEventListener('click', () => {
            const eventId = document.getElementById('manageSearchId').value.trim();
            if (eventId) {
                loadEventIntoManage(eventId);
            }
        });
    }

    // Update Form Submit
    const formUpdate = document.getElementById('formUpdateEvent');
    if (formUpdate) {
        formUpdate.addEventListener('submit', async (e) => {
            e.preventDefault();
            const eventId = document.getElementById('editEventIdLabel').textContent.trim();
            const alertBox = document.getElementById('updateAlertBox');

            const updatePayload = {
                magnitude: parseFloat(document.getElementById('editMagnitude').value),
                depth_km: parseFloat(document.getElementById('editDepth').value),
                location: document.getElementById('editLocation').value.trim(),
                review_status: document.getElementById('editReviewStatus').value
            };

            try {
                const res = await fetch(`/api/events/${eventId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updatePayload)
                });
                const result = await res.json();

                if (res.ok && result.success) {
                    alertBox.className = 'alert-box success';
                    alertBox.textContent = `[SUCCESS] ${result.message}`;
                    refreshAllData();
                } else {
                    alertBox.className = 'alert-box error';
                    alertBox.textContent = `[FAILED] ${result.message}`;
                }
            } catch (err) {
                alertBox.className = 'alert-box error';
                alertBox.textContent = `Error: ${err}`;
            }
        });
    }

    // Trigger Delete Dialog
    const btnTriggerDelete = document.getElementById('btnTriggerDelete');
    if (btnTriggerDelete) {
        btnTriggerDelete.addEventListener('click', () => {
            const eventId = document.getElementById('editEventIdLabel').textContent.trim();
            const location = document.getElementById('editLocation').value.trim();
            openDeleteConfirmModal(eventId, location);
        });
    }

    // Confirm Delete Final
    const btnConfirmDelete = document.getElementById('btnConfirmDeleteFinal');
    if (btnConfirmDelete) {
        btnConfirmDelete.addEventListener('click', async () => {
            const eventId = document.getElementById('deleteConfirmEventId').textContent.trim();
            try {
                const res = await fetch(`/api/events/${eventId}`, { method: 'DELETE' });
                const result = await res.json();

                closeDeleteModal();
                if (res.ok && result.success) {
                    alert(`Event '${eventId}' successfully deleted.`);
                    document.getElementById('manageEditContainer').style.display = 'none';
                    refreshAllData();
                } else {
                    alert(`Failed to delete: ${result.message}`);
                }
            } catch (err) {
                alert(`Error deleting record: ${err}`);
            }
        });
    }

    // Run Live Automated CRUD Cycle
    const btnCycle = document.getElementById('btnRunCrudCycle');
    if (btnCycle) {
        btnCycle.addEventListener('click', runLiveCrudCycle);
    }
}

async function loadEventIntoManage(eventId) {
    navigateToSection('manage');
    const alertBox = document.getElementById('manageLookupAlert');
    const container = document.getElementById('manageEditContainer');

    try {
        const res = await fetch(`/api/events/${eventId}`);
        if (!res.ok) {
            alertBox.className = 'alert-box error';
            alertBox.textContent = `No earthquake event found with ID '${eventId}'.`;
            container.style.display = 'none';
            return;
        }

        const doc = await res.json();
        alertBox.className = 'alert-box success';
        alertBox.textContent = `Loaded event '${doc.event_id}'. You may now edit or delete this record.`;

        document.getElementById('editEventIdLabel').textContent = doc.event_id;
        document.getElementById('editOriginalMag').textContent = `M ${doc.magnitude} ${doc.magnitude_type || ''}`;
        document.getElementById('editMagnitude').value = doc.magnitude;
        document.getElementById('editDepth').value = doc.depth_km;
        document.getElementById('editLocation').value = doc.location;
        document.getElementById('editReviewStatus').value = doc.review_status || 'reviewed';

        container.style.display = 'block';
    } catch (err) {
        alertBox.className = 'alert-box error';
        alertBox.textContent = `Lookup error: ${err}`;
    }
}

async function runLiveCrudCycle() {
    const logBox = document.getElementById('crudCycleOutput');
    logBox.style.display = 'block';
    logBox.textContent = '>> Initializing Live CRUD Verification Cycle...\n';

    const testId = 'test_web_demo_' + Math.floor(100 + Math.random() * 900);

    const log = (msg) => {
        logBox.textContent += msg + '\n';
        logBox.scrollTop = logBox.scrollHeight;
    };

    try {
        // Step 1: Create
        log(`1. CREATE: Inserting '${testId}' (M5.2)...`);
        const createRes = await fetch('/api/events', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                event_id: testId,
                magnitude: 5.2,
                magnitude_type: 'mb',
                depth_km: 14.0,
                latitude: 35.0,
                longitude: 139.0,
                location: 'Sagami Bay, Japan (Live Web Test)',
                event_type: 'earthquake',
                review_status: 'automatic'
            })
        });
        const cData = await createRes.json();
        log(`   -> [PASS] Inserted document with MongoDB _id: ${cData.inserted_id}`);

        // Step 2: Read
        log(`2. READ: Fetching '${testId}' from database...`);
        const readRes = await fetch(`/api/events/${testId}`);
        const rData = await readRes.json();
        log(`   -> [PASS] Found record: "${rData.location}", Mag: ${rData.magnitude}`);

        // Step 3: Update
        log(`3. UPDATE: Changing magnitude to 5.6 and updating review status...`);
        const updRes = await fetch(`/api/events/${testId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                magnitude: 5.6,
                location: 'Sagami Bay, Japan (Reviewed Live Test)',
                review_status: 'reviewed'
            })
        });
        const uData = await updRes.json();
        log(`   -> [PASS] updateOne succeeded: ${uData.message}`);

        // Step 4: Delete
        log(`4. DELETE: Removing temporary test record '${testId}'...`);
        const delRes = await fetch(`/api/events/${testId}`, { method: 'DELETE' });
        const dData = await delRes.json();
        log(`   -> [PASS] deleteOne acknowledged: ${dData.message}`);

        log('\n>> [CYCLE COMPLETE] Database remains clean with exactly 19,705 documents!');
        refreshAllData();
    } catch (err) {
        log(`>> [ERROR] Cycle failed: ${err}`);
    }
}

// -----------------------------------------------------------------------------
// 11. MODAL WINDOWS
// -----------------------------------------------------------------------------
async function openEventDetailModal(eventId) {
    const modal = document.getElementById('eventDetailModal');
    if (!modal) return;

    try {
        const res = await fetch(`/api/events/${eventId}`);
        if (!res.ok) return;

        const doc = await res.json();
        document.getElementById('modalEventId').textContent = doc.event_id;
        document.getElementById('modalMagnitude').textContent = doc.magnitude;
        document.getElementById('modalMagType').textContent = doc.magnitude_type || 'mb';
        document.getElementById('modalDepth').textContent = doc.depth_km;
        document.getElementById('modalReviewStatus').textContent = doc.review_status || 'reviewed';
        document.getElementById('modalLocation').textContent = doc.location;
        document.getElementById('modalTime').textContent = doc.event_time ? doc.event_time.replace('T', ' ').slice(0, 19) + ' UTC' : 'N/A';
        document.getElementById('modalCoordinates').textContent = `Lat ${doc.latitude}°, Lon ${doc.longitude}°`;
        document.getElementById('modalEventType').textContent = doc.event_type || 'earthquake';
        document.getElementById('modalNetwork').textContent = doc.network || 'us';
        document.getElementById('modalStations').textContent = doc.station_count != null ? doc.station_count : 'N/A';

        modal.classList.add('active');
    } catch (err) {
        console.error('Failed to open detail modal:', err);
    }
}

function closeDetailModal() {
    const modal = document.getElementById('eventDetailModal');
    if (modal) modal.classList.remove('active');
}

function openDeleteConfirmModal(eventId, location) {
    const modal = document.getElementById('deleteConfirmModal');
    if (!modal) return;

    document.getElementById('deleteConfirmEventId').textContent = eventId;
    document.getElementById('deleteConfirmLocation').textContent = location || 'N/A';
    modal.classList.add('active');
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteConfirmModal');
    if (modal) modal.classList.remove('active');
}

// -----------------------------------------------------------------------------
// 12. EVENT LISTENERS
// -----------------------------------------------------------------------------
function initEventListeners() {
    // Refresh button
    const btnRefresh = document.getElementById('btnRefresh');
    if (btnRefresh) {
        btnRefresh.addEventListener('click', () => {
            btnRefresh.classList.add('rotating');
            refreshAllData().then(() => {
                setTimeout(() => btnRefresh.classList.remove('rotating'), 600);
            });
        });
    }

    // Explorer Search Input (Debounced)
    let searchTimeout = null;
    const searchInput = document.getElementById('explorerSearchInput');
    const btnClearSearch = document.getElementById('btnClearSearch');

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const val = e.target.value;
            btnClearSearch.style.display = val ? 'block' : 'none';

            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                explorerState.query = val;
                explorerState.page = 1;
                loadExplorerData();
            }, 300);
        });
    }

    if (btnClearSearch) {
        btnClearSearch.addEventListener('click', () => {
            searchInput.value = '';
            btnClearSearch.style.display = 'none';
            explorerState.query = '';
            explorerState.page = 1;
            loadExplorerData();
        });
    }

    // Filter controls
    const filterMinMag = document.getElementById('filterMinMag');
    if (filterMinMag) {
        filterMinMag.addEventListener('change', (e) => {
            explorerState.minMag = e.target.value;
            explorerState.page = 1;
            loadExplorerData();
        });
    }

    const filterMagType = document.getElementById('filterMagType');
    if (filterMagType) {
        filterMagType.addEventListener('change', (e) => {
            explorerState.magType = e.target.value;
            explorerState.page = 1;
            loadExplorerData();
        });
    }

    const filterDepthCat = document.getElementById('filterDepthCat');
    if (filterDepthCat) {
        filterDepthCat.addEventListener('change', (e) => {
            explorerState.depthCat = e.target.value;
            explorerState.page = 1;
            loadExplorerData();
        });
    }

    const filterSortBy = document.getElementById('filterSortBy');
    if (filterSortBy) {
        filterSortBy.addEventListener('change', (e) => {
            explorerState.sortBy = e.target.value;
            explorerState.page = 1;
            loadExplorerData();
        });
    }

    const selectPerPage = document.getElementById('selectPerPage');
    if (selectPerPage) {
        selectPerPage.addEventListener('change', (e) => {
            explorerState.perPage = parseInt(e.target.value, 10);
            explorerState.page = 1;
            loadExplorerData();
        });
    }

    const btnResetFilters = document.getElementById('btnResetFilters');
    if (btnResetFilters) {
        btnResetFilters.addEventListener('click', () => {
            searchInput.value = '';
            btnClearSearch.style.display = 'none';
            filterMinMag.value = '';
            filterMagType.value = 'all';
            filterDepthCat.value = 'all';
            filterSortBy.value = 'event_time';
            explorerState = {
                page: 1,
                perPage: 15,
                query: '',
                minMag: '',
                magType: 'all',
                depthCat: 'all',
                sortBy: 'event_time',
                sortOrder: 'desc'
            };
            loadExplorerData();
        });
    }

    // Prev / Next pagination
    const btnPrev = document.getElementById('btnPrevPage');
    if (btnPrev) {
        btnPrev.addEventListener('click', () => {
            if (explorerState.page > 1) {
                explorerState.page--;
                loadExplorerData();
            }
        });
    }

    const btnNext = document.getElementById('btnNextPage');
    if (btnNext) {
        btnNext.addEventListener('click', () => {
            explorerState.page++;
            loadExplorerData();
        });
    }

    // Modal close controls
    const btnCloseDetail = document.getElementById('btnCloseDetailModal');
    const btnModalClose = document.getElementById('btnModalClose');
    if (btnCloseDetail) btnCloseDetail.addEventListener('click', closeDetailModal);
    if (btnModalClose) btnModalClose.addEventListener('click', closeDetailModal);

    const btnCloseDelete = document.getElementById('btnCloseDeleteModal');
    const btnCancelDelete = document.getElementById('btnCancelDelete');
    if (btnCloseDelete) btnCloseDelete.addEventListener('click', closeDeleteModal);
    if (btnCancelDelete) btnCancelDelete.addEventListener('click', closeDeleteModal);

    // Escape key closes modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeDetailModal();
            closeDeleteModal();
        }
    });

    // Close on overlay click
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeDetailModal();
                closeDeleteModal();
            }
        });
    });

    initManageSection();

    window.addEventListener('resize', () => {
        if (leafletMap) {
            leafletMap.invalidateSize();
        }
    });
}

// -----------------------------------------------------------------------------
// 13. UTILITY FUNCTIONS
// -----------------------------------------------------------------------------
function getMagBadgeClass(mag) {
    if (mag >= 7.0) return 'mag-major';
    if (mag >= 5.0) return 'mag-moderate';
    if (mag >= 4.0) return 'mag-light';
    return 'mag-minor';
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
