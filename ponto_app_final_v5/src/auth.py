from functools import wraps
from flask import request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
from supabase_models import SupabaseUser

def generate_token(user_id):
    exp = datetime.utcnow() + timedelta(days=current_app.config.get("JWT_EXP_DAYS", 7))
    payload = {"sub": user_id, "exp": exp}
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm="HS256")
    return token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"erro": "Token ausente ou formato inválido"}), 401
        token = parts[1]
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            user = SupabaseUser.find_by_id(data['sub'])
            if not user:
                return jsonify({"erro": "Usuário do token não encontrado"}), 401
            request.user = user
        except jwt.ExpiredSignatureError:
            return jsonify({"erro": "Token expirado"}), 401
        except Exception:
            return jsonify({"erro": "Token inválido"}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Primeiro verifica se o token é válido
        auth = request.headers.get("Authorization", "")
        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"erro": "Token ausente ou formato inválido"}), 401
        token = parts[1]
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            user = SupabaseUser.find_by_id(data['sub'])
            if not user:
                return jsonify({"erro": "Usuário do token não encontrado"}), 401
            if not user.is_admin:
                return jsonify({"erro": "Acesso negado. Privilégios de administrador necessários"}), 403
            request.user = user
        except jwt.ExpiredSignatureError:
            return jsonify({"erro": "Token expirado"}), 401
        except Exception:
            return jsonify({"erro": "Token inválido"}), 401
        return f(*args, **kwargs)
    return decorated
