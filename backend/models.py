from datetime import datetime
from supabase_config import supabase

class Domain:
    @staticmethod
    def create(name, base_url, legal_entity_name=None):
        data = {
            'name': name,
            'base_url': base_url,
            'legal_entity_name': legal_entity_name,
            'processing_status': 'not_processed',
            'policy_count': 0
        }
        return supabase.table('domains').insert(data).execute()

    @staticmethod
    def get_by_name(name):
        return supabase.table('domains').select('*').eq('name', name).single().execute()

    @staticmethod
    def update(id, data):
        return supabase.table('domains').update(data).eq('id', id).execute()

    @staticmethod
    def get_all():
        return supabase.table('domains').select('*').execute()

    @staticmethod
    def delete(id):
        return supabase.table('domains').delete().eq('id', id).execute()

class Policy:
    @staticmethod
    def create(domain_id, policy_type, page_name, page_url):
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
        return supabase.table('policies').insert(data).execute()

    @staticmethod
    def get_by_domain(domain_id):
        return supabase.table('policies').select('*').eq('domain_id', domain_id).execute()

    @staticmethod
    def update(id, data):
        if 'last_updated_at' not in data:
            data['last_updated_at'] = datetime.utcnow().isoformat()
        return supabase.table('policies').update(data).eq('id', id).execute()

    @staticmethod
    def get_by_url(url):
        return supabase.table('policies').select('*').eq('page_url', url).single().execute()

    @staticmethod
    def delete(id):
        return supabase.table('policies').delete().eq('id', id).execute()

    @staticmethod
    def get_all():
        return supabase.table('policies').select('*, domains(*)').execute()