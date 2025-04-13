from flask import Flask, render_template, request, flash, redirect, session, url_for
import mysql.connector
from mysql.connector import errorcode
from datetime import date
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mariana'


# Renderização para pagina de login
@app.route("/")
def login():
    return render_template('login.html')



# Verificação de usuario e senha no banco de dados para acesso 
@app.route('/acesso', methods=['POST'])
def acesso():
    usuario_input = request.form.get('usuario')
    senha_input = request.form.get('senha')

    try:
        # Conectando ao banco de dados
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )

        if conect_BD.is_connected():
            print('Conectado ao banco de dados.')
            cursor = conect_BD.cursor(dictionary=True)

            # Consulta o banco para verificar o usuário
            cursor.execute('SELECT * FROM usuarios WHERE usuario = %s', (usuario_input,))
            usuario = cursor.fetchone()

            if usuario:
                senha_bd = usuario['senha']

                # Verifica se a senha está correta
                if senha_input == senha_bd:
                    session['logado'] = True
                    session['usuario'] = {
                        'nome': usuario['usuario'],
                        'permissao': usuario['permissao'],
                        'primeiro_acesso': usuario['primeiro_acesso']
                    }
                    

                    # Verifica se é o primeiro acesso
                    if usuario['primeiro_acesso']:
                        flash('Por favor, redefina sua senha para continuar.', 'info')
                        return redirect('/redefinicao-senha')  # Redireciona para a página de redefinição de senha

                    # Caso contrário, redireciona para a página inicial
                    return redirect('/home')

            flash('Usuário e/ou senha incorretos. Tente novamente ou entre em contato com o suporte.', 'erro')
            return redirect('/')

    except mysql.connector.Error as err:
        print(f"Erro de conexão com o banco: {err}")
        flash('Erro na conexão com o banco de dados.', 'erro')
        return redirect('/')

    finally:
        if conect_BD.is_connected():
            conect_BD.close()   

def tipo_permissao(*permissao):
    def decorator(f):
        @wraps(f)
        def permissao_funcao(*args, **kwargs):
            if not session.get('logado'):
                flash('Você precisa estar logado.', 'erro')
                return redirect('/')

            usuario = session.get('usuario', {})
            permissao_usuario = usuario.get('permissao')

            if permissao_usuario not in permissao:
                flash('Você não tem permissão para acessar essa página.', 'erro')
                return redirect('/home')

            return f(*args, **kwargs)
        return permissao_funcao
    return decorator           


@app.route('/redefinicao-senha', methods=['GET', 'POST'])
def redefinicao_senha():
    if request.method == 'POST':
        nova_senha = request.form['nova_senha']
        confirmar_senha = request.form['confirmar_senha']

        # Verificar se as senhas coincidem
        if nova_senha != confirmar_senha:
            flash("As senhas não coincidem", "erro")
            return redirect(url_for('alterar_senha'))

        # Atualizar a senha no banco de dados diretamente (sem hash)
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )
        cursor = conect_BD.cursor()

        cursor.execute("""
            UPDATE usuarios
            SET senha = %s, primeiro_acesso = FALSE
            WHERE usuario = %s
        """, (nova_senha, session['usuario']['nome']))  # Corrigido para acessar o nome do usuário na sessão

        conect_BD.commit()
        cursor.close()
        conect_BD.close()

        flash("Senha alterada com sucesso", "sucesso")
        return redirect(url_for('login'))

    return render_template('redefinicao-senha.html')       


@app.route('/home')
def home():
    if session.get('logado'):

        return render_template('home.html') # Renderiza a página home se o usuário estiver logado
    else:
        flash('Você precisa estar logado para acessar essa página.')
        return redirect('/')




@app.route('/funcionario-pesquisa', methods=['GET'])

@tipo_permissao("analista_pessoas","gerente_pessoas","administrador") 

def funcionario_pesquisa():
    matricula = request.args.get('matricula')
    funcionario = None
    if matricula:
        try:
            conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'

            )
            if conect_BD.is_connected():
                cursur = conect_BD.cursor(dictionary=True)

                query = 'SELECT * FROM funcionarios WHERE id_matricula = %s'
                cursur.execute(query,(matricula,))
                funcionario = cursur.fetchone()

        except mysql.connector.Error as err:
            print("Erro ao buscar funcionario:", err)
            flash('Erro ao buscar o funcionario. Tente novamente.')

        finally:
            if conect_BD.is_connected():
                cursur.close()
                conect_BD.close()


    return render_template('funcionario-pesquisar.html',funcionario=funcionario, matricula=matricula)
    

@app.route('/funcionario-cadastro')

def funcionario_cadastro():
    proxima_matricula=""
    data_hoje=date.today().isoformat()
   
    try:
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )
        if conect_BD.is_connected():
            cursur = conect_BD.cursor()

            cursur.execute("SELECT MAX(id_matricula) FROM funcionarios")  
            resultado = cursur.fetchone()
            ultima_matricula = resultado[0] if resultado[0] is not None else 0
            proxima_matricula = int(ultima_matricula) + 1
        
    except mysql.connector.Error as err:
        print(f"Erro ao buscar matricula: {err}:")
        flash("Erro ao carregar o formulário")
        
    finally:
        if 'cursur'in locals():
            cursur.close()
        if 'conect_BD' in locals() and conect_BD.is_connected():
            conect_BD.close()
    return render_template('funcionario-cadastrar.html', proxima_matricula=proxima_matricula, data_hoje=data_hoje)




@app.route('/funcionario-cadastrar', methods=['GET', 'POST'])

@tipo_permissao("analista_pessoas","gerente_pessoas","administrador") 

def funcionario_cadastrar():
    if request.method == 'POST':
        id_matricula = request.form.get('matricula')
        nome_completo = request.form.get('nome_completo')
        data_nascimento = request.form.get('data_nascimento')
        rg = request.form.get('rg')
        cpf = request.form.get('cpf')
        data_admissao = request.form.get('data_admissao')
        cargo = request.form.get('cargo')
        email_corporativo = request.form.get('email')
        telefone_corporativo = request.form.get('telefone_corporativo')
        data_demissao = '1900-01-01'
        try:
            conect_BD = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Rm.123456',
                database='BDWAYNE'
            )
            if conect_BD.is_connected():
                cursor = conect_BD.cursor()

                # Verifica se funcionário já existe
                cursor.execute("SELECT * FROM funcionarios WHERE id_matricula = %s", (id_matricula,))
                funcionario_existente = cursor.fetchone()

                if funcionario_existente:
                    flash('Funcionário já existe.')
                    return redirect('/funcionario-cadastrar')

                # Cadastrar funcionário
                query_func = """
                    INSERT INTO funcionarios (id_matricula, nome_completo, data_nascimento, rg, cpf, data_admissao, cargo, email_corporativo, telefone_corporativo, data_demissao)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
                valores_func = (id_matricula,nome_completo, data_nascimento, rg, cpf, data_admissao, cargo, email_corporativo, telefone_corporativo, data_demissao)
                cursor.execute(query_func, valores_func)

                # Cadastrar usuário automático (com senha padrão ou em branco)
                query_user = """
                    INSERT INTO usuarios (id_matricula, usuario, senha, data_criacao_senha, data_alteracao_senha, primeiro_acesso, permissao)
                    VALUES (%s, %s, %s, CURDATE(),'1900-01-01', %s, %s)
                """
                valores_user = (id_matricula, f"w-{nome_completo.lower().split()[0]}-{id_matricula}",'1234','1','visualizacao')
                cursor.execute(query_user, valores_user)

                conect_BD.commit()
                flash('Funcionário e usuário criados com sucesso!')
                return redirect('/funcionario-cadastrar')

        except mysql.connector.Error as err:
            print("Erro ao cadastrar:", err)
            flash("Erro ao cadastrar funcionário.")

        finally:
            if conect_BD.is_connected():
                cursor.close()
                conect_BD.close()

    return render_template('funcionario-cadastrar.html')



@app.route('/funcionario-editar', methods=['POST'])

@tipo_permissao('gerente_pessoas',"administrador")

def funcionario_editar():
    matricula = request.form.get('matricula')
    nome_completo = request.form.get('nome_completo')
    data_nascimento = request.form.get('data_nascimento')
    rg = request.form.get('rg')
    cpf = request.form.get('cpf')
    data_admissao = request.form.get('data_admissao')
    cargo = request.form.get('cargo')
    email_corporativo = request.form.get('email_corporativo')
    telefone_corporativo = request.form.get('telefone_corporativo')
    data_demissao = '1900-01-01'


    try:
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )
        if conect_BD.is_connected():
            cursor = conect_BD.cursor()

            query = """
            UPDATE funcionarios 
            SET  nome_completo = %s, data_nascimento = %s, rg = %s, cpf = %s, data_admissao = %s, cargo = %s, email_corporativo = %s, telefone_corporativo = %s, data_demissao = %s
            WHERE id_matricula = %s
            """
            valores = (nome_completo, data_nascimento, rg, cpf, data_admissao, cargo, email_corporativo, telefone_corporativo,data_demissao, matricula)
            cursor.execute(query, valores)
            conect_BD.commit()

            flash("Equipamento atualizado com sucesso!")

    except mysql.connector.Error as err:
        print("Erro ao atualizar:", err)
        flash("Erro ao atualizar funcionario.")
    finally:
        if conect_BD.is_connected():
            cursor.close()
            conect_BD.close()

    return redirect(f"/funcionario-pesquisa?matricula={matricula}")

@app.route('/funcionario-excluir', methods=['POST'])

@tipo_permissao("gerente_pessoas","administrador") 

def funcionario_excluir():
    matricula = request.form.get('matricula')

    try:
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )

        if conect_BD.is_connected():
            cursor = conect_BD.cursor()

            # Exclui primeiro da tabela usuarios (por causa da restrição)
            query_usuarios = "DELETE FROM usuarios WHERE id_matricula = %s"
            cursor.execute(query_usuarios, (matricula,))

            # Depois exclui da tabela funcionarios
            query_funcionarios = "DELETE FROM funcionarios WHERE id_matricula = %s"
            cursor.execute(query_funcionarios, (matricula,))

            conect_BD.commit()
            flash('Funcionário e usuário excluídos com sucesso!')

    except mysql.connector.Error as err:
        print("Erro ao excluir:", err)
        flash("Erro ao excluir os registros.")

    finally:
        if conect_BD.is_connected():
            cursor.close()
            conect_BD.close()

    return redirect('/funcionario-pesquisa')


@app.route('/veiculo-pesquisa')

@tipo_permissao("analista_frota","gerente_frota","administrador") 

def veiculo_pesquisa():
    registro = request.args.get('registro')
    veiculo = None
    if registro:
        try:
            conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'

            )
            if conect_BD.is_connected():
                cursur = conect_BD.cursor(dictionary=True)

                query = 'SELECT * FROM veiculos WHERE id_registro = %s'
                cursur.execute(query,(registro,))
                veiculo = cursur.fetchone()

        except mysql.connector.Error as err:
            print("Erro ao buscar veiculo:", err)
            flash('Erro ao buscar o veiculo. Tente novamente.')

        finally:
            if conect_BD.is_connected():
                cursur.close()
                conect_BD.close()


    return render_template('veiculo-pesquisar.html',veiculo=veiculo, registro=registro)
    


@app.route('/veiculo-cadastro')
def veiculo_cadastro():
    proximo_registro=""
   
    try:
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )
        if conect_BD.is_connected():
            cursur = conect_BD.cursor()

            cursur.execute("SELECT MAX(id_registro) FROM veiculos")  
            resultado = cursur.fetchone()
            ultimo_registro = resultado[0] if resultado[0] is not None else 0
            proximo_registro = int(ultimo_registro) + 1
        
    except mysql.connector.Error as err:
        print(f"Erro ao buscar registro: {err}:")
        flash("Erro ao carregar o formulário")
        
    finally:
        if 'cursur'in locals():
            cursur.close()
        if 'conect_BD' in locals() and conect_BD.is_connected():
            conect_BD.close()
    return render_template('veiculo-cadastrar.html', proximo_registro=proximo_registro)


@app.route('/veiculo-cadastrar', methods=['POST'])

@tipo_permissao("analista_frota","gerente_frota","administrador") 

def veiculo_cadastrar():
    registro = request.form.get('registro')
    placa = request.form.get('placa')
    marca = request.form.get('marca')
    modelo = request.form.get('modelo')
    ano = request.form.get('ano')
    chassi = request.form.get('chassi')
    renavam = request.form.get('renavam')
    data_compra = request.form.get('data_compra')
    fornecedor = request.form.get('fornecedor')
    valor_compra = request.form.get('valor_compra')
    documento_fiscal_compra = request.form.get('documento_fiscal_compra')
    data_venda = request.form.get('data_venda','1900-01-01')
    comprador = request.form.get('comprador','')
    valor_venda = request.form.get('valor_venda','')
    documento_fiscal_venda = request.form.get('documento_fiscal_venda','')

    valor_compra = float(valor_compra) if valor_compra else 0.0
    valor_venda = float(valor_venda) if valor_venda else 0.0
    
    try:
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )
        if conect_BD.is_connected():
            cursur = conect_BD.cursor()

            query = """
            INSERT INTO veiculos(id_registro,placa,marca,modelo,ano,chassi,renavam,data_compra,fornecedor,valor_compra,documento_fiscal_compra,data_venda,comprador,valor_venda,documento_fiscal_venda)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            valores = (registro,placa,marca,modelo,ano,chassi,renavam,data_compra,fornecedor,valor_compra,documento_fiscal_compra,data_venda,comprador,valor_venda,documento_fiscal_venda)
            
            print('valores inseridos:', valores)

            cursur.execute(query , valores)

            conect_BD.commit()

            flash(f"Veiculo {placa} cadastrado!")
            return redirect ('/veiculo-cadastro')

    except mysql.connector.Error as err:
        print(f" Erro ao cadastrar: {err}")
        flash('Erro ao tentar cadatradar o veiculo. Tente novamente mais tarde')
        
    finally:
        if conect_BD.is_connected():
            cursur.close()
            conect_BD.close()


    return redirect ('/veiculo-cadastro')

@app.route('/veiculo-editar', methods=['POST'])

@tipo_permissao("gerente_frota","administrador") 

def veiculo_editar():
    registro = request.form.get('registro')
    placa = request.form.get('placa')
    marca = request.form.get('marca')
    modelo = request.form.get('modelo')
    ano = request.form.get('ano')
    chassi = request.form.get('chassi')
    renavam = request.form.get('renavam')
    data_compra = request.form.get('data_compra')
    fornecedor = request.form.get('fornecedor')
    valor_compra = request.form.get('valor_compra')
    documento_fiscal_compra = request.form.get('documento_fiscal_compra')
    data_venda = request.form.get('data_venda')
    comprador = request.form.get('comprador')
    valor_venda = request.form.get('valor_venda')
    documento_fiscal_venda = request.form.get('documento_fiscal_venda')


    valor_compra = float(valor_compra) if valor_compra else 0.0
    valor_venda = float(valor_venda) if valor_venda else 0.0

    try:
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )
        if conect_BD.is_connected():
            cursor = conect_BD.cursor()

            query = """
            UPDATE veiculos 
            SET  placa = %s, marca = %s, modelo = %s, ano = %s, chassi = %s, renavam = %s, data_compra = %s, fornecedor = %s, valor_compra = %s, documento_fiscal_compra = %s, data_venda = %s,  comprador = %s, valor_venda = %s, documento_fiscal_venda = %s
            WHERE id_registro = %s
            """
            valores = (placa, marca, modelo, ano, chassi, renavam,  data_compra, fornecedor, valor_compra, documento_fiscal_compra, data_venda, comprador, valor_venda, documento_fiscal_venda, registro)
            cursor.execute(query, valores)
            conect_BD.commit()

            flash("Veiculo atualizado com sucesso!")

    except mysql.connector.Error as err:
        print("Erro ao atualizar:", err)
        flash("Erro ao atualizar veiculo.")
    finally:
        if conect_BD.is_connected():
            cursor.close()
            conect_BD.close()

    return redirect(f"/veiculo-pesquisa?registro={registro}")

@app.route('/veiculo-excluir', methods=['POST'])

@tipo_permissao("gerente_frota","administrador") 

def veiculo_excluir():
    registro = request.form.get('registro')

    try:
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )
        if conect_BD.is_connected():
            cursor = conect_BD.cursor()

            query = "DELETE FROM veiculos WHERE id_registro = %s"
            cursor.execute(query, (registro,))
            conect_BD.commit()

            flash('Registro excluído com sucesso!')

    except mysql.connector.Error as err:
        print("Erro ao excluir:", err)
        flash("Erro ao excluir o registro.")

    finally:
        if conect_BD.is_connected():
            cursor.close()
            conect_BD.close()

    return redirect('/veiculo-pesquisa')



@app.route('/veiculo-controle', methods=['GET', 'POST'])
@app.route('/veiculo-controle/<int:id_registro>', methods=['GET', 'POST'])

@tipo_permissao("analista_frota","gerente_frota","administrador") 

def veiculo_controle(id_registro=None):
    conect_BD = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Rm.123456',
        database='BDWAYNE'
    )
    cursor = conect_BD.cursor(dictionary=True)

    # Buscar todas as placas disponíveis
    cursor.execute("SELECT id_registro, placa FROM veiculos")
    placas = cursor.fetchall()

    # Buscar todos os funcionários
    cursor.execute("SELECT id_matricula, nome_completo FROM funcionarios")
    funcionarios = cursor.fetchall()

    # Verifica se há controle em aberto (sem entrada registrada)
    controle_aberto = None
    if id_registro:
        cursor.execute("""
            SELECT * FROM controle_veiculos
            WHERE id_registro = %s AND data_hora_entrada IS NULL
            ORDER BY data_hora_saida DESC LIMIT 1
        """, (id_registro,))
        controle_aberto = cursor.fetchone()

    if request.method == 'POST':
        try:
            id_registro = int(request.form.get('placa', '').strip())
        except ValueError:
            flash("Placa inválida. Selecione uma opção correta.", "erro")
            return redirect(url_for('veiculo_controle'))

  
        id_matricula = request.form.get('condutor_responsavel', '').strip()

        # Validação de funcionário
        if not id_matricula.isdigit():
            flash("Selecione um funcionário válido.", "erro")
            return redirect(url_for('veiculo_controle', id_registro=id_registro))

        id_matricula = int(id_matricula)
        motivo = request.form.get('motivo', '')
        observacao = request.form.get('observacao', '')
        enviar_para = request.form.get('enviar_para', '')

        if controle_aberto:
            # REGISTRO DE ENTRADA
            data_hora_entrada = datetime.now()
            cursor.execute("""
                UPDATE controle_veiculos
                SET data_hora_entrada = %s,
                    observacao_entrada = %s,
                    enviar_para_entrada = %s
                WHERE id_contr_veiculos = %s
            """, (data_hora_entrada, observacao, enviar_para, controle_aberto['id_contr_veiculos']))
        else:
            # REGISTRO DE SAÍDA
            data_hora_saida = datetime.now()
            cursor.execute("""
                INSERT INTO controle_veiculos (
                    id_registro, id_matricula, data_hora_saida, motivo
                ) VALUES (%s, %s, %s, %s)
            """, (id_registro, id_matricula, data_hora_saida, motivo))

        conect_BD.commit()
        cursor.close()
        conect_BD.close()
        return redirect(url_for('veiculo_controle', id_registro=id_registro))

    cursor.close()
    conect_BD.close()
    return render_template('veiculo-controle.html', placas=placas, funcionarios=funcionarios, id_registro=id_registro, controle_aberto=controle_aberto)




@app.route('/equipamento-pesquisa', methods=['GET'])

@tipo_permissao("analista_equipamentos","gerente_equipamentos","administrador") 

def equipamento_pesquisa():
    patrimonio = request.args.get('patrimonio')
    equipamento = None
    if patrimonio:
        try:
            conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'

            )
            if conect_BD.is_connected():
                cursur = conect_BD.cursor(dictionary=True)

                query = 'SELECT * FROM equipamentos WHERE id_patrimonio = %s'
                cursur.execute(query,(patrimonio,))
                equipamento = cursur.fetchone()

        except mysql.connector.Error as err:
            print("Erro ao buscar equipamento:", err)
            flash('Erro ao buscar o equipamento. Tente novamente.')

        finally:
            if conect_BD.is_connected():
                cursur.close()
                conect_BD.close()


    return render_template('equipamento-pesquisar.html',equipamento=equipamento, patrimonio=patrimonio)

@app.route('/equipamento-cadastro')
def equipamento_cadastro():
    
    proximo_patrimonio=""
   
    try:
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )
        if conect_BD.is_connected():
            cursur = conect_BD.cursor()

            cursur.execute("SELECT MAX(id_patrimonio) FROM equipamentos")  
            resultado = cursur.fetchone()
            ultimo_patrimonio = resultado[0] if resultado[0] is not None else 0
            proximo_patrimonio = int(ultimo_patrimonio) + 1
        
    except mysql.connector.Error as err:
        print(f"Erro ao buscar patrimonio: {err}:")
        flash("Erro ao carregar o formulário")
        
    finally:
        if 'cursur'in locals():
            cursur.close()
        if 'conect_BD' in locals() and conect_BD.is_connected():
            conect_BD.close()
    return render_template('equipamento-cadastrar.html', proximo_patrimonio=proximo_patrimonio)


@app.route('/equipamento-cadastrar', methods=['POST'])

@tipo_permissao("analista_equipamentos","gerente_equipamentos","administrador") 

def equipamento_cadastrar():
    patrimonio = request.form.get('patrimonio')
    descricao = request.form.get('descricao')
    marca = request.form.get('marca')
    modelo = request.form.get('modelo')
    serie = request.form.get('serie')
    imei = request.form.get('imei')
    data_compra = request.form.get('data_compra')
    fornecedor = request.form.get('fornecedor')
    valor_compra = request.form.get('valor_compra')
    documento_fiscal_compra = request.form.get('documento_fiscal_compra') 
    data_venda = request.form.get('data_venda','1900-01-01')
    comprador = request.form.get('comprador','')
    valor_venda = request.form.get('valor_venda','')
    documento_fiscal_venda = request.form.get('documento_fiscal_venda','') 

    valor_compra = float(valor_compra) if valor_compra else 0.0
    valor_venda = float(valor_venda) if valor_venda else 0.0
    
    try:
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )
        if conect_BD.is_connected():
            cursur = conect_BD.cursor()

            query = """
            INSERT INTO equipamentos(id_patrimonio,descricao,marca,modelo,serie,imei,data_compra,fornecedor,valor_compra,documento_fiscal_compra,data_venda,comprador,valor_venda,documento_fiscal_venda)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            valores = (patrimonio,descricao,marca,modelo,serie,imei,data_compra,fornecedor,valor_compra,documento_fiscal_compra,data_venda,comprador,valor_venda,documento_fiscal_venda)
            
            print('valores inseridos:', valores)

            cursur.execute(query , valores)

            conect_BD.commit()

            flash(f"Equipamento cadastrado!")
            return redirect ('/equipamento-cadastro')

    except mysql.connector.Error as err:
        print(f" Erro ao cadastrar: {err}")
        flash('Erro ao tentar cadatradar o equipamento. Tente novamente mais tarde')
        
    finally:
        if conect_BD.is_connected():
            cursur.close()
            conect_BD.close()



    return redirect ('/equipamento-cadastro')

@app.route('/equipamento-editar', methods=['POST'])

@tipo_permissao("gerente_equipamentos","administrador") 

def equipamento_editar():
    patrimonio = request.form.get('patrimonio')
    descricao = request.form.get('descricao')
    marca = request.form.get('marca')
    modelo = request.form.get('modelo')
    serie = request.form.get('serie')
    imei = request.form.get('imei')
    data_compra = request.form.get('data_compra')
    fornecedor = request.form.get('fornecedor')
    valor_compra = request.form.get('valor_compra')
    documento_fiscal_compra = request.form.get('documento_fiscal_compra') 
    data_venda = request.form.get('data_venda')
    comprador = request.form.get('comprador')
    valor_venda = request.form.get('valor_venda')
    documento_fiscal_venda = request.form.get('documento_fiscal_venda') 

    valor_compra = float(valor_compra) if valor_compra else 0.0
    valor_venda = float(valor_venda) if valor_venda else 0.0

    try:
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )
        if conect_BD.is_connected():
            cursor = conect_BD.cursor()

            query = """
            UPDATE equipamentos 
            SET descricao = %s, marca = %s, modelo = %s, serie = %s, imei = %s, data_compra = %s, fornecedor = %s, valor_compra = %s, documento_fiscal_compra = %s, data_venda = %s,  comprador = %s, valor_venda = %s, documento_fiscal_venda = %s
            WHERE id_patrimonio = %s
            """
            valores = (descricao, marca, modelo, serie, imei, data_compra, fornecedor, valor_compra, documento_fiscal_compra,data_venda, comprador, valor_venda, documento_fiscal_venda, patrimonio)
            cursor.execute(query, valores)
            conect_BD.commit()

            flash("Equipamento atualizado com sucesso!")

    except mysql.connector.Error as err:
        print("Erro ao atualizar:", err)
        flash("Erro ao atualizar equipamento.")
    finally:
        if conect_BD.is_connected():
            cursor.close()
            conect_BD.close()

    return redirect(f"/equipamento-pesquisa?,patrimonio={patrimonio}")

@app.route('/equipamento-excluir', methods=['POST'])

@tipo_permissao("gerente_equipamentos","administrador") 

def equipamento_excluir():
    patrimonio = request.form.get('patrimonio')

    try:
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )
        if conect_BD.is_connected():
            cursor = conect_BD.cursor()

            query = "DELETE FROM equipamentos WHERE id_patrimonio = %s"
            cursor.execute(query, (patrimonio,))
            conect_BD.commit()

            flash('Registro excluído com sucesso!')

    except mysql.connector.Error as err:
        print("Erro ao excluir:", err)
        flash("Erro ao excluir o registro.")

    finally:
        if conect_BD.is_connected():
            cursor.close()
            conect_BD.close()

    return redirect('/equipamento-pesquisa')



    
@app.route("/equipamento-controle", methods=["GET", "POST"])

@tipo_permissao("analista_equipamentos","gerente_equipamentos","administrador") 

def equipamento_controle():
    try:
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )
        cursor = conect_BD.cursor(dictionary=True)

        # Carrega dados para os selects
        cursor.execute("SELECT id_patrimonio, descricao FROM equipamentos")
        equipamentos = cursor.fetchall()

        cursor.execute("SELECT id_matricula, nome_completo FROM funcionarios")
        funcionarios = cursor.fetchall()

        if request.method == "POST":
            # Pega os dados do formulário
            patrimonio = request.form.get("patrimonio")
            matricula = request.form.get("matricula")
            setor = request.form.get("setor")
            data_registro = request.form.get("data_registro")  # OBRIGATÓRIO!
            motivo = request.form.get("motivo")
            observacao = request.form.get("observacao")


            # INSERIR DADOS
            cursor2 = conect_BD.cursor()
            query = """
                INSERT INTO controle_equipamentos 
                (id_patrimonio, id_matricula, setor, data_registro, motivo, observacao) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            valores = (patrimonio, matricula, setor, data_registro, motivo, observacao)
            cursor2.execute(query, valores)
            conect_BD.commit()
            cursor2.close()
            conect_BD.close()

            return redirect("/equipamento-controle")

        cursor.close()
        conect_BD.close()
        return render_template("equipamento-controle.html", equipamentos=equipamentos, funcionarios=funcionarios)

    except mysql.connector.Error as erro:
        print("Erro ao registrar movimentação:", erro)
        return f"Erro ao carregar a página: {erro}"


@app.route('/seguranca-pesquisa', methods=['GET'])

@tipo_permissao("analista_segurança","gerente_segurança","administrador") 

def seguranca_pesquisa():
    matricula = request.args.get('matricula')
    usuario = None
    funcionario = None
    if matricula:
        try:
            conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'

            )
            if conect_BD.is_connected():
                cursur = conect_BD.cursor(dictionary=True)

                query_usuario = 'SELECT * FROM usuarios WHERE id_matricula = %s'
                cursur.execute(query_usuario,(matricula,))
                usuario = cursur.fetchone()

                query_funcionario = 'SELECT * FROM funcionarios WHERE id_matricula = %s'
                cursur.execute(query_funcionario, (matricula,))
                funcionario = cursur.fetchone()

        except mysql.connector.Error as err:
            print("Erro ao buscar funcionario:", err)
            flash('Erro ao buscar o funcionario. Tente novamente.')

        finally:
            if conect_BD.is_connected():
                cursur.close()
                conect_BD.close()


    return render_template('seguranca-cadastrar.html',usuario=usuario, funcionario=funcionario, matricula=matricula)



@app.route('/seguranca-editar', methods=['POST'])

@tipo_permissao("gerente_segurança","administrador") 

def seguranca_editar():
    matricula = request.form.get('matricula')
    usuario = request.form.get('usuario')
    senha = request.form.get('senha') 
    primeiro_acesso = request.form.get('primeiro_acesso')
    data_criacao_senha = request.form.get('data_criacao_senha')
    data_alteracao_senha = date.today()
    permissao = request.form.get('permissao')
    


    try:
        conect_BD = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Rm.123456',
            database='BDWAYNE'
        )
        if conect_BD.is_connected():
            cursor = conect_BD.cursor()

            query = """
            UPDATE usuarios 
            SET usuario = %s, senha = %s, primeiro_acesso = %s, data_criacao_senha = %s, data_alteracao_senha = %s, permissao = %s
            WHERE id_matricula = %s
            """
            valores = (usuario, senha, primeiro_acesso, data_criacao_senha, data_alteracao_senha, permissao, matricula)
            cursor.execute(query, valores)
            conect_BD.commit()

            flash(" atualizado com sucesso!")

    except mysql.connector.Error as err:
        print("Erro ao atualizar:", err)
        flash("Erro ao atualizar equipamento.")
    finally:
        if conect_BD.is_connected():
            cursor.close()
            conect_BD.close()

    return redirect(f"/seguranca-pesquisa?matricula={matricula}")

@app.route("/suporte", methods=["GET", "POST"])
def suporte():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        problema = request.form.get("problema")

        try:
            conect_BD = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Rm.123456",
                database="BDWAYNE"
            )
            cursor = conect_BD.cursor()

            query = "INSERT INTO suporte (nome_usuario, email, problema) VALUES (%s, %s, %s)"
            valores = (nome, email, problema)

            cursor.execute(query, valores)
            conect_BD.commit()
            cursor.close()

            return redirect("/suporte") 

        except mysql.connector.Error as erro:
            print("Erro ao enviar suporte:", erro)
            return "Erro ao registrar a solicitação de suporte"

    return render_template("suporte.html")

@app.route('/suporte-chamados')

@tipo_permissao("analista_segurança","gerente_segurança","administrador") 

def exibir_suporte_chamados():
    conect_BD = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Rm.123456',
        database='BDWAYNE'
    )
    cursor = conect_BD.cursor(dictionary=True)

    cursor.execute("SELECT * FROM suporte ORDER BY data_solicitacao DESC;")
    lista_suporte = cursor.fetchall()

    cursor.close()
    conect_BD.close()

    return render_template('suporte-chamados.html', lista_suporte=lista_suporte)



def get_counts():
    conect_BD = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Rm.123456",
        database="BDWAYNE"
    )
    cursor = conect_BD.cursor()

    queries = {
        "Funcionários": "SELECT COUNT(*) FROM funcionarios",
        "Usuários": "SELECT COUNT(*) FROM usuarios",
        "Veículos": "SELECT COUNT(*) FROM veiculos",
        "Controle de Veículos": "SELECT COUNT(*) FROM controle_veiculos",
        "Equipamentos": "SELECT COUNT(*) FROM equipamentos",
        "Controle de Equipamentos": "SELECT COUNT(*) FROM controle_equipamentos",
        "Chamados de Suporte": "SELECT COUNT(*) FROM suporte"
    }

    counts = {}
    for nome, query in queries.items():
        cursor.execute(query)
        counts[nome] = cursor.fetchone()[0]

    cursor.close()
    conect_BD.close()
    return counts

@app.route("/dashboard")
def dashboard():
    totais = get_counts()
    return render_template("dashboard.html", totais=totais)














if __name__ == "__main__":
    app.run(debug=True)