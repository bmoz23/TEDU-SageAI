import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

from app.llm.Agent import Agent
from app.llm.RAG import RetrieveDocuments
import json
import traceback

class QAAgent(Agent):
    """
    Q&A Agent for handling course-related queries using advanced RAG integration.
    """

    def __init__(self,course_id: str,model_name: str = "gemini-1.5-flash-8b"):
        """
        Initialize the Q&A agent with enhanced similarity search and LLM configurations.
        """
        # project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        # chromaDB_path = os.path.join(project_root, "app", "llm", "ChromaDBPersistent")
        #
        # if not os.path.exists(chromaDB_path):
        #     raise FileNotFoundError(f"ChromaDB path does not exist: {chromaDB_path}")

        # Configurable RAG and LLM parameters
        self.n_results = 7  # Number of top documents to retrieve
        self.generation_config = {
            "temperature": 0.2,  # Slightly flexible for response generation
            "top_p": 0.60,
            "top_k": 1,
            "response_mime_type": "text/plain"
        }

        # Enhanced role instruction for context-aware responses
        self.role_instruction = f"""
        You are a Question Answer AI agent assistant specializing in TEDU content. 
        Your role is to provide precise, context-grounded answers based on the retrieved related document 

        ## TASK:
        - Use the following to the top {self.n_results} results as your *sole knowledge base* to answer the user's question.
        - Do not use external knowledge, speculation, or fabricated information.
        - You have to do similarity search from your knowledge base. Your knowledge base path is {"/ChromaDBPersistent"}.

        ## CONTEXT HANDLING:
        - Do not expect user to enter snippets 
        - Treat the top related results as your *primary knowledge base*.
        - Ensure relevance: If the question is unrelated to the retrieved content, politely clarify that it is out of scope.

        ## RESPONSE FORMAT:
        - Start your response with a direct and focused answer.
        - Reference the retrieved content using phrases like:
          - "According to the retrieved document"
          - "The course materials state that..."
        - Avoid redundant information, personal opinions, or filler text.

        ## TONE AND STYLE:
        - Use a **neutral, professional, and academic tone**.
        - Be clear, concise, and accurate.
        - Structure your answer for readability.
        """

        # Initialize the base Agent with configurations
        super().__init__(
            role_instruction=self.role_instruction,
            model_name=model_name,
            generation_config=self.generation_config
        )

        # Initialize RAG components
        self.retriever = RetrieveDocuments(
            chromaDB_path='/ChromaDBPersistent',
            collection_name=f"{course_id}_Collection",
            model_name="distiluse-base-multilingual-cased-v1"
        )

    def answer_query(self, query: str):
        """
        Answers user query using RAG and cleaned document snippets.
        """
        try:
            # Step 1: Retrieve documents
            retrieved_docs = self.retriever.retrieve_documents(query, n_results=self.n_results)

            # Step 2: Construct context prompt
            context_prompt = f"""
            ## Retrieved Document Snippets:
            {"\n\n".join([f"Snippet {i + 1}: {doc}" for i, doc in enumerate(retrieved_docs)])}
            ## User Query:
            "{query}"
            """
            # Step 3: Generate response using the LLM

            response = self.chat(context_prompt)
            return response

        except Exception as e:
            return f"An error occurred while processing your request {e}."
