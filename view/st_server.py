from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# Mock AI response generation function (replace with actual AI model logic)
def generate_ai_response(user_input):
    return "testset"
    
# Endpoint to receive user input and return AI-generated response
@app.route('/input', methods=['POST'])
def receive_input():
    user_input = request.json.get('user_input')
    
    if user_input:
        # Generate AI response based on the user input
        ai_response = generate_ai_response(user_input)
        
        # Return the AI response back to Streamlit
        return jsonify({"status": "success", "ai_response": ai_response}), 200
    
    return jsonify({"status": "error", "message": "No input received"}), 400

if __name__ == '__main__':
    app.run(port=5000, debug=True)
