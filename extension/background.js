// Background service worker - captures videomanifest URLs
let capturedUrls = [];

// Load saved URLs on startup
chrome.storage.local.get(['capturedUrls'], (result) => {
    if (result.capturedUrls) {
        capturedUrls = result.capturedUrls;
        updateBadge();
    }
});

// Trim URL to end at &format=dash
function trimUrl(url) {
    const marker = '&format=dash';
    const idx = url.indexOf(marker);
    if (idx !== -1) {
        return url.substring(0, idx + marker.length);
    }
    return url;
}

// Listen for web requests - using onCompleted to catch all requests
chrome.webRequest.onCompleted.addListener(
    (details) => {
        const url = details.url;

        // Look for videomanifest or manifest patterns
        if (url.includes('videomanifest') ||
            url.includes('getplaybackinfo') ||
            url.includes('manifest(format=') ||
            url.includes('manifest?') ||
            (url.includes('sharepoint') && url.includes('manifest'))) {

            const trimmedUrl = trimUrl(url);

            // Avoid duplicates
            if (!capturedUrls.includes(trimmedUrl)) {
                capturedUrls.push(trimmedUrl);

                // Save to storage
                chrome.storage.local.set({ capturedUrls: capturedUrls });

                // Update badge
                updateBadge();

                console.log(`✅ Captured manifest #${capturedUrls.length}: ${trimmedUrl.substring(0, 100)}...`);
            }
        }
    },
    { urls: ["<all_urls>"] }
);

// Also listen to onBeforeRequest as backup
chrome.webRequest.onBeforeRequest.addListener(
    (details) => {
        const url = details.url;

        if (url.includes('videomanifest')) {
            const trimmedUrl = trimUrl(url);

            if (!capturedUrls.includes(trimmedUrl)) {
                capturedUrls.push(trimmedUrl);
                chrome.storage.local.set({ capturedUrls: capturedUrls });
                updateBadge();
                console.log(`✅ Captured (before): ${trimmedUrl.substring(0, 80)}...`);
            }
        }
    },
    { urls: ["<all_urls>"] }
);

function updateBadge() {
    const count = capturedUrls.length;
    chrome.action.setBadgeText({ text: count > 0 ? count.toString() : '' });
    chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getUrls') {
        sendResponse({ urls: capturedUrls });
    } else if (request.action === 'clearUrls') {
        capturedUrls = [];
        chrome.storage.local.set({ capturedUrls: [] });
        updateBadge();
        sendResponse({ success: true });
    }
    return true;
});
