from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.llm.RAG import create_embedding_collection
from app.users import current_active_user
from app.database.db import User, get_async_session
from app.utils.lms_client import LMSClient
import os
import requests
from sqlalchemy.future import select
from app.database.db import Resource

# Router for homepage functionality
homepage_router = APIRouter(prefix="/homepage", tags=["homepage"])

@homepage_router.get("/")
async def get_enrolled_courses(user: User = Depends(current_active_user)):
    """
    Fetch all courses the logged-in user is enrolled in.
    """
    # Validate the user's LMS API key
    if not user.moodle_user_id or not user.lms_security_key:
        raise HTTPException(
            status_code=400,
            detail="Moodle user ID or LMS API key not available. Please update your profile."
        )

    # Create an instance of the LMS client
    lms_client = LMSClient(user.lms_security_key)

    # Fetch enrolled courses
    courses = lms_client.call_api("core_enrol_get_users_courses", {"userid": user.moodle_user_id})

    if not courses:
        raise HTTPException(
            status_code=404,
            detail="No courses found for this user."
        )

    # Format and return the response to Streamlit Frontend
    return {
        "user": f"{user.first_name} {user.last_name}",
        "courses": [{"id": course["id"], "name": course["fullname"]} for course in courses]
    }


@homepage_router.get("/{course_id}")
async def get_course_homepage(course_id: int, user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)):
    """
    Return a welcome statement and available resources for the specified course.
    """
    if not user.lms_security_key:
        raise HTTPException(status_code=400, detail="LMS API key is required.")

    # Initialize LMS client
    lms_client = LMSClient(user.lms_security_key)

    try:
        # Fetch course content from LMS
        course_content = lms_client.call_api("core_course_get_contents", {"courseid": course_id})
        if not course_content:
            raise HTTPException(status_code=404, detail="No content found for this course.")

        # Extract resources from the course content
        resources = extract_resources_from_course(course_content)

        # Process resources: download, check/update metadata and embed into CromaDB
        new_resources = await process_resources(course_id, resources, db, user.lms_security_key)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching resources: {str(e)}")



    if not user.lms_security_key:
        raise HTTPException(
            status_code=400, detail="LMS API key is required to fetch course data."
        )

    try:
        # Initialize LMS Client
        lms_client = LMSClient(user.lms_security_key)

        # Fetch course name and resources
        course_contents = lms_client.call_api(
            "core_course_get_contents", {"courseid": course_id}
        )
        if not course_contents:
            raise HTTPException(
                status_code=404, detail="No course content found for the given course ID."
            )

        # Extract resources
        resources = []
        for section in course_contents:
            for module in section.get("modules", []):
                for content in module.get("contents", []):
                    if "fileurl" in content:
                        resources.append(
                            {
                                "name": content.get("filename")
                            }
                        )

        return {
            "welcome_message": f"Welcome to the homepage for Course {course_id}!",
            "resources": resources,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching course data: {str(e)}")


def extract_resources_from_course(course_content: list) -> list:
    """
    Extract resources from the course content fetched from the LMS.

    Args:
        course_content (list): Raw course content fetched from LMS.

    Returns:
        list: A list of extracted resources.
    """
    resources = []
    for section in course_content:
        for module in section.get("modules", []):
            for resource in module.get("contents", []):
                if "fileurl" in resource:
                    resources.append({
                        "filename": resource.get("filename"),
                        "fileurl": resource.get("fileurl"),
                        "mimetype": resource.get("mimetype"),
                        "time_modified": resource.get("timemodified"),
                    })
    return resources


async def process_resources(course_id: int, resources: list, db: AsyncSession, lms_security_key: str) -> list:
    """
    Process resources: download, update metadata in DB, and embed new PDFs.

    Args:
        course_id (int): ID of the course.
        resources (list): List of resources to process.
        db (AsyncSession): Database session.
        lms_security_key (str): LMS API key for authentication.

    Returns:
        list: List of new or updated resources.
    """
    resource_dir = f"./resources/{course_id}"
    os.makedirs(resource_dir, exist_ok=True)

    new_resources = []  # Track new resources for embedding

    for resource in resources:
        file_path = os.path.join(resource_dir, resource["filename"])

        # Check if resource exists in the database
        existing_resource = await db.execute(
            select(Resource).filter_by(course_id=course_id, filename=resource["filename"])
        )
        existing_resource = existing_resource.scalar_one_or_none()

        # Download and process only if new or updated
        if not existing_resource or resource["time_modified"] > existing_resource.time_modified:
            # Download the resource
            response = requests.get(resource["fileurl"], params={"token": lms_security_key})
            response.raise_for_status()
            with open(file_path, "wb") as f:
                f.write(response.content)

            # Update the database
            if existing_resource:
                existing_resource.time_modified = resource["time_modified"]
                existing_resource.file_path = file_path
            else:
                new_resource = Resource(
                    course_id=course_id,
                    filename=resource["filename"],
                    fileurl=resource["fileurl"],
                    mimetype=resource["mimetype"],
                    time_modified=resource["time_modified"],
                    file_path=file_path,
                )
                db.add(new_resource)

            await db.commit()
            new_resources.append(file_path)

    # Embed newly downloaded PDFs**
    if new_resources:
        create_embedding_collection(
            input_files=new_resources,
            collection_name=f"{course_id}_Collection",
        )
        print(f"Embeddings created for {len(new_resources)} new resources.")

    return [os.path.basename(path) for path in new_resources]


def download_resource(resource: dict, lms_security_key: str, course_id: int) -> str:
    """
    Download a resource from LMS and save it locally in a folder organized by course.

    Args:
        resource (dict): Metadata of the resource to download.
        lms_security_key (str): LMS API key for authentication.
        course_id (int): The ID of the course the resource belongs to.

    Returns:
        str: The local file path where the resource is saved.
    """
    RESOURCE_BASE_PATH = "./resources"
    # Create a folder for the course
    course_folder = os.path.join(RESOURCE_BASE_PATH, str(course_id))
    os.makedirs(course_folder, exist_ok=True)

    # Define the full file path inside the course folder
    file_path = os.path.join(course_folder, resource["filename"])

    # Download the resource
    response = requests.get(resource["fileurl"], params={"token": lms_security_key})
    response.raise_for_status()  # Raise an error if the request fails

    # Save the resource to the file
    with open(file_path, "wb") as f:
        f.write(response.content)

    return file_path