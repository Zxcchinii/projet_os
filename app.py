from flask import Flask, request, jsonify

app = Flask(__name___)
message = []

@app.route('/send', methods=['POST'])
def send_message():
	data = request.get_json()
	messages.append(data)
	return jsonify({"status":"Message received", "message": data}), 200
	
@app.route('/messages', methods=['GET'])
def get_messages():
    return jsonify(messages), 200
    
if __name__ == "main":
    app.run(host="0.0.0.0", port=5000)


