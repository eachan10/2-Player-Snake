from game import SnakeGame

from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, join_room, leave_room, emit

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
    for game in games:
        if not game.food_sid:
            game.food_sid = request.sid
            emit('food')
            break
        if not game.sid:
            game.sid = request.sid
            break
    else:
        print('new game')
        games.append(SnakeGame([40, 40], request.sid))
        emit('snake')

    join_room(request.sid)

@socketio.event
def disconnect():
    # leave room when a client disconnects
    for game in games:
        if game.sid == request.sid:
            game.sid = None
        if game.food_sid == request.sid:
            game.food_sid == None
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

@socketio.on('start')
def handle_start():
    for game in games:
        if game.sid == request.sid:
            game.start()
            print('starting')

def game_loop():
    while True:
        for game in games:
            # update all game states
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