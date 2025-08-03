import os
import google.generativeai as genai 
from fastapi import FastAPI, UploadFile, File
from starlette.responses import FileResponse, RedirectResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from dotenv import load_dotenv
import uvicorn
from google.cloud import texttospeech
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from PIL import Image
import io
from moviepy import *
import time
from functions import *
from fastapi.staticfiles import StaticFiles
# from google.cloud import storage

load_dotenv(dotenv_path='.env')

request_lock = asyncio.Lock()

# Configure Google Gemini API
genai.configure(api_key=os.getenv('API_KEY'))

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account.json"

# Initialize Vertex AI
vertexai.init(project="helpful-cipher-453421-c1", location="us-central1")

# output_file = "/Images/"

# Define Text Model
text_model = genai.GenerativeModel("gemini-2.0-flash-001")

# Define Image Model
model = ImageGenerationModel.from_pretrained("imagen-3.0-fast-generate-001")

# Define TTS Client
client = texttospeech.TextToSpeechClient()

# OUTPUT_BUCKET_NAME = os.getenv('BUCKET_NAME')

# Initialize Google Cloud Storage client
# storage_client = storage.Client()

# def upload_to_gcs(local_file_path, gcs_file_path):
#     bucket = storage_client.bucket(OUTPUT_BUCKET_NAME)
#     blob = bucket.blob(gcs_file_path)
#     blob.upload_from_filename(local_file_path)
#     print(f"File {local_file_path} uploaded to {gcs_file_path}.")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_index():
    with open("a1.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)


# def clear_cache_folders():
    # Clear cache folders in Bucket
        

def delete_all_files_in_directory(directory):
    """Deletes all files in a given directory."""
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print(f"All files in '{directory}' have been deleted.")
    except FileNotFoundError:
        print(f"Directory '{directory}' not found.")
    except Exception as e:
        print(f"An error occurred while deleting files in '{directory}': {e}")


def generate_video_content(subject,topic):
    
    content_lines = generate_content(topic)
    prompt_dict = generate_image_prompts(content_lines)
    image_list, audio_list, invalid_indices = generate_images_and_audio(
        prompt_dict
    )

    # Remove items corresponding to invalid indices
    new_audio_list = remove_indices(audio_list, invalid_indices)
    new_captions_list = remove_indices(content_lines, invalid_indices)

    # img_dir = os.makedirs(f"Images/{subject}/{topic}")
    img_dir = os.path.join("Images", subject.strip(), topic.strip())
    os.makedirs(img_dir, exist_ok=True)

    saved_images = save_generated_images(image_list,img_dir)
     
    video_dir = os.path.join("Videos", subject.strip(), topic.strip())  # Directory path
    os.makedirs(video_dir, exist_ok=True)  # Ensure the directory exists

    video_path = os.path.join(video_dir, f"{topic.strip()}_output.mp4")  # Full file path

    create_video_from_images_audios_captions(
        saved_images, new_audio_list, new_captions_list, video_path
    )

    # generate thumbnail for video 
    thumbnail_dir = os.path.join("Thumbnails", subject.strip(), topic.strip())
    os.makedirs(thumbnail_dir, exist_ok=True)
    
    thumbnail_filename = "thumbnail.png"
    thumbnail_filepath = os.path.join(thumbnail_dir, thumbnail_filename)
    prompt = f" generate a thumbnail for the topic {topic} with a large {topic} written in the center of the image, the image's background must convey the idea of the topic or blank"

    try:
        image = generate_image(prompt)
        if image is not None:  # Check if generate_image returned a valid image
            directory = os.path.dirname(filepath)
            if not os.path.exists(directory):
                os.makedirs(directory)
            image.save(thumbnail_filepath)
            print("Thumbnail generated and saved successfully!")
        else:
            print(f"Error: generate_image() returned None for prompt: '{prompt}'")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    #Delete files in Audio and Images
    delete_all_files_in_directory("Audio")
    delete_all_files_in_directory("Images")


    return thumbnail_filepath,video_path
    



       
#         # # Define output file paths
#         # OUTPUT_FOLDER = f"gs://{OUTPUT_BUCKET_NAME}/videos/{SUBJECT}/{TOPIC_NAME}"
        



from pydantic import BaseModel
class SearchRequest(BaseModel):
    input_text: str  
import json


@app.post("/search/")
async def search_topic(request: SearchRequest):
    global request_lock
    if request_lock.locked():
        return JSONResponse({"message": "🔄 You are in queue, another request is being processed. Please wait..."}, status_code=429)
    
    async with request_lock:
        print("🚀 Processing request... Other requests will wait!")

        try:
            print("Extracting subject, topic, and description...")
            sub, topic, desc = get_sub_top_desc(request.input_text)
            
            print("Generating video content...")
            thumbnail, video_path = generate_video_content(sub, topic)

            # Prepare data to save
            data = {
                "subject": sub,
                "topic": topic,
                "description": desc,
                "thumbnail": thumbnail,
                "videoPath": video_path
            }
            print(sub," ",topic," ",desc," ",thumbnail," ",video_path)
            return JSONResponse(data)

        except Exception as e:
            print("❌ Error:", str(e))
            return JSONResponse({"error": str(e)}, status_code=500)
        
app.mount("/Thumbnails", StaticFiles(directory="Thumbnails"), name="thumbnails")
app.mount("/Videos", StaticFiles(directory="Videos"), name="videos")
@app.get("/health_check/")
async def health():
    return JSONResponse({"status_code": "This is working"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) # For running on local machine
