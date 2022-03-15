import random
import time

from .vector import Vector

from eventlet.semaphore import Semaphore


class SnakeGame:
    MAX_SECONDS = 600
    WINNING_SNAKE_LENGTH = 20

    def __init__(self, size=None):
        self.size = size or (40, 40)  # dimensions of game tuple/list [x, y]
        self.snake_sid = None
        self.food_sid = None
        self.ready = [False, False]  # ready states for snake and food [snake, food]
        self._lock = Semaphore()

    def start(self):
        # positions of each snake piece
        # last element is head
        self.snake = [Vector()]
        self._snake_dir = Vector(1, 0)
        self._snake_last_movement = Vector(self._snake_dir.x, self._snake_dir.y)
        self.food = Vector(
            random.randint(0, self.size[0] - 1), random.randint(0, self.size[1] - 1)
        )
        self._food_last_pos = Vector(self.food.x, self.food.y)
        self._food_dir = Vector(0, 0)
        self._food_move_counter = 0
        self.ready = [False, False]
        self.winner = None
        self.end_time = int(time.time()) + self.MAX_SECONDS

    def set_food_dir(self, dir):
        """
        Update direction of movement based on input
        'u' 'd' 'l' 'r'
        """
        with self._lock:
            if dir == "u":
                self._food_dir.set(0, -1)
            elif dir == "d":
                self._food_dir.set(0, 1)
            elif dir == "l":
                self._food_dir.set(-1, 0)
            elif dir == "r":
                self._food_dir.set(1, 0)

    def set_snake_dir(self, dir):
        """
        Update direction of movement based on input
        'u' 'd' 'l' 'r'
        """
        with self._lock:
            if dir == "u" and self._snake_last_movement.y != 1:
                self._snake_dir.set(0, -1)
            elif dir == "d" and self._snake_last_movement.y != -1:
                self._snake_dir.set(0, 1)
            elif dir == "l" and self._snake_last_movement.x != 1:
                self._snake_dir.set(-1, 0)
            elif dir == "r" and self._snake_last_movement.x != -1:
                self._snake_dir.set(1, 0)

    def next_loop(self):
        """
        Move snake head in current direction
        Snake tail follows segment ahead
        If food is consumed increase length
        """
        if not self.snake_sid or not self.food_sid:
            return False

        with self._lock:
            w, h = self.size

            # move the head of the snake
            self.snake.append(self.snake[-1] + self._snake_dir)
            self._snake_last_movement.set(self._snake_dir.x, self._snake_dir.y)

            # move the food
            self._food_move_counter += 1
            if self._food_move_counter <= 1:
                pass
            elif len(self.snake) > 4 or self._food_move_counter > 2:
                self._food_last_pos.set(self.food.x, self.food.y)
                self.food += self._food_dir
                self._food_move_counter = 0

            # move the body
            # check if food not at head
            if self.snake[-1] == self.food:
                # don't remove end if snake ate food
                while self.food in self.snake:
                    self.food = Vector(
                        random.randint(0, self.size[0] - 1),
                        random.randint(0, self.size[1] - 1),
                    )
                    self._food_dir.set(0, 0)
            else:
                self.snake.pop(0)
                if self.food in self.snake:
                    self.food.set(self._food_last_pos.x, self._food_last_pos.y)
                    self._food_dir.set(0, 0)

            # check if the game is over

            head = self.snake[-1]
            # self collision of snake
            for body in self.snake[:-1]:
                if body == head:
                    self.winner = "food"

            # check for board boundaries
            if head.x < 0 or head.x >= w or head.y < 0 or head.y >= h:
                self.winner = "food"
            if (
                self.food.x < 0
                or self.food.x >= w
                or self.food.y < 0
                or self.food.y >= h
            ):
                if not self.winner:
                    self.winner = "snake"
                else:
                    self.winner = "draw"

            # snake loses to clock
            if time.time() > self.end_time:
                self.winner = "food"
            # food eaten too many times
            if len(self.snake) > self.WINNING_SNAKE_LENGTH:
                self.winner = "snake"
        return True

    def get_data(self):
        """Return dict to send data to client"""
        snake = [[v.x, v.y] for v in self.snake]
        food = [self.food.x, self.food.y]
        w, h = self.size
        d = {
            "snake": snake,
            "food": food,
            "width": w,
            "height": h,
            "winner": self.winner,
            "timer": self.end_time - int(time.time()),
        }
        return d
