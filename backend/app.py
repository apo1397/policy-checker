import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import Session, PolicyAnalysis
from analysis import perform_analysis
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "chrome-extension://lplaiigjeepfpcoodfafefgehgiaheal"}})
CORS(app, debug=True)

db_session = Session()

@app.route('/analyze', methods=['POST'])
def analyze_policy():
    data = request.get_json()
    log.info(f"Received request to analyze policy: {data}")

    if not data or 'content' not in data or 'domain' not in data:
        log.error('Invalid request: Missing "content" or "domain".')
        return jsonify({'error': 'Invalid request. "content" and "domain" are required.'}), 400

    content = data['content']
    domain = data['domain']
    title = data.get('title')  # New title parameter

    # Check if the domain already exists in the database
    existing_analysis = db_session.query(PolicyAnalysis).filter_by(domain=domain).first()
    if existing_analysis:
        log.info(f"Returning cached analysis for domain: {domain}")
        return jsonify({
            'summary': existing_analysis.summary,
            'keyPoints': json.loads(existing_analysis.key_points),
            'concerns': json.loads(existing_analysis.concerns)
        }), 200

    # Create a new entry in the database
    new_analysis = PolicyAnalysis(
        domain=domain,
        title=title,
        url=data.get('url'),  # Assume this comes with the request
        status='not_processed',
        created_at=datetime.utcnow(),
        summary=None,
        key_points=json.dumps([]),
        concerns=json.dumps([]),
        llm_model=None
    )
    db_session.add(new_analysis)
    db_session.commit()
    log.info(f"Saved new policy analysis to database for domain: {domain}")

    # Perform the analysis
    analysis_result = perform_analysis(content)
    log.info(f"Analysis result for domain {domain}: {analysis_result}")

    new_analysis.summary = analysis_result['summary']
    new_analysis.key_points = json.dumps(analysis_result['keyPoints'])
    new_analysis.concerns = json.dumps(analysis_result['concerns'])
    new_analysis.status = 'processed'  # Update status to processed
    new_analysis.updated_at = datetime.utcnow()
    db_session.commit()
    log.info(f"Updated existing policy analysis for domain: {domain}")

    return jsonify(analysis_result), 200

@app.route('/cached-analysis/<string:domain>', methods=['GET'])
def get_cached_analysis(domain):
    log.info(f"Request for cached analysis for domain: {domain}")
    analysis = db_session.query(PolicyAnalysis).filter_by(domain=domain).first()
    if not analysis:
        log.warning(f"Cached analysis not found for domain: {domain}")
        return jsonify({'error': 'No cached analysis found for this domain.'}), 404

    log.info(f"Returning cached analysis for domain: {domain}")
    return jsonify({
        'domain': analysis.domain,
        'summary': analysis.summary,
        'keyPoints': json.loads(analysis.key_points),
        'concerns': json.loads(analysis.concerns)
    }), 200

@app.route('/cached-analysis/<string:domain>', methods=['POST'])
def update_cached_analysis(domain):
    data = request.get_json()
    log.info(f"Request to update cached analysis for domain: {domain} with data: {data}")

    if not data or 'summary' not in data or 'keyPoints' not in data or 'concerns' not in data:
        log.error('Invalid request: Missing required fields.')
        return jsonify({'error': 'Invalid request. "summary", "keyPoints", and "concerns" are required.'}), 400

    analysis = db_session.query(PolicyAnalysis).filter_by(domain=domain).first()
    if not analysis:
        log.warning(f"No existing analysis found for domain: {domain}")
        return jsonify({'error': 'No existing analysis found for this domain.'}), 404

    analysis.summary = data['summary']
    analysis.key_points = json.dumps(data['keyPoints'])
    analysis.concerns = json.dumps(data['concerns'])
    db_session.commit()
    log.info(f"Updated cached analysis for domain: {domain}")

    return jsonify({'message': 'Analysis updated successfully.'}), 200

@app.route('/fetch-and-analyze', methods=['POST'])
def fetch_and_analyze_policies():
    data = request.get_json()
    log.info(f"Received request to fetch and analyze policies: {data}")

    if not data or 'urls' not in data:
        log.error('Invalid request: Missing "urls" field.')
        return jsonify({'error': 'Invalid request. "urls" are required.'}), 400
    
    urls = data['urls']
    aggregate_summary = ""
    aggregate_key_points = []
    aggregate_concerns = []

    for url in urls:
        domain = extract_domain(url)
        analysis = db_session.query(PolicyAnalysis).filter_by(domain=domain).first()
        
        if not analysis:
            policy_content = fetch_policy_content(url)
            if not policy_content:
                log.warning(f"Failed to fetch content from URL: {url}")
                continue

            analysis_result = perform_analysis(policy_content)
            log.info(f"Analysis result for domain {domain}: {analysis_result}")

            # Create a new entry for fetched policy
            new_analysis = PolicyAnalysis(
                domain=domain,
                url=url,
                title='Policy Title Here',  # Update with actual title from policy content parsing
                status='processed',
                created_at=datetime.utcnow(),
                summary=analysis_result['summary'],
                key_points=json.dumps(analysis_result['keyPoints']),
                concerns=json.dumps(analysis_result['concerns']),
                llm_model='Model details here'  # Include model details if applicable
            )
            db_session.add(new_analysis)
            db_session.commit()
            log.info(f"Saved new analysis to database for domain: {domain}")

            analysis = new_analysis

        aggregate_summary += f"\n{analysis.summary}"
        aggregate_key_points.extend(json.loads(analysis.key_points))
        aggregate_concerns.extend(json.loads(analysis.concerns))

    log.info(f"Aggregated analysis result: {aggregate_summary}, {aggregate_key_points}, {aggregate_concerns}")
    return jsonify({
        "aggregateSummary": aggregate_summary.strip(),
        "aggregateKeyPoints": aggregate_key_points,
        "aggregateConcerns": aggregate_concerns
    }), 200

def extract_domain(url):
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    return parsed_url.hostname

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