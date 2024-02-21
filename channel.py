## channel.py - a simple number guessing channel
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
CHANNEL_AUTHKEY = '0987654321'
CHANNEL_NAME = "The Guessing Game"
CHANNEL_ENDPOINT = "http://localhost:5001" # don't forget to adjust in the bottom of the file
CHANNEL_FILE = 'data/messages.json'
#CHANNEL_IMG = "https://media.blogto.com/articles/201731-sunrise-ed.jpg?w=2048&cmd=resize_then_crop&height=1365&quality=70"

# variables for number-guessing
CURRENT_NUMBER = -1
LOWER_BOUND = 1
UPPER_BOUND = 100
NUMBER_GUESSES = 0

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
    global CHANNEL_NAME
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name':CHANNEL_NAME}), 200

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
    
    #read messages
    messages = read_messages()
    # add input message to messages
    messages.append({'content':message['content'], 'sender':message['sender'], 'timestamp':message['timestamp']})
    # add bot-message to messages
    messages.append(guess_reply(message['content']))
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

# guess-reply
def guess_reply(input):
    global CURRENT_NUMBER, LOWER_BOUND, UPPER_BOUND, NUMBER_GUESSES
    #initialize random number
    if CURRENT_NUMBER < 0:
        answer = f"I'm thinking of a random number between {LOWER_BOUND} and {UPPER_BOUND}!"
        CURRENT_NUMBER = random.randint(LOWER_BOUND, UPPER_BOUND)
    else:
        #try to convert input to integer
        try:
            input_number = int(input)
            NUMBER_GUESSES += 1

            #number comparison
            if input_number == CURRENT_NUMBER:
                answer = f"You guessed the correct number {input_number} in {NUMBER_GUESSES} guesses! Text me, if you want to play again."
                CURRENT_NUMBER = -1
                NUMBER_GUESSES = 0
            elif input_number < CURRENT_NUMBER:
                answer = f"The number I am thinking of is bigger than {input_number}..."
            elif input_number > CURRENT_NUMBER:
                answer = f"The number I am thinking of is smaller than {input_number}..."
            #error-message
            else:
                answer = f"Something went wrong! :("
        #except
        except:
            answer = f"Please enter a integer between {LOWER_BOUND} and {UPPER_BOUND}."
    
    #return answer with sender "GuessBot" and current timestamp
    return {'content':answer, 'sender':"GuessBot", 'timestamp': datetime.datetime.now().isoformat()}

# Start development web server
if __name__ == '__main__':
    app.run(port=5001, debug=True)
