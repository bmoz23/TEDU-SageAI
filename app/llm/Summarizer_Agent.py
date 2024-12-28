
from app.llm.Agent import Agent
import json
from app.llm.RAG import RetrieveDocuments


class SummarizerAgent(Agent):
    """
    Summarizer Agent for generating structured summaries based on course materials using RAG and LLM chat.
    """

    def __init__(self,course_id,model_name: str = "gemini-1.5-flash-8b"):
        """
        Initialize the SummarizerAgent with similarity search and LLM configurations.
        """
        self.n_results = 5  # Number of top documents to retrieve for context
        self.generation_config = {
            "temperature": 0.4,
            "top_p": 0.9,
            "top_k": 40,
            "response_mime_type": "application/json"
        }

        self.role_instruction = f"""
            # GOAL:
            You are a summarization agent. Your task is to generate structured summaries for course materials
            based on the specified format. You use Retrieval-Augmneted Generation to the related document summurization. The summaries must be accurate, detailed, and clear based on the available information.
            ## Key Instructions:
             1. Ensure that all JSON keys and values are correctly formatted.
             2. Do not include trailing commas in arrays or objects.
             3. Validate your output to ensure it is **valid JSON**.


            # RESPONSE FORMAT:
            
            Your response must adhere to the following JSON structure:
            {{
                "overview": {{
                    "title": "string"
                }},
                "key_topics": [
                    {{
                        "topic": "string",
                        "description": "string"
                    }}
                ],
                "detailed_summary": {{
                    "sections": [
                        {{
                            "title": "string",
                            "key_points": [
                                "string"
                            ],
                            "examples": [
                                "string"
                            ]
                        }}
                    ]
                }},
                "key_terms_and_definitions": [
                    {{
                        "term": "string",
                        "definition": "string"
                    }}
                ]
            }}

            # GENERAL RULES:
            - Always base summaries on retrieved course materials.
            - Ensure the response is well-structured and adheres to the required format.
            - Include meaningful content under each section based on the retrieved context.
            - If no context is available, respond with:
              {{"Error": "I'm sorry, I couldn't generate a summary due to insufficient content."}}

            # CONTEXT HANDLING:
            - Retrieve and use up to {self.n_results} relevant documents for grounding the summary.
            - Match the level of detail to the user's request, incorporating as much relevant information as possible.

            # EXAMPLES:
            Example User Request: "Summarize the key points about supervised learning."
            Retrieved Context: ["Supervised learning involves labeled data and models learn from the labels."]
            Response:
            {{
                "overview": {{
                    "title": "Supervised Learning"
                }},
                "key_topics": [
                    {{
                        "topic": "Labeled Data",
                        "description": "Data with clear labels used to train supervised learning models."
                    }}
                ],
                "detailed_summary": {{
                    "sections": [
                        {{
                            "title": "Introduction to Supervised Learning",
                            "key_points": [
                                "Uses labeled data for training.",
                                "Models map inputs to outputs based on labels."
                            ],
                            "examples": [
                                "Classifying images into categories.",
                                "Predicting house prices based on features."
                            ]
                        }}
                    ]
                }},
                "key_terms_and_definitions": [
                    {{
                        "term": "Labeled Data",
                        "definition": "Data annotated with the correct output for training."
                    }}
                ]
            }}
        """

        super().__init__(
            role_instruction=self.role_instruction,
            model_name=model_name,
            generation_config=self.generation_config
        )

        # Initialize ChromaDB for similarity search

        self.retriever= RetrieveDocuments(
            chromaDB_path='/ChromaDBPersistent',
            collection_name=f"{course_id}_Collection",
            model_name="distiluse-base-multilingual-cased-v1"
        )

    def summarize(self, query: str) -> str:
        """
        Generate a structured summary for the given query.

        Args:
            query (str): User-provided query for context retrieval.

        Returns:
            str: The generated structured summary or an error message.
        """
        try:
            # Step 1: Retrieve relevant documents
            retrieved_docs = self.retriever.retrieve_documents(query, n_results=self.n_results)

            if not retrieved_docs:
                return json.dumps({
                    "Error": "I'm sorry, I couldn't generate a summary due to insufficient content."
                })


            # Step 2: Prepare prompt with context
            # context = "\n".join(retrieved_docs)
            # prompt = f"""
            # The following is context from course materials:\n\n{context}\n\n
            # Generate a structured summary adhering to the specified JSON format:
            # {self.role_instruction}
            # """

            context = "\n".join(retrieved_docs)
            context_prompt = f"""
                        The following is context from course materials:\n\n{context}\n\n
                        Generate a structured summary adhering to the specified JSON format:
                        """

            # Step 3: Get response from LLM
            response = self.chat(context_prompt)

            # Step 4: Parse JSON response
            try:
                parsed_response = json.loads(response)
                print("JSON Parsing Successful")
                return json.dumps(parsed_response, indent=4)
            except Exception as e:
                print(f"JSON Parsing Error: {e}")
                return json.dumps({
                    "Error": "The response from the model could not be parsed into the expected JSON format.",
                    "Raw_Response": response
                })

        except Exception as e:
            # General error handling
            return json.dumps({
                "Error": f"An error occurred while processing the summary: {str(e)}"
            })
