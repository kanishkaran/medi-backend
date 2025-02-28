from langchain_groq import ChatGroq
# from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
# from langchain_core.prompts import ChatPromptTemplate


# Initialize OpenAI LLM for intent recognition and entity extraction
llm = ChatGroq(model='llama-3.1-8b-instant', api_key="")

output_parser = StrOutputParser()



def generate_response(prompt):
    """
    Generates a conversational response using the LLM.
    :param prompt: The input prompt for the LLM
    :return: Generated response as a string
    """
    # print(prompt, type(prompt))
    chain =  llm | output_parser

    return chain.invoke(prompt)

