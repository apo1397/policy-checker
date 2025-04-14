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
function detectPolicies() {
    const title = document.title.toLowerCase();
    const url = window.location.href;
    const links = Array.from(document.querySelectorAll('a'));

    const policyData = [];

    // Check if the current page is a policy page
    const matchedPolicyType = Object.keys(policyTypeMap).find(keyword => title.includes(keyword));
    if (matchedPolicyType) {
        policyData.push({
            title: document.title,
            url: url,
            policy_type: policyTypeMap[matchedPolicyType],
        });
    }

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

    return policyData;
}


// Function to save policy data to the backend
async function savePolicyData(policyData) {
    const domain = new URL(window.location.href).hostname; // Get the current domain
    const base_url = window.location.href; // Get the base URL for this domain

    // Handle the case where no policies are found
    const policiesToSave = policyData.length > 0 ? policyData : [];

    try {
        const response = await fetch('http://localhost:5000/save-policies', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                domain: domain,
                base_url: base_url,
                policies: policiesToSave,
                legal_entity_name: 'Example Legal Entity', // Placeholder, ideally fetch dynamically
            }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Failed to save policy data: ${response.status} ${response.statusText} - ${errorData.error}`);
        }

        log.info('Policy data saved successfully.');
    } catch (error) {
        log.error('Error saving policy data:', error);
    }
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


async function promptUserForAnalysis(policyData) {
    const userConfirmed = confirm('Policy Detected: Would you like to analyze the policies?');
    if (userConfirmed) {
        // Analyze each policy item
        await Promise.all(policyData.map(async (item) => {
            try{
                await analyzePolicy(item.url, item.title);
            } catch (error) {
                log.error('Error during policy analysis', error);
            }
        }));
    } else {
        log.info('User declined to analyze the policy.');
    }
}

// Function to analyze a single policy
async function analyzePolicy(url, title) {
    try {
        const response = await fetch(`http://localhost:5000/analyze-policy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, title }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Failed to analyze policy ${url}: ${errorData.error || response.statusText}`);
        }

        log.info(`Analysis of ${url} successful.`);
    } catch (error) {
        log.error(`Error analyzing policy ${url}: ${error.message}`);
        throw error; // Re-throw the error to be handled by the caller
    }
}

// Function to prompt the user for analysis upon policy detection
async function promptUserForAnalysis() {
    const userConfirmed = confirm('Policy Detected: Would you like to analyze the policies?');
    if (userConfirmed) {
        const policyContent = extractPolicyContent();
        // Here we need to prepare the analysis request
        const analysisData = {
            content: policyContent,
            domain: new URL(window.location.href).hostname,
            url: window.location.href // Optionally send the current URL
        };

        // Send the analysis request
        fetch('http://localhost:5000/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(analysisData),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                log.error('Failed to analyze the policy:', data.error);
            } else {
                log.info('Analysis completed successfully:', data);
            }
        })
        .catch(error => log.error('Error during policy analysis:', error));
    } else {
        log.info('User declined to analyze the policy.');
    }
}

// Function to extract the main content of a policy page
function extractPolicyContent() {
    const mainContent = document.querySelector('main') || 
                       document.querySelector('article') || 
                       document.body; // Fallback to the entire body if specific elements aren't found
                       
    return mainContent.innerText; // Return the text content of the selected element
}

// Log functionality for monitoring actions in the content script
const log = {
    info: (message) => console.log(`INFO: ${message}`),
    error: (message) => console.error(`ERROR: ${message}`)
};

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
        const response = await fetch(`http://localhost:5000/get-domain/${encodeURIComponent(domain)}`);
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
window.addEventListener('load', detectPolicyPages);
