# Modified from https://www.youtube.com/watch?v=4y1a4syMJHM
# Let's Build a ChatGPT Interview Bot
# by Travis Media

# To run a fastAPI server...
#   `uvicorn text-chat-bot:app --reload`
#   uvicorn is the server that runs the API
#   text-chat-bot is text-chat-bot.py
#   app is the instantiation (ie app = FastAPI())
#   --reload means that the app will automatically
#     reload when you make changes to it.

# Go to "localhost:8000" in your browser,
# to see the app running

# Go to "localhost:8000/docs" in your browser,
# to see the Swagger docs for the API

import os, json
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
# Next Whisper returns the text transcription of the speech.
# Finally get gpt's chat response to our speech.
@app.post("/talk")
async def post_audio(file: UploadFile):
    user_message = transcribe_audio(file)
    chat_response = get_chat_response(user_message)


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

    gpt_response_json = {
        "role": "assistant",
        "content": gpt_response.choices[0].message.content
    }

    # Save messages
    save_messages(user_message_json, gpt_response_json)

    return


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
