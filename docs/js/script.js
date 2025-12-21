// Theme Management
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('themeIcon');
    icon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// Initialize Theme
const savedTheme = localStorage.getItem('theme') ||
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
document.documentElement.setAttribute('data-theme', savedTheme);
updateThemeIcon(savedTheme);

// Mobile Menu
function toggleMenu() {
    const nav = document.getElementById('navMenu');
    nav.classList.toggle('active');
}

// Smooth Scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
        // Close mobile menu if open
        document.getElementById('navMenu').classList.remove('active');
    });
});

// Guide Tabs
function showGuide(tabId) {
    // Hide all contents
    document.querySelectorAll('.guide-content').forEach(content => {
        content.classList.remove('active');
    });

    // Deactivate all tabs
    document.querySelectorAll('.guide-tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected content and activate tab
    document.getElementById('guide-' + tabId).classList.add('active');
    event.currentTarget.classList.add('active');
}

// FAQ Accordion
function toggleFaq(element) {
    const item = element.parentElement;
    const wasActive = item.classList.contains('active');

    // Close all items
    document.querySelectorAll('.faq-item').forEach(i => {
        i.classList.remove('active');
    });

    // Open clicked item if it wasn't active
    if (!wasActive) {
        item.classList.add('active');
    }
}

// Installation Guide Tabs
function showInstallGuide(os) {
    // Hide all guides
    ['windows', 'macos', 'linux'].forEach(sys => {
        document.getElementById('guide-' + sys).style.display = 'none';
    });

    // Show selected guide
    document.getElementById('guide-' + os).style.display = 'block';

    // Update buttons
    document.querySelectorAll('#installation .btn').forEach(btn => {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-secondary');
    });
    event.currentTarget.classList.remove('btn-secondary');
    event.currentTarget.classList.add('btn-primary');
}

// Antivirus Instructions
const antivirusData = {
    'defender': `
        <h4>Windows Defender</h4>
        <ol>
            <li>Cliquez sur "Informations complémentaires" dans la fenêtre bleue.</li>
            <li>Cliquez sur le bouton "Exécuter quand même".</li>
        </ol>`,
    'avast': `
        <h4>Avast / AVG</h4>
        <ol>
            <li>Ouvrez l'interface d'Avast.</li>
            <li>Allez dans Menu > Paramètres > Exceptions.</li>
            <li>Ajoutez le dossier de l'application aux exceptions.</li>
        </ol>`,
    'norton': `
        <h4>Norton</h4>
        <ol>
            <li>Dans la fenêtre d'alerte, cliquez sur "Voir les détails".</li>
            <li>Sélectionnez "Faire confiance à ce fichier".</li>
        </ol>`
};

function showAntivirusInstructions(antivirus) {
    const container = document.getElementById('antivirusInstructions');
    if (antivirus && antivirusData[antivirus]) {
        container.innerHTML = `<div class="alert alert-info">${antivirusData[antivirus]}</div>`;
    } else {
        container.innerHTML = '';
    }
}

// GitHub Release & OS Detection
async function fetchLatestRelease() {
    try {
        const response = await fetch('https://api.github.com/repos/mdjabi2005-commits/gestion-financiere_little/releases/latest');
        const data = await response.json();

        const releaseBox = document.getElementById('releaseBox');
        const date = new Date(data.published_at).toLocaleDateString('fr-FR');

        let html = `
            <div class="release-header">
                <span class="release-version">${data.tag_name}</span>
                <span class="release-date">Publié le ${date}</span>
            </div>
            <p>${data.body.split('\n')[0]}</p>
            <div class="download-buttons">
        `;

        data.assets.forEach(asset => {
            let icon = '📦';
            let name = 'Autre';

            if (asset.name.includes('.exe') || asset.name.includes('Windows')) {
                icon = '🪟';
                name = 'Windows (.exe)';
            } else if (asset.name.includes('Linux')) {
                icon = '🐧';
                name = 'Linux';
            } else if (asset.name.includes('Mac') || asset.name.includes('dmg')) {
                icon = '🍎';
                name = 'macOS';
            }

            html += `
                <a href="${asset.browser_download_url}" class="btn btn-primary" style="display: flex; align-items: center; gap: 0.5rem;">
                    <span>${icon}</span>
                    <span>${name}</span>
                </a>
            `;
        });

        html += '</div>';
        releaseBox.innerHTML = html;

    } catch (error) {
        console.error('Erreur GitHub:', error);
        document.getElementById('releaseBox').innerHTML = `
            <div class="alert alert-warning">
                Impossible de charger la dernière version. 
                <a href="https://github.com/mdjabi2005-commits/gestion-financiere_little/releases/latest" target="_blank">Voir sur GitHub</a>
            </div>
        `;
    }
}

function detectOS() {
    const platform = navigator.platform.toLowerCase();
    const userAgent = navigator.userAgent.toLowerCase();
    let os = 'Inconnu';
    let icon = '❓';

    if (platform.includes('win') || userAgent.includes('windows')) {
        os = 'Windows';
        icon = '🪟';
        showInstallGuide('windows');
    } else if (platform.includes('mac') || userAgent.includes('macintosh')) {
        os = 'macOS';
        icon = '🍎';
        showInstallGuide('macos');
    } else if (platform.includes('linux') || userAgent.includes('linux')) {
        os = 'Linux';
        icon = '🐧';
        showInstallGuide('linux');
    }

    const osDetected = document.getElementById('osDetected');
    if (osDetected) {
        osDetected.style.display = 'flex';
        document.getElementById('detectedOS').textContent = os;
        document.querySelector('.os-detected-icon').textContent = icon;
    }
}

function autoDownloadLatest() {
    document.getElementById('telecharger').scrollIntoView({ behavior: 'smooth' });
}

function scrollToDownload() {
    document.getElementById('telecharger').scrollIntoView({ behavior: 'smooth' });
}

// Feedback Form
function submitFeedback(event) {
    event.preventDefault();
    const btn = event.target.querySelector('button[type="submit"]');
    const originalText = btn.textContent;

    btn.textContent = 'Envoi en cours...';
    btn.disabled = true;

    // Simulate API call
    setTimeout(() => {
        btn.textContent = '✅ Merci pour votre avis !';
        btn.style.backgroundColor = 'var(--success)';
        event.target.reset();

        setTimeout(() => {
            btn.textContent = originalText;
            btn.disabled = false;
            btn.style.backgroundColor = '';
        }, 3000);
    }, 1500);
}

// Rating Stars
document.querySelectorAll('.rating-star').forEach(star => {
    star.addEventListener('click', function () {
        const value = this.dataset.value;
        const parent = this.parentElement;

        parent.querySelectorAll('.rating-star').forEach(s => {
            s.classList.remove('active');
            if (s.dataset.value <= value) {
                s.classList.add('active');
            }
        });
    });
});

// Scroll to Top
window.onscroll = function () {
    const btn = document.getElementById('scrollTop');
    if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
        btn.classList.add('visible');
    } else {
        btn.classList.remove('visible');
    }
};

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    detectOS();
    fetchLatestRelease();
});
