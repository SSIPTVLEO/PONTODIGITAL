from datetime import datetime, date
from typing import Optional, Dict, Any, List
from supabase_client import get_supabase_client, get_supabase_admin_client

class SupabaseUser:
    """Modelo para usuários no Supabase"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.nome = data.get('nome')
        self.email = data.get('email')
        self.senha_hash = data.get('senha_hash')
        self.is_admin = data.get('is_admin', False)
        self.confirmed = data.get('confirmed', False)
        self.confirmed_on = data.get('confirmed_on')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')

    @classmethod
    def create(cls, nome: str, email: str, senha_hash: str, is_admin: bool = False, confirmed: bool = False):
        """Criar novo usuário"""
        supabase = get_supabase_admin_client()
        
        user_data = {
            'nome': nome,
            'email': email,
            'senha_hash': senha_hash,
            'is_admin': is_admin,
            'confirmed': confirmed
        }
        
        response = supabase.table('users').insert(user_data).execute()
        if response.data:
            return cls(response.data[0])
        return None

    @classmethod
    def find_by_email(cls, email: str):
        """Buscar usuário por email"""
        supabase = get_supabase_admin_client()
        
        response = supabase.table('users').select('*').eq('email', email).execute()
        if response.data:
            return cls(response.data[0])
        return None

    @classmethod
    def find_by_id(cls, user_id: int):
        """Buscar usuário por ID"""
        supabase = get_supabase_admin_client()
        
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        if response.data:
            return cls(response.data[0])
        return None

    @classmethod
    def get_all(cls):
        """Buscar todos os usuários (apenas para admins)"""
        supabase = get_supabase_admin_client()
        
        response = supabase.table('users').select('*').execute()
        return [cls(user_data) for user_data in response.data]

    def update(self, **kwargs):
        """Atualizar usuário"""
        supabase = get_supabase_admin_client()
        
        # Adicionar timestamp de atualização
        kwargs['updated_at'] = datetime.now().isoformat()
        
        response = supabase.table('users').update(kwargs).eq('id', self.id).execute()
        if response.data:
            # Atualizar atributos locais
            for key, value in kwargs.items():
                setattr(self, key, value)
            return True
        return False

    def confirm_email(self):
        """Confirmar email do usuário"""
        return self.update(confirmed=True, confirmed_on=datetime.now().isoformat())

class SupabaseRegistroPonto:
    """Modelo para registros de ponto no Supabase"""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.data = data.get('data')
        self.entrada = data.get('entrada')
        self.saida_almoco = data.get('saida_almoco')
        self.retorno_almoco = data.get('retorno_almoco')
        self.saida_final = data.get('saida_final')
        self.entrada_lat = data.get('entrada_lat')
        self.entrada_lng = data.get('entrada_lng')
        self.saida_almoco_lat = data.get('saida_almoco_lat')
        self.saida_almoco_lng = data.get('saida_almoco_lng')
        self.retorno_almoco_lat = data.get('retorno_almoco_lat')
        self.retorno_almoco_lng = data.get('retorno_almoco_lng')
        self.saida_final_lat = data.get('saida_final_lat')
        self.saida_final_lng = data.get('saida_final_lng')
        self.banco_horas = data.get('banco_horas')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')

    @classmethod
    def find_by_user_and_date(cls, user_id: int, data: date):
        """Buscar registro por usuário e data"""
        supabase = get_supabase_admin_client()
        
        response = supabase.table('registros_ponto').select('*').eq('user_id', user_id).eq('data', data.isoformat()).execute()
        if response.data:
            return cls(response.data[0])
        return None

    @classmethod
    def find_by_user(cls, user_id: int, limit: int = 180):
        """Buscar registros por usuário"""
        supabase = get_supabase_admin_client()
        
        response = supabase.table('registros_ponto').select('*').eq('user_id', user_id).order('data', desc=True).limit(limit).execute()
        return [cls(registro_data) for registro_data in response.data]

    @classmethod
    def find_by_user_and_period(cls, user_id: int, data_inicio: Optional[date] = None, data_fim: Optional[date] = None):
        """Buscar registros por usuário e período"""
        supabase = get_supabase_admin_client()
        
        query = supabase.table('registros_ponto').select('*').eq('user_id', user_id)
        
        if data_inicio:
            query = query.gte('data', data_inicio.isoformat())
        if data_fim:
            query = query.lte('data', data_fim.isoformat())
            
        response = query.order('data', desc=True).execute()
        return [cls(registro_data) for registro_data in response.data]

    @classmethod
    def get_all_by_period(cls, data_inicio: Optional[date] = None, data_fim: Optional[date] = None):
        """Buscar todos os registros por período (apenas para admins)"""
        supabase = get_supabase_admin_client()
        
        query = supabase.table('registros_ponto').select('*')
        
        if data_inicio:
            query = query.gte('data', data_inicio.isoformat())
        if data_fim:
            query = query.lte('data', data_fim.isoformat())
            
        response = query.order('data', desc=True).execute()
        return [cls(registro_data) for registro_data in response.data]

    @classmethod
    def create(cls, user_id: int, data: date):
        """Criar novo registro de ponto"""
        supabase = get_supabase_admin_client()
        
        registro_data = {
            'user_id': user_id,
            'data': data.isoformat()
        }
        
        response = supabase.table('registros_ponto').insert(registro_data).execute()
        if response.data:
            return cls(response.data[0])
        return None

    def update(self, **kwargs):
        """Atualizar registro de ponto"""
        supabase = get_supabase_admin_client()
        
        # Adicionar timestamp de atualização
        kwargs['updated_at'] = datetime.now().isoformat()
        
        response = supabase.table('registros_ponto').update(kwargs).eq('id', self.id).execute()
        if response.data:
            # Atualizar atributos locais
            for key, value in kwargs.items():
                setattr(self, key, value)
            return True
        return False

    def to_dict(self):
        """Converter para dicionário"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'data': self.data,
            'entrada': self.entrada,
            'saida_almoco': self.saida_almoco,
            'retorno_almoco': self.retorno_almoco,
            'saida_final': self.saida_final,
            'banco_horas': self.banco_horas
        }

