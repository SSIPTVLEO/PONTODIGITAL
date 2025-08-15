import os
from flask import Flask, request, jsonify, render_template, url_for, current_app, make_response, session
from datetime import datetime, date
from passlib.hash import bcrypt
from models import db
from supabase_models import SupabaseUser, SupabaseRegistroPonto
from utils import calcular_distancia_em_metros, EMPRESA_LAT, EMPRESA_LNG, calcular_banco_horas
from auth import generate_token, token_required, admin_required
from tokens import generate_confirmation_token, confirm_token
from email_service import mail, send_email
from supabase_models import SupabaseUser, SupabaseRegistroPonto
from config import Config
def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    
    # Inicializa mail dentro do contexto da aplicação
    mail.init_app(app)

    return app

app = create_app()
@app.route("/")
def index():
    # Redirecionar para dashboard
    return redirect(url_for('dashboard'))

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", max_dist=app.config['MAX_DIST_METERS'])

@app.route("/historico")
def historico():
    return render_template("historico.html")

@app.route("/relatorios")
def relatorios():
    return render_template("relatorios.html")

@app.route("/perfil")
def perfil():
    return render_template("perfil.html")

# Rota para página admin
@app.route("/admin")
def admin():
    return render_template("admin.html")

# Telas separadas (GET) para login e cadastro
@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/cadastro", methods=["GET"])
def cadastro_page():
    return render_template("cadastro.html")

@app.route("/confirm-page")
def confirm_page():
    return render_template("confirm.html")

# API Auth
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    nome = data.get("nome")
    email = data.get("email")
    senha = data.get("senha")
    if not all([nome, email, senha]):
        return jsonify({"erro":"nome, email e senha são obrigatórios"}), 400
    
    # Verificar se email já existe no Supabase
    existing_user = SupabaseUser.find_by_email(email)
    if existing_user:
        return jsonify({"erro":"email já cadastrado"}), 400
    
    senha_hash = bcrypt.hash(senha)
    user = SupabaseUser.create(nome=nome, email=email, senha_hash=senha_hash, confirmed=False)
    
    if not user:
        return jsonify({"erro":"Erro ao criar usuário"}), 500

    token = generate_confirmation_token(user.email)
    confirm_url = url_for("confirm_email", token=token, _external=True)
    
    try:
        send_email(user.email, "Confirme seu Email", "email/activate", user=user, confirm_url=confirm_url)
    except Exception as e:
        # Se falhar no envio do email, ainda retorna sucesso mas avisa
        return jsonify({"sucesso":"Usuário criado, mas houve problema no envio do email de confirmação. Contate o suporte."}), 201

    return jsonify({"sucesso":"Usuário criado. Por favor, confirme seu email para ativar sua conta."}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    senha = data.get("senha")
    if not all([email, senha]):
        return jsonify({"erro":"email e senha são obrigatórios"}), 400
    
    user = SupabaseUser.find_by_email(email)
    if not user or not bcrypt.verify(senha, user.senha_hash):
        return jsonify({"erro":"credenciais inválidas"}), 401
    if not user.confirmed:
        return jsonify({"erro":"Por favor, confirme seu email para ativar sua conta."}), 401
    
    token = generate_token(user.id)
    return jsonify({
        "token": token, 
        "user_id": user.id, 
        "nome": user.nome,
        "is_admin": user.is_admin
    }), 200

# Endpoints protegidos
@app.route("/registrar-ponto", methods=["POST"])
@token_required
def registrar_ponto():
    data = request.get_json() or {}
    tipo = data.get("tipo")
    lat = data.get("lat")
    lng = data.get("lng")

    if tipo not in ("entrada", "saida_almoco", "retorno_almoco", "saida_final"):
        return jsonify({"erro": "Tipo inválido"}), 400
    if lat is None or lng is None:
        return jsonify({"erro": "Localização não enviada"}), 400

    user = request.user

    distancia = calcular_distancia_em_metros(lat, lng, EMPRESA_LAT, EMPRESA_LNG)
    if distancia > app.config['MAX_DIST_METERS']:
        return jsonify({"erro": f"Você está fora do raio permitido de {app.config['MAX_DIST_METERS']} metros (distância: {int(distancia)} m)"}), 400

    hoje = date.today()
    registro = RegistroPonto.query.filter_by(user_id=user.id, data=hoje).first()
    if not registro:
        registro = RegistroPonto(user_id=user.id, data=hoje)
        db.session.add(registro)

    agora = datetime.utcnow().time()

    # Imutabilidade: só grava se o campo ainda estiver vazio
    if tipo == "entrada":
        if registro.entrada:
            return jsonify({"erro": "Entrada já registrada e não pode ser alterada"}), 400
        registro.entrada = agora
        registro.entrada_lat = lat
        registro.entrada_lng = lng
    elif tipo == "saida_almoco":
        if registro.saida_almoco:
            return jsonify({"erro": "Saída para almoço já registrada e não pode ser alterada"}), 400
        registro.saida_almoco = agora
        registro.saida_almoco_lat = lat
        registro.saida_almoco_lng = lng
    elif tipo == "retorno_almoco":
        if registro.retorno_almoco:
            return jsonify({"erro": "Retorno do almoço já registrado e não pode ser alterado"}), 400
        registro.retorno_almoco = agora
        registro.retorno_almoco_lat = lat
        registro.retorno_almoco_lng = lng
    elif tipo == "saida_final":
        if registro.saida_final:
            return jsonify({"erro": "Saída final já registrada e não pode ser alterada"}), 400
        registro.saida_final = agora
        registro.saida_final_lat = lat
        registro.saida_final_lng = lng

    # Recalcula banco de horas se todos os horários existirem
    if registro.entrada and registro.saida_almoco and registro.retorno_almoco and registro.saida_final:
        banco = calcular_banco_horas(registro.entrada, registro.saida_almoco, registro.retorno_almoco, registro.saida_final)
        registro.banco_horas = banco

    db.session.commit()
    return jsonify({"sucesso": "Ponto registrado com sucesso", "distancia_m": int(distancia)}), 200

@app.route("/relatorio", methods=["GET"])
@token_required
def relatorio():
    user = request.user
    registros = RegistroPonto.query.filter_by(user_id=user.id).order_by(RegistroPonto.data.desc()).limit(180).all()
    out = []
    for r in registros:
        out.append({
            "data": r.data.isoformat(),
            "entrada": r.entrada.isoformat() if r.entrada else None,
            "saida_almoco": r.saida_almoco.isoformat() if r.saida_almoco else None,
            "retorno_almoco": r.retorno_almoco.isoformat() if r.retorno_almoco else None,
            "saida_final": r.saida_final.isoformat() if r.saida_final else None,
            "banco_horas": r.banco_horas
        })
    return jsonify(out)

@app.route("/relatorio/csv", methods=["GET"])
@token_required
def relatorio_csv():
    from flask import make_response
    import csv
    from io import StringIO
    
    user = request.user
    data_inicio = request.args.get('inicio')
    data_fim = request.args.get('fim')
    
    query = RegistroPonto.query.filter_by(user_id=user.id)
    
    if data_inicio:
        query = query.filter(RegistroPonto.data >= data_inicio)
    if data_fim:
        query = query.filter(RegistroPonto.data <= data_fim)
    
    registros = query.order_by(RegistroPonto.data.desc()).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Cabeçalho
    writer.writerow(['Data', 'Entrada', 'Saída Almoço', 'Retorno Almoço', 'Saída Final', 'Banco de Horas'])
    
    # Dados
    for r in registros:
        writer.writerow([
            r.data.strftime('%d/%m/%Y'),
            r.entrada.strftime('%H:%M') if r.entrada else '',
            r.saida_almoco.strftime('%H:%M') if r.saida_almoco else '',
            r.retorno_almoco.strftime('%H:%M') if r.retorno_almoco else '',
            r.saida_final.strftime('%H:%M') if r.saida_final else '',
            f"{r.banco_horas:.2f}" if r.banco_horas is not None else ''
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=relatorio_ponto_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response

@app.route("/relatorio/pdf", methods=["GET"])
@token_required
def relatorio_pdf():
    from flask import make_response
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from io import BytesIO
    
    user = request.user
    data_inicio = request.args.get('inicio')
    data_fim = request.args.get('fim')
    
    query = RegistroPonto.query.filter_by(user_id=user.id)
    
    if data_inicio:
        query = query.filter(RegistroPonto.data >= data_inicio)
    if data_fim:
        query = query.filter(RegistroPonto.data <= data_fim)
    
    registros = query.order_by(RegistroPonto.data.desc()).all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Centralizado
    )
    
    # Título
    title = Paragraph("Relatório de Ponto Eletrônico", title_style)
    elements.append(title)
    
    # Informações do relatório
    info_style = styles['Normal']
    periodo = f"Período: {data_inicio or 'Início'} a {data_fim or 'Fim'}"
    gerado_em = f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    usuario = f"Usuário: {user.nome}"
    
    elements.append(Paragraph(periodo, info_style))
    elements.append(Paragraph(gerado_em, info_style))
    elements.append(Paragraph(usuario, info_style))
    elements.append(Spacer(1, 20))
    
    # Tabela de dados
    data = [['Data', 'Entrada', 'Saída Almoço', 'Retorno Almoço', 'Saída Final', 'Banco de Horas']]
    
    for r in registros:
        data.append([
            r.data.strftime('%d/%m/%Y'),
            r.entrada.strftime('%H:%M') if r.entrada else '--:--',
            r.saida_almoco.strftime('%H:%M') if r.saida_almoco else '--:--',
            r.retorno_almoco.strftime('%H:%M') if r.retorno_almoco else '--:--',
            r.saida_final.strftime('%H:%M') if r.saida_final else '--:--',
            f"{r.banco_horas:.2f}h" if r.banco_horas is not None else '--'
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Estatísticas
    elements.append(Spacer(1, 30))
    stats_title = Paragraph("Estatísticas do Período", styles['Heading2'])
    elements.append(stats_title)
    
    # Calcular estatísticas
    dias_trabalhados = len([r for r in registros if r.entrada])
    total_banco_horas = sum([r.banco_horas for r in registros if r.banco_horas is not None])
    
    stats_text = f"""
    Dias trabalhados: {dias_trabalhados}<br/>
    Total banco de horas: {total_banco_horas:.2f}h<br/>
    Média diária: {(total_banco_horas / dias_trabalhados):.2f}h (se dias_trabalhados > 0)
    """
    
    elements.append(Paragraph(stats_text, info_style))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=relatorio_ponto_{datetime.now().strftime("%Y%m%d")}.pdf'
    
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)

# Rotas Admin
@app.route("/admin/usuarios", methods=["GET"])
@admin_required
def admin_listar_usuarios():
    """Lista todos os usuários do sistema (apenas para admins)"""
    usuarios = User.query.all()
    usuarios_data = []
    for user in usuarios:
        # Buscar estatísticas básicas do usuário
        registros = RegistroPonto.query.filter_by(user_id=user.id).all()
        total_dias = len(registros)
        
        usuarios_data.append({
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "is_admin": user.is_admin,
            "total_registros": total_dias
        })
    
    return jsonify({"usuarios": usuarios_data}), 200

@app.route("/admin/usuario/<int:user_id>/registros", methods=["GET"])
@admin_required
def admin_registros_usuario(user_id):
    """Busca registros de ponto de um usuário específico (apenas para admins)"""
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    
    # Verificar se o usuário existe
    usuario = User.query.get(user_id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    
    query = RegistroPonto.query.filter_by(user_id=user_id)
    
    # Aplicar filtros de data se fornecidos
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            query = query.filter(RegistroPonto.data >= data_inicio_obj)
        except ValueError:
            return jsonify({"erro": "Formato de data_inicio inválido. Use YYYY-MM-DD"}), 400
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d").date()
            query = query.filter(RegistroPonto.data <= data_fim_obj)
        except ValueError:
            return jsonify({"erro": "Formato de data_fim inválido. Use YYYY-MM-DD"}), 400
    
    registros = query.order_by(RegistroPonto.data.desc()).all()
    
    registros_data = []
    for registro in registros:
        registros_data.append({
            "id": registro.id,
            "data": registro.data.strftime("%Y-%m-%d"),
            "entrada": registro.entrada.strftime("%H:%M") if registro.entrada else None,
            "saida_almoco": registro.saida_almoco.strftime("%H:%M") if registro.saida_almoco else None,
            "retorno_almoco": registro.retorno_almoco.strftime("%H:%M") if registro.retorno_almoco else None,
            "saida_final": registro.saida_final.strftime("%H:%M") if registro.saida_final else None,
            "banco_horas": registro.banco_horas
        })
    
    return jsonify({
        "usuario": {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email
        },
        "registros": registros_data
    }), 200

@app.route("/admin/relatorio/<int:user_id>", methods=["GET"])
@admin_required
def admin_relatorio_usuario(user_id):
    """Gera relatório de um usuário específico (apenas para admins)"""
    formato = request.args.get("formato", "html")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    tipo = request.args.get("tipo", "completo")
    
    # Verificar se o usuário existe
    usuario = User.query.get(user_id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    
    query = RegistroPonto.query.filter_by(user_id=user_id)
    
    # Aplicar filtros de data
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            query = query.filter(RegistroPonto.data >= data_inicio_obj)
        except ValueError:
            return jsonify({"erro": "Formato de data_inicio inválido"}), 400
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d").date()
            query = query.filter(RegistroPonto.data <= data_fim_obj)
        except ValueError:
            return jsonify({"erro": "Formato de data_fim inválido"}), 400
    
    registros = query.order_by(RegistroPonto.data.desc()).all()
    
    # Calcular estatísticas
    total_dias = len(registros)
    total_horas = sum([r.banco_horas or 0 for r in registros])
    
    dados_relatorio = {
        "usuario": {
            "nome": usuario.nome,
            "email": usuario.email
        },
        "periodo": {
            "inicio": data_inicio or "Início dos registros",
            "fim": data_fim or "Fim dos registros"
        },
        "estatisticas": {
            "total_dias": total_dias,
            "total_horas": total_horas,
            "media_diaria": total_horas / total_dias if total_dias > 0 else 0
        },
        "registros": []
    }
    
    for registro in registros:
        dados_relatorio["registros"].append({
            "data": registro.data.strftime("%d/%m/%Y"),
            "entrada": registro.entrada.strftime("%H:%M") if registro.entrada else "--:--",
            "saida_almoco": registro.saida_almoco.strftime("%H:%M") if registro.saida_almoco else "--:--",
            "retorno_almoco": registro.retorno_almoco.strftime("%H:%M") if registro.retorno_almoco else "--:--",
            "saida_final": registro.saida_final.strftime("%H:%M") if registro.saida_final else "--:--",
            "banco_horas": f"{registro.banco_horas:.2f}h" if registro.banco_horas else "0.00h"
        })
    
    if formato == "csv":
        return gerar_csv_admin(dados_relatorio)
    elif formato == "pdf":
        return gerar_pdf_admin(dados_relatorio)
    else:
        return jsonify(dados_relatorio), 200

@app.route("/admin/relatorio-geral", methods=["GET"])
@admin_required
def admin_relatorio_geral():
    """Gera relatório geral de todos os usuários (apenas para admins)"""
    formato = request.args.get("formato", "html")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    
    usuarios = User.query.all()
    dados_relatorio = {
        "periodo": {
            "inicio": data_inicio or "Início dos registros",
            "fim": data_fim or "Fim dos registros"
        },
        "usuarios": []
    }
    
    for usuario in usuarios:
        query = RegistroPonto.query.filter_by(user_id=usuario.id)
        
        # Aplicar filtros de data
        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d").date()
                query = query.filter(RegistroPonto.data >= data_inicio_obj)
            except ValueError:
                continue
        
        if data_fim:
            try:
                data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d").date()
                query = query.filter(RegistroPonto.data <= data_fim_obj)
            except ValueError:
                continue
        
        registros = query.all()
        total_dias = len(registros)
        total_horas = sum([r.banco_horas or 0 for r in registros])
        
        dados_relatorio["usuarios"].append({
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "total_dias": total_dias,
            "total_horas": total_horas,
            "media_diaria": total_horas / total_dias if total_dias > 0 else 0
        })
    
    if formato == "csv":
        return gerar_csv_geral_admin(dados_relatorio)
    elif formato == "pdf":
        return gerar_pdf_geral_admin(dados_relatorio)
    else:
        return jsonify(dados_relatorio), 200

def gerar_csv_admin(dados):
    """Gera CSV para relatório admin de usuário específico"""
    import io
    output = io.StringIO()
    output.write("Data,Entrada,Saída Almoço,Retorno Almoço,Saída Final,Banco de Horas\n")
    
    for registro in dados["registros"]:
        output.write(f"{registro['data']},{registro['entrada']},{registro['saida_almoco']},{registro['retorno_almoco']},{registro['saida_final']},{registro['banco_horas']}\n")
    
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=relatorio_{dados['usuario']['nome'].replace(' ', '_')}.csv"
    response.headers["Content-type"] = "text/csv"
    return response

def gerar_pdf_admin(dados):
    """Gera PDF para relatório admin de usuário específico"""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    import io
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center
    )
    story.append(Paragraph(f"Relatório de Ponto - {dados['usuario']['nome']}", title_style))
    story.append(Spacer(1, 12))
    
    # Informações do usuário
    info_style = styles['Normal']
    story.append(Paragraph(f"<b>Usuário:</b> {dados['usuario']['nome']}", info_style))
    story.append(Paragraph(f"<b>Email:</b> {dados['usuario']['email']}", info_style))
    story.append(Paragraph(f"<b>Período:</b> {dados['periodo']['inicio']} a {dados['periodo']['fim']}", info_style))
    story.append(Spacer(1, 20))
    
    # Estatísticas
    story.append(Paragraph("<b>Estatísticas:</b>", styles['Heading2']))
    story.append(Paragraph(f"Total de dias trabalhados: {dados['estatisticas']['total_dias']}", info_style))
    story.append(Paragraph(f"Total de horas: {dados['estatisticas']['total_horas']:.2f}h", info_style))
    story.append(Paragraph(f"Média diária: {dados['estatisticas']['media_diaria']:.2f}h", info_style))
    story.append(Spacer(1, 20))
    
    # Tabela de registros
    story.append(Paragraph("<b>Registros:</b>", styles['Heading2']))
    
    table_data = [["Data", "Entrada", "Saída Almoço", "Retorno Almoço", "Saída Final", "Banco de Horas"]]
    for registro in dados["registros"]:
        table_data.append([
            registro["data"],
            registro["entrada"],
            registro["saida_almoco"],
            registro["retorno_almoco"],
            registro["saida_final"],
            registro["banco_horas"]
        ])
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    doc.build(story)
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=relatorio_{dados['usuario']['nome'].replace(' ', '_')}.pdf"
    response.headers["Content-Type"] = "application/pdf"
    return response

def gerar_csv_geral_admin(dados):
    """Gera CSV para relatório geral admin"""
    import io
    output = io.StringIO()
    output.write("Nome,Email,Total Dias,Total Horas,Média Diária\n")
    
    for usuario in dados["usuarios"]:
        output.write(f"{usuario['nome']},{usuario['email']},{usuario['total_dias']},{usuario['total_horas']:.2f},{usuario['media_diaria']:.2f}\n")
    
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=relatorio_geral.csv"
    response.headers["Content-type"] = "text/csv"
    return response

def gerar_pdf_geral_admin(dados):
    """Gera PDF para relatório geral admin"""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    import io
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center
    )
    story.append(Paragraph("Relatório Geral de Usuários", title_style))
    story.append(Spacer(1, 12))
    
    # Período
    info_style = styles['Normal']
    story.append(Paragraph(f"<b>Período:</b> {dados['periodo']['inicio']} a {dados['periodo']['fim']}", info_style))
    story.append(Spacer(1, 20))
    
    # Tabela de usuários
    table_data = [["Nome", "Email", "Total Dias", "Total Horas", "Média Diária"]]
    for usuario in dados["usuarios"]:
        table_data.append([
            usuario["nome"],
            usuario["email"],
            str(usuario["total_dias"]),
            f"{usuario['total_horas']:.2f}h",
            f"{usuario['media_diaria']:.2f}h"
        ])
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    doc.build(story)
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=relatorio_geral.pdf"
    response.headers["Content-Type"] = "application/pdf"
    return response

@app.route("/confirm/<token>")
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        return jsonify({"erro": "O link de confirmação é inválido ou expirou."}), 400

    user = SupabaseUser.find_by_email(email)
    if not user:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    if user.confirmed:
        return jsonify({"sucesso": "Conta já confirmada. Por favor, faça login."}), 200

    if user.confirm_email():
        return jsonify({"sucesso": "Você confirmou sua conta! Por favor, faça login."}), 200
    else:
        return jsonify({"erro": "Erro ao confirmar conta. Tente novamente."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
