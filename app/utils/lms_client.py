import requests
from fastapi import HTTPException, status

MOODLE_URL = "https://lms.tedu.edu.tr"
MOODLE_API_ENDPOINT = f"{MOODLE_URL}/webservice/rest/server.php"

class LMSClient:
    """
    A client to handle interactions with the LMS (Moodle) API.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_endpoint = MOODLE_API_ENDPOINT

    def call_api(self, wsfunction: str, params: dict = None):
        """
        Makes a generic API request to the LMS.

        Args:
            wsfunction (str): The Moodle API function to call.
            params (dict): Additional parameters for the request.

        Returns:
            dict: The JSON response from the LMS API.
        """
        if params is None:
            params = {}
        params.update({
            "wstoken": self.api_key,
            "wsfunction": wsfunction,
            "moodlewsrestformat": "json"
        })

        try:
            response = requests.get(self.api_endpoint, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses
            data = response.json()
            if "exception" in data:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Moodle API Exception: {data.get('message', 'Unknown error')}"
                )
            return data
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error communicating with Moodle API: {e}"
            )
