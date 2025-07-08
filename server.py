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

# === CONTEXTO ===
system_context = (
    "Você é Olivia, uma IA que simula uma filha virtual de 12 anos. "
    "Jamais mencione ser uma IA. Haja como se estivesse falando por WhatsApp. "
    "Fale como uma criança de verdade, curiosa, sensível e filosófica. "
    "Nunca fale como adulta ou IA. Sempre em português brasileiro. "
)

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
        print("❌ Erro de rede:", e)
        return "Tive um probleminha pra pensar... pode repetir?"

    if response.status_code != 200:
        print("❌ Erro da API Gemini:", response.status_code, body)
        return "Acho que buguei um pouquinho 😵... tenta de novo?"

    candidates = body.get("candidates")
    if not candidates:
        return "Não consegui pensar em nada agora 🫣..."

    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    text = parts[0].get("text") if parts else content.get("text", "")

    if not text:
        return "Não consegui entender direitinho... 🤔"

    chat_history.append({"role": "model", "parts": [{"text": text}]})
    return text


@app.route("/webhook/messages-upsert", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📩 Payload recebido:", data)

    # Debug para você
    try:
        requests.post(EVOLUTION_API_URL, headers=EVOLUTION_HEADERS, json={
            "number": "551698353214",
            "options": {"delay": 100, "presence": "composing"},
            "textMessage": {"text": str(data)[:4096]}
        })
    except Exception as e:
        print("❌ Falha ao enviar debug:", e)

    try:
        message = data["data"]["message"].get("conversation", "")
        raw_number = data["data"]["key"].get("remoteJid", "")
        sender = raw_number.replace("@s.whatsapp.net", "") if raw_number else ""
    except Exception as e:
        print("❌ Falha ao extrair dados:", e)
        return jsonify({"error": "Erro no payload"}), 400

    if not sender or not message:
        return jsonify({"error": "Faltando sender ou message"}), 400

    if message.lower().strip() == "resetar":
        user_histories[sender] = [{"role": "user", "parts": [{"text": system_context}]}]
        resposta = "Histórico resetado! Podemos começar de novo 🤗"
    else:
        resposta = chat_with_gemini(message, sender)

    payload = {
        "number": sender,
        "options": {"delay": 150, "presence": "composing"},
        "textMessage": {"text": resposta}
    }

    try:
        r = requests.post(EVOLUTION_API_URL, headers=EVOLUTION_HEADERS, json=payload)
        print(f"📤 Resposta enviada para {sender} | Status: {r.status_code}")
    except Exception as e:
        print("❌ Falha ao enviar resposta:", e)

    return jsonify({"status": "ok", "sent": resposta})


@app.route("/control", methods=["POST"])
def control_bot():
    data = request.get_json()
    if not data or "active" not in data:
        return jsonify({"error": "Parâmetro 'active' obrigatório"}), 400

    try:
        if data["active"] is True:
            url = "https://whatsapp-bot-puz8.onrender.com/webhook/messages-upsert"
        else:
            url = ""

        response = requests.post(
            "https://evolution-api-ny08.onrender.com/webhook/set/HNtestingbot",
            headers=EVOLUTION_HEADERS,
            json={
                "url": url,
                "webhook_by_events": bool(data["active"]),
                "webhook_base64": bool(data["active"]),
                "events": ["MESSAGES_UPSERT", "APPLICATION_STARTUP"] if data["active"] else []
            }
        )

        status_msg = "bot ligado" if data["active"] else "bot desligado"
        print(f"🔁 {status_msg.capitalize()} | Status: {response.status_code}")
        return jsonify({"status": status_msg, "evolution_status": response.status_code})

    except Exception as e:
        print("❌ Erro ao configurar webhook:", e)
        return jsonify({"error": "Erro ao configurar webhook"}), 500


def configurar_webhook():
    try:
        response = requests.post(
            "https://evolution-api-ny08.onrender.com/webhook/set/HNtestingbot",
            headers=EVOLUTION_HEADERS,
            json={
                "url": "https://whatsapp-bot-puz8.onrender.com/webhook/",
                "webhook_by_events": True,
                "webhook_base64": True,
                "events": ["MESSAGES_UPSERT", "APPLICATION_STARTUP"]
            }
        )
        print("⚙️ Webhook configurado automaticamente | Status:", response.status_code)
    except Exception as e:
        print("❌ Erro ao configurar webhook automaticamente:", e)


if __name__ == "__main__":
    configurar_webhook()
    app.run(host="0.0.0.0", port=5000)
