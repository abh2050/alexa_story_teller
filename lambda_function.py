import logging
import os
import requests

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ensure your Deepseek API key is set as an environment variable (DEEPSEEK_API_KEY)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

def generate_story(prompt, max_tokens):
    """Generate a story using the Deepseek API."""
    url = "https://api.deepseek.ai/v1/generate"  # Replace with the actual Deepseek endpoint
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": 0.95,
        # Include any additional parameters required by Deepseek here.
        # For example, if Deepseek requires a model name:
        # "model": "deepseek-story-generator"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        logger.error(f"Deepseek API error: {response.text}")
        raise Exception("Deepseek API error: " + response.text)
    # Assume the response JSON contains the generated text under the key 'generated_text'
    story_text = response.json().get("generated_text")
    return story_text

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speech_text = (
            "Welcome to Magic Storyland. "
            "You can ask me to tell you a story. For example, say, 'Tell me a story about a monkey on an adventure.'"
        )
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

class StoryIntentHandler(AbstractRequestHandler):
    """Handler for Story Intent."""
    def can_handle(self, handler_input):
        return is_intent_name("StoryIntent")(handler_input)

    def handle(self, handler_input):
        # Extract slot values (using default values if slots are missing)
        slots = handler_input.request_envelope.request.intent.slots
        subject = slots.get("subject").value if slots.get("subject") and slots.get("subject").value else "monkey"
        theme = slots.get("theme").value if slots.get("theme") and slots.get("theme").value else "adventure"
        activity = slots.get("activity").value if slots.get("activity") and slots.get("activity").value else "in a magical forest"
        additional_elements = (
            slots.get("additionalElements").value
            if slots.get("additionalElements") and slots.get("additionalElements").value
            else "cookies, rain, and a mysterious treasure"
        )
        
        # Define a fixed approximate word count for simplicity
        word_count = 300  
        max_tokens = int(word_count / 0.75)  # Estimate conversion from words to tokens

        # Build the prompt
        mega_prompt = (
            f"Write a creative and engaging story for children with the following details: "
            f"Main Subject: {subject}. Theme: {theme}. Setting/Activity: {activity}. "
            f"Additional Elements: {additional_elements}. "
            f"The story should be approximately {word_count} words long, have a clear beginning, middle, and end, "
            f"and include a moral related to {theme}."
        )
        
        logger.info("Generated prompt: " + mega_prompt)

        try:
            story = generate_story(mega_prompt, max_tokens)
        except Exception as e:
            logger.error("Error generating story: " + str(e))
            story = "I'm sorry, I encountered an error while generating your story. Please try again later."
        
        # Wrap the story in SSML for better voice rendering (optional)
        speech_output = f"<speak>{story}</speak>"
        return handler_input.response_builder.speak(speech_output).set_should_end_session(True).response

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speech_text = "You can ask me to tell you a story. For example, say, 'Tell me a story about a robot in space.'"
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Handler for Cancel and Stop Intents."""
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or 
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speech_text = "Goodbye!"
        return handler_input.response_builder.speak(speech_text).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # Any cleanup logic goes here.
        return handler_input.response_builder.response

# Build the skill
sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(StoryIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

lambda_handler = sb.lambda_handler()
