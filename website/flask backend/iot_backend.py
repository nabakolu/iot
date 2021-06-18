"""
handles infromation flow between angular frontend and the rest of the IoT system
"""
# %%
from flask import request
from flask import Flask, render_template
from flask_socketio import SocketIO, Namespace, emit
from threading import Lock
import random
import time
# %%
CORS_CONFIG = "http://localhost:4200"
async_mode = "threading"
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!iot-key'
socketio = SocketIO(app, port=5000, cors_allowed_origins=CORS_CONFIG, async_mode=async_mode)
thread = None
thread_lock = Lock()


@socketio.on('connect')
def test_connect(auth):
    print("Client connected", request.sid)
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(mockedData)
    emit('message', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)

@socketio.on('log')
def handle_my_custom_event(string):
    print(string)

randomVar = 50
def mockedData():
    global randomVar
    while True:
        if random.random() > 0.5: randomVar += random.random()
        else: randomVar -= random.random()
        socketio.emit("exDataValue", randomVar)
        time.sleep(10)

if __name__ == '__main__':
    socketio.run(app)