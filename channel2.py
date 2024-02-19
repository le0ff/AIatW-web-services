## channel2.py - a simple Eliza bot talking about the Mensa 
##

from flask import Flask, request, render_template, jsonify
import json
import requests
import datetime
import random

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db

HUB_URL = 'http://localhost:5555'
HUB_AUTHKEY = '1234567890'
CHANNEL_AUTHKEY = '22334455'
CHANNEL_NAME = "Eliza's Mensa"
CHANNEL_IMG = "https://static.boredpanda.com/blog/wp-content/uploads/2016/02/20-Photos-that-show-India-like-youve-never-seen-before35__880.jpg"
CHANNEL_ENDPOINT = "http://localhost:5002"
CHANNEL_FILE = 'data/messages2.json'

@app.cli.command('register')
def register_command():
    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    # send a POST request to server /channels
    response = requests.post(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY},
                             data=json.dumps({
            "name": CHANNEL_NAME,
            "endpoint": CHANNEL_ENDPOINT,
            "authkey": CHANNEL_AUTHKEY}))

    if response.status_code != 200:
        print("Error creating channel: "+str(response.status_code))
        return

def check_authorization(request):
    global CHANNEL_AUTHKEY
    # check if Authorization header is present
    if 'Authorization' not in request.headers:
        return False
    # check if authorization header is valid
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health_check():
    global CHANNEL_NAME, CHANNEL_IMG
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name':CHANNEL_NAME, 'image':CHANNEL_IMG}), 200

# GET: Return list of messages
@app.route('/', methods=['GET'])
def home_page():
    if not check_authorization(request):
        return "Invalid authorization", 400
    # fetch channels from server
    return jsonify(read_messages())

# POST: Send a message
@app.route('/', methods=['POST'])
def send_message():
    # fetch channels from server
    # check authorization header
    if not check_authorization(request):
        return "Invalid authorization", 400
    # check if message is present
    message = request.json
    if not message:
        return "No message", 400
    if not 'content' in message:
        return "No content", 400
    if not 'sender' in message:
        return "No sender", 400
    if not 'timestamp' in message:
        return "No timestamp", 400
    # add message to messages
    messages = read_messages()
    messages.append({'content':message['content'], 'sender':message['sender'], 'timestamp':message['timestamp']})
    messages.append({'content':eliza_reply(message['content']), 'sender':"MensaBot", 'timestamp': datetime.datetime.now().isoformat()})
    save_messages(messages)
    return "OK", 200

def read_messages():
    global CHANNEL_FILE
    try:
        f = open(CHANNEL_FILE, 'r')
    except FileNotFoundError:
        return []
    try:
        messages = json.load(f)
    except json.decoder.JSONDecodeError:
        messages = []
    f.close()
    return messages

def save_messages(messages):
    global CHANNEL_FILE
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(messages, f)

# List of possible responses
responses = {
    "greeting": ["Hello! Have you been in the Mensa today?", "Hi there! How was your meal at the Mensa?"],
    "meal": ["What did you eat in the Mensa today?", "How was the food at the Mensa today?"],
    "positive_feedback": ["That sounds delicious!", "Glad to hear you enjoyed your meal!"],
    "negative_feedback": ["Oh, that's unfortunate. Hopefully, it'll be better next time.", "Sorry to hear that. Did you try something else?"],
    "farewell": ["Have a great day!", "See you later!"],
    "default": ["Interesting, tell me more.", "I see.", "Could you elaborate on that?"],
    "ask_about_location": ["Which Mensa did you visit?", "Is the Mensa you went to crowded?"],
    "ask_about_cost": ["How much did your meal cost?", "Is the food in the Mensa affordable?"],
    "ask_about_quality": ["How would you rate the quality of the food?", "Was the food fresh?"],
    "ask_about_menu_options": ["What menu options were available?", "Did you have any vegetarian options?"],
    "compliment_location": ["That's a great choice!", "I've heard good things about that Mensa."],
    "compliment_cost": ["It's good to hear that it's affordable.", "Sounds like a good deal!"],
    "compliment_quality": ["Glad to hear the food was fresh!", "Quality is important, glad you enjoyed it."],
    "compliment_menu_options": ["Sounds like they have a good variety!", "Nice to have options to choose from."],
}

def eliza_reply(input):

    input = input.lower()
    if any(word in input for word in ["hello", "hi", "hey", "howdy", "greetings"]):
        return random.choice(responses["greeting"])
    elif any(word in input for word in ["eat", "meal", "food", "lunch", "dinner", "breakfast"]):
        return random.choice(responses["meal"])
    elif any(word in input for word in ["good", "delicious", "great", "tasty", "yummy", "fantastic"]):
        return random.choice(responses["positive_feedback"])
    elif any(word in input for word in ["bad", "terrible", "awful", "disgusting", "horrible"]):
        return random.choice(responses["negative_feedback"])
    elif any(word in input for word in ["bye", "goodbye", "farewell", "see you", "take care"]):
        return random.choice(responses["farewell"])
    elif any(word in input for word in ["where", "location", "at"]):
        return random.choice(responses["ask_about_location"])
    elif any(word in input for word in ["cost", "price", "expensive", "cheap"]):
        return random.choice(responses["ask_about_cost"])
    elif any(word in input for word in ["quality", "fresh", "taste", "flavor"]):
        return random.choice(responses["ask_about_quality"])
    elif any(word in input for word in ["menu", "options", "variety", "vegetarian"]):
        return random.choice(responses["ask_about_menu_options"])
    elif any(word in input for word in ["good choice", "nice", "excellent", "perfect"]):
        return random.choice(responses["compliment_location"])
    elif any(word in input for word in ["affordable", "cheap", "reasonable"]):
        return random.choice(responses["compliment_cost"])
    elif any(word in input for word in ["fresh", "quality", "good taste"]):
        return random.choice(responses["compliment_quality"])
    elif any(word in input for word in ["variety", "options", "great menu"]):
        return random.choice(responses["compliment_menu_options"])
    else:
        return random.choice(responses["default"])

# Start development web server
if __name__ == '__main__':
    app.run(port=5002, debug=True)
