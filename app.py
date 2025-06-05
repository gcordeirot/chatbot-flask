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
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Chatbot Pingback</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
  <style>
    body {
      font-family: 'Inter', sans-serif;
      background-color: #f7f8fa;
      margin: 0;
      padding: 0;
      display: flex;
      justify-content: center;
    }
    .container {
      max-width: 700px;
      width: 100%;
      padding: 40px 20px;
    }
    h1 {
      text-align: center;
      color: #1a1a1a;
      margin-bottom: 30px;
    }
    form {
      display: flex;
      gap: 10px;
      margin-bottom: 30px;
    }
    input[type="text"] {
      flex: 1;
      padding: 14px;
      border-radius: 8px;
      border: 1px solid #ccc;
      font-size: 16px;
    }
    button {
      background-color: #5c6ac4;
      color: white;
      border: none;
      padding: 14px 24px;
      border-radius: 8px;
      font-size: 16px;
      cursor: pointer;
    }
    button:hover {
      background-color: #3f51b5;
    }
    #chatbox {
      background: white;
      padding: 24px;
      border-radius: 12px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    .user, .bot {
      margin-bottom: 10px;
    }
    .user {
      color: #333;
    }
    .bot {
      font-weight: 600;
      color: #111;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Chatbot da Pingback</h1>
    <form method="POST">
      <input type="text" name="mensagem" placeholder="Oi, eu sou o Pê, me pergunte algo!" required>
      <button type="submit">Enviar</button>
    </form>

    {% if pergunta and resposta %}
    <div id="chatbox">
      <div class="user">Você: {{ pergunta }}</div>
      <div class="bot">Pê: {{ resposta }}</div>
    </div>
    {% endif %}
  </div>
</body>
</html>
"""

# Página web interativa
@app.route('/', methods=['GET', 'POST'])
def home():
    global mensagens
    resposta = ""
    pergunta = ""

    if request.method == 'POST':
        pergunta = request.form['mensagem']
        mensagens = [('user', pergunta)]

        mensagem_system = '''Você é um assistente amigável chamado Pê, vc tenta ser mais resumido mas entregando a informação como um todo.
Você utiliza as seguintes informações para formular suas respostas: {informacoes}'''

        mensagens_modelo = [('system', mensagem_system)] + mensagens
        template = ChatPromptTemplate.from_messages(mensagens_modelo)
        chain = template | chat
        resposta = chain.invoke({'informacoes': documento}).content

        mensagens.append(('assistant', resposta))

    return render_template_string(HTML, pergunta=pergunta, resposta=resposta)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
