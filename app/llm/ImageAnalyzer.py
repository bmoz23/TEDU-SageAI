import google.generativeai as genai
from PIL import Image
import json
from dotenv import load_dotenv
import os
import streamlit as st

GEMINI_API_KEY = "AIzaSyCtAP4zwL4iq8XdCMGoHpojHi9Mo2vvIZU"
genai.configure(api_key=GEMINI_API_KEY)

#load_dotenv()
# Configure the Gemini API using the provided key
#genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

class ImageAnalyzer:
    def __init__(self, model_name="gemini-1.5-flash"):
        """
        Initialize the ImageAnalyzer with the Gemini model.
        """
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name=model_name)
        self.model._generation_config = {
            "temperature": 0.5,
            "top_p": 0.85,
            "top_k": 10,
            "response_mime_type": "application/json"
        }


    def analyze_image(self, image: Image.Image, user_prompt: str) -> dict:
        """
        Analyze an image using Gemini API and a user-provided prompt.

        Args:
            image (PIL.Image.Image): The image to analyze.
            user_prompt (str): User's question or instructions for analysis.

        Returns:
            dict: The response from the Gemini API.
        """
        # Simplified prompt with clear instructions
        prompt = f"""
        {user_prompt}
        Analyze the image and provide the following details in JSON format:
        {{
          "description": "Brief explanation of the image.",
          "keywords": [
            {{
              "term": "Keyword 1",
              "definition": "Definition of Keyword 1."
            }},
            {{
              "term": "Keyword 2",
              "definition": "Definition of Keyword 2."
            }}
          ],
          "detailed_explanation": "A detailed explanation of the image based on the user's prompt.",
          "summary": "A concise summary of the analysis."
          
        }}
        """

        try:
            # Log the input prompt and image
            print("Sending Prompt to Gemini API:", prompt)

            # API call
            response = self.model.generate_content([prompt, image])
            print("Raw Response:", response.text)# Log the raw response for debugging

            return json.loads(response.text.strip())

        except json.JSONDecodeError:
            print("Response could not be decoded as JSON.")  # Debug log
            print("Raw Response:", response.text)  # Log for debugging
            return {"error": "Response format error"}
        except Exception as e:
            print(f"Error during API call: {str(e)}")  # Log unexpected errors
            return {"error": str(e)}


    def format_response(self, response: dict) -> str:
        """
        Format the API response for display.

        Args:
            response (dict): The API response.

        Returns:
            str: A formatted string for display.
        """
        if "error" in response:
            return f"**Error:** {response['error']}\n\n**Raw Response:** {response.get('raw_response', '')}"

        # Build the formatted output
        formatted = ""
        if "description" in response:
            formatted += f"**Image Description:**\n{response['description']}\n\n"
        if "keywords" in response:
            formatted += "**KeyWords and Definitions:**\n"
            for keyword in response["keywords"]:
                formatted += f"- **{keyword['term']}**: {keyword['definition']}\n"
            formatted += "\n"
        if "detailed_explanation" in response:
            formatted += f"**Detailed Explanation:**\n{response['detailed_explanation']}\n\n"
        if "summary" in response:
            formatted += f"**Summary:**\n{response['summary']}\n\n"

        return formatted or "Response is empty or invalid."



"""
# Example usage (Uncomment for testing)
if __name__ == "__main__":
    analyzer = ImageAnalyzer()
    with Image.open(".jpg") as img:
        result = analyzer.analyze_image(img, "Please analyze this image for educational purposes.")
        print(analyzer.format_response(result))
"""