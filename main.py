import os
import glob
from openai import OpenAI
import requests
import base64
import aiohttp
import random
import asyncio
import shutil

IMAGE_LABEL_PROMPT = """
                Classify each image. 
                Delimit labels for the classification with _
                The first label should be one of the following primary labels
                Primary labels: ["Screenshot", "Photograph", "Meme", "Graphic", "Document", "Art", "Misc"]
                The second label should be the main label for what the image contains, 1-3 words
                For screenshots, the second label should be the program being used in the screenshot. The third label should describe what the program is doing or the general purpose of the program. Be as specific as possible so there is no ambiguity as to what being described
                For photographs the second label should be the setting of the photograph, and the third should be the subejct/additional details about it
                For graphics, the second label should be the main text in the graphic or a short name for it to describe its purpose, and the third label should be additional details
                In general the third label should cover the general idea or purpose of the image as descriptively as possible. If there is large text in the image, use that as part of the labelling if it is significant to the main purpose of the image
                Example label:
                Screenshot_Visual Studio Code_Python image classification program
                """


def find_images(directory):
    extensions = ['png', 'jpg', 'jpeg', 'gif', 'webp']
    files = []
    for ext in extensions:
        files.extend(glob.glob(f"{directory}/**/*.{ext}", recursive=True))
    return files


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


async def label_image_async(session, image_path, openai_api_key, max_retries=5, initial_delay=1.0):

    base64_image = encode_image(image_path)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
        {
            "role": "user",
            "content": [
            {
                "type": "text",
                "text": IMAGE_LABEL_PROMPT,
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "low",
                }
            }
            ]
        }
        ],
        "max_tokens": 400,
    }

    # Use GPT-4 Turbo to label the image

    delay = initial_delay

    for attempt in range(max_retries):
        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data["choices"][0]["message"]["content"]
            elif response.status == 429:
                print("Rate limit error: backing off and retrying")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay + random.uniform(0, 1))
                    delay *= 2
                else:
                    return f"Error: {response.status}"

async def get_labels(image_files):
    labels = []
    async with aiohttp.ClientSession() as session:
        tasks = [label_image_async(session, image_file, openai_api_key) for image_file in image_files]
        labels = await asyncio.gather(*tasks)
    return labels


def label_and_move_images(src_path, dst_path, ask_to_proceed=True, debug_output=False, keep_originals=False):
    print(f"Searcing for images in {src_path}")
    extensions = ['png', 'jpg', 'jpeg', 'gif', 'webp']
    image_files = []
    for ext in extensions:
        image_files.extend(glob.glob(f"{src_path}/**/*.{ext}", recursive=True))

    if debug_output:
        for file in image_files:
            print(f"Found file: {file}")
    
    num_images = len(image_files)

    num_input_tokens = num_images * 350 # 265 text input + 85 image input
    num_output_tokens = num_images * 10
    openai_price = num_input_tokens*0.00001 + num_output_tokens*0.00003
    print(f"Calculated cost: ${openai_price}")

    if ask_to_proceed:
        proceed = input(f"Found {num_images} images. Proceed with classification? (y/n) ") 
        if proceed[0] != 'y':
            return

    print("Labelling image files. This may take a while.")

    labels = asyncio.run(get_labels(image_files))

    print(f"Retrieved labels from OpenAI. Moving to {dst_path}")

    for image, label in zip(image_files, labels):
        folder_name = label.split("_")[0]
        folder_path = os.path.join(dst_path, folder_name + "s")
        os.makedirs(folder_path, exist_ok=True)
        if keep_originals:
            shutil.copy(image, os.path.join(folder_path, label[len(folder_name)+1:]) + "." + image.split(".")[-1])
        else:
            shutil.move(image, os.path.join(folder_path, label[len(folder_name)+1:]) + "." + image.split(".")[-1])


client = OpenAI(
  api_key=os.environ.get("OPENAI_API_KEY"),
)

HOME = os.path.expanduser('~') # Home path
SOURCE_DIRECTORY = "Source directory path"
DESTINATION_DIRECTORY = "Destination directory path"

label_and_move_images(
    SOURCE_DIRECTORY,
    DESTINATION_DIRECTORY,
    ask_to_proceed = True, # Ask user before requesting labels from OpenAI
    debug_output = True, # Print the path of every image it finds
    keep_originals = True # If true, copy images from src to dest, if false, cut
)


# TODO implement params:
    # pagination = 0,
    # additional_instructions = "",
    # exclude_dirs = [],
