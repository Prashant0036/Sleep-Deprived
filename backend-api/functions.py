import os
import google.generativeai as genai
from fastapi import FastAPI, UploadFile, File
from starlette.responses import FileResponse, RedirectResponse, JSONResponse
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
import cv2
from PIL import Image, ImageDraw, ImageFont  # For image processing
import numpy as np  # For handling image arrays
from moviepy import VideoFileClip, concatenate_videoclips, AudioFileClip
import re
from main import client, model, text_model  # For video processing


def generate_image(prompt):
    """Generates a single image from a given prompt and returns the image."""
    try:
        images = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            language="en",
            add_watermark=False,
            seed=400,
            aspect_ratio="16:9",
            safety_filter_level="block_some"
        )

        # Handle empty response
        if not images:
            print(f"Warning: No image generated for prompt: {prompt}")
            return None

        return images[0]  # Return the generated image

    except Exception as e:
        print(f"Error generating image for prompt '{prompt}': {e}")
        return None


def generate_audio(prompt, i):
    """Generates audio from text and saves it to an MP3 file."""
    synthesis_input = texttospeech.SynthesisInput(text=prompt)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    file_path = f"Audio/output{i}.mp3"
    with open(file_path, "wb") as out:
        out.write(response.audio_content)

    return file_path


def generate_content(topic):
    """Generates text content from a given topic."""
    prompt_for_content_generation = f"""Give me a 15 to 16 short line para without any preamble on a topic,
    Actually I want to generate a video script from this topic so that anyone can understand it easily so the line should be inter connecting to each other.
    Keep the lines easy such a way that an image can be generated from those lines. Topic is : {topic}"""
    Content_response = text_model.generate_content(
        prompt_for_content_generation
    )

    # Extract the generated text from response
    if Content_response and Content_response.candidates:
        content = Content_response.candidates[0].content.parts[0].text
    else:
        raise ValueError("Failed to generate content for the topic.")

    content = content.replace("\n", " ")
    fullStop_separated_list = content.split(".")

    return fullStop_separated_list

def generate_image_prompts(fullStop_separated_list):
    """Generates descriptive prompts for image generation from lines of text."""
    prompt_dict = {}

    for line in fullStop_separated_list:
        time.sleep(10)
        response = text_model.generate_content(
            "Generate a easy and simple descriptive para from this line, that para should be good enough to generate an image : " + line
        )
        # Extract text from response
        if response and hasattr(response, "text"):
            prompt = response.text
        else:
            raise ValueError("Failed to generate image prompt.")

        prompt_dict[line] = prompt

    return prompt_dict

def generate_images_and_audio(prompt_dict):
    """Generates images and audio using a dictionary of prompts."""
    audio_list = []
    image_list = []
    index_for_which_image_doesnt_get_generated = []
    i = 0
    for line, prompt in prompt_dict.items():
        # Generate audio from line
        audio = generate_audio(line, i)
        audio_list.append(audio)

        # Generate image from prompt
        image = generate_image(prompt)
        if image:
            image_list.append(image)
        else:
            index_for_which_image_doesnt_get_generated.append(i)

        i += 1

    print(f"Generated {len(image_list)} images successfully.")

    return image_list, audio_list, index_for_which_image_doesnt_get_generated

def remove_indices(lst, indices_to_ignore):
    """Removes items from a list based on given indices."""
    return [item for i, item in enumerate(lst) if i not in indices_to_ignore]

def save_generated_images(image_objects, save_dir):
    """Saves generated Vertex AI images to disk and returns file paths."""
    # if not os.path.exists(save_dir):
    #     os.makedirs(save_dir)  # Create directory if it doesn't exist

    image_paths = []
    for i, img_obj in enumerate(image_objects):
        img_path = f"{save_dir}/image_{i}.png"
        img_obj.save(img_path)  # Save the image
        image_paths.append(img_path)

    return image_paths

def add_text_to_image(image_path, text, font_size=30):
    """Adds text to an image using PIL and returns the modified image."""
    # Load image
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    # Try loading a default font
    try:
        font = ImageFont.truetype("arial.ttf", font_size)  # Works if Arial is available
    except IOError:
        font = ImageFont.load_default()  # Fallback font

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Calculate position (centered at bottom)
    img_width, img_height = img.size
    x = (img_width - text_width) // 2
    y = img_height - text_height - 80  # Adjusted spacing from bottom

    # Add text to image
    draw.text((x, y), text, font=font, fill="white")

    return img

def create_video_from_images_audios_captions(
    image_paths, audio_paths, captions, output_path, fps=24
):
    """Creates a video from images, audio, and captions."""
    if (
        len(image_paths) != len(audio_paths)
        or len(image_paths) != len(captions)
    ):
        raise ValueError(
            "Number of images, audio files, and captions must be the same."
        )

    video_clips = []

    for img_path, aud_path, caption in zip(
        image_paths, audio_paths, captions
    ):
        # Generate image with text
        modified_img = add_text_to_image(img_path, caption)

        # Convert PIL Image to OpenCV format (numpy array)
        frame = np.array(modified_img)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Get audio duration
        audio = AudioFileClip(aud_path)
        duration = audio.duration

        # Save the modified image as a temporary video frame
        temp_video_path = f"{img_path}.mp4"
        height, width, _ = frame.shape
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # Codec for MP4
        out = cv2.VideoWriter(
            temp_video_path, fourcc, fps, (width, height)
        )

        # Create video frames for the duration of the audio
        for _ in range(int(fps * duration)):
            out.write(frame)

        out.release()

        # Load video and add audio
        clip = VideoFileClip(temp_video_path).with_audio(audio)

        video_clips.append(clip)

    # Concatenate all video clips
    final_video = concatenate_videoclips(video_clips, method="compose")

    # Write final video file
    final_video.write_videofile(
        output_path, fps=fps, codec="libx264", audio_codec="aac"
    )

    print(f"Video saved successfully at {output_path}")



def sanitize_filename(name):
    """Remove invalid characters from filenames."""
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()

def get_sub_top_desc(input_text):
    prompt_for_sub_topic = f"""
    Analyze the given user input: '{input_text}' and classify it into:
    1. A specific **subject** that directly represents the domain of the topic, the subject should be the most generalized form eg. Machine Learning is not generalized but Computer Science is so we will use Computer Science for topics of Machine Learning aswell.
    2. A **topic name** that best represents the core idea of the input in a concise and standardized form.
    3. A **short 1-2 line description** explaining the video topic clearly like : Python Basics from creating variables to Object Oriented Programming or Getting Started with Data Science and Machine Learning, something short like these.

    Ensure:
    - The subject is the **most relevant** high-level category (e.g., 'Computer Science' for 'Support Vector Machine').
    - The topic name is a **refined version** of the input (e.g., 'Working of Support Vector Machine' for 'How Support Vector Machine Works').
    - The response is strictly formatted as: **Subject - Topic - Short Description**
    - Do not add any extra text or explanations beyond this format.
    """

    Returned_Content_response = text_model.generate_content(prompt_for_sub_topic)

    if Returned_Content_response and Returned_Content_response.candidates:
        content_response = Returned_Content_response.candidates[0].content.parts[0].text.strip()
    else:
        raise ValueError("Failed to generate content for the topic.")

    parts = [part.strip() for part in content_response.split(" - ")]

    if len(parts) != 3:
        raise ValueError(f"Unexpected response format: {content_response}")

    sub, topic, desc = map(sanitize_filename, parts)  # Sanitize all names

    return sub, topic, desc




