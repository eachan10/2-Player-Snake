from flask import abort, Flask, redirect, render_template, request, url_for
from flask_socketio import SocketIO, join_room, emit, disconnect

from string import ascii_letters, digits
from random import choices

from game import SnakeGame


app = Flask(__name__)
app.rooms = {}  # dictionary of game rooms
io = SocketIO(app, ping_interval=3, ping_timeout=10)


@app.route('/')
def redirect_to_home():
    return redirect('/home')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template('home.html')
    elif request.method == 'POST':
        room_id = request.form.get('room_id')
        if room_id is None:
            while 1:
                room_id = ''.join(choices(ascii_letters + digits, k=4))
                if room_id not in app.rooms:
                    break
            app.rooms[room_id] = None
            return redirect(url_for('room', room_id=room_id))
        return redirect(url_for('room', room_id=room_id))

@app.route('/room/<room_id>')
def room(room_id):
    # room not created
    if room_id not in app.rooms:
        return redirect('/noroom')
    game = app.rooms.get(room_id)
    # room already has players for food and snake
    if game is not None and game.snake_sid is not None and game.food_sid is not None:
        return redirect('/fullroom')
    # room exists or game exists and is not full
    return render_template('room.html')
    
@app.route('/noroom')
def noroom():
    return render_template('noroom.html')

@app.route('/fullroom')
def fullroom():
    return render_template('fullroom.html')

@app.route('/disconnected')
def disconnected():
    return render_template('disconnected.html')

@io.on('new con')
def on_new_con(room_id):
    print(f'New connection from {request.sid}')
    game = app.rooms.get(room_id, None)
    # if game full already the app route should have denied access already
    if game is not None:  # room exists already
        if game.snake_sid is None:
            game.snake_sid = request.sid
            emit('role', 'snake')
        elif game.food_sid is None:
            game.food_sid = request.sid
            emit('role', 'food')
    else:
        # the first connection to this game creates a game
        # and sets the snake to this user
        app.rooms[room_id] = SnakeGame()
        app.rooms[room_id].snake_sid = request.sid
        emit('role', 'snake')
    join_room(room_id)

@io.on('ready')
def on_start(room_id):
    print(f'ready {room_id}')
    try:
        app.rooms[room_id]
    except KeyError:
        # connected client to nonexistent game id
        # maybe game deleted after inactivity
        emit('expired')  # replace with a 404 page to say game not found
        return
    game = app.rooms[room_id]

    if game.snake_sid == request.sid:
        game.ready[0] = True
    elif game.food_sid == request.sid:
        game.ready[1] = True
    if not all(game.ready):
        return
    emit('starting', room=room_id)
    io.sleep(5)
    print('start')
    game.reset()
    def update():
        while game.winner is None:
            if game.next_loop():
                io.emit('game update', game.get_data(), room=room_id)
            else:
                io.emit('opponent dc', room=room_id)
            io.sleep(0.1)
        print('game over')
    io.start_background_task(update)

@io.on('user input')
def on_user_input(data):
    game_id = data['game_id']
    direction = data['direction']
    game = app.rooms[game_id]
    if request.sid == game.snake_sid:
        app.rooms[game_id].set_snake_dir(direction)
    elif request.sid == game.food_sid:
        app.rooms[game_id].set_food_dir(direction)

# client tell server it's alive
@io.on('disconnect')
def on_disconnect():
    to_del = []
    for room_id, game in app.rooms.items():
        if game.snake_sid == request.sid:
            game.snake_sid = None
        elif game.food_sid == request.sid:
            game.food_sid = None
        if game.snake_sid is None and game.food_sid is None:
            to_del.append(room_id)
        else:
            game.reset()
    for td in to_del:
        del app.rooms[td]


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    io.run(app, host='0.0.0.0', port=port)