# GPT-4-image-labeller
IMPORTANT: OpenAI limits use of GPT-4 Vision to 100 requests a day, so this will be unusable for large directories of images.
If there's any interest in this I'll develop it more but until this this is just an exercise.

Labels images on your computer with the GPT-4 Vision api and sorts them into a destination folder

## Usage

1. Run pip3 install requirements.txt
2. In main.py, change SOURCE_DIRECTORY to the root source directory for your images, and DESTINATION_DIRECTORY to where you want to save them to.
3. run python3 main.py. Will run label_and_move_images()

By default it doesn't delete original images. Currently implements some exponential backoff to avoid rate limits though not perfect yet
Some todos:

1. Implmenet pagination params for doing only portions of the images at once
2. Add additional instructions param for the prompt
3. add exclude_dirs array as a param for directory paths to exclude
