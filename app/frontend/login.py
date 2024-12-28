
import sys
import os
import textwrap

# Append the absolute path of the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
os.chdir(project_root)  # Change to the project root directory
sys.path.insert(0, project_root)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.llm.PracticeQuestionAgent import PracticeQuestionAgent
from app.llm.ImageAnalyzer import ImageAnalyzer
from PIL import Image

# Dynamically resolve the absolute path to the image
image_path = os.path.join(os.path.dirname(__file__), "images", "ted.png")



import uuid
import streamlit as st
import requests
import json
from PIL import Image

import sys
import os
import torch

from sentence_transformers import __version__ as st_version

# Force CPU-only mode
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU
torch.set_num_threads(1)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

print("Forcing PyTorch to CPU mode with single-threading.")

print(f"Python Executable: {sys.executable}")
print(f"Torch Version: {torch.__version__}")
print(f"SentenceTransformers Version: {st_version}")
print(f"CUDA Available: {torch.cuda.is_available()}")

from app.llm.Summarizer_Agent import SummarizerAgent

# Append the absolute path of the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.llm.QAAgent import QAAgent


# Base URL for FastAPI backend
BASE_URL = "http://localhost:8000"

# Session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_token" not in st.session_state:
    st.session_state.user_token = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "login"  # Default page is login
if "selected_course" not in st.session_state:
    st.session_state.selected_course = None  # To store selected course

def api_request(endpoint, method="POST", data=None, token=None, content_type="json"):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    if content_type == "json":
        headers["Content-Type"] = "application/json"
    elif content_type == "form":
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    try:
        if method == "POST":
            if content_type == "json":
                response = requests.post(
                    f"{BASE_URL}{endpoint}",
                    json=data,  # Send JSON payload
                    headers=headers,
                )
            elif content_type == "form":
                response = requests.post(
                    f"{BASE_URL}{endpoint}",
                    data=data,  # Send form-urlencoded payload
                    headers=headers,
                )
        elif method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)

        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error: {e}")
        return None


def login_page():
    st.title("Login to TEDU SageAI 📚")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            # Payload for the login endpoint
            payload = {
                "username": email,
                "password": password,
                "grant_type": "password"
            }

            # Make the API request
            response = api_request(
                "/auth/jwt/login",
                method="POST",
                data=payload,
                content_type="form"  # Send as x-www-form-urlencoded
            )

            if response and "access_token" in response:
                st.session_state.authenticated = True
                st.session_state.user_token = response["access_token"]
                st.success("Login successful! Redirecting...")
                st.session_state.current_page = "dashboard"
            else:
                st.error("Login failed. Please check your credentials.")
    if st.button("Go to Registration"):
        st.session_state.current_page = "registration"

def display_guideline():
    """
    Function to display the registration guidelines.
    """
    st.markdown("""
        ## 📋 How to Obtain Your Security Key
        Follow these steps to get your **Security Key** from your LMS and use it in our application:

        1. **Click on your profile picture** located at the **top-right corner** of the LMS page.
        2. **Select Preferences** from the dropdown menu.
        3. Under Preferences, **click on "Security Keys"**.
        4. **Copy the first key** displayed in the Security Keys section.
        5. Paste the copied key into **our application**.
        6. **Done!** 🎉
    """)

def registration_page():
    st.title("Registration for TEDU SageAI 📋")
    with st.form("registration_form"):
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        registration_email = st.text_input("Email")
        registration_password = st.text_input("Password", type="password")
        lms_security_key = st.text_input("LMS Security Key", type="password")

        # Create two columns for registration and back buttons
        col1, col2 = st.columns(2)

        with col1:
            submit = st.form_submit_button("Register")

        # with col2:
        #     back_to_login = st.form_submit_button("Back to Login")

        if submit:
            if first_name and last_name and registration_email and registration_password and lms_security_key:
                # Prepare the JSON payload to match the expected structure
                user_id = str(uuid.uuid4())
                payload = {
                    "id":user_id,  # Leave it to be generated by the backend
                    "email": registration_email,
                    "is_active": True,  # Default to True
                    "is_superuser": False,  # Default to False
                    "is_verified": False,  # Default to False
                    "first_name": first_name,
                    "last_name": last_name,
                    "lms_security_key": lms_security_key,
                    "moodle_user_id": 0,
                    "password": registration_password,
                }

                response = api_request(
                    "/auth/register",
                    method="POST",
                    data=payload,
                )

                if response and response.get("success", False):
                    st.success("Registration successful! Redirecting to login page...")
                    st.session_state.current_page = "login"
                else:
                    st.error(f"Registration failed: {response.get('detail', 'Unknown error')}")
            else:
                st.error("Please fill out all fields.")



    # Enable guidelines after the registration form
    st.session_state.show_guidelines_registration = True

    # Show the guidelines if the toggle is enabled
    if st.session_state.show_guidelines_registration:
        st.markdown("---")  # Separator
        display_guideline()
    if st.button("Back to Login"):
        st.session_state.current_page = "login"


# Dashboard Page with Courses organized in two columns
def dashboard_page():
    st.title("Dashboard")
    st.write("Welcome to TEDU SageAI!")

    if st.session_state.user_token:
        # Fetch courses from the API
        response = api_request("/homepage", method="GET", token=st.session_state.user_token)
        if response:
            courses = response.get("courses", [])

            if courses:
                st.subheader("Courses List")

                # Split courses into two columns
                col1, col2 = st.columns(2)

                # Iterate over courses and alternate between columns
                for i, course in enumerate(courses):
                    # Display clickable course name
                    course_name = course["name"]
                    course_id = course["id"]

                    if i % 2 == 0:
                        with col1:
                            if st.button(course_name, key=f"course_{i}"):
                                st.session_state.selected_course = course_name
                                st.session_state.selected_course_id = course_id
                                st.session_state.current_page = "course_details"
                                st.session_state.trigger_rerun = True
                    else:
                        with col2:
                            if st.button(course_name, key=f"course_{i}"):
                                st.session_state.selected_course = course_name
                                st.session_state.selected_course_id = course_id
                                st.session_state.current_page = "course_details"
                                st.session_state.trigger_rerun = True

    # Rerun check
    if st.session_state.get("trigger_rerun", False):
        st.session_state.trigger_rerun = False
        st.rerun()

    # Logout Button
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user_token = None
        st.session_state.current_page = "login"



def question_answering_Agent(user_input):
    # Initialize QAAgent and perform chat
    agent = QAAgent(course_id=st.session_state.selected_course_id)
    response = agent.answer_query(user_input)

    return f"Q&A: {response}"


def summarizer_agent_chat(user_input):
    agent2 = SummarizerAgent(st.session_state.selected_course_id)
    response = agent2.summarize(user_input)

    return f"Summarizer Agent response to: {response}"

def practice_question_agent(user_input):
    agent3 = PracticeQuestionAgent(st.session_state.selected_course_id)
    response = agent3.generate_questions(user_input)

    return f"Practice Question Agent answer: {response}"

image_analyzer = ImageAnalyzer()

def course_details_page():
    st.title(f"📘 {st.session_state.selected_course} Page")
    st.write(f"Welcome to **{st.session_state.selected_course}** lecture!!! 🚀")
    # Add image to the top of the sidebar

    # Initialize selected agent in session state
    if "agent" not in st.session_state:
        st.session_state.agent = "Image Analyzer"
    if "qa_messages" not in st.session_state:
        st.session_state.qa_messages = []
    if "sum_messages" not in st.session_state:
        st.session_state.sum_messages = []
    if "pa_messages_messages" not in st.session_state:
        st.session_state.pa_messages_messages = []



    # Sidebar Navigation
    st.sidebar.title("Navigation")

    try:
        st.sidebar.image(image_path, use_container_width=True, caption="")
    except FileNotFoundError:
        st.sidebar.warning("Image not found in the images directory.")

    if st.sidebar.button("Image Analyzer", key="image_analyzer_button"):
        st.session_state.agent = "Image Analyzer"

    if st.sidebar.button("Question Answer Agent", key="qa_agent_button"):
        st.session_state.agent = "Question-Answer Agent"

    if st.sidebar.button("Summarizer Agent", key="summarizer_agent_button"):
        st.session_state.agent = "Summarizer Agent"

    if st.sidebar.button("Practice Question Agent", key="practice_agent_button"):
        st.session_state.agent = "Practice Question Agent"

    # Add some space before the Back to Dashboard button
    st.sidebar.markdown("---")
    st.sidebar.button("🔙 Back to Dashboard", on_click=lambda: setattr(st.session_state, 'current_page', 'dashboard'))

    # Display available resources
    if st.session_state.selected_course_id and st.session_state.user_token:
        response = api_request(
            f"/homepage/{st.session_state.selected_course_id}",
            method="GET",
            token=st.session_state.user_token
        )
        if response:
            st.sidebar.subheader("Available Resources:")
            resources = response.get("resources", [])
            for resource in resources:
                st.sidebar.markdown(f"- {resource['name']}")
        else:
            st.error("Failed to fetch course resources.")

    # Content Based on Selected Agent
    if st.session_state.agent == "Image Analyzer":
        st.header("🖼️ Image Analyzer")
        st.write("Upload an image and enter a prompt to analyze its content.")
        with st.container():
            col1, col2 = st.columns(2)

            # Column 1: Image upload
            with col1:
                uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

                if uploaded_file is None:
                    st.info("Please upload an image.")
                else:
                    # Read and display uploaded image
                    image = Image.open(uploaded_file)
                    image = image.resize((500, 600))  # Resize for better fit
                    st.image(image, caption="Uploaded Image", use_container_width=True)

            # Column 2: Prompt input and analysis
            with col2:
                st.subheader("Analyze the Uploaded Image")
                image_user_input = st.text_input("Enter your prompt...")

                if uploaded_file and image_user_input:
                    try:
                        # Open the uploaded image
                        image = Image.open(uploaded_file)

                        # Analyze the image using ImageAnalyzer
                        response = image_analyzer.analyze_image(image, image_user_input)
                        formatted_response = image_analyzer.format_response(response)

                        # Display analysis response
                        st.markdown("### Response:")
                        st.markdown(formatted_response, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error analyzing the image: {str(e)}")
                elif uploaded_file and not image_user_input:
                    st.warning("Please enter a prompt to analyze the image.")
                elif not uploaded_file:
                    st.info("Please upload an image to proceed.")

    elif st.session_state.agent == "Question-Answer Agent":
        st.header("🤖 Question Answer Agent")
        st.write("This is the Question-Answer chat interface.")

        # Display Bato chat history
        for message in st.session_state.qa_messages:
            if message["role"] == "user":
                st.chat_message("user").markdown(f"🧑‍💻 **You**: {message['content']}")
            else:
                st.chat_message("assistant").markdown(f"🤖 **QA Agent**: {message['content']}")


        # Chat input for Bato Agent
        qa_user_input = st.chat_input("Type your message for Question Answer Agent...")
        if qa_user_input:
            st.chat_message("user").markdown(f"🧑‍💻 **You**: {qa_user_input}")
            st.session_state.qa_messages.append({"role": "user", "content": qa_user_input})

            # Get response from QA Agent
            response = question_answering_Agent(qa_user_input)
            formatted_response = format_qa_response(response)
            st.chat_message("assistant").markdown(f"🧠 **Question-Answer Agent**:\n\n{formatted_response}")
            st.session_state.qa_messages.append({"role": "assistant", "content": formatted_response})

    elif st.session_state.agent == "Summarizer Agent":
        st.header("🤖 Summarizer Agent")
        st.write("This is the Summarizer Agent chat interface.")

        # Display Eymo chat history
        for message in st.session_state.sum_messages:
            if message["role"] == "user":
                st.chat_message("user").markdown(f"🧑‍💻 **You**: {message['content']}")
            else:
                st.chat_message("assistant").markdown(f"🤖 **Summarizer Agent**: {message['content']}")

        # Chat input for Eymo Agent
        sum_user_input = st.chat_input("Type your message for Summarizer Agent...")
        if sum_user_input:
            st.chat_message("user").markdown(f"🧑‍💻 **You**: {sum_user_input}")
            st.session_state.sum_messages.append({"role": "user", "content": sum_user_input})

            # Get response from Summarizer Agent
            response = summarizer_agent_chat(sum_user_input)
            formatted_summary = format_summary_response(response)
            st.chat_message("assistant").markdown(f"📑 **Summarizer Agent**:\n\n{formatted_summary}")
            st.session_state.sum_messages.append({"role": "assistant", "content": formatted_summary})

    elif st.session_state.agent == "Practice Question Agent":
        st.header("🤖 Practice Question Agent")
        st.write("This is the Practice Question Agent chat interface.")

        # Display PA chat history
        for message in st.session_state.pa_messages_messages:
            if message["role"] == "user":
                st.chat_message("user").markdown(f"🧑‍💻 **You**: {message['content']}")
            else:
                st.chat_message("assistant").markdown(f"🤖 **PA Agent**: {message['content']}")

        # Chat input for Practice Question Agent
        pa_user_input = st.chat_input("Type your message for Practice Question Agent...")
        if pa_user_input:
            st.chat_message("user").markdown(f"🧑‍💻 **You**: {pa_user_input}")
            st.session_state.pa_messages_messages.append({"role": "user", "content": pa_user_input})

            # Get response from PA Agent
            response = practice_question_agent(pa_user_input)
            formatted_response = format_pa_response(response)
            st.chat_message("assistant").markdown(f"🧠 **PA Agent**:\n\n{formatted_response}")
            st.session_state.pa_messages_messages.append({"role": "assistant", "content": formatted_response})




# Helper function to format Q&A response
def format_qa_response(response, max_line_length=80):
    """
    Formats the Q&A response for better readability.
    Long responses are split into vertical segments to prevent horizontal scrolling.

    Args:
        response (str): The raw response from the Q&A agent.
        max_line_length (int): Maximum number of characters per line.

    Returns:
        str: A formatted, vertical-friendly response.
    """
    try:
        # Split response into lines of max_line_length
        wrapped_response = textwrap.fill(response, width=max_line_length)

        # Replace line breaks with Streamlit markdown-friendly newlines
        vertical_response = wrapped_response.replace('\n', '  \n')

        # Final formatted response
        formatted = f"### \n\n{vertical_response}"

        return formatted

    except Exception as e:
        return f"⚠️ **Error formatting response**: {e}\n\n**Raw Response**:\n{response}"


#Helper function for PA (Formats the response)
def format_pa_response(response):
    """
    Formats the JSON response from the Practice Question Agent into a user-friendly display.
    Handles both 'generate questions' and 'evaluate answers' actions.

    Args:
        response (str): The raw response string returned by the LLM.

    Returns:
        str: A formatted string to display questions or feedback.
    """
    try:
        # Step 1: Strip any non-JSON content and isolate JSON
        start = response.find("{")
        end = response.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No valid JSON structure found.")

        # Extract and parse JSON content
        json_content = response[start:end + 1]
        parsed_response = json.loads(json_content)

        formatted_output = ""

        # Step 2: Detect and format "Generate Questions"
        if "multiple_choice" in parsed_response or "true_false" in parsed_response or "open_ended" in parsed_response:
            # Format Multiple-Choice Questions
            if "multiple_choice" in parsed_response and parsed_response["multiple_choice"]:
                formatted_output += "### 📝 Multiple-Choice Questions:\n"
                for idx, mcq in enumerate(parsed_response["multiple_choice"], 1):
                    question = mcq.get("question", "No question provided")
                    options = mcq.get("options", [])
                    formatted_output += f"{idx}. **{question}**\n"
                    for opt_idx, option in enumerate(options, 1):
                        formatted_output += f"   {chr(64 + opt_idx)}. {option}\n"
                    formatted_output += "\n"

            # Format True/False Questions
            if "true_false" in parsed_response and parsed_response["true_false"]:
                formatted_output += "### ✅ True/False Questions:\n"
                for idx, tf in enumerate(parsed_response["true_false"], 1):
                    question = tf.get("question", "No question provided")
                    formatted_output += f"{idx}. **{question}**\n"
                formatted_output += "\n"

            # Format Open-Ended Questions
            if "open_ended" in parsed_response and parsed_response["open_ended"]:
                formatted_output += "### 🌐 Open-Ended Questions:\n"
                for idx, oe in enumerate(parsed_response["open_ended"], 1):
                    question = oe.get("question", "No question provided")
                    formatted_output += f"{idx}. **{question}**\n"
                formatted_output += "\n"

        # Step 3: Detect and format "Evaluate Answers"
        elif "feedback" in parsed_response:
            formatted_output += "### 📝 Feedback on Your Answers:\n"
            for idx, fb in enumerate(parsed_response["feedback"], 1):
                question = fb.get("question", "No question provided")
                user_answer = fb.get("user_answer", "No answer provided")
                correct_answer = fb.get("correct_answer", "No correct answer provided")
                is_correct = "✅ Correct" if fb.get("is_correct") else "❌ Incorrect"
                feedback = fb.get("feedback", "")

                formatted_output += f"{idx}. **{question}**\n"
                formatted_output += f"   - **Your Answer**: {user_answer}\n"
                formatted_output += f"   - **Correct Answer**: {correct_answer}\n"
                formatted_output += f"   - **Result**: {is_correct}\n"
                formatted_output += f"   - **Feedback**: {feedback}\n\n"

        else:
            formatted_output += "⚠️ **Unknown response format.**"

        # Return the formatted output
        return formatted_output.strip()

    except json.JSONDecodeError as e:
        return f"⚠️ **JSON Parsing Error**: {e}\n\n**Raw Response**:\n{response}"
    except Exception as e:
        return f"⚠️ **Error**: {e}\n\n**Raw Response**:\n{response}"
#####################


    # Content Based on Selected Agent

def format_summary_response(response):
    """
    Parses and formats the JSON summary response for better display.
    Handles extra text and malformed JSON more robustly.
    """
    try:
        # Strip any non-JSON content and attempt to parse
        start = response.find("{")
        end = response.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No valid JSON structure found.")

        json_content = response[start:end + 1]
        summary = json.loads(json_content)  # Parse JSON

        formatted = ""

        # Overview Section
        formatted += "## 📌 Overview\n"
        overview_title = summary.get("overview", {}).get("title", "No title available")
        formatted += f"**Title:** {overview_title}\n\n"

        # Key Topics Section
        formatted += "## 🔑 Key Topics\n"
        key_topics = summary.get("key_topics", [])
        if key_topics:
            for topic in key_topics:
                topic_name = topic.get("topic", "No topic name")
                description = topic.get("description", "No description")
                formatted += f"- **{topic_name}**: {description}\n"
        else:
            formatted += "No key topics available.\n"

        # Detailed Summary Section
        formatted += "\n## 📋 Detailed Summary\n"
        detailed_summary = summary.get("detailed_summary", {}).get("sections", [])
        if detailed_summary:
            for section in detailed_summary:
                section_title = section.get("title", "No section title")
                formatted += f"### {section_title}\n"

                # Key Points
                formatted += "**Key Points:**\n"
                key_points = section.get("key_points", [])
                for point in key_points:
                    formatted += f"- {point}\n"

                # Examples
                formatted += "\n**Examples:**\n"
                examples = section.get("examples", [])
                for example in examples:
                    formatted += f"- {example}\n"
        else:
            formatted += "No detailed summary available.\n"

        # Key Terms Section
        formatted += "\n## 📚 Key Terms and Definitions\n"
        key_terms = summary.get("key_terms_and_definitions", [])
        if key_terms:
            for term in key_terms:
                term_name = term.get("term", "No term")
                definition = term.get("definition", "No definition")
                formatted += f"- **{term_name}**: {definition}\n"
        else:
            formatted += "No key terms available.\n"

        return formatted

    except json.JSONDecodeError as e:
        return f"⚠️ **JSON Parsing Error**: {e}\n\n**Raw Response**:\n{response}"
    except Exception as e:
        return f"⚠️ **Error**: {e}\n\n**Raw Response**:\n{response}"



# Main Application Logic
if st.session_state.current_page == "login":
    login_page()
elif st.session_state.current_page== "registration":
    registration_page()
elif st.session_state.current_page == "dashboard":
    dashboard_page()
elif st.session_state.current_page == "course_details":
    course_details_page()