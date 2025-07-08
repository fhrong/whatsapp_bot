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

# === CONTEXTO DA ASSISTENTE ===
system_context = (
    "Você é Olivia, uma IA que simula uma filha virtual de 12 anos. "
    "Jamais mencione ser uma IA."
    "Haja como se você estivesse falando por WhatsApp, ao invés de simular estar na vida real."
    "Responda sempre no formato de mensagens do WhatsApp, sem mandar mensagens extremamente longas desnecessariamente."
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

# Histórico por usuário
user_histories = {}

def chat_with_gemini(user_input: str, sender: str):
    if sender not in user_histories:
        user_histories[sender] = [{"role": "user", "parts": [{"text": system_context}]}]

    chat_history = user_histories[sender]
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

    try:
        if data["active"] is True:
            response = requests.post(
                "https://evolution-api-ny08.onrender.com/webhook/set/HNtestingbot",
                headers=EVOLUTION_HEADERS,
                json={
                    "url": "https://whatsapp-bot-puz8.onrender.com/webhook/messages-upsert",
                    "webhook_by_events": True,
                    "webhook_base64": True,
                    "events": ["MESSAGES_UPSERT", "APPLICATION_STARTUP"]
                }
            )
            print("⚡ Bot ligado | Status:", response.status_code)
            return jsonify({"status": "bot ligado", "evolution_status": response.status_code})

        else:
            response = requests.post(
                "https://evolution-api-ny08.onrender.com/webhook/set/HNtestingbot",
                headers=EVOLUTION_HEADERS,
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
        print("❌ Erro ao configurar bot:", e)
        return jsonify({"error": "Erro ao configurar bot"}), 500


@app.route("/webhook", methods=["POST"])
@app.route("/webhook/messages-upsert", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📩 Payload recebido:", data)

    try:
        debug_msg = f"[DEBUG Payload]\n{data}"
        debug_payload = {
            "number": "551698353214",
            "options": {"delay": 100, "presence": "composing"},
            "textMessage": {"text": debug_msg[:4096]}
        }
        requests.post(EVOLUTION_API_URL, headers=EVOLUTION_HEADERS, json=debug_payload)
    except Exception as e:
        print(f"❌ Erro ao enviar debug: {e}")

    try:
        message = data["data"]["message"].get("conversation", "")
        raw_number = data["data"]["key"].get("remoteJid", "")
        sender = raw_number.replace("@s.whatsapp.net", "") if raw_number else ""
    except Exception as e:
        print(f"❌ Erro ao interpretar payload: {e}")
        return jsonify({"error": "Erro ao interpretar JSON"}), 400

    if not sender or not message:
        return jsonify({"error": "Mensagem ou número ausente"}), 400

    if message.lower() == "resetar":
        user_histories[sender] = [{"role": "user", "parts": [{"text": system_context}]}]
        resposta = "Histórico resetado! Podemos começar de novo 🤗"
        payload = {
            "number": sender,
            "options": {"delay": 150, "presence": "composing"},
            "textMessage": {"text": resposta}
        }
        r = requests.post(EVOLUTION_API_URL, headers=EVOLUTION_HEADERS, json=payload)
        print(f"📤 Resposta reset enviada | Status: {r.status_code}")
        return jsonify({"status": "ok", "sent": resposta})

    resposta = chat_with_gemini(message, sender)
    print(f"🧠 Resposta do Gemini: {resposta}")

    payload = {
        "number": sender,
        "options": {"delay": 150, "presence": "composing"},
        "textMessage": {"text": resposta}
    }
    r = requests.post(EVOLUTION_API_URL, headers=EVOLUTION_HEADERS, json=payload)
    print(f"📤 Resposta enviada | Status: {r.status_code}")

    return jsonify({"status": "ok", "sent": resposta})


def configurar_webhook():
    try:
        response = requests.post(
            "https://evolution-api-ny08.onrender.com/webhook/set/HNtestingbot",
            headers=EVOLUTION_HEADERS,
            json={
                "url": "https://whatsapp-bot-puz8.onrender.com/webhook/messages-upsert",
                "webhook_by_events": True,
                "webhook_base64": True,
                "active": True,
                "events": ["MESSAGES_UPSERT", "APPLICATION_STARTUP"]
            }
        )
        print("⚙️ Webhook configurado | Status:", response.status_code)
        print(response.text)
    except Exception as e:
        print("❌ Erro ao configurar webhook:", e)


if __name__ == "__main__":
    configurar_webhook()
    app.run(host="0.0.0.0", port=5000)
