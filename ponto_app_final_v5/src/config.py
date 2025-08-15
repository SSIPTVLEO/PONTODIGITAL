import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_EXP_DAYS = int(os.environ.get("JWT_EXP_DAYS", "7"))
    DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///ponto.db"
    MAX_DIST_METERS = int(os.environ.get("MAX_DIST_METERS", "3000"))


    # Configurações de E-mail para Flask-Mail
    MAIL_SERVER = os.environ.get("MAIL_SERVER") or "mail.bellaotica.com"
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 465)
    MAIL_USE_TLS = False # Porta 465 usa SSL, não TLS
    MAIL_USE_SSL = True # Força SSL para porta 465
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME") or "_mainaccount@bellaotica.com"
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD") or "SUA_SENHA_DO_CPANEL_AQUI" # Substitua pela sua senha real
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER") or "_mainaccount@bellaotica.com"

    # Salt para itsdangerous
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT") or "very-secret-salt-change-me"
    
    # Configurações do Supabase
    SUPABASE_URL = os.environ.get("SUPABASE_URL") or "https://jrjgcrirhpvjussscolf.supabase.co"
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpyamdjcmlyaHB2anVzc3Njb2xmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjM3NDI0NTAsImV4cCI6MjAzOTMxODQ1MH0.G3-gkb2WUm-FQYQ0Rx8fUZHIwlwGv4wjlnRFLzEJfxs"
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpyamdjcmlyaHB2anVzc3Njb2xmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcyMzc0MjQ1MCwiZXhwIjoyMDM5MzE4NDUwfQ.DnvUeddS6HbQxMkXdKIsoS1-eW4mySOfLvhLYuKDd5s"

