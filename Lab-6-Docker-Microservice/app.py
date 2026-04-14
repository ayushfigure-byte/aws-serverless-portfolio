from flask import Flask, jsonify

app = Flask(__name__)

# Endpoint 1: The Health Check (Crucial for Containers)
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Microservice is running!"}), 200

# Endpoint 2: The Actual Business Logic
@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({
        "data": "Hello from inside the Docker container!", 
        "version": "1.0"
    }), 200

if __name__ == '__main__':
    # Bind to all network interfaces so AWS can route traffic to it
    app.run(host='0.0.0.0', port=80)
