import json
import logging
import google.generativeai as genai
from llm_config import get_llm_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

async def perform_analysis(content):
    log.info(f"Starting analysis of policy content (length: {len(content)})")
    
    try:
        # Get LLM configuration
        llm_config = get_llm_config()
        
        # Configure Gemini
        genai.configure(api_key=llm_config['api_key'])
        model = genai.GenerativeModel(llm_config['model'])
        
        # Prepare prompt with content
        prompt = llm_config['default_prompt'] + f"\n\nPolicy Content:\n{content}"
        
        # Generate response
        response = await model.generate_content_async(prompt)
        
        # Parse the response into structured format
        analysis_result = parse_llm_response(response.text)
        
        log.info("Analysis complete using Gemini 1.5")
        return analysis_result
        
    except Exception as e:
        log.error(f"Error during analysis: {str(e)}")
        return {
            "summary": "Error analyzing policy",
            "keyPoints": [],
            "concerns": [f"Analysis failed: {str(e)}"]
        }

def parse_llm_response(response_text):
    """Parse LLM response into structured format"""
    try:
        # Basic parsing - you might want to enhance this based on actual response format
        sections = response_text.split('\n\n')
        return {
            "summary": sections[0] if len(sections) > 0 else "",
            "keyPoints": [point.strip() for point in sections[1].split('\n')] if len(sections) > 1 else [],
            "concerns": [concern.strip() for concern in sections[2].split('\n')] if len(sections) > 2 else []
        }
    except Exception as e:
        log.error(f"Error parsing LLM response: {str(e)}")
        return {
            "summary": response_text[:500],  # First 500 chars as summary
            "keyPoints": [],
            "concerns": ["Error parsing analysis results"]
        }