from datetime import datetime
import logging
from typing import Optional, Dict, Any, List
from postgrest.exceptions import APIError
from supabase_config import supabase

# Configure logging
logger = logging.getLogger(__name__)

class Domain:
    @staticmethod
    def create(name: str, base_url: str, legal_entity_name: Optional[str] = None) -> Dict[str, Any]:
        try:
            data = {
                'name': name,
                'base_url': base_url,
                'legal_entity_name': legal_entity_name,
                'processing_status': 'pending',
                'policy_count': 0,
                'updated_at': datetime.utcnow().isoformat()
            }
            result = supabase.table('domains').insert(data).execute()
            logger.info(f"Created domain: {name}")
            return result
        except APIError as e:
            logger.error(f"Failed to create domain {name}: {str(e)}")
            raise

    @staticmethod
    def get_by_name(name: str) -> Optional[Dict[str, Any]]:
        try:
            result = supabase.table('domains').select('*').eq('name', name).execute()
            if result.data:
                return result.data[0]
            logger.debug(f"No domain found for name: {name}")
            return None
        except APIError as e:
            logger.error(f"Error fetching domain {name}: {str(e)}")
            raise

    @staticmethod
    def update(id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = supabase.table('domains').update(data).eq('id', id).execute()
            logger.info(f"Updated domain {id}")
            return result
        except APIError as e:
            logger.error(f"Failed to update domain {id}: {str(e)}")
            raise

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        try:
            result = supabase.table('domains').select('*').execute()
            return result.data
        except APIError as e:
            logger.error(f"Failed to fetch all domains: {str(e)}")
            raise

    @staticmethod
    def delete(id: str) -> Dict[str, Any]:
        try:
            result = supabase.table('domains').delete().eq('id', id).execute()
            logger.info(f"Deleted domain {id}")
            return result
        except APIError as e:
            logger.error(f"Failed to delete domain {id}: {str(e)}")
            raise

class Policy:
    @staticmethod
    def create(domain_id: str, policy_type: str, page_name: str, page_url: str) -> Dict[str, Any]:
        try:
            data = {
                'domain_id': domain_id,
                'policy_type': policy_type,
                'page_name': page_name,
                'page_url': page_url,
                'processing_status': 'not_processed',
                'last_updated_at': datetime.utcnow().isoformat(),
                'checksum': '',
                'llm_details': '',
                'llm_prompt': '',
                'processing_output': ''
            }
            result = supabase.table('policies').insert(data).execute()
            logger.info(f"Created policy for domain {domain_id}: {policy_type}")
            return result
        except APIError as e:
            logger.error(f"Failed to create policy for domain {domain_id}: {str(e)}")
            raise

    @staticmethod
    def get_by_domain(domain_id: str) -> List[Dict[str, Any]]:
        try:
            result = supabase.table('policies').select('*').eq('domain_id', domain_id).execute()
            return result.data
        except APIError as e:
            logger.error(f"Failed to fetch policies for domain {domain_id}: {str(e)}")
            raise

    @staticmethod
    def update(id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if 'last_updated_at' not in data:
                data['last_updated_at'] = datetime.utcnow().isoformat()
            result = supabase.table('policies').update(data).eq('id', id).execute()
            logger.info(f"Updated policy {id}")
            return result
        except APIError as e:
            logger.error(f"Failed to update policy {id}: {str(e)}")
            raise

    @staticmethod
    def get_by_url(url: str) -> Optional[Dict[str, Any]]:
        try:
            result = supabase.table('policies').select('*').eq('page_url', url).execute()
            if result.data:
                return result.data[0]
            logger.debug(f"No policy found for URL: {url}")
            return None
        except APIError as e:
            logger.error(f"Failed to fetch policy by URL {url}: {str(e)}")
            raise

    @staticmethod
    def delete(id: str) -> Dict[str, Any]:
        try:
            result = supabase.table('policies').delete().eq('id', id).execute()
            logger.info(f"Deleted policy {id}")
            return result
        except APIError as e:
            logger.error(f"Failed to delete policy {id}: {str(e)}")
            raise

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        try:
            result = supabase.table('policies').select('*, domains(*)').execute()
            return result.data
        except APIError as e:
            logger.error(f"Failed to fetch all policies: {str(e)}")
            raise