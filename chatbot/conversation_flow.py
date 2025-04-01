from flask import jsonify
from ..chatbot.nlu import process_user_input
from ..services.medicine_service import get_medicine_details, get_medicine_info, get_medicine_availability
from ..services.order_service import fetch_cart, checkout_order
from ..llm_connector import generate_response

class ConversationFlow:
    """
    Manages the conversation flow between the chatbot and the user, using an LLM for responses.
    """
    
    def __init__(self):
        self.state = {}

    def handle_message(self, user_id, message):
        """ 
        Processes user messages and provides appropriate responses via LLM.
        :param user_id: ID of the user interacting with the chatbot
        :param message: User's message
        :return: JSON response with the chatbot's reply
        """
        try:
            intent, entities = process_user_input(message)

            handlers = {
                "greet": self._greet_user,
                "search_medicine": self._handle_medicine_search,
                "medicine_info": self._handle_medicine_info,
                "medicine_availability": self._handle_availability_inquiry,
                "view_cart": self._view_cart,
                "checkout": self._checkout_cart,
            }

            handler = handlers.get(intent, self._fallback_response)
            return handler(user_id, entities)
        except Exception as e:
            return jsonify({"response": f"An error occurred: {str(e)}"}), 500

    def _fallback_response(self, user_id, entities=None):
        fallback_response = generate_response("I didn't understand that. Could you rephrase?")
        return jsonify({"response": fallback_response})

    def _greet_user(self, user_id, entities=None):
        """
        Greets the user dynamically using the LLM.
        """
        prompt = "Generate a friendly greeting for a returning user."
        response = generate_response(prompt)
        return jsonify({"response": response, "intent": "greet"})

    def _handle_medicine_search(self, user_id, entities):
        """
        Handles medicine search by returning relevant medicine details dynamically via the LLM.
        :param user_id: ID of the user
        :param entities: Entities containing search criteria
        """
        medicine_name = entities.get("medicine_name")

        if not medicine_name:
            prompt = "Generate a polite response asking the user to specify a medicine name."
            response = generate_response(prompt)
            return jsonify({"response": response})

        medicine = get_medicine_details(medicine_name)

        if not medicine:
            prompt = f"Generate a response apologizing for not finding the medicine '{medicine_name}'. Be short."
            response = generate_response(prompt)
            return jsonify({"response": response})

        # LLM-driven response for medicine details
        prompt = (
            f"Generate a response showing details for the medicine '{medicine['name']}' with its price. Be short."
        )
        response = generate_response(prompt)

        return jsonify({
            "response": response,
            "intent": "search_medicine",
            "medicine_details": {
                "id": medicine["id"],
                "name": medicine["name"],
                "pack_size_label": medicine["pack_size_label"],
                "price": medicine["price"],
                "image_url": medicine["image_url"],
                "clickable_link": f"/order/{medicine['id']}"
            }
        })

    def _handle_medicine_info(self, user_id, entities):
        """
        Handles user requests for detailed information about a specific medicine.
        :param user_id: ID of the user
        :param entities: Entities containing the medicine name or other identifiers
        """
        medicine_name = entities.get("medicine_name")

        if not medicine_name:
            prompt = "Generate a response asking the user to specify which medicine they need more information about."
            response = generate_response(prompt)
            return jsonify({"response": response})

        medicine_info = get_medicine_info(medicine_name)

        if not medicine_info:
            prompt = f"Generate a response apologizing for not finding detailed information about the medicine '{medicine_name}'."
            response = generate_response(prompt)
            return jsonify({"response": response})

        # LLM-driven response for detailed information
        prompt = (
            f"Generate a detailed response providing information about the medicine '{medicine_name}', including its uses, "
            f"side effects. The details are as follows: {medicine_info}. Make it short and informative."
        )
        response = generate_response(prompt)

        return jsonify({
            "response": response,
            "intent": "medicine_info",
            "medicine_info": medicine_info
        })

    def _handle_availability_inquiry(self, user_id, entities):
        """
        Handles medicine availability inquiry by returning relevant medicine details dynamically via the LLM.
        :param user_id: ID of the user
        :param entities: Entities containing search criteria
        """
        medicine_name = entities.get("medicine_name")

        if not medicine_name:
            prompt = "Generate a polite response asking the user to specify a medicine name to check for availability."
            response = generate_response(prompt)
            return jsonify({"response": response})

        medicine = get_medicine_availability(medicine_name)

        if not medicine:
            prompt = f"Generate a response apologizing for not finding the medicine '{medicine_name}'."
            response = generate_response(prompt)
            return jsonify({"response": response})

        # LLM-driven response for medicine details
        prompt = (
            f"Generate a short response showing details for the medicine '{medicine['name']}' with its stock. "
            f"The stock remaining is {medicine['stock']}."
        )
        response = generate_response(prompt)

        return jsonify({
            "response": response,
            "intent": "medicine_availability",
            "medicine_details": {
                "id": medicine["id"],
                "name": medicine["name"],
                "stock": medicine["stock"],
            }
        })

    def _view_cart(self, user_id, entities=None):
        """
        Retrieves and displays the user's cart via LLM response.
        """
        cart = fetch_cart(user_id)
        if not cart:
            prompt = "Generate a response informing the user that their cart is empty."
            response = generate_response(prompt)
            return jsonify({"response": response})

        cart_items = [
            f"{item['quantity']} x {item['medicine_name']} @ {item['price']} each"
            for item in cart
        ]
        cart_summary = "\n".join(cart_items)

        prompt = f"Generate a response summarizing the cart items: {cart_summary}"
        response = generate_response(prompt)

        return jsonify({"response": response, "intent": "view_cart"})

    def _checkout_cart(self, user_id, entities=None):
        """
        Handles the checkout process and dynamically responds using the LLM.
        """
        success, order_id, message = checkout_order(user_id)
        if success:
            prompt = f"Generate a congratulatory response for successfully placing order #{order_id}."
            response = generate_response(prompt)
            return jsonify({"response": response, "intent": "checkout"})
        else:
            prompt = f"Generate an error response for failed checkout: {message}"
            response = generate_response(prompt)
            return jsonify({"response": response})