import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from banco import BancoLocal
from relatorios import GeradorRelatoriosPDF

class SistemaCompletoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle Logístico Remoto - Sincronizado")
        self.root.geometry("350x250")
        self.usuario_atual = None
        self.perfil_atual = None
        
        try:
            # Conexão direta com a classe cliente da API PHP
            self.banco = BancoLocal()
            self.relatorios = GeradorRelatoriosPDF(self.banco)
        except Exception as e:
            messagebox.showerror("Erro de Inicialização", f"Falha ao carregar o conector do sistema:\n{e}")
            self.root.destroy()
            return
            
        self.tela_login()

    def validar_reais(self, texto):
        if texto == "" or texto == ".": return True
        try:
            float(texto)
            return True
        except ValueError:
            return False

    def validar_inteiros(self, texto):
        if texto == "": return True
        return texto.isdigit()

    def limpar_tela(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def tela_login(self):
        self.limpar_tela()
        self.root.geometry("350x250")
        
        tk.Label(self.root, text="Login - ONLINE", font=("Arial", 14, "bold")).pack(pady=20)
        tk.Label(self.root, text="Usuário:").pack()
        self.ent_usuario = tk.Entry(self.root)
        self.ent_usuario.pack(pady=2)
        
        tk.Label(self.root, text="Senha:").pack()
        self.ent_senha = tk.Entry(self.root, show="*")
        self.ent_senha.pack(pady=2)
        
        tk.Button(self.root, text="Conectar ao Sistema", command=self.processar_login, bg="#2980b9", fg="white", width=18).pack(pady=15)

    def processar_login(self):
        usuario = self.ent_usuario.get().strip()
        senha = self.ent_senha.get().strip()
        
        try:
            resultado = self.banco.verificar_login(usuario, senha)
            if resultado:
                self.usuario_atual = usuario
                self.perfil_atual = resultado  # Atribui 'ADMINISTRADOR' ou 'OPERADOR' como string pura
                self.banco.registrar_log(self.usuario_atual, f"Usuário conectou via API Web HTTPS.")
                self.tela_principal()
            else:
                # REGISTRA TENTATIVA DE INVASÃO/ERRO NA NUVEM
                if usuario:
                    self.banco.registrar_log(usuario, "Tentativa de login malsucedida: Usuário ou senha incorretos.")
                messagebox.showerror("Erro de Acesso", "Usuário ou senha inválidos no servidor online.")
        except Exception as e:
            messagebox.showerror("Erro de Conexão", str(e))

    def tela_principal(self):
        self.limpar_tela()
        self.root.geometry("1100x600")
        
        topo = tk.Frame(self.root, bg="#2c3e50", height=35)
        topo.pack(fill="x", side="top")
        tk.Label(topo, text=f"Operador Online: {self.usuario_atual} ({self.perfil_atual})", bg="#2c3e50", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=10, pady=8)
        
        def acao_desconectar():
            self.banco.registrar_log(self.usuario_atual, "Usuário desconectou do sistema voluntariamente.")
            self.tela_login()
            
        tk.Button(topo, text="Desconectar", command=acao_desconectar, bg="#c0392b", fg="white", bd=0, padx=10).pack(side="right", padx=10, pady=5)

        caderno = ttk.Notebook(self.root)
        caderno.pack(fill="both", expand=True, pady=10)
        
        aba_produtos = tk.Frame(caderno)
        aba_movimentacao = tk.Frame(caderno)
        aba_relatorios = tk.Frame(caderno)
        aba_usuarios = tk.Frame(caderno)
        aba_logs = tk.Frame(caderno)
        
        caderno.add(aba_produtos, text="Estoque Geral em Tempo Real")
        caderno.add(aba_movimentacao, text="Lançar Movimentações")
        caderno.add(aba_relatorios, text="Filtros e Relatórios PDF")
        
        if self.perfil_atual == "ADMINISTRADOR":
            caderno.add(aba_usuarios, text="Gerenciar Usuários (Operadores)")
            caderno.add(aba_logs, text="Auditoria de Logs Remotos")
        
        self.montar_aba_produtos(aba_produtos)
        self.montar_aba_movimentacao(aba_movimentacao)
        self.montar_aba_relatorios(aba_relatorios)
        
        if self.perfil_atual == "ADMINISTRADOR":
            self.montar_aba_usuarios(aba_usuarios)
            self.montar_aba_logs(aba_logs)
            
    def montar_aba_produtos(self, frame):
        val_float = (self.root.register(self.validar_reais), '%P')
        
        f_cad = tk.LabelFrame(frame, text="Salvar/Editar Item Remoto", padx=10, pady=5)
        f_cad.pack(side="left", fill="y", padx=10, pady=10)
        
        campos = ["ID Único", "Nome do Produto", "Localização (Almoxarifado)", "Custo Entrada (R$)", "Venda Base (R$)", "Taxa Interna Loja (%)"]
        self.entradas_cad = {}
        
        for c in campos:
            tk.Label(f_cad, text=f"{c}:").pack(anchor="w")
            if "R$" in c or "%" in c:
                e = tk.Entry(f_cad, validate="key", validatecommand=val_float)
            else:
                e = tk.Entry(f_cad)
            e.pack(fill="x", pady=2)
            self.entradas_cad[c] = e

        # === 1. FUNÇÃO DE LIMPAR CAMPOS ===
        def limpar_campos():
            self.entradas_cad["ID Único"].config(state="normal")
            for e in self.entradas_cad.values(): 
                e.delete(0, tk.END)

        # === 2. FUNÇÃO DE ATUALIZAR O GRID (CRUCIAL ESTAR NO TOPO) ===
        def acao_atualizar():
            try:
                selecionado = self.grid.selection()
                foco_id = self.grid.item(selecionado, 'values')[0] if selecionado else None
                for row in self.grid.get_children(): 
                    self.grid.delete(row)
                for p in self.banco.listar_produtos():
                    item = self.grid.insert('', tk.END, values=(p['id'], p['nome'], p['localizacao'], p['quantidade'], p['valor_entrada'], p['valor_saida_base'], p['taxa_venda_porcentagem']))
                    if foco_id and str(p['id']) == str(foco_id):
                        self.grid.selection_set(item)
            except Exception:
                pass
            frame.after(5000, acao_atualizar)

        # === 3. FUNÇÃO INTELIGENTE DE SALVAR COM VERIFICAÇÃO DE ID DUPLICADO ===
        def acao_salvar():
            try:
                p_id = self.entradas_cad["ID Único"].get().strip()
                nome = self.entradas_cad["Nome do Produto"].get().strip()
                local = self.entradas_cad["Localização (Almoxarifado)"].get().strip()
                v_ent = float(self.entradas_cad["Custo Entrada (R$)"].get() or 0)
                v_sai = float(self.entradas_cad["Venda Base (R$)"].get() or 0)
                taxa = float(self.entradas_cad["Taxa Interna Loja (%)"].get() or 0)
                
                if not p_id or not nome: 
                    raise ValueError("ID e Nome são obrigatórios.")
                
                produtos_existentes = self.banco.listar_produtos()
                existe = any(str(p['id']).strip() == str(p_id).strip() for p in produtos_existentes)
                
                if existe:
                    pergunta = messagebox.askyesno(
                        "ID Já Cadastrado", 
                        f"O ID Único '{p_id}' já está cadastrado no sistema.\n\n"
                        f"Deseja ATUALIZAR os dados deste produto para '{nome}'?"
                    )
                    if pergunta:
                        self.banco.editar_produto(p_id, nome, local, v_ent, v_sai, taxa, self.usuario_atual)
                        messagebox.showinfo("Sucesso", "Produto atualizado com sucesso na nuvem!")
                    else:
                        self.banco.registrar_log(self.usuario_atual, f"Bloqueou tentativa de duplicar o ID de produto: {p_id}")
                        return
                else:
                    self.banco.cadastrar_produto(p_id, nome, local, v_ent, v_sai, taxa, self.usuario_atual)
                    messagebox.showinfo("Sucesso", "Novo produto registrado com sucesso na nuvem!")
                
                acao_atualizar()
                limpar_campos()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar dados:\n{e}")

        # === 4. FUNÇÃO DE DELETAR PRODUTO ===
        def acao_deletar():
            item_selecionado = self.grid.selection()
            if not item_selecionado:
                messagebox.showwarning("Aviso", "Selecione um item na tabela para excluir.")
                return
            valores = self.grid.item(item_selecionado, 'values')
            p_id = valores[0]
            nome_p = valores[1]
            
            if messagebox.askyesno("Confirmar Exclusão", f"Deseja apagar o ID {p_id} de forma definitiva da rede?"):
                try:
                    self.banco.deletar_produto(p_id, self.usuario_atual)
                    messagebox.showinfo("Sucesso", "Item removido da nuvem!")
                    acao_atualizar()
                    limpar_campos()
                except Exception as e:
                    messagebox.showerror("Erro", f"Não foi possível excluir:\n{e}")
            else:
                self.banco.registrar_log(self.usuario_atual, f"Cancelou a exclusão do produto ID: {p_id} ({nome_p}).")

        # === 5. FUNÇÃO DE SELEÇÃO DA TABELA ===
        def carregar_campos(event):
            item_selecionado = self.grid.selection()
            if item_selecionado:
                valores = self.grid.item(item_selecionado, 'values')
                limpar_campos()
                self.entradas_cad["ID Único"].insert(0, valores[0])
                self.entradas_cad["ID Único"].config(state="disabled")
                self.entradas_cad["Nome do Produto"].insert(0, valores[1])
                self.entradas_cad["Localização (Almoxarifado)"].insert(0, valores[2])
                self.entradas_cad["Custo Entrada (R$)"].insert(0, valores[4])
                self.entradas_cad["Venda Base (R$)"].insert(0, valores[5])
                self.entradas_cad["Taxa Interna Loja (%)"].insert(0, valores[6])

        # === 6. BOTÕES DA INTERFACE (AGORA CONHECEM TODAS AS FUNÇÕES ACIMA) ===
        tk.Button(f_cad, text="💾 Salvar / Editar Item", bg="#27ae60", fg="white", command=acao_salvar).pack(fill="x", pady=5)
        tk.Button(f_cad, text="🗑️ Remover Produto", bg="#c0392b", fg="white", command=acao_deletar).pack(fill="x", pady=5)
        tk.Button(f_cad, text="🧹 Limpar Seleção", bg="#7f8c8d", fg="white", command=limpar_campos).pack(fill="x", pady=5)

        f_grid = tk.LabelFrame(frame, text="Produtos Sincronizados na Nuvem", padx=10, pady=10)
        f_grid.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        colunas = ('id', 'nome', 'local', 'qtd', 'v_ent', 'v_sai', 'taxa')
        self.grid = ttk.Treeview(f_grid, columns=colunas, show='headings')
        for col, label in zip(colunas, ['ID', 'Produto', 'Localização', 'Estoque', 'Val. Ent', 'Saída Base', 'Taxa %']):
            self.grid.heading(col, text=label)
            self.grid.column(col, width=95)
        self.grid.pack(fill="both", expand=True)
        self.grid.bind('<<TreeviewSelect>>', carregar_campos)
                
        tk.Button(f_grid, text="🔄 Forçar Sincronia", command=acao_atualizar).pack(anchor="e", pady=5)
        acao_atualizar()


    def montar_aba_movimentacao(self, frame):
        val_float = (self.root.register(self.validar_reais), '%P')
        val_int = (self.root.register(self.validar_inteiros), '%P')

        f_mov = tk.LabelFrame(frame, text="Lançar Entrada ou Venda de Mercadoria", padx=15, pady=15)
        f_mov.pack(fill="both", expand=True, padx=20, pady=20)
        
        # dicionário interno para vincular o ID selecionado com os dados do produto
        self.produtos_map = {}
        
        # Linha 0: ID do Produto (Mapeado via Combobox Dinâmico)
        tk.Label(f_mov, text="Selecionar ID:").grid(row=0, column=0, sticky="w", pady=5)
        cb_id_mov = ttk.Combobox(f_mov, width=15, state="readonly")
        cb_id_mov.grid(row=0, column=1, sticky="w")
        
        # Campo informativo que exibe o nome do produto automaticamente
        tk.Label(f_mov, text="Nome do Produto:").grid(row=0, column=2, sticky="w", padx=15)
        lbl_nome_prod_dinamico = tk.Label(f_mov, text="Selecione um ID...", font=("Arial", 10, "italic"), fg="#7f8c8d")
        lbl_nome_prod_dinamico.grid(row=0, column=3, sticky="w")
        
        # Linha 1: Operação Fiscal
        tk.Label(f_mov, text="Operação:").grid(row=1, column=0, sticky="w", pady=5)
        cb_tipo = ttk.Combobox(f_mov, values=["ENTRADA", "SAÍDA"], width=15, state="readonly")
        cb_tipo.set("ENTRADA")
        cb_tipo.grid(row=1, column=1, sticky="w")
        
        # Linha 2: Quantidade do Lote
        tk.Label(f_mov, text="Quantidade Lote:").grid(row=2, column=0, sticky="w", pady=5)
        ent_qtd = tk.Entry(f_mov, width=18, validate="key", validatecommand=val_int)
        ent_qtd.grid(row=2, column=1, sticky="w")
        
        # Linha 3: Custo de Frete e Alíquota de Imposto
        tk.Label(f_mov, text="Custo do Frete (R$):").grid(row=3, column=0, sticky="w", pady=5)
        ent_frete = tk.Entry(f_mov, width=18, validate="key", validatecommand=val_float)
        ent_frete.insert(0, "0")
        ent_frete.grid(row=3, column=1, sticky="w")
        
        tk.Label(f_mov, text="Alíquota Imposto (%):").grid(row=3, column=2, sticky="w", padx=15)
        ent_imp = tk.Entry(f_mov, width=18, validate="key", validatecommand=val_float)
        ent_imp.insert(0, "0")
        ent_imp.grid(row=3, column=3, sticky="w")
        
        # Linha 4: Desconto Aplicado
        tk.Label(f_mov, text="Desconto Aplicado (R$):").grid(row=4, column=0, sticky="w", pady=5)
        ent_desc = tk.Entry(f_mov, width=18, validate="key", validatecommand=val_float)
        ent_desc.insert(0, "0")
        ent_desc.grid(row=4, column=1, sticky="w")

        # FUNÇÃO: Atualiza a lista de IDs puxando direto do banco remoto
        def carregar_ids_disponiveis():
            try:
                produtos = self.banco.listar_produtos()
                ids_lista = []
                self.produtos_map = {}
                
                for p in produtos:
                    id_str = str(p['id']).strip()
                    ids_lista.append(id_str)
                    self.produtos_map[id_str] = p['nome']
                
                cb_id_mov['values'] = ids_lista
            except Exception:
                pass
                
        # FUNÇÃO: Escuta a seleção do Combobox e puxa automaticamente o nome na interface
        def ao_selecionar_id(event):
            id_selecionado = cb_id_mov.get()
            nome_encontrado = self.produtos_map.get(id_selecionado, "Não localizado")
            lbl_nome_prod_dinamico.config(text=nome_encontrado, font=("Arial", 10, "bold"), fg="#2c3e50")

        cb_id_mov.bind("<<ComboboxSelected>>", ao_selecionar_id)

        # FUNÇÃO: Redireciona o usuário para a primeira aba (Estoque Geral) para efetuar o cadastro
        def ir_para_cadastro_produto():
            # Busca o widget Notebook ancestral
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    widget.select(0) # Aba 0 é o Estoque Geral
                    break

        # Botão Inteligente adicionado ao lado do cabeçalho informativo de cadastro
        btn_atalho_cad = tk.Button(f_mov, text="➕ Cadastrar Novo Item", bg="#34495e", fg="white", font=("Arial", 8, "bold"), command=ir_para_cadastro_produto)
        btn_atalho_cad.grid(row=0, column=4, padx=20, sticky="w")

        def executar_movimento():
            try:
                p_id = cb_id_mov.get().strip()
                tipo = cb_tipo.get()
                qtd_str = ent_qtd.get().strip()
                
                if not p_id or not qtd_str: 
                    raise ValueError("Selecione o ID do produto e defina a Quantidade.")
                
                self.banco.processar_movimentacao(
                    p_id, tipo, int(qtd_str),
                    float(ent_frete.get() or 0), float(ent_imp.get() or 0), float(ent_desc.get() or 0),
                    self.usuario_atual
                )
                messagebox.showinfo("Sucesso", f"Fluxo de {tipo} atualizado remotamente no SERVIDOR!")
                
                # Reseta o painel operacional para o estado inicial
                cb_id_mov.set("")
                lbl_nome_prod_dinamico.config(text="Selecione um ID...", font=("Arial", 10, "italic"), fg="#7f8c8d")
                ent_qtd.delete(0, tk.END)
                ent_frete.delete(0, tk.END); ent_frete.insert(0, "0")
                ent_imp.delete(0, tk.END); ent_imp.insert(0, "0")
                ent_desc.delete(0, tk.END); ent_desc.insert(0, "0")
                
                # Recarrega os IDs para capturar novas alterações se houver
                carregar_ids_disponiveis()
            except Exception as e:
                self.banco.registrar_log(self.usuario_atual, f"Erro operacional na movimentação do ID {p_id}: {e}")
                messagebox.showerror("Erro Operacional", str(e))

        tk.Button(f_mov, text="⚡ Salvar e Calcular Custos Fiscais", bg="#e67e22", fg="white", font=("Arial", 10, "bold"), command=executar_movimento).grid(row=5, column=0, columnspan=5, pady=25, sticky="ew")
        
        # Inicializa o mapeamento de produtos assim que a aba é aberta
        carregar_ids_disponiveis()
        # Agenda atualizações periódicas da lista de IDs a cada 10 segundos
        def sincronizar_combobox():
            carregar_ids_disponiveis()
            frame.after(10000, sincronizar_combobox)
            
        frame.after(10000, sincronizar_combobox)

    def montar_aba_relatorios(self, frame):
        f_ind = tk.LabelFrame(frame, text="Histórico Individual do Produto", padx=15, pady=15)
        f_ind.pack(fill="x", padx=20, pady=10)
        
        tk.Label(f_ind, text="Digite o ID do Produto desejado:").pack(side="left", padx=5)
        ent_id_pdf = tk.Entry(f_ind, width=12); ent_id_pdf.pack(side="left", padx=5)
        
        def emitir_ind():
            try:
                p_id = ent_id_pdf.get().strip()
                if not p_id: raise ValueError("Informe o ID do produto.")
                arq = self.relatorios.gerar_pdf_produto(p_id, self.usuario_atual)
                import os, webbrowser
                caminho_absoluto = os.path.abspath(arq)
                webbrowser.open(f"file:///{caminho_absoluto}")
                messagebox.showinfo("Sucesso", f"PDF Gerado com Sucesso:\n{arq}")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        tk.Button(f_ind, text="📋 Gerar PDF Físico", bg="#8e44ad", fg="white", command=emitir_ind).pack(side="left", padx=15)
        
        # === O CONTAINER 'f_geral' É CRIADO AQUI ===
        f_geral = tk.LabelFrame(frame, text="Balanço Consolidado por Período de Datas", padx=15, pady=15)
        f_geral.pack(fill="both", expand=True, padx=20, pady=10)
        
        hoje_str = datetime.now().strftime("%Y-%m-%d")
        
        tk.Label(f_geral, text="Data Inicial (AAAA-MM-DD):").grid(row=0, column=0, sticky="w", pady=5)
        ent_dt_ini = tk.Entry(f_geral, width=15); ent_dt_ini.insert(0, hoje_str); ent_dt_ini.grid(row=0, column=1, pady=5)
        
        tk.Label(f_geral, text="Data Final (AAAA-MM-DD):").grid(row=1, column=0, sticky="w", pady=5)
        ent_dt_fim = tk.Entry(f_geral, width=15); ent_dt_fim.insert(0, hoje_str); ent_dt_fim.grid(row=1, column=1, pady=5)
        
        def emitir_geral():
            try:
                arq = self.relatorios.gerar_pdf_periodo(ent_dt_ini.get().strip(), ent_dt_fim.get().strip(), self.usuario_atual)
                import os, webbrowser
                caminho_absoluto = os.path.abspath(arq)
                webbrowser.open(f"file:///{caminho_absoluto}")
                messagebox.showinfo("Sucesso", f"Relatório emitido:\n{arq}")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        # --- FUNÇÃO DO NOVO BOTÃO DE PRODUTOS ---
        def emitir_todos_produtos():
            try:
                arq = self.relatorios.gerar_pdf_todos_produtos(self.usuario_atual)
                import os, webbrowser
                caminho_absoluto = os.path.abspath(arq)
                webbrowser.open(f"file:///{caminho_absoluto}")
                messagebox.showinfo("Sucesso", f"Lista de produtos gerada:\n{arq}")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        # POSIÇÃO CORRETA: Botões criados estritamente APÓS a definição do 'f_geral'
        btn_geral = tk.Button(f_geral, text="📊 Emitir Relatório Consolidado Periódico", bg="#2c3e50", fg="white", font=("Arial", 11, "bold"), command=emitir_geral)
        btn_geral.grid(row=2, column=0, columnspan=2, pady=15, sticky="ew")

        btn_todos_p = tk.Button(f_geral, text="📋 Emitir Relatório Geral de Estoque (Todos os Produtos)", bg="#27ae60", fg="white", font=("Arial", 10, "bold"), command=emitir_todos_produtos)
        btn_todos_p.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")

    def montar_aba_usuarios(self, frame):
        if self.perfil_atual != "ADMINISTRADOR":
            tk.Label(frame, text="Acesso Negado. Apenas Administradores podem gerenciar usuários.", font=("Arial", 12, "bold"), fg="red").pack(pady=50)
            return

        f_cad_u = tk.LabelFrame(frame, text="Cadastrar Novo Usuário do Sistema", padx=15, pady=10)
        f_cad_u.pack(side="left", fill="y", padx=15, pady=15)
        
        tk.Label(f_cad_u, text="Nome de Usuário (Login):").pack(anchor="w")
        ent_u_nome = tk.Entry(f_cad_u); ent_u_nome.pack(fill="x", pady=2)
        
        tk.Label(f_cad_u, text="E-mail corporativo:").pack(anchor="w")
        ent_u_email = tk.Entry(f_cad_u); ent_u_email.pack(fill="x", pady=2)
        
        tk.Label(f_cad_u, text="Senha de Acesso:").pack(anchor="w")
        ent_u_senha = tk.Entry(f_cad_u, show="*"); ent_u_senha.pack(fill="x", pady=2)
        
        tk.Label(f_cad_u, text="Perfil / Nível:").pack(anchor="w")
        cb_perfil = ttk.Combobox(f_cad_u, values=["OPERADOR", "ADMINISTRADOR"], state="readonly")
        cb_perfil.set("OPERADOR"); cb_perfil.pack(fill="x", pady=5)
        
        def salvar_usuario():
            u = ent_u_nome.get().strip()
            em = ent_u_email.get().strip()
            s = ent_u_senha.get().strip()
            p = cb_perfil.get()
            
            if not u or not em or not s:
                messagebox.showwarning("Aviso", "Preencha todos os campos (Nome, E-mail e Senha).")
                return
                
            if "@" not in em or "." not in em:
                messagebox.showwarning("Aviso", "Por favor, digite um e-mail válido.")
                return

            try:
                self.banco.cadastrar_usuario(u, s, em, p, self.usuario_atual)
                messagebox.showinfo("Sucesso", f"Usuário '{u}' cadastrado com sucesso!")
                ent_u_nome.delete(0, tk.END)
                ent_u_email.delete(0, tk.END)
                ent_u_senha.delete(0, tk.END)
                atualizar_lista_usuarios()
            except Exception as e:
                self.banco.registrar_log(self.usuario_atual, f"Tentativa falha de cadastrar usuário {u}: {e}")
                messagebox.showerror("Erro", f"Falha ao registrar usuário:\n{e}")
                
        tk.Button(f_cad_u, text="👤 Salvar Novo Usuário", bg="#2980b9", fg="white", command=salvar_usuario).pack(fill="x", pady=10)
        
        # === PRIMEIRO CRIA O PAINEL DA DIREITA ===
        f_lista_u = tk.LabelFrame(frame, text="Usuários Ativos no Banco de Dados", padx=10, pady=10)
        f_lista_u.pack(side="right", fill="both", expand=True, padx=15, pady=15)
        
        # === DEPOIS CRIA O CONTAINER DOS BOTÕES 'f_botoes_u' ===
        f_botoes_u = tk.Frame(f_lista_u)
        f_botoes_u.pack(fill="x", pady=5)
        
        self.grid_u = ttk.Treeview(f_lista_u, columns=('user', 'email', 'perfil'), show='headings')
        self.grid_u.heading('user', text='Nome de Usuário')
        self.grid_u.heading('email', text='E-mail')
        self.grid_u.heading('perfil', text='Nível de Acesso')
        self.grid_u.pack(fill="both", expand=True)
        
        def atualizar_lista_usuarios(apenas_operadores=False):
            for row in self.grid_u.get_children(): 
                self.grid_u.delete(row)
            try:
                for u in self.banco.listar_usuarios():
                    if apenas_operadores and u['perfil'] != "OPERADOR":
                        continue
                    self.grid_u.insert('', tk.END, values=(u['usuario'], u['email'], u['perfil']))
            except Exception:
                pass

        # --- FUNÇÃO DO NOVO BOTÃO DE USUÁRIOS ---
        def emitir_todos_usuarios():
            try:
                arq = self.relatorios.gerar_pdf_todos_usuarios(self.usuario_atual)
                import os, webbrowser
                caminho_absoluto = os.path.abspath(arq)
                webbrowser.open(f"file:///{caminho_absoluto}")
                messagebox.showinfo("Sucesso", f"Lista de usuários gerada e aberta:\n{arq}")
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                
        # === AGORA QUE 'f_botoes_u' EXISTE, ADICIONAMOS OS BOTÕES NELE ===
        tk.Button(f_botoes_u, text="🔍 Filtro: Apenas Operadores", bg="#f39c12", fg="white", command=lambda: atualizar_lista_usuarios(apenas_operadores=True)).pack(side="left", padx=5)
        tk.Button(f_botoes_u, text="👥 Mostrar Todos", bg="#7f8c8d", fg="white", command=lambda: atualizar_lista_usuarios(apenas_operadores=False)).pack(side="left", padx=5)
        
        # BOTÃO DE IMPRESSÃO POSICIONADO NO LUGAR CORRETO
        tk.Button(f_botoes_u, text="🖨️ Imprimir Usuários (PDF)", bg="#8e44ad", fg="white", command=emitir_todos_usuarios).pack(side="left", padx=5)
        
        atualizar_lista_usuarios()

    def montar_aba_logs(self, frame):
        f_log = tk.LabelFrame(frame, text="Histórico Completo de Ações (Auditoria)", padx=10, pady=10)
        f_log.pack(fill="both", expand=True, padx=15, pady=15)
        
        grid_l = ttk.Treeview(f_log, columns=('id', 'data', 'user', 'msg'), show='headings')
        grid_l.heading('id', text='ID Log'); grid_l.column('id', width=60, anchor="center")
        grid_l.heading('data', text='Data/Hora'); grid_l.column('data', width=140, anchor="center")
        grid_l.heading('user', text='Operador'); grid_l.column('user', width=100)
        grid_l.heading('msg', text='Mensagem Registrada'); grid_l.column('msg', width=450)
        grid_l.pack(fill="both", expand=True)
        
        def carregar_logs():
            for row in grid_l.get_children(): grid_l.delete(row)
            for l in self.banco.listar_logs():
                grid_l.insert('', tk.END, values=(l['id'], l['data_hora'], l['usuario'], l['mensagem']))
                
        tk.Button(f_log, text="🔄 Recarregar Histórico de Auditoria", command=carregar_logs).pack(anchor="e", pady=5)
        carregar_logs()

if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaCompletoApp(root)
    root.mainloop()
