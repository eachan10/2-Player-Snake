from game import SnakeGame

from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, join_room, leave_room

from time import sleep
import threading


games = []

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/test')
def test():
    return render_template('client.html')

@socketio.on('connect')
def on_connect(data):
    print(f'joined {request.sid}')
    games.append(SnakeGame([40, 40], request.sid))

    join_room(request.sid)

@socketio.event
def disconnect():
    # leave room when a client disconnects
    room = session.get('room')
    leave_room(room)
    
@socketio.on('user input')
def handle_input(data):
    for game in games:
        if game.sid == request.sid:
            if game.alive:
                game.set_snake_dir(data)

@socketio.on('start')
def handle_start():
    for game in games:
        if game.sid == request.sid:
            game.start()

def game_loop():
    while True:
        for game in games:
            # update all game states
            if game.alive:
                game.move()
                socketio.emit('game update', game.get_data(), room=game.sid)
        sleep(0.1)

if __name__ == '__main__':
    # socketio.start_background_task(game_loop)
    threading.Thread(target=game_loop, daemon=True).start()
    socketio.run(app)