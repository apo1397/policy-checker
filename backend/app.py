import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import Domain, Policy
from analysis import perform_analysis
import json
from datetime import datetime
from urllib.parse import urlparse
from logging.handlers import RotatingFileHandler
import os
from typing import Optional, Dict, Any, List # Add this import


# Configure logging
import logging
from logging.handlers import RotatingFileHandler
import os

# Enhanced logging configuration
def setup_logging():
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure logging with more detailed format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )

    # File handler with rotation
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'policy_analyzer.log'),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return logging.getLogger(__name__)

# Initialize logger
log = setup_logging()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Remove the SQLAlchemy session
# db_session = Session()  # This line should be removed

@app.route('/get-domain/<string:domain_name>', methods=['GET'])
def get_domain(domain_name):
    """
    Retrieves domain information by its name.

    Args:
        domain_name: The name of the domain to retrieve.

    Returns:
        JSON response with domain details or 404 if not found.
    """
    try:
        domain = Domain.get_by_name(domain_name)  # Returns dict or None
        if not domain:
            log.info(f"Domain not found: {domain_name}")
            return jsonify({'exists': False}), 404
        
        log.info(f"Domain found: {domain_name}")
        return jsonify({
            'exists': True,
            'policy_count': domain.get('policy_count', 0),
            'processing_status': domain.get('processing_status', 'unknown'),
            'updated_at': domain.get('updated_at')
        }), 200
    except Exception as e:
        log.exception(f"Error checking domain {domain_name}: {e}")
        return jsonify({'error': f"Internal server error: {str(e)}"}), 500

@app.route('/save-policies', methods=['POST', 'OPTIONS'])
def save_policies():
    """
    Saves policies for a given domain. Creates the domain if it doesn't exist.
    Handles CORS preflight requests.
    """
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
        
    data = request.get_json()
    log.info(f"Received request to save policies for domain: {data.get('domain')}")

    if not data or 'domain' not in data or 'policies' not in data:
        log.warning("Invalid request received for save_policies")
        return jsonify({'error': 'Invalid request: domain and policies are required'}), 400

    domain_name = data['domain']
    policies_data = data['policies']
    base_url = data.get('base_url') # Ensure base_url is present if creating domain
    legal_entity_name = data.get('legal_entity_name', '')

    try:
        # Check if domain exists
        domain = Domain.get_by_name(domain_name) # Returns dict or None
        
        if not domain:
            log.info(f"Domain '{domain_name}' not found. Creating new domain.")
            if not base_url:
                 log.error(f"Cannot create domain '{domain_name}' without base_url.")
                 return jsonify({'error': 'Invalid request: base_url is required when creating a new domain'}), 400
            # Create new domain
            domain_creation_response = Domain.create(
                name=domain_name,
                base_url=base_url,
                legal_entity_name=legal_entity_name
            )
            if not domain_creation_response.data:
                 log.error(f"Failed to create domain '{domain_name}' in database.")
                 raise Exception("Failed to create domain in database")
            domain = domain_creation_response.data[0] # Extract the created domain dict
            log.info(f"Successfully created domain '{domain_name}' with ID: {domain['id']}")
        else:
             log.info(f"Domain '{domain_name}' found with ID: {domain['id']}")

        domain_id = domain['id']
        new_policies_count = 0

        # Save each policy if it doesn't exist
        for policy_data in policies_data:
            policy_url = policy_data.get('url')
            if not policy_url:
                log.warning(f"Skipping policy due to missing URL for domain {domain_id}")
                continue

            existing_policy = Policy.get_by_url(policy_url) # Returns dict or None
            if not existing_policy:
                log.info(f"Policy URL '{policy_url}' not found. Creating new policy.")
                Policy.create(
                    domain_id=domain_id,
                    policy_type=policy_data.get('policy_type', 'unknown'),
                    page_name=policy_data.get('title', 'Untitled'),
                    page_url=policy_url,
                    # processing_status='pending_analysis' # Let create handle default
                )
                new_policies_count += 1
            else:
                 log.info(f"Policy URL '{policy_url}' already exists with ID: {existing_policy['id']}. Skipping creation.")


        # Update domain status if new policies were added or status needs update
        # Fetch current policy count for accuracy
        current_policies = Policy.get_by_domain(domain_id)
        total_policy_count = len(current_policies) if current_policies else 0

        update_data = {
            'policy_count': total_policy_count,
            'updated_at': datetime.utcnow().isoformat()
        }
        # Optionally update processing status if needed, e.g., if new policies trigger analysis
        if new_policies_count > 0:
             update_data['processing_status'] = 'pending_analysis' # Or relevant status

        Domain.update(domain_id, update_data)
        log.info(f"Updated domain '{domain_name}' (ID: {domain_id}) policy count to {total_policy_count}.")

        return jsonify({'message': 'Policies processed successfully'}), 200

    except Exception as e:
        log.exception(f"Error saving policies for domain {domain_name}: {e}")
        return jsonify({'error': f"Internal server error: {str(e)}"}), 500

@app.route('/get-policies/<string:domain_id>', methods=['GET']) # Changed to string ID
def get_policies(domain_id):
    """
    Retrieves all policies associated with a given domain ID.

    Args:
        domain_id: The ID of the domain.

    Returns:
        JSON list of policies or empty list if none found.
    """
    try:
        log.info(f"Fetching policies for domain ID: {domain_id}")
        # get_by_domain returns a list of dicts directly
        policies = Policy.get_by_domain(domain_id)
        if not policies:
            log.info(f"No policies found for domain ID: {domain_id}")
            return jsonify([]), 200 # Return empty list, not 404

        log.info(f"Found {len(policies)} policies for domain ID: {domain_id}")
        return jsonify(policies), 200 # Return the list directly
    except Exception as e:
        log.exception(f"Error fetching policies for domain {domain_id}: {e}")
        return jsonify({'error': f"Internal server error: {str(e)}"}), 500

@app.route('/analyze-policy', methods=['POST'])
def analyze_policy():
    """
    Analyzes a single policy URL. Creates domain/policy if they don't exist.
    """
    data = request.get_json()
    url = data.get('url')
    title = data.get('title')

    log.info(f"Received policy analysis request for URL: {url}")

    if not url or not title:
        log.warning("Invalid request received for analyze_policy: URL or title missing.")
        return jsonify({'error': 'Invalid request: "url" and "title" are required.'}), 400

    try:
        domain_name = extract_domain(url)
        if not domain_name:
             log.error(f"Could not extract domain from URL: {url}")
             return jsonify({'error': 'Invalid URL provided.'}), 400

        # Check if domain exists
        domain = Domain.get_by_name(domain_name) # Returns dict or None
        
        if not domain:
            log.info(f"Domain '{domain_name}' not found for analysis. Creating new domain.")
            # Create new domain - assuming base_url is the policy URL for simplicity here
            # Might need refinement based on how base_url should be determined
            domain_creation_response = Domain.create(
                name=domain_name,
                base_url=f"https://{domain_name}" # Construct a base URL
            )
            if not domain_creation_response.data:
                 log.error(f"Failed to create domain '{domain_name}' for analysis.")
                 raise Exception("Failed to create domain for analysis")
            domain = domain_creation_response.data[0]
            log.info(f"Created domain '{domain_name}' (ID: {domain['id']}) for analysis.")
        else:
             log.info(f"Domain '{domain_name}' (ID: {domain['id']}) found for analysis.")

        domain_id = domain['id']

        # Check if policy exists
        policy = Policy.get_by_url(url) # Returns dict or None

        if not policy:
            log.info(f"Policy URL '{url}' not found. Creating new policy entry.")
            # Create new policy entry
            policy_creation_response = Policy.create(
                domain_id=domain_id,
                policy_type='privacy_policy', # Assuming default, adjust if needed
                page_name=title,
                page_url=url
            )
            if not policy_creation_response.data:
                 log.error(f"Failed to create policy entry for URL '{url}'.")
                 raise Exception("Failed to create policy entry")
            policy = policy_creation_response.data[0]
            log.info(f"Created policy entry for URL '{url}' (ID: {policy['id']}).")
        else:
            log.info(f"Policy URL '{url}' (ID: {policy['id']}) found. Proceeding with analysis.")

        policy_id = policy['id']

        # Fetch content and perform analysis
        log.info(f"Fetching content for policy URL: {url}")
        content = fetch_policy_content(url)
        if content is None:
            log.error(f"Failed to fetch content for URL: {url}")
            # Update policy status to failed
            Policy.update(policy_id, {'processing_status': 'failed_fetch'})
            return jsonify({'error': 'Failed to fetch policy content.'}), 500

        log.info(f"Performing analysis for policy ID: {policy_id}")
        # Update status to 'processing' before starting analysis
        Policy.update(policy_id, {'processing_status': 'processing'})

        # Assuming perform_analysis is synchronous for now
        # If it becomes async, this needs adjustment (e.g., background task)
        analysis_result = perform_analysis(content)
        
        # Update policy with results
        log.info(f"Analysis complete for policy ID: {policy_id}. Updating database.")
        Policy.update(policy_id, {
            'processing_status': 'processed',
            'last_updated_at': datetime.utcnow().isoformat(),
            'llm_details': 'Gemini 1.5', # Example, fetch from config if dynamic
            'llm_prompt': 'Default analysis prompt', # Example, fetch from config
            'processing_output': json.dumps(analysis_result) # Ensure result is JSON serializable
        })

        log.info(f"Policy {policy_id} analyzed and saved successfully.")
        return jsonify({'message': 'Policy analyzed and saved successfully.', 'policy_id': policy_id}), 200

    except Exception as e:
        log.exception(f"Error analyzing policy {url}: {e}")
        # Attempt to update policy status to failed if possible
        if 'policy_id' in locals():
            try:
                Policy.update(policy_id, {'processing_status': 'failed_analysis'})
            except Exception as update_e:
                log.error(f"Failed to update policy status to failed_analysis for {policy_id}: {update_e}")
        return jsonify({'error': f'Internal server error during analysis: {str(e)}'}), 500

def extract_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc


def fetch_policy_content(url: str) -> Optional[str]:
    """
    Fetches the text content of a given URL.

    Args:
        url: The URL to fetch content from.

    Returns:
        The text content of the page, or None if fetching fails.
    """
    import requests
    try:
        headers = {'User-Agent': 'PolicyAnalyzerBot/1.0 (+http://example.com/bot)'} # Be a good citizen
        response = requests.get(url, timeout=20, headers=headers, allow_redirects=True) # Increased timeout, allow redirects
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        # Basic check for HTML content type
        content_type = response.headers.get('Content-Type', '').lower()
        if 'html' not in content_type and 'text' not in content_type:
             log.warning(f"Unexpected content type '{content_type}' for URL: {url}")
             # Decide if you want to proceed or return None/error
             # return None 

        # Consider adding basic HTML parsing here if needed (e.g., using BeautifulSoup)
        # from bs4 import BeautifulSoup
        # soup = BeautifulSoup(response.text, 'html.parser')
        # return soup.get_text() 
        
        log.info(f"Successfully fetched content from {url}")
        return response.text
    except requests.exceptions.Timeout:
        log.error(f"Timeout error fetching policy content from {url}")
        return None
    except requests.exceptions.RequestException as e:
        log.exception(f"Request error fetching policy content from {url}: {e}")
        return None
    except Exception as e:
        log.exception(f"Unexpected error fetching policy content from {url}: {e}")
        return None


if __name__ == '__main__':
    # Use environment variables for host and port if available, otherwise default
    host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']
    
    log.info(f"Starting Flask server on {host}:{port} with debug={debug_mode}")
    app.run(host=host, port=port, debug=debug_mode)