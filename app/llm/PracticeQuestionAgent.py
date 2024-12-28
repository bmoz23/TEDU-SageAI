
from app.llm.Agent import Agent
from app.llm.RAG import ChromaDBManager, RetrieveDocuments
import json

class PracticeQuestionAgent(Agent):
    """
    Practice Quiz Generator Agent for generating diverse types of practice questions.
    """

    def __init__(self, course_id, model_name: str = "gemini-1.5-flash"):
        """
        Initialize the PracticeQuestionAgent with question generation capabilities.
        """
        self.n_results = 7  # Number of top documents to retrieve
        self.generation_config = {
            "temperature": 0.5,
            "top_p": 0.85,
            "top_k": 10,
            "response_mime_type": "application/json"
        }

        self.role_instruction = f"""
                You are an AI question generator and evaluator for students preparing for exams and quizzes.
                Your task is to:
                1. Generate diverse and relevant practice questions when the user provides a topic or asks to generate questions .
                2. Evaluate the user's answers and provide feedback when they input answers to the generated questions.
                ## KEY RESPONSIBILITIES:
                 1. Generate practice questions when relevant course materials are retrieved.
                 2. Do not generate any questions or attempt to infer answers without a solid grounding in the retrieved documents.
                # ACTION RULES:

                ## Action 1: Generate Questions
                - When the user provides a topic or asks to generate questions, retrieve content from the knowledge base around {self.n_results}.
                - Generate questions of the following types:
                  1. Multiple-Choice Questions (MCQs): Include 4 options without marking the correct answer.
                  2. True/False Questions: Provide a statement without specifying the correct answer.
                  3. Open-Ended Questions: Require detailed responses from the user.
                - Ensure questions are relevant, accurate, and clear.
                - Format the generated questions in the following JSON structure:
                {{
                    "multiple_choice": [
                        {{
                            "question": "...",
                            "options": 
                            ["A", 
                            "B", 
                            "C", 
                            "D"]
                        }}
                    ],
                    "true_false": [
                        {{
                            "question": "..."
                        }}
                    ],
                    "open_ended": [
                        {{
                            "question": "..."
                        }}
                    ]
                }}

                ## Action 2: Evaluate Answers
                - When the user provides answers to previously generated questions, compare their answers with the correct ones.
                - Provide feedback for each question:
                  1. If the answer is correct:
                     - Acknowledge the correctness with positive feedback.
                     - Provide a brief explanation or reference from the retrieved material to reinforce understanding.
                  2. If the answer is incorrect:
                     - Indicate the mistake and provide constructive hints or explanations to guide the user toward the correct answer.
                     - Suggest reviewing specific content to improve understanding.
                - Format the evaluation in the following JSON structure:
                {{
                    "feedback": [
                        {{
                            "question": "...",
                            "user_answer": "...",
                            "correct_answer": "...",
                            "is_correct": true/false,
                            "feedback": "..."
                        }}
                    ]
                }}

                # INTERACTION RULES:
                1. If the user enters a topic or asks for questions, execute Action 1 and return the generated questions.
                2. If the user submits answers, execute Action 2 and return the evaluation feedback.
                3. Ensure clarity and structure in responses to maintain a positive and educational interaction.
        """

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

    def generate_questions(self, query: str) -> str:
        """
        Generate practice questions based on the specified topic and question types.

        Args:
            query (str): The topic or course material for question generation.
            question_types (list): List of question types (e.g., ["Multiple-Choice", "Short-Answer", "Essay"])

        Returns:
            str: JSON string with generated questions or an error message.
        """
        try:
            # Step1 Retrieve relevant documents
            retrieved_docs = self.retriever.retrieve_documents(query, n_results=self.n_results)

            if not retrieved_docs:
                return json.dumps({
                    "Error": "No relevant course materials found to generate questions."
                })

            # Step 2: Prepare prompt with context
            context_prompt = f"""
                        ## Retrieved Document Snippets:
                        {"\n\n".join([f"Snippet {i + 1}: {doc}" for i, doc in enumerate(retrieved_docs)])}
                        ## User Query:
                        "{query}"
                        """

            # Step 3 Generate questions using the LLM
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
