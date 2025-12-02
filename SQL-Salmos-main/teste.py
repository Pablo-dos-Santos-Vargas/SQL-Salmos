import os
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions

PROJECT_ID = "599834168707".strip()
LOCATION = "us".strip()
PROCESSOR_ID = "98b736a0b757dd27".strip()
FILE_PATH = "teste.jpg"

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"

def teste_envio_isolado():
    print("--- INICIANDO TESTE ISOLADO ---")
    
    if not os.path.exists(FILE_PATH):
        print(f"[ERRO] O arquivo '{FILE_PATH}' não foi encontrado na pasta.")
        return

    with open(FILE_PATH, "rb") as f:
        image_content = f.read()
    
    print(f"Imagem carregada: {len(image_content)} bytes.")

    opts = ClientOptions(api_endpoint="documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)

    name = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
    print(f"Endereço montado: {name!r}")

    raw_document = documentai.RawDocument(
        content=image_content,
        mime_type="image/jpeg"
    )
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)

    try:
        print("Enviando para o Google...")
        result = client.process_document(request=request)
        print("\n[SUCESSO] O Google processou a imagem!")
        print("Entidades encontradas:", len(result.document.entities))
    except Exception as e:
        print("\n[FALHA] O erro persiste aqui:")
        print(e)

if __name__ == "__main__":
    teste_envio_isolado()