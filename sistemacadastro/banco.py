import os
import requests
from dotenv import load_dotenv

load_dotenv()

class BancoLocal:
    def __init__(self):
        # ATENÇÃO: Certifique-se de que o arquivo se chama api.php na HostGator.
        # Se você o colocou direto na raiz sem o ".php", pode deixar apenas "https://serz.com.br"
        self.url_api = "https://serz.com.br/api.php"
        self.token = os.getenv("API_TOKEN", "CHAVE_SECRETA_MUITO_FORTE_AQUI_123456789_XYZ")
        
        # Mantém as conexões HTTP persistentes e otimizadas para múltiplos acessos
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Token": self.token, 
            "Content-Type": "application/json",
            # CORREÇÃO CRÍTICA PARA MOD_SECURITY: Simula um navegador real para evitar o bloqueio 406
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def registrar_log(self, usuario, mensagem):
        try:
            payload = {"usuario": usuario, "mensagem": mensagem}
            self.session.post(f"{self.url_api}?action=registrar_log", json=payload, timeout=5)
        except Exception:
            pass

    def verificar_login(self, usuario, senha):
        try:
            payload = {"usuario": usuario, "senha": senha}
            resposta = self.session.post(f"{self.url_api}?action=verificar_login", json=payload, timeout=10)
            
            # ========================================================
            # BLOCO DE DIAGNÓSTICO: Mostra o erro real no terminal
            # ========================================================
            print("\n" + "="*40)
            print("         DIAGNÓSTICO DE LOGIN DA API")
            print("="*40)
            print(f"URL Chamada: {self.url_api}?action=verificar_login")
            print(f"Status Code retornado: {resposta.status_code}")
            print(f"Resposta bruta do servidor:\n{resposta.text}")
            print("="*40 + "\n")
            # ========================================================

            if resposta.status_code == 200:
                dados = resposta.json()
                return dados.get("perfil")
            return None
        except Exception as e:
            raise Exception(f"Servidor HostGator indisponível ou erro no script Python:\n{e}")

    def cadastrar_usuario(self, usuario, senha, email, perfil, usuario_autor):
        try:
            payload = {"usuario": usuario, "senha": senha, "email": email, "perfil": perfil}
            resposta = self.session.post(f"{self.url_api}?action=cadastrar_usuario", json=payload, timeout=10)
            if resposta.status_code != 200:
                raise Exception(resposta.json().get("erro", "Erro desconhecido"))
            self.registrar_log(usuario_autor, f"Cadastrou novo usuário: {usuario} ({perfil}) com e-mail {email}")
        except Exception as e:
            raise Exception(f"Falha ao salvar usuário na nuvem:\n{e}")

    def listar_usuarios(self):
        try:
            resposta = self.session.post(f"{self.url_api}?action=listar_usuarios", timeout=10)
            if resposta.status_code == 200:
                return resposta.json()
            return []
        except Exception:
            return []

    def listar_produtos(self):
        try:
            resposta = self.session.post(f"{self.url_api}?action=listar_produtos", timeout=10)
            if resposta.status_code == 200:
                return resposta.json()
            return []
        except Exception:
            return []

    def listar_movimentacoes(self):
        try:
            resposta = self.session.post(f"{self.url_api}?action=listar_movimentacoes", timeout=10)
            if resposta.status_code == 200:
                return resposta.json()
            return []
        except Exception:
            return []

    def listar_logs(self):
        try:
            resposta = self.session.post(f"{self.url_api}?action=listar_logs", timeout=10)
            if resposta.status_code == 200:
                return resposta.json()
            return []
        except Exception:
            return []

    def cadastrar_produto(self, p_id, nome, local, v_ent, v_sai, taxa, usuario):
        try:
            payload = {
                "id": p_id, "nome": nome, "localizacao": local,
                "valor_entrada": v_ent, "valor_saida_base": v_sai, "taxa_venda_porcentagem": taxa
            }
            resposta = self.session.post(f"{self.url_api}?action=cadastrar_produto", json=payload, timeout=10)
            if resposta.status_code != 200:
                raise Exception(resposta.json().get("erro", "Erro no servidor"))
            self.registrar_log(usuario, f"Produto cadastrado: {nome} (ID: {p_id})")
        except Exception as e:
            raise Exception(f"Erro ao salvar produto remotamente:\n{e}")

    def editar_produto(self, p_id, nome, local, v_ent, v_sai, taxa, usuario):
        try:
            payload = {
                "id": p_id, "nome": nome, "localizacao": local,
                "valor_entrada": v_ent, "valor_saida_base": v_sai, "taxa_venda_porcentagem": taxa
            }
            resposta = self.session.post(f"{self.url_api}?action=editar_produto", json=payload, timeout=10)
            if resposta.status_code != 200:
                raise Exception(resposta.json().get("erro", "Erro no servidor"))
            self.registrar_log(usuario, f"Produto ID {p_id} editado na nuvem.")
        except Exception as e:
            raise Exception(f"Erro ao editar produto:\n{e}")

    def deletar_produto(self, p_id, usuario):
        try:
            payload = {"id": p_id}
            resposta = self.session.post(f"{self.url_api}?action=deletar_produto", json=payload, timeout=10)
            if resposta.status_code != 200:
                raise Exception(resposta.json().get("erro", "Erro no servidor"))
            self.registrar_log(usuario, f"Produto ID {p_id} excluído da nuvem.")
        except Exception as e:
            raise Exception(f"Erro ao remover produto:\n{e}")

    def processar_movimentacao(self, p_id, tipo, qtd, frete, imposto, desconto, usuario):
        try:
            payload = {
                "produto_id": p_id, "tipo": tipo, "quantidade": qtd,
                "frete": frete, "imposto": imposto, "desconto": desconto, "usuario": usuario
            }
            resposta = self.session.post(f"{self.url_api}?action=processar_movimentacao", json=payload, timeout=12)
            if resposta.status_code != 200:
                raise Exception(resposta.json().get("erro", "Erro na operação"))
            self.registrar_log(usuario, f"Movimentação [{tipo}] de {qtd} un para o ID {p_id}.")
        except Exception as e:
            raise Exception(f"Erro ao registrar movimentação na nuvem:\n{e}")
