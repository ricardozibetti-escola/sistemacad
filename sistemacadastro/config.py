import os
import requests
from dotenv import load_dotenv

# Carrega o token secreto do arquivo .env
load_dotenv()

# Configurações da sua API Web que está rodando no seu domínio
# (Ajuste 'api.php' para o nome real do seu arquivo de API se for diferente)
API_URL = "https://serz.com.br"  
API_TOKEN = os.getenv("API_TOKEN", "CHAVE_SECRETA_MUITO_FORTE_AQUI_123456789_XYZ")

def requisitar_api(action, dados_json=None):
    """
    Função centralizada para fazer requisições seguras para a API online.
    Evita bloqueios de IP e suporta múltiplos usuários ao mesmo tempo.
    """
    url_completa = f"{API_URL}?action={action}"
    
    headers = {
        "X-API-Token": API_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        # Envia a requisição POST com o JSON para a API PHP
        response = requests.post(url_completa, json=dados_json, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            return {"erro": "Token da API inválido ou não autorizado."}
        else:
            return {"erro": f"Erro no servidor web (Status {response.status_code})"}
            
    except requests.exceptions.RequestException as e:
        return {"erro": f"Falha ao conectar na API Web: {e}"}
