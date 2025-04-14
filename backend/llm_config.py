import os
from dotenv import load_dotenv

load_dotenv()

LLM_CONFIGS = {
    'gemini-1.5': {
        'name': 'Gemini 1.5',
        'api_key': os.getenv('GEMINI_API_KEY'),
        'model': 'gemini-1.5-pro',
        'max_tokens': 4096,
        'temperature': 0.7,
        'default_prompt': """
            Analyze this privacy policy and extract the following information:
            1. Data Collection Practices
            2. Data Sharing Policies
            3. User Rights
            4. Security Measures
            5. Contact Information
            
            Provide a clear, structured response highlighting key points and potential concerns.
        """.strip()
    },
    # Add more LLM configurations here as needed
}

DEFAULT_LLM = 'gemini-1.5'

def get_llm_config(llm_name=None):
    """Get configuration for specified LLM or default if none specified"""
    if not llm_name:
        llm_name = DEFAULT_LLM
    return LLM_CONFIGS.get(llm_name)