// Event listener for when the popup's DOM content is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get references to various sections in the popup
    const loadingSection = document.getElementById('loading');
    const noPolicySection = document.getElementById('no-policy');
    const policyLinksSection = document.getElementById('policy-links');
    const analysisResultsSection = document.getElementById('analysis-results');
    
    // Initially display the loading section
    showSection(loadingSection);
    
    // Query the active tab in the current window
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        const currentTab = tabs[0]; // Get the first (active) tab
        const domain = new URL(currentTab.url).hostname; // Extract the domain from the tab's URL
        
        // Check if there's cached analysis for this domain
        checkCachedAnalysis(domain)
            .then(analysis => {
                if (analysis) {
                    // If cached analysis exists, display it
                    displayAnalysis(analysis);
                } else {
                    // If no cached analysis, send a message to the content script to check for policies
                    chrome.tabs.sendMessage(
                        currentTab.id, 
                        {action: 'checkForPolicies'},
                        response => handleContentResponse(response, currentTab)
                    );
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // If an error occurs, display the 'no policy' section
                showSection(noPolicySection);
            });
    });
    
    // Attach event listeners to popup buttons
    document.getElementById('scan-page').addEventListener('click', scanPage);
    document.getElementById('analyze-selected').addEventListener('click', analyzeSelected);
});

// Function to display a specific section in the popup and hide others
function showSection(section) {
    document.querySelectorAll('.container > div').forEach(div => {
        div.classList.add('hidden'); // Hide all sections
    });
    section.classList.remove('hidden'); // Show the specified section
}

// Function to handle responses from the content script
function handleContentResponse(response, tab) {
    const noPolicySection = document.getElementById('no-policy');
    const policyLinksSection = document.getElementById('policy-links');

    if (!response) {
        // If there's no response, show the 'no policy' section
        showSection(noPolicySection);
        return;
    }

    if (response.policyContent) {
        // If policy content is directly available, analyze it
        analyzePolicy(response.policyContent, new URL(tab.url).hostname);
    } else if (response.policyLinks && response.policyLinks.length > 0) {
        // If policy links are found, display them for user selection
        showPolicyLinks(response.policyLinks);
    } else {
        // If neither policies nor links are found, show the 'no policy' section
        showSection(noPolicySection);
    }
}

// Function to display a list of policy links for user selection
function showPolicyLinks(links) {
    const linksList = document.getElementById('links-list');
    linksList.innerHTML = ''; // Clear any existing links
    
    // Iterate over each policy link and create a list item with a checkbox
    links.forEach((link, index) => {
        const li = document.createElement('li');
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = link.url; // Set the checkbox value to the link URL
        checkbox.id = `link-${index}`; // Assign a unique ID for labeling
        
        const label = document.createElement('label');
        label.htmlFor = `link-${index}`; // Associate the label with the checkbox
        label.textContent = link.text || link.url; // Use link text or URL as the label
        
        li.appendChild(checkbox); // Add checkbox to the list item
        li.appendChild(label); // Add label to the list item
        linksList.appendChild(li); // Append the list item to the links list
    });
    
    // Display the section containing policy links
    showSection(document.getElementById('policy-links'));
}

// Function to handle analysis results (simplified)
function handleAnalysisResponse(response) {
    if (response && response.success && response.analysis) {
        displayAnalysis(response.analysis); // Assuming displayAnalysis still works
    } else if (response && response.error) {
        console.error('Analysis Error:', response.error);
        showSection(document.getElementById('no-policy'));
    } else {
        console.error('Unexpected response format:', response);
        showSection(document.getElementById('no-policy'));
    }
}

// Asynchronous function to analyze selected policy links
async function analyzeSelected() {
    // Get all checked checkboxes representing selected policy links
    const checkboxes = document.querySelectorAll('#links-list input[type="checkbox"]:checked');
    if (checkboxes.length === 0) return; // If no links are selected, do nothing
    
    // Show the loading section while analysis is in progress
    showSection(document.getElementById('loading'));
    
    // Extract the URLs of the selected links
    const urls = Array.from(checkboxes).map(cb => cb.value);
    
    try {
        // Send a message to the background script to fetch and analyze the selected policies
        const results = await chrome.runtime.sendMessage({
            action: 'fetchAndAnalyzePolicies',
            urls
        });
        
        // Display the aggregated analysis results
        displayAnalysis(results);
    } catch (error) {
        console.error('Error analyzing policies:', error);
        // If an error occurs, show the 'no policy' section
        showSection(document.getElementById('no-policy'));
    }
}

// Asynchronous function to initiate scanning of the current page for policies
async function scanPage() {
    // Show the loading section while scanning
    showSection(document.getElementById('loading'));
    
    // Query the active tab in the current window
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        // Send a message to the content script to force a scan for policies
        chrome.tabs.sendMessage(
            tabs[0].id, 
            {action: 'forceScan'},
            response => handleContentResponse(response, tabs[0])
        );
    });
}

// Asynchronous function to analyze policy content by sending a message to the background script
async function analyzePolicy(content, domain) {
    // Show the loading section while analysis is in progress
    showSection(document.getElementById('loading'));

    try {
        // Send a message to the background script to analyze the policy content
        const messageResponse = await chrome.runtime.sendMessage({
            action: 'analyzePolicy',
            policyContent: content,
            domain
        });

        handleAnalysisResponse(messageResponse);
    } catch (error) {
        console.error('Error:', error);
        // If an error occurs, show the 'no policy' section
        showSection(document.getElementById('no-policy'));
    }
}

// Function to display the analysis results in the popup
function displayAnalysis(analysis) {
    // Populate the summary section with the analysis summary
    document.getElementById('summary').textContent = analysis.summary;
    
    // Populate the key points list
    const keyPointsList = document.getElementById('key-points');
    keyPointsList.innerHTML = ''; // Clear existing key points
    analysis.keyPoints.forEach(point => {
        const li = document.createElement('li');
        li.textContent = point; // Set the text content to the key point
        keyPointsList.appendChild(li); // Append the list item to the key points list
    });
    
    // Populate the concerns list
    const concernsList = document.getElementById('concerns');
    concernsList.innerHTML = ''; // Clear existing concerns
    analysis.concerns.forEach(concern => {
        const li = document.createElement('li');
        li.textContent = concern; // Set the text content to the concern
        concernsList.appendChild(li); // Append the list item to the concerns list
    });
    
    // Display the section containing analysis results
    showSection(document.getElementById('analysis-results'));
}

// Asynchronous function to check for cached analysis in Chrome's local storage
async function checkCachedAnalysis(domain) {
    try {
        // Retrieve cached analysis data for the given domain
        const data = await chrome.storage.local.get(domain);
        return data[domain] || null; // Return the cached analysis or null if not found
    } catch (error) {
        console.error('Error checking cache:', error);
        return null; // Return null if an error occurs
    }
}