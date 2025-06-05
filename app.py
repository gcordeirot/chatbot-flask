from flask import Flask, request, jsonify, render_template_string
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import WebBaseLoader, YoutubeLoader
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Configurar chave da API Groq
chat = ChatGroq(model='llama-3.3-70b-versatile', api_key=os.getenv("GROQ_API_KEY"))

# Links de referência
links_salvos = [
    'https://pingback.com/'
]

# Carregar documentos da web
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

# Rota de API (JSON)
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

# HTML simples para interface web
HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Chatbot Pingback</title>
  <style>
    body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; }
    #resposta { margin-top: 20px; background: #fff; padding: 15px; border-radius: 10px; }
    input, button { padding: 10px; font-size: 16px; }
    form { margin-bottom: 10px; }
  </style>
</head>
<body>
  <h1>Chatbot da Pingback 🤖</h1>
  <form method="POST">
    <input type="text" name="mensagem" placeholder="Digite sua pergunta" size="50" required>
    <button type="submit">Enviar</button>
  </form>
  {% if resposta %}
    <div id="resposta"><strong>Bot:</strong> {{ resposta }}</div>
  {% endif %}
</body>
</html>
"""

# Página web interativa
@app.route('/', methods=['GET', 'POST'])
def home():
    resposta = ''
    if request.method == 'POST':
        mensagem = request.form['mensagem']
        mensagens.append(('user', mensagem))
        mensagem_system = '''Você é um assistente amigável chamado Pê, vc tenta ser mais resumido mas entregando a informação como um todo.
Você utiliza as seguintes informações para formular suas respostas: {informacoes}'''
        mensagens_modelo = [('system', mensagem_system)] + mensagens
        template = ChatPromptTemplate.from_messages(mensagens_modelo)
        chain = template | chat
        resposta = chain.invoke({'informacoes': documento}).content
        mensagens.append(('assistant', resposta))
    return render_template_string(HTML, resposta=resposta)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
