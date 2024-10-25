from flask import Blueprint, request, jsonify


endpoint_blueprint = Blueprint("webhook", __name__)

def define_endpoints(view_callback):
    # Endpoint to receive user input and return AI-generated response
    @endpoint_blueprint.route("/input", methods=["POST"])
    def receive_input():
        user_input = request.json.get("user_input")

        if user_input:
            # Generate AI response based on the user input
            data_dict = {
                "type": "text",
                "chat_id": "streamlit-demo",
                "text": user_input
            }
            ai_response = view_callback(data_dict)

            # Return the AI response back to Streamlit
            return jsonify({"status": "success", "ai_response": ai_response}), 200

        return jsonify({"status": "error", "message": "No input received"}), 400


    # Endpoint to delete chat history
    @endpoint_blueprint.route("/delete_history", methods=["POST"])
    def delete_history():
        try:
            # Delete chat history
            data_dict = {
                "type": "delete_history", 
                "chat_id": "streamlit-demo"
            }
            view_callback(data_dict)
            # Return the AI response back to Streamlit
            return jsonify(
                {"status": "success", "graph_response": "graph history deleted"}
            ), 200
        except Exception as e:
            print(f"Error occurred while deleting chat history: {e}")
            return jsonify({"status": "error", "Error": str(e)}), 400