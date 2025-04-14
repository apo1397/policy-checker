import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import Session, Domain, Policy
from analysis import perform_analysis
import json
from datetime import datetime
from urllib.parse import urlparse


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "chrome-extension://lplaiigjeepfpcoodfafefgehgiaheal"}})
CORS(app, debug=True)

db_session = Session()

@app.route('/get-domain/<string:domain_name>', methods=['GET'])
def get_domain(domain_name):
    try:
        domain_response = Domain.get_by_name(domain_name)
        if not domain_response.data:
            return jsonify({'exists': False}), 404
        
        domain = domain_response.data[0]
        return jsonify({
            'exists': True,
            'policy_count': domain['policy_count'],
            'processing_status': domain['processing_status'],
            'updated_at': domain['updated_at']
        }), 200
    except Exception as e:
        log.exception(f"Error checking domain {domain_name}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/save-policies', methods=['POST'])
def save_policies():
    data = request.get_json()
    log.info(f"Received request to save policies: {data}")

    if not data or 'domain' not in data or 'policies' not in data:
        return jsonify({'error': 'Invalid request: domain and policies are required'}), 400

    try:
        # Check if domain exists
        domain_response = Domain.get_by_name(data['domain'])
        if not domain_response.data:
            # Create new domain
            domain_response = Domain.create(
                name=data['domain'],
                base_url=data['base_url'],
                legal_entity_name=data.get('legal_entity_name', '')
            )
        domain = domain_response.data[0]

        # Save each policy
        for policy_data in data['policies']:
            existing_policy = Policy.get_by_url(policy_data['url'])
            if not existing_policy.data:
                Policy.create(
                    domain_id=domain['id'],
                    policy_type=policy_data['policy_type'],
                    page_name=policy_data['title'],
                    page_url=policy_data['url'],
                    processing_status='pending_analysis'  # Updated status
                )

        # Update domain status
        Domain.update(domain['id'], {
            'policy_count': len(data['policies']),
            'processing_status': 'pending_analysis',  # Added status update
            'updated_at': datetime.utcnow().isoformat()
        })

        return jsonify({'message': 'Policies saved successfully'}), 200

    except Exception as e:
        log.exception(f"Error saving policies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-policies/<int:domain_id>', methods=['GET'])
def get_policies(domain_id):
    policies = db_session.query(Policy).filter_by(domain_id=domain_id).all()
    if not policies:
        return jsonify([])

    return jsonify([
        {
            'id': policy.id,
            'policy_type': policy.policy_type,
            'page_name': policy.page_name,
            'page_url': policy.page_url,
            'processing_status': policy.processing_status,
            'last_updated_at': policy.last_updated_at.isoformat(),
            'checksum': policy.checksum,
            'llm_details': policy.llm_details,
            'llm_prompt': policy.llm_prompt,
            'processing_output': policy.processing_output
        } for policy in policies
    ]), 200

@app.route('/analyze-policy', methods=['POST'])
def analyze_policy():
    data = request.get_json()
    log.info(f"Received request to analyze policy: {data}")

    if not data or 'url' not in data or 'title' not in data:
        return jsonify({'error': 'Invalid request: "url" and "title" are required.'}), 400

    url = data['url']
    title = data['title']
    domain_name = extract_domain(url)

    try:
        # Check if domain exists
        domain_response = Domain.get_by_name(domain_name)
        if not domain_response.data:
            # Create new domain
            domain_response = Domain.create(
                name=domain_name,
                base_url=url
            )
        
        domain = domain_response.data[0]

        # Create new policy
        policy_response = Policy.create(
            domain_id=domain['id'],
            policy_type='privacy_policy',
            page_name=title,
            page_url=url
        )
        policy = policy_response.data[0]

        # Perform analysis
        analysis_result = perform_analysis(fetch_policy_content(url))
        
        # Update policy with results
        Policy.update(policy['id'], {
            'processing_status': 'processed',
            'last_updated_at': datetime.utcnow().isoformat(),
            'llm_details': 'GPT-3.5',
            'llm_prompt': 'Prompt used for LLM processing',
            'processing_output': json.dumps(analysis_result)
        })

        return jsonify({'message': 'Policy analyzed and saved successfully.'}), 200

    except Exception as e:
        log.exception(f"Error analyzing policy {url}: {e}")
        return jsonify({'error': f'Error analyzing policy: {str(e)}'}), 500

def extract_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc


def fetch_policy_content(url):
    import requests
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            log.error(f"Failed to fetch policy content from {url}. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        log.exception(f"Error fetching policy content from {url}: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True)