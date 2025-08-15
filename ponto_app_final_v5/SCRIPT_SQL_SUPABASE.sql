-- Script SQL para criar tabelas no Supabase
-- Execute este script no SQL Editor do seu projeto Supabase

-- Criar tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    confirmed BOOLEAN DEFAULT FALSE,
    confirmed_on TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Criar tabela de registros de ponto
CREATE TABLE IF NOT EXISTS registros_ponto (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    data DATE DEFAULT CURRENT_DATE NOT NULL,
    entrada TIME,
    saida_almoco TIME,
    retorno_almoco TIME,
    saida_final TIME,
    entrada_lat FLOAT,
    entrada_lng FLOAT,
    saida_almoco_lat FLOAT,
    saida_almoco_lng FLOAT,
    retorno_almoco_lat FLOAT,
    retorno_almoco_lng FLOAT,
    saida_final_lat FLOAT,
    saida_final_lng FLOAT,
    banco_horas FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_registros_user_id ON registros_ponto(user_id);
CREATE INDEX IF NOT EXISTS idx_registros_data ON registros_ponto(data);

-- Habilitar RLS (Row Level Security)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE registros_ponto ENABLE ROW LEVEL SECURITY;

-- Políticas de segurança para usuários
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Políticas de segurança para registros de ponto
CREATE POLICY "Users can view own records" ON registros_ponto
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own records" ON registros_ponto
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own records" ON registros_ponto
    FOR UPDATE USING (auth.uid()::text = user_id::text);

-- Políticas para admins (acesso total)
CREATE POLICY "Admins can view all users" ON users
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text 
            AND is_admin = TRUE
        )
    );

CREATE POLICY "Admins can view all records" ON registros_ponto
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id::text = auth.uid()::text 
            AND is_admin = TRUE
        )
    );

