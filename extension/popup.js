// Popup script
document.addEventListener('DOMContentLoaded', () => {
    loadUrls();

    document.getElementById('copyBtn').addEventListener('click', copyJson);
    document.getElementById('exportBtn').addEventListener('click', exportJson);
    document.getElementById('clearBtn').addEventListener('click', clearUrls);
});

function loadUrls() {
    chrome.runtime.sendMessage({ action: 'getUrls' }, (response) => {
        const urls = response.urls || [];
        updateUI(urls);
    });
}

function updateUI(urls) {
    const countEl = document.getElementById('count');
    const listEl = document.getElementById('urlList');

    countEl.textContent = urls.length;

    if (urls.length === 0) {
        listEl.innerHTML = '<div class="empty">No URLs captured yet.<br>Click on videos in SharePoint!</div>';
    } else {
        listEl.innerHTML = urls.map((url, i) => `
            <div class="url-item">
                <span class="num">#${i + 1}</span> ${url.substring(0, 80)}...
            </div>
        `).join('');
    }
}

function generateJson(urls) {
    const manifest = {
        "AdvanceCyberSecurity": urls.map((url, i) => ({
            "name": `Lecture_${String(i + 1).padStart(2, '0')}`,
            "url": url
        }))
    };
    return JSON.stringify(manifest, null, 2);
}

function copyJson() {
    chrome.runtime.sendMessage({ action: 'getUrls' }, (response) => {
        const urls = response.urls || [];
        if (urls.length === 0) {
            alert('No URLs to copy!');
            return;
        }

        const json = generateJson(urls);
        navigator.clipboard.writeText(json).then(() => {
            alert('JSON copied to clipboard! Paste it into manifest_urls.json');
        });

        // Show JSON
        document.getElementById('jsonOutput').style.display = 'block';
        document.getElementById('jsonText').value = json;
    });
}

function exportJson() {
    chrome.runtime.sendMessage({ action: 'getUrls' }, (response) => {
        const urls = response.urls || [];
        if (urls.length === 0) {
            alert('No URLs to export!');
            return;
        }

        const json = generateJson(urls);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = 'manifest_urls.json';
        a.click();

        URL.revokeObjectURL(url);
    });
}

function clearUrls() {
    if (confirm('Clear all captured URLs?')) {
        chrome.runtime.sendMessage({ action: 'clearUrls' }, () => {
            loadUrls();
            document.getElementById('jsonOutput').style.display = 'none';
        });
    }
}
