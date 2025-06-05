from flask import Flask, request, jsonify
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import WebBaseLoader, YoutubeLoader
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Configurar chave da API Groq
os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
chat = ChatGroq(model='llama-3.3-70b-versatile')

links_salvos = [
    'https://pingback.com/',
    'https://pingback.com/pricing'
]

def carregar_todos_documentos():
    documento_completo = ''
    for url in links_salvos:
        try:
            if 'youtube.com' in url:
                loader = YoutubeLoader.from_youtube_url(url, language=['pt'])
            else:
                loader = WebBaseLoader(url)
            docs = loader.load()
            for doc in docs:
                documento_completo += doc.page_content
        except Exception as e:
            print(f'Erro ao carregar {url}: {e}')
    return documento_completo

documento = carregar_todos_documentos()
mensagens = []

@app.route('/chat', methods=['POST'])
def chat_bot():
    user_msg = request.json.get("mensagem")
    mensagens.append(('user', user_msg))
    mensagem_system = '''Você é um assistente amigável chamado Pê, vc tenta ser mais resumido mas entregando a informação como um todo.
Você utiliza as seguintes informações para formular suas respostas: {informacoes}'''
    mensagens_modelo = [('system', mensagem_system)] + mensagens
    template = ChatPromptTemplate.from_messages(mensagens_modelo)
    chain = template | chat
    resposta = chain.invoke({'informacoes': documento}).content
    mensagens.append(('assistant', resposta))
    return jsonify({"resposta": resposta})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
