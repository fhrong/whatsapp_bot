from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return "Webhook está ativo!", 200

    data = request.get_json(silent=True)
    print("Recebido do Evolution:", data)


    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
