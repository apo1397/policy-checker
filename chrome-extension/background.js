// backend.js
const API_BASE_URL = 'http://127.0.0.1:5000'; // Update with your backend URL

// Listen for the extension's installation event
chrome.runtime.onInstalled.addListener(() => {
    console.log('Policy Analyzer Extension installed');
});

// Listen for messages sent from other parts of the extension (e.g., content scripts or popup)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'analyzePolicy') {
        analyzePolicyContent(request.policyContent, request.domain)
            .then(analysis => sendResponse({ success: true, analysis }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true; // Required for async sendResponse
    } else if (request.action === 'fetchAndAnalyzePolicies') {
        fetchAndAnalyzePolicies(request.urls)
            .then(results => sendResponse({ success: true, analysis: results }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
    }
});

// Function to analyze policy content by communicating with the Flask backend
async function analyzePolicyContent(content, domain) {
    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, domain })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to analyze policy');
        }

        const data = await response.json();
        return data; // Returns { summary, keyPoints, concerns }
    } catch (error) {
        console.error('Error in analyzePolicyContent:', error);
        throw error;
    }
}

// Function to fetch and analyze multiple policy URLs
async function fetchAndAnalyzePolicies(urls) {
    try {
        const response = await fetch(`${API_BASE_URL}/fetch-and-analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ urls })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch and analyze policies');
        }

        const data = await response.json();
        return data; // Returns aggregated analysis
    } catch (error) {
        console.error('Error in fetchAndAnalyzePolicies:', error);
        throw error;
    }
}

// Asynchronous function to check if analysis for a domain is already cached
async function checkCachedAnalysis(domain) {
    // Attempt to retrieve cached analysis from Chrome's local storage
    const data = await chrome.storage.local.get(domain);
    if (data[domain]) return data[domain]; // If found in local storage, return it

    // If not found in local storage, attempt to fetch from the backend database
    try {
        const response = await fetch(`${API_BASE_URL}/cached-analysis/${encodeURIComponent(domain)}`);
        if (response.ok) {
            const result = await response.json();
            // Validate that all necessary fields are present
            if (result.summary && Array.isArray(result.keyPoints) && Array.isArray(result.concerns)) {
                const analysis = {
                    summary: result.summary,
                    keyPoints: result.keyPoints,
                    concerns: result.concerns
                };
                // Cache the fetched analysis locally
                await chrome.storage.local.set({ [domain]: analysis });
                return analysis;
            } else {
                console.error('Incomplete analysis data received from backend.');
            }
        }
    } catch (error) {
        // Log any errors encountered during the fetch
        console.error('Error checking cached analysis:', error);
    }

    // If analysis is not found in either cache or backend, return null
    return null;
}