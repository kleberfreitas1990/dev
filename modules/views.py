# modules/views.py

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from .models import db, Usuario, Apoiador, Produto, Pedido, Configuracao
from .auth import login_required, admin_required
from .serper import SerperAPI
from datetime import datetime
import json
import logging

# Criação do Blueprint
main_bp = Blueprint('main', __name__)

# ============================================
# LISTA DE APOIADORES (DADOS ESTÁTICOS)
# ============================================
APOIADORES = [
    {'nome': 'Iago Coelho', 'numero': '#2'},
    {'nome': 'Sandra Lopes', 'numero': '#3'},
    {'nome': 'Kaiky', 'numero': '#4'},
    {'nome': 'Vanessa Profiro', 'numero': '#5'},
]

# ============================================
# ROTAS PRINCIPAIS
# ============================================

@main_bp.route('/')
def index():
    """Página inicial"""
    produtos = Produto.query.filter_by(ativo=True).limit(6).all()
    return render_template('index.html', produtos=produtos)


@main_bp.route('/apoiadores')
def apoiadores():
    """Página de apoiadores"""
    return render_template('apoiadores.html', apoiadores=APOIADORES)


@main_bp.route('/sobre')
def sobre():
    """Página sobre"""
    return render_template('sobre.html')


@main_bp.route('/contato')
def contato():
    """Página de contato"""
    return render_template('contato.html')


@main_bp.route('/produtos')
def listar_produtos():
    """Listar todos os produtos"""
    produtos = Produto.query.filter_by(ativo=True).all()
    return render_template('produtos.html', produtos=produtos)


@main_bp.route('/produto/<int:id>')
def detalhe_produto(id):
    """Detalhe de um produto específico"""
    produto = Produto.query.get_or_404(id)
    return render_template('produto_detalhe.html', produto=produto)


@main_bp.route('/buscar')
def buscar():
    """Busca de produtos usando Serper API"""
    query = request.args.get('q', '')
    resultados = []
    
    if query:
        serper = SerperAPI()
        resultados = serper.buscar(query)
    
    return render_template('busca.html', query=query, resultados=resultados)


@main_bp.route('/carrinho')
def carrinho():
    """Página do carrinho de compras"""
    return render_template('carrinho.html')


@main_bp.route('/finalizar-pedido', methods=['GET', 'POST'])
@login_required
def finalizar_pedido():
    """Finalizar compra"""
    if request.method == 'POST':
        # Lógica para finalizar pedido
        return redirect(url_for('main.pedido_confirmado'))
    
    return render_template('finalizar_pedido.html')


@main_bp.route('/pedido-confirmado')
@login_required
def pedido_confirmado():
    """Página de confirmação de pedido"""
    return render_template('pedido_confirmado.html')


# ============================================
# ROTAS ADMINISTRATIVAS
# ============================================

@main_bp.route('/admin')
@admin_required
def admin():
    """Painel administrativo"""
    return render_template('admin/dashboard.html')


@main_bp.route('/admin/apoiadores')
@admin_required
def admin_apoiadores():
    """Gerenciar apoiadores"""
    # Aqui você pode buscar do banco de dados
    return render_template('admin/apoiadores.html', apoiadores=APOIADORES)


@main_bp.route('/admin/apoiadores/adicionar', methods=['POST'])
@admin_required
def admin_apoiador_adicionar():
    """Adicionar novo apoiador"""
    nome = request.form.get('nome')
    numero = request.form.get('numero')
    
    if nome:
        # Salvar no banco de dados
        novo = Apoiador(nome=nome, numero=numero)
        db.session.add(novo)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Apoiador adicionado!'})
    
    return jsonify({'success': False, 'message': 'Nome é obrigatório'})


@main_bp.route('/admin/apoiadores/remover/<int:id>', methods=['DELETE'])
@admin_required
def admin_apoiador_remover(id):
    """Remover apoiador"""
    apoiador = Apoiador.query.get_or_404(id)
    db.session.delete(apoiador)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Apoiador removido!'})


@main_bp.route('/admin/produtos')
@admin_required
def admin_produtos():
    """Gerenciar produtos"""
    produtos = Produto.query.all()
    return render_template('admin/produtos.html', produtos=produtos)


@main_bp.route('/admin/produtos/adicionar', methods=['POST'])
@admin_required
def admin_produto_adicionar():
    """Adicionar novo produto"""
    nome = request.form.get('nome')
    preco = request.form.get('preco')
    descricao = request.form.get('descricao')
    
    if nome and preco:
        produto = Produto(
            nome=nome,
            preco=float(preco),
            descricao=descricao,
            ativo=True
        )
        db.session.add(produto)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Produto adicionado!'})
    
    return jsonify({'success': False, 'message': 'Dados incompletos'})


@main_bp.route('/admin/configuracoes', methods=['GET', 'POST'])
@admin_required
def admin_configuracoes():
    """Configurações do sistema"""
    if request.method == 'POST':
        config = Configuracao.query.first()
        if not config:
            config = Configuracao()
        
        config.nome_site = request.form.get('nome_site')
        config.email_contato = request.form.get('email_contato')
        
        db.session.add(config)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Configurações salvas!'})
    
    config = Configuracao.query.first()
    return render_template('admin/configuracoes.html', config=config)


# ============================================
# ROTAS DE USUÁRIO
# ============================================

@main_bp.route('/perfil')
@login_required
def perfil():
    """Perfil do usuário"""
    return render_template('perfil.html')


@main_bp.route('/perfil/editar', methods=['POST'])
@login_required
def perfil_editar():
    """Editar perfil do usuário"""
    usuario = Usuario.query.get(session['usuario_id'])
    
    usuario.nome = request.form.get('nome', usuario.nome)
    usuario.email = request.form.get('email', usuario.email)
    usuario.telefone = request.form.get('telefone', usuario.telefone)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Perfil atualizado!'})


@main_bp.route('/meus-pedidos')
@login_required
def meus_pedidos():
    """Listar pedidos do usuário"""
    pedidos = Pedido.query.filter_by(usuario_id=session['usuario_id']).all()
    return render_template('meus_pedidos.html', pedidos=pedidos)


# ============================================
# ERROR HANDLERS
# ============================================

@main_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@main_bp.app_errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500


@main_bp.app_errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


# ============================================
# CONTEXT PROCESSORS
# ============================================

@main_bp.context_processor
def inject_config():
    """Injetar configurações em todos os templates"""
    config = Configuracao.query.first()
    return {
        'site_nome': config.nome_site if config else 'Meu Site',
        'site_email': config.email_contato if config else 'contato@site.com',
        'ano_atual': datetime.now().year
    }


@main_bp.context_processor
def inject_carrinho_count():
    """Injetar contagem do carrinho"""
    carrinho = session.get('carrinho', [])
    return {'carrinho_count': len(carrinho)}


# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def get_apoiadores():
    """Retorna lista de apoiadores"""
    # Se tiver no banco, busca do banco
    # apoiadores = Apoiador.query.all()
    # return [{'nome': a.nome, 'numero': a.numero} for a in apoiadores]
    
    # Senão, usa a lista estática
    return APOIADORES


def get_produtos_destaque():
    """Retorna produtos em destaque"""
    return Produto.query.filter_by(destaque=True, ativo=True).limit(6).all()


def get_categorias():
    """Retorna lista de categorias"""
    return ['Eletrônicos', 'Roupas', 'Livros', 'Casa', 'Esportes']
