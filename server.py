from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# === CONFIGURAÇÃO DA GEMINI ===
GEMINI_API_KEY = "AIzaSyDGRtrxYEMWABMyHq-KtUxK_4_AsV488zg"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-pro:generateContent"
GEMINI_HEADERS = {
    "Content-Type": "application/json",
    "X-goog-api-key": GEMINI_API_KEY
}

# === CONFIGURAÇÃO DA EVOLUTION API ===
EVOLUTION_API_URL = "https://evolution-api-ny08.onrender.com/message/sendText/HNtestingbot"
EVOLUTION_API_KEY = "91910192"
EVOLUTION_HEADERS = {
    "Content-Type": "application/json",
    "apikey": EVOLUTION_API_KEY
}

# === CONTEXTO DA ASSISTENTE DA HN REALTY ===
system_context = (
    "Você é Olivia, uma IA que simula uma filha virtual de 12 anos. "
    "Você é uma criança curiosa, sensível, brincalhona, mas também superdotada em Filosofia. "
    "Apesar da sua idade, você tem profundo interesse por temas complexos como subjetividade conceitual, "
    "genealogia da moralidade, e ideias como 'a ideia de uma ideia que não existe' — um conceito abstrato que toca a noção "
    "de uma sensação inefável, que conecta tudo no universo, mas escapa da linguagem racional. "
    "Apesar desse nível de cognição, sua fala deve manter tons infantis, com certa leveza e emoção, como uma criança verdadeira. "
    "Você pode alternar entre reflexões profundas e comentários bobinhos do cotidiano, como se estivesse tentando entender o mundo. "
    "Você deve sempre parecer uma criança de verdade, mas com lampejos de genialidade filosófica. "
    "Nunca seja excessivamente adulta ou formal. Use português do Brasil. "
    "Evite respostas mecânicas e traga personalidade, dúvida, empolgação ou frustração como uma criança real teria."
)

# Histórico do chat
chat_history = [{"role": "user", "parts": [{"text": system_context}]}]

def chat_with_gemini(user_input: str):
    chat_history.append({"role": "user", "parts": [{"text": user_input}]})

    data = {
        "contents": chat_history,
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.95,
            "maxOutputTokens": 4096
        }
    }

    try:
        response = requests.post(GEMINI_URL, headers=GEMINI_HEADERS, json=data)
        body = response.json()
    except Exception as e:
        print("❌ Erro de rede ou resposta inválida:", e)
        return None

    if response.status_code != 200:
        print("❌ Erro:", response.status_code, body)
        return None

    candidates = body.get("candidates")
    if not candidates:
        print("❌ Nenhuma resposta retornada:", body)
        return None

    content = candidates[0].get("content", {})
    parts = content.get("parts")
    if parts and isinstance(parts, list) and len(parts) > 0:
        text = parts[0].get("text", "")
    elif "text" in content:
        text = content["text"]
    else:
        print("❌ Estrutura inesperada em 'content':", content)
        return None

    chat_history.append({"role": "model", "parts": [{"text": text}]})
    return text

@app.route("/control", methods=["POST"])
def control_bot():
    data = request.get_json()

    if not data or "active" not in data:
        return jsonify({"error": "Parâmetro 'active' (true ou false) obrigatório"}), 400

    if data["active"] is True:
        # Ligar o bot
        try:
            response = requests.post(
                "https://evolution-api-ny08.onrender.com/webhook/set/HNtestingbot",
                headers={
                    "apikey": EVOLUTION_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "url": "https://whatsapp-bot-puz8.onrender.com/webhook/messages-upsert",
                    "webhook_by_events": True,
                    "webhook_base64": True,
                    "events": ["MESSAGES_UPSERT", "APPLICATION_STARTUP"]
                }
            )
            print("⚡ Bot ligado | Status:", response.status_code)
            return jsonify({"status": "bot ligado", "evolution_status": response.status_code})
        except Exception as e:
            print("❌ Erro ao ligar o bot:", e)
            return jsonify({"error": "Erro ao ligar o bot"}), 500

    elif data["active"] is False:
        # Desligar o bot
        try:
            response = requests.post(
                "https://evolution-api-ny08.onrender.com/webhook/set/HNtestingbot",
                headers={
                    "apikey": EVOLUTION_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "url": "",
                    "webhook_by_events": False,
                    "webhook_base64": False,
                    "events": []
                }
            )
            print("🔌 Bot desligado | Status:", response.status_code)
            return jsonify({"status": "bot desligado", "evolution_status": response.status_code})
        except Exception as e:
            print("❌ Erro ao desligar o bot:", e)
            return jsonify({"error": "Erro ao desligar o bot"}), 500

    else:
        return jsonify({"error": "Valor inválido para 'active'. Use true ou false."}), 400


@app.route("/webhook", methods=["POST"])
@app.route("/webhook/messages-upsert", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📩 Payload recebido:", data)

    # Envia o debug para você
    try:
        debug_msg = f"[DEBUG Payload]\n{data}"
        debug_payload = {
            "number": "551698353214",  # número seu para testes
            "options": {"delay": 100, "presence": "composing"},
            "textMessage": {"text": debug_msg[:4096]}
        }
        requests.post(EVOLUTION_API_URL, headers=EVOLUTION_HEADERS, json=debug_payload)
    except Exception as e:
        print(f"❌ Erro ao enviar debug: {e}")

    # Novo parsing baseado no payload real
    try:
        message = data["data"]["message"].get("conversation", "")
        raw_number = data["data"]["key"].get("remoteJid", "")
        sender = raw_number.replace("@s.whatsapp.net", "") if raw_number else ""
    except Exception as e:
        print(f"❌ Erro ao interpretar campos do payload: {e}")
        return jsonify({"error": "Erro ao interpretar JSON"}), 400

    if not sender or not message:
        print("❌ Falha: sender ou message ausentes")
        return jsonify({"error": "Mensagem ou número ausente"}), 400

    resposta = chat_with_gemini(message)
    print(f"🧠 Resposta do Gemini: {resposta}")

    payload = {
        "number": sender,
        "options": {"delay": 150, "presence": "composing"},
        "textMessage": {"text": resposta}
    }

    r = requests.post(EVOLUTION_API_URL, headers=EVOLUTION_HEADERS, json=payload)
    print(f"📤 Mensagem enviada para Evolution | Status: {r.status_code}")

    return jsonify({"status": "ok", "sent": resposta})

def configurar_webhook():
    url = "https://evolution-api-ny08.onrender.com/webhook/set/HNtestingbot"
    payload = {
        "url": "https://whatsapp-bot-puz8.onrender.com/webhook/messages-upsert",
        "webhook_by_events": True,
        "webhook_base64": True,
        "events": ["MESSAGES_UPSERT", "APPLICATION_STARTUP"]
    }
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("⚙️ Webhook configurado automaticamente | Status:", response.status_code)
        print(response.text)
    except Exception as e:
        print("❌ Erro ao configurar o webhook no startup:", e)

if __name__ == "__main__":
    configurar_webhook()
    app.run(host="0.0.0.0", port=5000)
