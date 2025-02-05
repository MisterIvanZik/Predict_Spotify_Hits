// Éléments du DOM
const continentSelect = document.getElementById('continentSelect');
const countrySelect = document.getElementById('countrySelect');
const topTracks = document.getElementById('topTracks');
const trackTemplate = document.getElementById('trackRowTemplate');
const statsContainer = document.getElementById('statsContainer');
let popularityChart = null;

// État de l'application
let currentContinent = '';
let currentCountry = '';

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    loadContinents();
    setupEventListeners();
});

// Configuration des écouteurs d'événements
function setupEventListeners() {
    continentSelect.addEventListener('change', handleContinentChange);
    countrySelect.addEventListener('change', handleCountryChange);
    
    // Écouteurs pour la recherche
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    
    searchButton.addEventListener('click', () => handleSearch(searchInput.value));
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch(searchInput.value);
        }
    });
}

// Gestionnaire de recherche
async function handleSearch(query) {
    if (!query.trim()) return;

    const searchResults = document.getElementById('searchResults');
    searchResults.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div></div>';

    try {
        const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
        const results = await response.json();

        if (results.length === 0) {
            searchResults.innerHTML = '<div class="alert alert-info">Aucun résultat trouvé</div>';
            return;
        }

        searchResults.innerHTML = '';
        results.forEach(track => {
            const trackRow = trackTemplate.content.cloneNode(true);

            const image = trackRow.querySelector('.track-image');
            image.src = track.track_image || 'path/to/default/image.png';
            image.alt = track.track_name;

            trackRow.querySelector('.track-name').textContent = track.track_name;
            trackRow.querySelector('.artist-name').textContent = track.artist_names;

            const streams = formatNumber(track.streams);
            trackRow.querySelector('.streams').textContent = `${streams} écoutes`;

            const popularity = track.popularity;
            trackRow.querySelector('.popularity-badge').textContent = 
                `Popularité: ${popularity}%`;

            const container = trackRow.querySelector('.d-flex');
            container.classList.add('track-row', 'search-result');

            searchResults.appendChild(trackRow);
        });
    } catch (error) {
        console.error('Erreur lors de la recherche:', error);
        searchResults.innerHTML = '<div class="alert alert-danger">Une erreur est survenue lors de la recherche</div>';
    }
}

// Chargement des continents
async function loadContinents() {
    try {
        const response = await fetch('/api/continents');
        const continents = await response.json();
        
        continentSelect.innerHTML = `
            <option value="">Choisissez un continent</option>
            ${continents.map(continent => 
                `<option value="${continent}">${continent}</option>`
            ).join('')}
        `;
    } catch (error) {
        console.error('Erreur lors du chargement des continents:', error);
        showError('Impossible de charger les continents');
    }
}

// Gestion du changement de continent
async function handleContinentChange() {
    const selectedContinent = continentSelect.value;
    currentContinent = selectedContinent;
    
    if (!selectedContinent) {
        countrySelect.disabled = true;
        countrySelect.innerHTML = '<option value="">Choisissez d\'abord un continent</option>';
        return;
    }

    try {
        const response = await fetch(`/api/countries/${selectedContinent}`);
        const countries = await response.json();
        
        countrySelect.innerHTML = `
            <option value="">Choisissez un pays</option>
            ${countries.map(country => 
                `<option value="${country.code}">${country.code} ${country.flag}</option>`
            ).join('')}
        `;
        countrySelect.disabled = false;
    } catch (error) {
        console.error('Erreur lors du chargement des pays:', error);
        showError('Impossible de charger les pays');
    }
}

// Gestion du changement de pays
async function handleCountryChange() {
    const selectedCountry = countrySelect.value;
    currentCountry = selectedCountry;
    
    if (!selectedCountry) return;
    
    try {
        const response = await fetch(`/api/charts/${currentContinent}/${selectedCountry}`);
        const data = await response.json();
        
        updateTopTracks(data.top_tracks);
        updatePopularityChart(data.popularity_trends);
        updateStats(data.top_tracks);
    } catch (error) {
        console.error('Erreur lors du chargement des données:', error);
        showError('Impossible de charger les données');
    }
}

// Mise à jour du top 10 des morceaux
function updateTopTracks(tracks) {
    topTracks.innerHTML = '';
    
    tracks.forEach((track, index) => {
        const trackRow = trackTemplate.content.cloneNode(true);
        
        const image = trackRow.querySelector('.track-image');
        image.src = track.track_image || 'path/to/default/image.png';
        image.alt = track.track_name;
        
        trackRow.querySelector('.track-name').textContent = track.track_name;
        trackRow.querySelector('.artist-name').textContent = track.artist_names;
        
        const streams = formatNumber(track.streams);
        trackRow.querySelector('.streams').textContent = `${streams} écoutes`;
        
        const popularity = track.popularity;
        trackRow.querySelector('.popularity-badge').textContent = 
            `Popularité: ${popularity}%`;
        
        const container = trackRow.querySelector('.d-flex');
        container.classList.add('track-row');
        container.style.animationDelay = `${index * 0.1}s`;
        
        topTracks.appendChild(trackRow);
    });
}

// Mise à jour du graphique de popularité
function updatePopularityChart(trends) {
    if (popularityChart) {
        popularityChart.destroy();
    }

    const ctx = document.getElementById('popularityChart').getContext('2d');
    popularityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: trends.map(trend => trend.week_date),
            datasets: [{
                label: 'Popularité moyenne',
                data: trends.map(trend => trend.popularity),
                borderColor: '#1DB954',
                backgroundColor: 'rgba(29, 185, 84, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#FFFFFF'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#FFFFFF'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#FFFFFF'
                    }
                }
            }
        }
    });
}

// Mise à jour des statistiques
function updateStats(tracks) {
    const totalStreams = tracks.reduce((sum, track) => sum + track.streams, 0);
    const avgPopularity = Math.round(
        tracks.reduce((sum, track) => sum + track.popularity, 0) / tracks.length
    );
    
    statsContainer.innerHTML = `
        <div class="col-md-6 col-lg-3">
            <div class="stat-card">
                <div class="stat-value">${formatNumber(totalStreams)}</div>
                <div class="stat-label">Total des écoutes</div>
            </div>
        </div>
        <div class="col-md-6 col-lg-3">
            <div class="stat-card">
                <div class="stat-value">${avgPopularity}%</div>
                <div class="stat-label">Popularité moyenne</div>
            </div>
        </div>
    `;
}

// Utilitaires
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function showError(message) {
    // TODO: Implémenter un système de notification d'erreur
    console.error(message);
}
