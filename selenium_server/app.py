from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import time
from scraper import capturar_buscas_shopee, buscar_produtos_shopee, capturar_tendencias_shopee

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "service": "Selenium Scraper API",
        "endpoints": {
            "/buscas": "GET - Retorna termos de busca da Shopee",
            "/tendencias": "GET - Retorna tendências completas",
            "/produtos": "POST - Busca produtos por termo"
        }
    })

@app.route('/buscas', methods=['GET'])
def get_buscas():
    """
    Retorna os termos de busca em alta da Shopee
    """
    try:
        logger.info("Capturando buscas da Shopee...")
        termos = capturar_buscas_shopee()
        
        return jsonify({
            "success": True,
            "data": termos,
            "total": len(termos),
            "fonte": "selenium"
        })
        
    except Exception as e:
        logger.error(f"Erro: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/tendencias', methods=['GET'])
def get_tendencias():
    """
    Retorna tendências completas da Shopee
    """
    try:
        logger.info("Capturando tendências da Shopee...")
        dados = capturar_tendencias_shopee()
        
        return jsonify({
            "success": True,
            "data": dados,
            "fonte": "selenium"
        })
        
    except Exception as e:
        logger.error(f"Erro: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/produtos', methods=['POST'])
def get_produtos():
    """
    Busca produtos para um termo específico
    Body: {"termo": "smartwatch", "limite": 5}
    """
    try:
        data = request.get_json()
        termo = data.get('termo', '')
        limite = data.get('limite', 5)
        
        if not termo:
            return jsonify({
                "success": False,
                "error": "Termo não informado"
            }), 400
        
        logger.info(f"Buscando produtos para '{termo}'...")
        produtos = buscar_produtos_shopee(termo, limite)
        
        return jsonify({
            "success": True,
            "data": produtos,
            "total": len(produtos),
            "termo": termo,
            "fonte": "selenium"
        })
        
    except Exception as e:
        logger.error(f"Erro: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
