const url = window.location.href;
const room_id = url.substring(url.lastIndexOf("/") + 1);
let alive = false;


const canvas = document.getElementById("game_canvas");
const ctx = canvas.getContext("2d");
w = canvas.getAttribute("width");
h = canvas.getAttribute("height");
ctx.clearRect(0, 0, w, h);

const snake_length_p = document.getElementById("snake_length");
const game_timer_p = document.getElementById("game_timer");

let socket = io();
socket.emit("new con", room_id)

const ready_button = document.getElementById("ready_button");
ready_button.addEventListener("click", () => {
    console.log("ready");
    socket.emit("ready", room_id);
    ready_button.disabled = true;
    ctx.clearRect(0, 0, w, h);
    ctx.textAlign = "center";
    ctx.font = "24px Georgia";
    ctx.fillStyle = "#000";
    ctx.fillText("Waiting for opponent...", w / 2, h / 2);
});

// event fired on an interval to update the game state
socket.on('game update', (data) => {
    // after starting a game the first update will set alive to true
    // this allows user input to be fed to the server
    if (!alive) {
        alive = true;
        console.log("start");
    }
    // redraw the game whenever it gets changed
    ctx.clearRect(0, 0, w, h);
    const g_alive = data.winner == null;  // whether the game is active or not
    if (g_alive) {
        const snake = data.snake;
        const food = data.food;
        const x_scale = w / data.width;
        const y_scale = h / data.height;
        // draw the snake body
        ctx.fillStyle = "#7a7a7a";
        for (const pos of snake) {
            ctx.fillRect(pos[0] * x_scale, pos[1] * y_scale, x_scale, y_scale);
        }
        // draw the food
        ctx.fillStyle = "#d61b1b";
        ctx.fillRect(food[0] * x_scale, food[1] * y_scale, x_scale, y_scale);

        game_timer_p.innerHTML = "Time Remaining: " + Math.floor(data.timer/60) + ":" + data.timer%60;
        snake_length_p.innerHTML = "Snake Length: " + snake.length;
    } else {
        console.log("dead");
        alive = false;;
        ctx.textAlign = "center";
        ctx.font = "48px Georgia";
        ctx.fillStyle = "#000";
        let t;
        console.log(data.winner);
        switch (data.winner) {
            case "snake":
                t = "Snake wins";
                break;
            case "food":
                t = "Food wins";
                break;
            case "draw":
                t = "Draw";
                break;
        }
        ctx.fillText("Game Over", w / 2, h / 2 - 20);
        ctx.fillText(t, w / 2, h / 2 + 20);
        ready_button.hidden = false;
        ready_button.disabled = false;
    }
});

socket.on("expired", () => {
    console.log("expired");
    // the room doesn't exist on server
    document.location.href = "/home";
});

socket.on("role", (role) => {
    if (role == "snake") {
        document.getElementById("role").innerHTML = "You are: snake"
    } else if (role == "food") {
        document.getElementById("role").innerHTML = "You are: food"
    }
});

socket.on("starting", () => {
    ready_button.hidden = true;
    ctx.clearRect(0, 0, w, h);
    ctx.textAlign = "center";
    ctx.font = "24px Georgia";
    ctx.fillStyle = "#000";
    ctx.fillText("Starting in a moment", 200, 200);
});

socket.on("opponent dc", () => {
    alive = false;
    ready_button.hidden = false;
    ready_button.disabled = false;
    ctx.clearRect(0, 0, w, h);
    ctx.textAlign = "center";
    ctx.font = "24px Georgia";
    ctx.fillStyle = "#000";
    ctx.fillText("Opponent Disconnected", 200, 200);
});

socket.on("disconnect", () => {
    document.location.href = "/disconnected"
});

document.addEventListener("keydown", (e) => {
    if (!alive) {
        return;
    }
    // send user input to server
    let dir;
    switch (e.key) {
        case "a":
            dir = "l";
            break;
        case "w":
            dir = "u";
            break;
        case "d":
            dir = "r";
            break;
        case "s":
            dir = "d";
            break;
    }
    if (dir) {
        socket.emit("user input", {
            "game_id": room_id,
            "direction": dir,
        });
    }
});