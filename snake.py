from game import SnakeGame

from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, join_room, leave_room, emit

from time import sleep
import threading


games = []

app = Flask(__name__)
socketio = SocketIO(app, ping_interval=5)

@app.route('/test')
def test():
    return render_template('client.html')

@socketio.on('connect')
def on_connect(data):
    print(f'joined {request.sid}')
    # check if any games have available space
    for game in games:
        if not game.food_sid:
            game.food_sid = request.sid
            emit('role', 'food')
            break
        if not game.sid:
            game.sid = request.sid
            emit('role', 'snake')
            break
    # if no open games, create a new game
    else:
        print('new game')
        games.append(SnakeGame([40, 40], request.sid))
        emit('role', 'snake')

    join_room(request.sid)

@socketio.event
def disconnect():
    # leave game when a client disconnects
    # delete game if it has no more players
    to_delete = []
    for game in games:
        if game.sid == request.sid:
            game.sid = None
        if game.food_sid == request.sid:
            game.food_sid == None
        if game.sid is None and game.food_sid is None:
            to_delete.append(game)
    for g in to_delete:
        games.remove(g)
    # leave room when a client disconnects
    room = session.get('room')
    leave_room(room)
    
@socketio.on('user input')
def handle_input(data):
    for game in games:
        if game.sid == request.sid:
            if game.alive:
                game.set_snake_dir(data)
        if game.food_sid == request.sid:
            if game.alive:
                game.set_food_dir(data)

# event fired when client starts a game
@socketio.on('start')
def handle_start():
    for game in games:
        if game.sid == request.sid:
            game.start()
            print('starting')

def game_loop():
    while True:
        for game in games:
            # update all game states and send data to clients
            if game.alive:
                game.move()
                data = game.get_data()
                socketio.emit('game update', data, room=game.sid)
                socketio.emit('game update', data, room=game.food_sid)
        sleep(0.2)

if __name__ == '__main__':
    # socketio.start_background_task(game_loop)
    threading.Thread(target=game_loop, daemon=True).start()
    socketio.run(app)