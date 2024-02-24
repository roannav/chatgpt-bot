# To run a fastAPI server...
#   `uvicorn whisper:app --reload`
#   uvicorn is the server that runs the API
#   whisper is whisper.py
#   app is the instantiation (ie app = FastAPI())
#   --reload means that the app will automatically
#     reload when you make changes to it.

# Go to "localhost:8000" in your browser,
# to see the app running

# Go to "localhost:8000/docs" in your browser,
# to see the Swagger docs for the API 

# Use Postman to test sending the request:
# POST http://localhost:8000/talk

import os
from openai import OpenAI

from fastapi import FastAPI, UploadFile

print(os.environ.get("OPENAI_API_KEY"))
client = OpenAI()
# defaults to getting the key using os.environ.get("OPENAI_API_KEY")
# if you saved the key under a different environment variable name, you can do something like:
# client = OpenAI(
#   api_key=os.environ.get("CUSTOM_ENV_NAME"),
# )

app = FastAPI()

# set up a route, to send an audio speech file to OpenAI.
# Then Whisper returns the text transcription of the speech.
@app.post("/talk")
async def post_audio(file: UploadFile):
    # convert speech to text with OpenAI's Whisper model
    audio_file= open("audio/" + file.filename, "rb")
    transcript = client.audio.transcriptions.create(
      model="whisper-1", 
      file=audio_file
    )   
    print(transcript)
    return {"message": "Speech to text complete."}

