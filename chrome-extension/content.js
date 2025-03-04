// Function to initiate detection of policy pages
function detectPolicyPages() {
    const url = window.location.href; // Get the current page URL
    const domain = new URL(url).hostname; // Extract the domain from the URL

    const isPolicyPage = checkIfPolicyPage(); // Check if it's a policy page
    const linksFound = findPolicyLinks(); // Check for links to policy-related content

    if (isPolicyPage || linksFound) {
        log.info(`Policy page detected or links found on ${domain}.`);
        
        // Call the backend to store the detected policy links
        const policyData = {
            content: document.body.innerText, // Placeholder for the actual policy content
            domain: domain,
            title: document.title, // Title of the current page
            url: url // URL of the current page
        };

        // Send the detected policy data to the backend
        fetch('http://127.0.0.1:5000/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(policyData),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                log.error(`Failed to analyze policy: ${data.error}`);
            } else {
                log.info('Policy analysis initiated successfully:', data);
            }
        })
        .catch(error => log.error('Error sending policy analysis request:', error));

        promptUserForAnalysis(); // Prompt the user to scan policies
    } else {
        log.info('No policy page or relevant links detected on the page.');
    }
}

// Function to check if the current page is a policy page based on keywords
function checkIfPolicyPage() {
    const title = document.title.toLowerCase(); // Get the page title in lowercase
    const bodyText = document.body.innerText.toLowerCase(); // Get the body text in lowercase

    const policyKeywords = [
        'terms of service', 'terms and conditions', 'privacy policy',
        'cookie policy', 'terms of use', 'user agreement'
    ];

    return policyKeywords.some(keyword => title.includes(keyword) || bodyText.includes(keyword));
}

// Function to find links on the page that likely point to policy documents
function findPolicyLinks() {
    const links = Array.from(document.querySelectorAll('a'));
    const policyLinks = links.filter(link => {
        const text = link.innerText.toLowerCase();
        const href = link.href.toLowerCase();
        
        return ['privacy', 'terms', 'conditions', 'cookie'].some(keyword => text.includes(keyword) || href.includes(keyword));
    });

    // If policy links are found, store them in the database
    if (policyLinks.length > 0) {
        policyLinks.forEach(link => {
            const policyLinkData = {
                title: link.innerText,
                url: link.href,
                status: 'not_processed',
                created_at: new Date().toISOString(),
                // Optionally include domain if necessary
                domain: new URL(link.href).hostname
            };
            
            // Send each link to the backend
            fetch('http://localhost:5000/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(policyLinkData),
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    log.error(`Failed to save link: ${data.error}`);
                } else {
                    log.info(`Saved link: ${link.href}`);
                }
            })
            .catch(error => log.error('Error sending link data to backend:', error));
        });

        log.info(`Found ${policyLinks.length} policy links on the page.`);
        return true; // Indicate that policy-related links were found
    }
    return false; // No relevant policy links found
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

// Execute the policy page detection when the content script runs
window.addEventListener('load', detectPolicyPages);