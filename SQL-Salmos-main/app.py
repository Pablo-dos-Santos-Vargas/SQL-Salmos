import os
import mysql.connector
from flask import Flask, request, jsonify
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions
from datetime import datetime
from dotenv import load_dotenv
from flask_cors import CORS

pasta_atual = os.path.dirname(os.path.abspath(__file__))

caminho_chave = os.path.join(pasta_atual, "key.json")
caminho_env = os.path.join(pasta_atual, ".env")

load_dotenv(caminho_env)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = caminho_chave

app = Flask(__name__)
CORS(app)

PROJECT_ID = "599834168707" 
LOCATION = "us"
PROCESSOR_ID = "98b736a0b757dd27"

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', 3306)
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_DEFAULT_BASE = os.environ.get('DB_DEFAULT_BASE') or os.environ.get('DB_NAME_ONLINE')

def processar_documento(imagem_bytes):
    print(f"--- INICIANDO PROCESSAMENTO ---")
    
    opts = ClientOptions(api_endpoint="documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)

    name = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
    
    raw_document = documentai.RawDocument(
        content=imagem_bytes,
        mime_type="image/jpeg"
    )

    request_google = documentai.ProcessRequest(name=name, raw_document=raw_document)

    print("Enviando para o Google...")
    try:
        result = client.process_document(request=request_google)
        print("Google respondeu com sucesso!")
    except Exception as e:
        print(f"ERRO NA API DO GOOGLE: {e}")
        raise e

    dados_limpos = {}
    document = result.document

    if not document.entities:
        return {}

    for entity in document.entities:
        nome = entity.type_
        valor = entity.mention_text

        if valor in ('checked', 'unchecked'):
            dados_limpos[nome] = True if valor == 'checked' else False
        else:
            dados_limpos[nome] = valor.replace('\n', ' ').strip()
    
    return dados_limpos

def salvar_no_banco(dados):
    print(f"Tentando salvar no banco: {DB_DEFAULT_BASE}...")
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DEFAULT_BASE
        )
        cursor = conn.cursor()

        # Tratamento de Data
        data_banco = None
        data_str = dados.get('Data')
        if data_str:
            for fmt in ("%d/%m/%y", "%d/%m/%Y"):
                try:
                    data_banco = datetime.strptime(data_str, fmt).strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue

        # Prepara os valores (mesma ordem do seu INSERT)
        valores = (
            data_banco, dados.get('Item'), dados.get('QntPecas'), dados.get('Maquina'),
            dados.get('Setor'), dados.get('NomeCracha'), dados.get('Montagem', False),
            dados.get('Regulagem', False), dados.get('MarcaRetifica', False),
            dados.get('Empenamento', False), dados.get('FalhaRaio', False),
            dados.get('FalhaZinco', False), dados.get('Rebarba', False),
            dados.get('Batida', False), dados.get('Risco', False),
            dados.get('Trepidacao', False), dados.get('Ressalto', False),
            dados.get('Oxidacao', False), dados.get('DiametroInt', False),
            dados.get('DiametroIntDimensao'), dados.get('DiametroExt', False),
            dados.get('DiametroExtDimensao'), dados.get('Comprimento', False),
            dados.get('ComprimentoDimensao'), dados.get('DimensaoMaior', False),
            dados.get('Menor', False), dados.get('Outros', False),
            dados.get('OutrosDescricao'), dados.get('Observacoes')
        )

        sql = """INSERT INTO formularios (
            Data, Item, QntPecas, Maquina, Setor, NomeCracha,
            Montagem, Regulagem, MarcaRetifica, Empenamento, FalhaRaio, FalhaZinco, 
            Rebarba, Batida, Risco, Trepidacao, Ressalto, Oxidacao,
            DiametroInt, DiametroIntDimensao, DiametroExt, DiametroExtDimensao, 
            Comprimento, ComprimentoDimensao, DimensaoMaior, Menor, 
            Outros, OutrosDescricao, Observacoes
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        
        cursor.execute(sql, valores)
        conn.commit()
        print("✅ Salvo no banco com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao salvar no banco: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/upload', methods=['POST'])
def handle_upload():
    try:
        if 'imagem' not in request.files:
            return jsonify({"status": "erro", "mensagem": "Sem imagem"}), 400

        imagem_file = request.files['imagem']
        imagem_bytes = imagem_file.read()
        
        if len(imagem_bytes) < 100:
             return jsonify({"status": "erro", "mensagem": "Imagem vazia"}), 400

        # Processa
        dados = processar_documento(imagem_bytes)
        
        # Salva
        salvar_no_banco(dados)

        return jsonify({"status": "sucesso", "dados_lidos": dados}), 200

    except Exception as e:
        print(f"❌ ERRO NO SERVIDOR: {e}")
        # Retorna o erro exato para facilitar o debug
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == '__main__':
    print("Iniciando servidor...")
    app.run(debug=True, host='0.0.0.0', port=5000)