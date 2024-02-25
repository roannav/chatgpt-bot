# Modified from https://www.youtube.com/watch?v=4y1a4syMJHM
# Let's Build a ChatGPT Interview Bot
# by Travis Media

# To run a fastAPI server...
#   `uvicorn voice-chat-bot:app --reload`
#   uvicorn is the server that runs the API
#   voice-chat-bot is voice-chat-bot.py
#   app is the instantiation (ie app = FastAPI())
#   --reload means that the app will automatically
#     reload when you make changes to it.

# Go to "localhost:8000" in your browser,
# to see the app running

# Go to "localhost:8000/docs" in your browser,
# to see the Swagger docs for the API

import os, json, requests
from openai import OpenAI
from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()
elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
print(elevenlabs_key)

print(os.environ.get("ELEVENLABS_API_KEY"))
print(os.environ.get("OPENAI_API_KEY"))
client = OpenAI()
# defaults to getting the key using os.environ.get("OPENAI_API_KEY")
# if you saved the key under a different environment variable name, you can do something like:
# client = OpenAI(
#   api_key=os.environ.get("CUSTOM_ENV_NAME"),
# )

app = FastAPI()


# set up a route, to send an audio speech file to OpenAI.
# Next Whisper returns the text transcription of the speech.
# Finally get gpt's chat response to our speech.
@app.post("/talk")
async def post_audio(file: UploadFile):
    user_message = transcribe_audio(file)
    chat_response = get_chat_response(user_message)
    audio_output = text_to_speech(chat_response)

    def iterfile():
        yield audio_output

    return StreamingResponse(iterfile(), media_type="audio/mpeg")


# RETURN: the transcription as a text string
def transcribe_audio(file):
    # convert speech to text with OpenAI's Whisper model
    audio_file = open("audio/" + file.filename, "rb")
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)

    # sample user prompt (for testing)
    # transcript = {"role": "user", "content": "Who won the world series in 2020?"}

    print(transcript)
    # Example:
    # Transcription(text='Why do they call it rush hour when nothing moves?')

    return transcript.text


# IN: user_message: text
#       eg. "Who won the world series in 2020?"
def get_chat_response(user_message):
    messages = load_messages()  # from the database

    user_message_json = {"role": "user", "content": user_message}
    messages.append({"role": "user", "content": user_message})

    # sample response (for testing)
    # gpt_response = {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."}

    # Send to OpenAI
    gpt_response = client.chat.completions.create(
        model="gpt-3.5-turbo", messages=messages
    )

    print(gpt_response)
    # Example:
    """
    ChatCompletion(
        id="chatcmpl-8vxJoTcJcR8ghb20GGG3uuQGIRqOY",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                logprobs=None,
                message=ChatCompletionMessage(
                    content="Ha, good one! Can you tell me about a project where you had to work with APIs in React?",
                    role="assistant",
                    function_call=None,
                    tool_calls=None,
                ),
            )
        ],
        created=1708823408,
        model="gpt-3.5-turbo-0125",
        object="chat.completion",
        system_fingerprint="fp_86156a94a0",
        usage=CompletionUsage(completion_tokens=22, prompt_tokens=72, total_tokens=94),
    )
    """

    print(gpt_response.choices[0].message)
    # Example
    """
    ChatCompletionMessage(
        content="Ha, good one! Can you tell me about a project where you had to work with APIs in React?",
        role="assistant",
        function_call=None,
        tool_calls=None,
    )
    """

    message_text = gpt_response.choices[0].message.content

    gpt_response_json = {"role": "assistant", "content": message_text}

    # Save messages
    save_messages(user_message_json, gpt_response_json)

    return message_text


def load_messages():  # from the database
    messages = []
    file = "database.json"

    # is file empty?
    empty = os.stat(file).st_size == 0

    # if file is not empty, loop through history (as saved in the file)
    # and add them to messages
    if not empty:
        with open(file) as db_file:
            data = json.load(db_file)
            for item in data:
                messages.append(item)
    else:
        # if file is empty, add the context
        messages.append(
            # {"role": "system", "content": "You are a helpful assistant."}
            {
                "role": "system",
                "content": "You are interviewing the user for a "
                + "front-end React developer position.  Ask short questions that "
                + "are relevant to a junior level developer.  Your name is Greg.  "
                + "The user is Marie.  Keep responses under 30 words and be "
                + "funny sometimes.",
            }
        )
    return messages


def save_messages(user_message, gpt_response):
    file = "database.json"
    messages = load_messages()
    messages.append(user_message)
    messages.append(gpt_response)

    with open(file, "w") as f:
        json.dump(messages, f)


def text_to_speech(text):

    voice_id = "pqHfZKP75CvOlQylNhV4"  # Bill

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    payload = {"text": text, "model_id": "eleven_multilingual_v2"}

    headers = {
        "xi-api-key": elevenlabs_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            print("ERROR: text_to_speech() POST failed.")
            print(f"ERROR: status_code is {response.status_code}")
    except Exception as e:
        print(e)


# Use FastAPI.  Set up a route and send audio to it.
# Use Uvicorn, which is the server that will run the API.

# 1 Send audio.  Transcribe it.

# 2 Send txt to ChatGPT.  Get a response.

# 3 Save the chat history to send back and forth for context.

# gpt-3.5-turbo doesn't have a memory.
# For every prompt, you have to send the history of the chat
# for it to remember what was said prior.
# So let's create a database to store the chat history.

# Who do you want this bot to be?
# roles: "system", "user", or "assistant"
