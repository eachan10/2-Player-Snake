from flask import abort, Flask, redirect, render_template, request, url_for
from flask_socketio import SocketIO, join_room, emit, disconnect
import gevent

from string import ascii_letters, digits
from random import choices

from game import SnakeGame


app = Flask(__name__)
app.rooms = {}  # dictionary of game rooms
io = SocketIO(app)


@app.route('/')
def redirect_to_home():
    return redirect('/home')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template('home.html')
    elif request.method == 'POST':
        while 1:
            game_id = ''.join(choices(ascii_letters + digits, k=4))
            if game_id not in app.rooms:
                break
        app.rooms[game_id] = None
        return redirect(url_for('room', game_id=game_id))

@app.route('/room/<game_id>')
def room(game_id):
    # room not created
    if game_id not in app.rooms:
        return render_template('noroom.html')
    game = app.rooms.get(game_id)
    # new room
    if game is None:
        return render_template('room.html')
    # room already has players
    if game.snake_id is not None:  # and game.food_id is not None -- to add when multiplayer
        return render_template('fullroom.html')
    

@io.on('new con')
def on_new_con(room_id):
    print(f'New connection from {request.sid}')
    if app.rooms.get(room_id, None) is not None:
        disconnect()  # no point in having this for now
        pass  # will implement for multiplyaer to allow second player to join a game
    else:
        # the first connection to this game creates a game
        # and sets the snake to this user
        app.rooms[room_id] = SnakeGame()
        app.rooms[room_id].snake_id = request.sid
        join_room(room_id)

@io.on('ready')
def on_start(room_id):
    print(f'ready {room_id}')
    try:
        app.rooms[room_id]
    except KeyError:
        # connected client to nonexistent game id
        # maybe game deleted after inactivity
        emit('expired', url_for('home'))  # replace with a 404 page to say game not found
        return
    game = app.rooms[room_id]

    if game.snake_id == request.sid:
        game.ready[0] = True
    elif game.food_id == request.sid:
        game.ready[1] = True
    # TEMP TEMP TEMP
    game.ready[1] = True  # only cuz single player atm
    if not all(game.ready):
        return
    gevent.sleep(5)
    print('start')
    game.reset()
    def update():
        while game.alive:
            game.next_loop()
            io.emit('game update', game.get_data(), room=room_id)
            gevent.sleep(0.2)
        print('game over')
    gevent.spawn(update)

@io.on('user input')
def on_user_input(data):
    game_id = data['game_id']
    direction = data['direction']
    app.rooms[game_id].set_snake_dir(direction)
    

if __name__ == '__main__':
    try:
        io.run(app, debug=True)
    except KeyboardInterrupt:
        print('Killed')