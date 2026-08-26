import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    GRAFICOS_DISPONIVEIS = True
except ImportError:
    GRAFICOS_DISPONIVEIS = False

class GeradorRelatoriosPDF:
    def __init__(self, banco):
        self.banco = banco
        self.estilos = getSampleStyleSheet()

    def gerar_pdf_produto(self, p_id, usuario_atual):
        produtos = self.banco.listar_produtos()
        prod = next((p for p in produtos if str(p['id']).strip() == str(p_id).strip()), None)
        
        if not prod:
            raise ValueError("Produto não encontrado para emissão do relatório.")
            
        movimentacoes = self.banco.listar_movimentacoes()
        movs_filtradas = [m for m in movimentacoes if str(m['produto_id']).strip() == str(p_id).strip()]
        
        nome_arquivo = f"Relatorio_Produto_{p_id}.pdf"
        doc = SimpleDocTemplate(nome_arquivo, pagesize=letter)
        elementos = []
        
        elementos.append(Paragraph(f"<b>RELATÓRIO INDIVIDUAL: {prod['nome'].upper()}</b>", self.estilos['Title']))
        elementos.append(Spacer(1, 15))
        
        info_html = (
            f"<b>ID único:</b> {p_id} | <b>Localização:</b> {prod['localizacao']} | "
            f"<b>Estoque Atual:</b> {prod['quantidade']} unidades<br/>"
            f"<b>Custo Entrada Base:</b> R$ {float(prod['valor_entrada']):.2f} | "
            f"<b>Preço Saída Base:</b> R$ {float(prod['valor_saida_base']):.2f} | "
            f"<b>Taxa Interna:</b> {prod['taxa_venda_porcentagem']}%"
        )
        elementos.append(Paragraph(info_html, self.estilos['Normal']))
        elementos.append(Spacer(1, 20))
        
        dados_tabela = [["Data/Hora", "Tipo", "Qtd", "Imp %", "Frete", "Desc", "Valor Un."]]
        for m in movs_filtradas:
            dados_tabela.append([
                m['data_hora'], m['tipo'], m['quantidade'],
                f"{m['imposto']}%", f"R$ {m['frete']}", f"R$ {m['desconto']}", f"R$ {m['valor_final']}"
            ])
            
        t = Table(dados_tabela, colWidths=[120, 50, 40, 50, 50, 50, 70])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2c3e50")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 9)
        ]))
        elementos.append(t)
        
        doc.build(elementos)
        # AUDITORIA ATIVA: Registra na nuvem quem gerou o relatório do produto
        self.banco.registrar_log(usuario_atual, f"PDF Individual gerado para o produto ID: {p_id} ({prod['nome']}).")
        return nome_arquivo

    def gerar_pdf_periodo(self, data_inicio, data_fim, usuario_atual):
        movimentacoes = self.banco.listar_movimentacoes()
        movs_filtradas = []
        
        for m in movimentacoes:
            try:
                apenas_data_mov = m['data_hora'].split(" ")[0]
                if data_inicio <= apenas_data_mov <= data_fim:
                    movs_filtradas.append(m)
            except Exception:
                continue
                
        nome_arquivo = f"Relatorio_Movimentacao_{data_inicio}_a_{data_fim}.pdf"
        doc = SimpleDocTemplate(nome_arquivo, pagesize=letter)
        elementos = []
        
        elementos.append(Paragraph(f"<b>FECHAMENTO FINANCEIRO E DE MOVIMENTAÇÃO</b>", self.estilos['Title']))
        elementos.append(Paragraph(f"Período: {data_inicio} até {data_fim} | Emitido por: {usuario_atual}", self.estilos['Normal']))
        elementos.append(Spacer(1, 20))
        
        if not movs_filtradas:
            elementos.append(Paragraph("<b>Nenhuma movimentação localizada neste período de datas.</b>", self.estilos['Normal']))
            doc.build(elementos)
            return nome_arquivo
            
        dados_tabela = [["Prod ID", "Tipo", "Qtd", "Imposto", "Frete", "Desconto", "Valor Final"]]
        tot_e, tot_s = 0, 0
        
        for m in movs_filtradas:
            dados_tabela.append([
                m['produto_id'], m['tipo'], m['quantidade'],
                f"{m['imposto']}%", f"R${m['frete']}", f"R${m['desconto']}", f"R${m['valor_final']}"
            ])
            # CORRIGIDO: Alterado de 'quantity' para 'quantidade' para evitar quebra do Python
            if m['tipo'] == "ENTRADA": 
                tot_e += int(m['quantidade'])
            else: 
                tot_s += int(m['quantidade'])
                
        t = Table(dados_tabela, colWidths=[60, 60, 40, 60, 60, 60, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#16a085")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.silver),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 9)
        ]))
        elementos.append(t)
        elementos.append(Spacer(1, 20))
        
        if GRAFICOS_DISPONIVEIS:
            fig, ax = plt.subplots(figsize=(5, 2.5))
            ax.bar(['Entradas', 'Saídas'], [tot_e, tot_s], color=['#3498db', '#e74c3c'])
            ax.set_ylabel('Quantidade de Itens')
            ax.set_title('Fluxo de Volumetria do Período')
            plt.tight_layout()
            
            grafico_path = "temp_grafico.png"
            plt.savefig(grafico_path, dpi=150)
            plt.close()
            
            elementos.append(Paragraph("<b>Gráfico Volumétrico de Controle:</b>", self.estilos['Heading3']))
            elementos.append(Spacer(1, 5))
            elementos.append(Image(grafico_path, width=300, height=150))
            
        elementos.append(Spacer(1, 15))
        elementos.append(Paragraph(f"<b>Balanço Final:</b> Entradas: {tot_e} un. | Saídas: {tot_s} un.", self.estilos['Heading4']))
        
        doc.build(elementos)
        if GRAFICOS_DISPONIVEIS and os.path.exists("temp_grafico.png"):
            os.remove("temp_grafico.png")
            
        # AUDITORIA ATIVA: Salva na tabela de logs da HostGator o fechamento realizado
        self.banco.registrar_log(usuario_atual, f"Fechamento financeiro em PDF gerado para o período de {data_inicio} até {data_fim}.")
        return nome_arquivo
    def gerar_pdf_todos_produtos(self, usuario_atual):
        """Gera um PDF contendo a listagem completa de produtos em estoque."""
        produtos = self.banco.listar_produtos()
        
        nome_arquivo = "Listagem_Completa_Produtos.pdf"
        doc = SimpleDocTemplate(nome_arquivo, pagesize=letter)
        elementos = []
        
        elementos.append(Paragraph("<b>RELATÓRIO: LISTAGEM GERAL DE PRODUTOS</b>", self.estilos['Title']))
        elementos.append(Paragraph(f"Emitido por: {usuario_atual} | Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", self.estilos['Normal']))
        elementos.append(Spacer(1, 20))
        
        if not produtos:
            elementos.append(Paragraph("<b>Nenhum produto cadastrado no banco de dados remoto.</b>", self.estilos['Normal']))
            doc.build(elementos)
            return nome_arquivo
            
        dados_tabela = [["ID", "Nome do Produto", "Almoxarifado / Localização", "Estoque"]]
        for p in produtos:
            dados_tabela.append([
                p['id'], p['nome'], p['localizacao'], f"{p['quantidade']} un"
            ])
            
        t = Table(dados_tabela, colWidths=[80, 180, 160, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2c3e50")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (3,0), (3,-1), 'CENTER'), # Centraliza apenas o estoque
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ]))
        elementos.append(t)
        
        doc.build(elementos)
        self.banco.registrar_log(usuario_atual, "Gerou relatório em PDF de todos os produtos do estoque.")
        return nome_arquivo

    def gerar_pdf_todos_usuarios(self, usuario_atual):
        """Gera um PDF contendo a listagem de todos os usuários do sistema."""
        usuarios = self.banco.listar_usuarios()
        
        nome_arquivo = "Listagem_Geral_Usuarios.pdf"
        doc = SimpleDocTemplate(nome_arquivo, pagesize=letter)
        elementos = []
        
        elementos.append(Paragraph("<b>RELATÓRIO: CONTROLE DE USUÁRIOS E PERFIS</b>", self.estilos['Title']))
        elementos.append(Paragraph(f"Emitido por: {usuario_atual} | Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", self.estilos['Normal']))
        elementos.append(Spacer(1, 20))
        
        dados_tabela = [["Nome de Usuário", "E-mail Corporativo", "Nível de Acesso"]]
        for u in usuarios:
            dados_tabela.append([
                u['usuario'], u['email'], u['perfil']
            ])
            
        t = Table(dados_tabela, colWidths=[140, 220, 140])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#7f8c8d")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.silver),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ]))
        elementos.append(t)
        
        doc.build(elementos)
        self.banco.registrar_log(usuario_atual, "Gerou relatório em PDF contendo a listagem geral de usuários.")
        return nome_arquivo
