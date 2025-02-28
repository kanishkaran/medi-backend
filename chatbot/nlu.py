# from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
import re

# Initialize OpenAI LLM for intent recognition and entity extraction
llm = ChatGroq(model='llama-3.1-8b-instant', api_key="")

# Define a prompt template for intent classification and entity extraction
intent_prompt_template = """
You are a helpful assistant for a chatbot system that can process medicine orders.
Here are the types of intents you can handle:
1. greet: User greets the bot.
2. search_medicine: User is looking for a specific medicine.
3. medicine_info: User asks for detailed information like uses and side effects about a medicine.
4. medicine_availability: User asks for the availability of a particular medicine.
5. view_cart: User wants to view the items in their cart.
6. checkout: User wants to checkout and complete the order.

Your task is to classify the user input into one of these intents, and if applicable, extract relevant entities (like medicine name, quantity, etc.).
Here is the user input: "{user_input}"

Provide the intent and entities in the following format:
{{
  "intent": "<intent_name>",
  "entities": {{
    "medicine_name": "<medicine_name>",
    "quantity": "<quantity>"
  }}
}}

Do not give anyother response other than the above format
"""

intent_prompt = PromptTemplate.from_template(intent_prompt_template)
intent_chain = intent_prompt | llm | StrOutputParser()

def process_user_input(user_input):
    """
    Processes the user's input to extract the intent and entities using LangChain and OpenAI.
    :param user_input: The input message from the user.
    :return: The extracted intent and entities.
    """
    print("Executing process user input function...")
    input = {"user_input": user_input}
    # Generate the response using the LLM chain
    response = intent_chain.invoke(input)
    print("got response..")

    # Parse the response into intent and entities
    response_data = eval(response)
    print('response parsed..')

    # Extract the intent and entities
    intent = response_data.get("intent")
    entities = response_data.get("entities", {})

    # Clean up entities, ensuring that they are well-formed (e.g., medicine name, quantity)
    if "medicine_name" in entities:
        entities["medicine_name"] = entities["medicine_name"].strip()
    
    if "quantity" in entities:
        entities["quantity"] = int(entities["quantity"]) if entities["quantity"].isdigit() else 1
    
    print('returned intents and entities...')
    return intent, entities


