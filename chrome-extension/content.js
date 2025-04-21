// Map of policy keywords to policy types
const policyTypeMap = {
    'terms of service': 'terms_of_service',
    'terms and conditions': 'terms_and_conditions',
    'terms of use': 'terms_of_use',
    'privacy policy': 'privacy_policy',
    'privacy notice': 'privacy_policy', // Add synonyms
    'cookie policy': 'cookie_policy',
    'cookie preferences': 'cookie_policy', // Add synonyms
    'cookies': 'cookie_policy', // Add synonyms
    'data protection': 'data_protection',
    'data privacy': 'data_protection',
    'acceptable use': 'acceptable_use_policy',
    'acceptable use policy': 'acceptable_use_policy',
    'security policy': 'security_policy',
    'intellectual property': 'intellectual_property_policy',
    'intellectual property policy': 'intellectual_property_policy',
    'copyright': 'copyright_policy',
    'copyright policy': 'copyright_policy',
    'return policy': 'return_policy',
    'refund policy': 'return_policy',
    'shipping policy': 'shipping_policy',
    'community guidelines': 'community_guidelines',
    'community standards': 'community_guidelines'
    // Add more keywords and types as needed
};

// Combined function to check for policy pages and links
// Create a more efficient policy matcher
const createPolicyMatcher = () => {
    const patterns = Object.entries(policyTypeMap).map(([key, value]) => ({
        regex: new RegExp(key, 'i'),
        type: value
    }));

    return (text) => {
        const match = patterns.find(pattern => pattern.regex.test(text));
        return match ? match.type : null;
    };
};

const policyMatcher = createPolicyMatcher();

// Use in detectPolicies
// Enhanced logging utility with Chrome extension compatible debug mode
const log = {
    info: (message, data = null) => {
        const logMessage = data ? `${message} | Data: ${JSON.stringify(data)}` : message;
        console.log(`[Policy Analyzer][INFO][${new Date().toISOString()}] ${logMessage}`);
    },
    error: (message, error = null) => {
        const errorDetails = error ? ` | Error: ${error.message || JSON.stringify(error)}` : '';
        console.error(`[Policy Analyzer][ERROR][${new Date().toISOString()}] ${message}${errorDetails}`);
        if (error?.stack) console.error(`Stack: ${error.stack}`);
    },
    warn: (message, data = null) => {
        const logMessage = data ? `${message} | Data: ${JSON.stringify(data)}` : message;
        console.warn(`[Policy Analyzer][WARN][${new Date().toISOString()}] ${logMessage}`);
    },
    debug: (message, data = null) => {
        // Chrome extensions don't have access to process.env
        // Instead, we can control debug logging through extension's storage or manifest
        const logMessage = data ? `${message} | Data: ${JSON.stringify(data)}` : message;
        console.debug(`[Policy Analyzer][DEBUG][${new Date().toISOString()}] ${logMessage}`);
    }
};

function detectPolicies() {
    log.debug('Starting policy detection');
    const title = document.title;
    const url = window.location.href;
    const links = Array.from(document.querySelectorAll('a'));
    const policyData = [];

    const titlePolicyType = policyMatcher(title);
    if (titlePolicyType) {
        policyData.push({ title, url, policy_type: titlePolicyType });
    }

    // Remove this duplicate check since we already have policyMatcher above
    // const matchedPolicyType = Object.keys(policyTypeMap).find(keyword => title.includes(keyword));
    // if (matchedPolicyType) {
    //     policyData.push({
    //         title: document.title,
    //         url: url,
    //         policy_type: policyTypeMap[matchedPolicyType],
    //     });
    // }

    // Find policy links and filter for only matching policy types
    const policyLinks = links.filter(link => {
        const text = link.innerText.toLowerCase();
        const href = link.href.toLowerCase();
        return Object.keys(policyTypeMap).some(keyword => text.includes(keyword) || href.includes(keyword));
    });

    // Map links to policy data objects, but only include those with a matched policy type.
    policyData.push(...policyLinks.map(link => {
        const matchedPolicyType = Object.keys(policyTypeMap).find(keyword => link.innerText.toLowerCase().includes(keyword) || link.href.toLowerCase().includes(keyword));
        if (matchedPolicyType) { // Only include if a policy type is matched.
            return {
                title: link.innerText,
                url: link.href,
                policy_type: policyTypeMap[matchedPolicyType],
            };
        }
    }).filter(item => item !== undefined)); //Remove undefined values.

    log.debug('Policy detection completed', { 
        policiesFound: policyData.length,
        policies: policyData 
    });
    return policyData;
}


// Enhanced error handling utility
const handleApiError = async (response, operation) => {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        const errorMessage = errorData.error || errorData.message || response.statusText;
        throw new Error(`${operation} failed: ${errorMessage}`);
    }
    return response.json();
};

// Function to save policy data to the backend
async function savePolicyData(policyData) {
    const domain = new URL(window.location.href).hostname;
    const base_url = window.location.href;
    const policiesToSave = policyData.length > 0 ? policyData : [];

    try {
        log.debug('Attempting to save policy data', {
            domain,
            policyCount: policiesToSave.length
        });

        const response = await fetch(`${API_BASE_URL}/save-policies`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                domain,
                base_url,
                policies: policiesToSave,
                legal_entity_name: 'Example Legal Entity',
            }),
        });

        await handleApiError(response, 'Save policies');
        log.info('Policy data saved successfully', { domain });
        
    } catch (error) {
        log.error('Failed to save policy data', {
            domain,
            error: error.message,
            statusCode: error.response?.status,
            errorDetails: error.response?.data
        });
        
        // If it's a security policy violation, we should handle it gracefully
        if (error.message.includes('security policy')) {
            log.warn('Access denied due to security policy. This might be expected for some domains.');
            return false;
        }
        
        throw error; // Re-throw other errors to be handled by the caller
    }
    return true;
}

// Function to check if the current page is a policy page based on keywords
function checkIfPolicyPage() {
    const title = document.title.toLowerCase();
    const url = window.location.href;

    const matchedPolicyType = Object.keys(policyTypeMap).find(keyword => title.includes(keyword));
    if (matchedPolicyType) {
        return [{ title: document.title, url: url, policy_type: policyTypeMap[matchedPolicyType] }];
    }
    return [];
}

// Function to find links on the page that likely point to policy documents and return URLs and titles
function findPolicyLinks() {
    const links = Array.from(document.querySelectorAll('a'));
    const policyLinks = links.filter(link => {
        const text = link.innerText.toLowerCase();
        const href = link.href.toLowerCase();

        return Object.keys(policyTypeMap).some(keyword => text.includes(keyword) || href.includes(keyword));
    });

    const policyLinkData = policyLinks.map(link => {
        const matchedPolicyType = Object.keys(policyTypeMap).find(keyword => link.innerText.toLowerCase().includes(keyword) || link.href.toLowerCase().includes(keyword));
        return {
            title: link.innerText,
            url: link.href,
            policy_type: matchedPolicyType ? policyTypeMap[matchedPolicyType] : 'unknown' // Default to unknown if not found
        };
    });

    return policyLinkData;
}


// Unified promptUserForAnalysis function
async function promptUserForAnalysis(policyData) {
    const userConfirmed = confirm('Policy Detected: Would you like to analyze the policies?');
    if (!userConfirmed) {
        log.info('User declined to analyze the policy.');
        return;
    }

    try {
        await Promise.all(policyData.map(async (item) => {
            const policyContent = await fetchPolicyContent(item.url);
            const analysisData = {
                content: policyContent,
                url: item.url,
                title: item.title,
                domain: new URL(item.url).hostname
            };

            const response = await fetch('http://127.0.0.1:5000/analyze-policy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(analysisData)
            });

            if (!response.ok) {
                throw new Error(`Analysis failed for ${item.url}`);
            }

            log.info(`Analysis of ${item.url} successful.`);
        }));
    } catch (error) {
        log.error('Error during policy analysis:', error);
    }
}

// Add fetchPolicyContent function
async function fetchPolicyContent(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Failed to fetch ${url}`);
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const mainContent = doc.querySelector('main') || 
                          doc.querySelector('article') || 
                          doc.body;
        return mainContent.innerText;
    } catch (error) {
        log.error(`Error fetching policy content: ${error}`);
        throw error;
    }
}

// Function to analyze a single policy
async function analyzePolicy(url, title) {
    try {
        log.debug('Starting policy analysis', { url, title });
        
        const response = await fetch(`${API_BASE_URL}/analyze-policy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                url, 
                title,
                timestamp: new Date().toISOString() 
            }),
        });

        const data = await handleApiError(response, 'Policy analysis');
        log.info('Policy analysis completed successfully', { url });
        return data;
    } catch (error) {
        log.error('Error analyzing policy', { url, error: error.message });
        throw error;
    }
}


// Function to initiate detection of policy pages
async function detectPolicyPages() {
    const url = window.location.href;
    const domain = new URL(url).hostname;

    // Check if we need to detect policies for this domain
    const shouldDetectPolicies = await shouldDetectPoliciesForDomain(domain);

    if (shouldDetectPolicies) {
        const allPolicyData = detectPolicies();

        if (allPolicyData.length > 0) {
            log.info(`Policy page detected or links found on ${domain}.`);
            savePolicyData(allPolicyData);
            promptUserForAnalysis(allPolicyData);
        } else {
            log.info('No policy page or relevant links detected on the page.');
        }
    } else {
        log.info(`Skipping policy detection for domain ${domain}.`);
    }
}

// Function to check if policy detection is needed for the domain
async function shouldDetectPoliciesForDomain(domain) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/get-domain/${encodeURIComponent(domain)}`);
        if (!response.ok) {
            // If there's an error fetching, treat it as if the domain doesn't exist
            return true;
        }

        const domainData = await response.json();

        // Check for non-existent or outdated domains
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

        return (domainData.policy_count === 0 || domainData.processing_status === 'processed' && new Date(domainData.updated_at) < thirtyDaysAgo);

    } catch (error) {
        log.error(`Error checking domain: ${error}`);
        return true; // In case of error, treat it as if the domain doesn't exist
    }
}

// Execute the policy page detection when the content script runs
// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Debounced event listener
window.addEventListener('load', debounce(detectPolicyPages, 300));

const API_BASE_URL = 'http://127.0.0.1:5000';