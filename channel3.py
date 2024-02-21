## channel3.py - a simple message channel
##

from flask import Flask, request, render_template, jsonify
import json
import requests
import datetime

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
CHANNEL_AUTHKEY = '11223344'
CHANNEL_NAME = "The Mocking Channel"
CHANNEL_ENDPOINT = "http://localhost:5003" # don't forget to adjust in the bottom of the file
CHANNEL_FILE = 'data/messages3.json'
#CHANNEL_IMG = "https://media.blogto.com/articles/201731-sunrise-ed.jpg?w=2048&cmd=resize_then_crop&height=1365&quality=70"

#numbers lists
SUPERSCRIPT_NUMBERS = ["⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"]
NUMBERS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

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
    # read messages
    messages = read_messages()
    # add input message to messages
    messages.append({'content':message['content'], 'sender':message['sender'], 'timestamp':message['timestamp']})
    # add bot message to messages
    messages.append({'content':mockify(message['content']), 'sender':mockify(message['sender']), 'timestamp': mockify(datetime.datetime.now().isoformat())})
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

#mockify method to simply change input-letters to alternating lower- and upper-cases and input-numbers to superscript and regular
def mockify(input):
    global SUPERSCRIPT_NUMBERS, NUMBERS
    answer = ''
    #input to lower-case
    input = input.lower()

    #iterate over input to change every 2nd occurence to upper-case or superscript number
    for i in range(len(input)):     
        if i % 2 == 0: 
            answer += str(input[i])
        else: 
            if input[i] in NUMBERS:
                answer += SUPERSCRIPT_NUMBERS[int(input[i])]
            else:
                answer += str(input[i].upper())
    #return the mockified input
    return answer

# Start development web server
if __name__ == '__main__':
    app.run(port=5003, debug=True)
