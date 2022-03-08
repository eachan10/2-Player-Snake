# game logic

import random
from eventlet.semaphore import Semaphore

class Vector:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def set(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        return Vector(self.x + other.x, self.y + other.y)

    def __iadd__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        self.x += other.x
        self.y += other.y
        return self

    def __eq__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        return self.x == other.x and self.y == other.y


class SnakeGame:
    def __init__(self, size=None):
        self.size = size or (40,40)  # dimensions of game tuple/list [x, y]
        self.snake_sid = None  # session id of snake player
        self.food_sid = None  # session id of the food player
        self.ready = [False, False]  # ready states for snake and food [snake, food]
        self._lock = Semaphore()

        # set all variables but don't actually start yet
        self.reset()

    def reset(self):
        # positions of each snake piece
        # last element is head
        self.snake = [Vector()]
        self.snake_dir = Vector(1, 0)
        self.snake_last_movement = Vector(self.snake_dir.x, self.snake_dir.y)
        self.food = Vector(random.randint(0, self.size[0] - 1), random.randint(0, self.size[1] - 1))
        self.food_dir = Vector(0, 0)
        self.food_can_move = False
        self.ready = [False, False]
        self.winner = None

    def set_food_dir(self, dir):
        """
        Update direction of movement based on input
        'u' 'd' 'l' 'r'
        """
        with self._lock:
            if dir == 'u':
                self.food_dir.set(0, -1)
            elif dir == 'd':
                self.food_dir.set(0, 1)
            elif dir == 'l':
                self.food_dir.set(-1, 0)
            elif dir == 'r':
                self.food_dir.set(1, 0)

    def set_snake_dir(self, dir):
        """
        Update direction of movement based on input
        'u' 'd' 'l' 'r'
        """
        with self._lock:
            if dir == 'u' and self.snake_last_movement.y != 1:
                # go up as long as dir isn't down
                self.snake_dir.set(0, -1)
            elif dir == 'd' and self.snake_last_movement.y != -1:
                # go down as long as dir isn't up
                self.snake_dir.set(0, 1)
            elif dir == 'l' and self.snake_last_movement.x != 1:
                # go left as long as dir isn't right
                self.snake_dir.set(-1, 0)
            elif dir == 'r' and self.snake_last_movement.x != -1:
                # go right as long as dir isn't left
                self.snake_dir.set(1, 0)

    def next_loop(self):
        """
        Move snake head in current direction
        Snake tail follows segment ahead
        If food is consumed increase length
        """
        # if not self.snake_sid or not self.food_sid:
        #     return False

        with self._lock:
            w, h = self.size

            # move the head of the snake
            self.snake.append(self.snake[-1] + self.snake_dir)
            self.snake_last_movement.set(self.snake_dir.x, self.snake_dir.y)

            # move the food
            if self.food_can_move:
                self.food += self.food_dir
            self.food_can_move = not self.food_can_move  # toggles so food moves every other frame

            if self.food.x < 0:
                self.food.x = 0
            if self.food.x >= w:
                self.food.x = w - 1
            if self.food.y < 0:
                self.food.y = 0
            if self.food.y >= h:
                self.food.y = h - 1

            # check if food not at head
            if self.snake[-1] != self.food:
                # remove end from snake
                self.snake.pop(0)
            else:
                # don't remove end if snake ate food
                while self.food in self.snake:
                    self.food = Vector(random.randint(0, self.size[0] - 1), random.randint(0, self.size[1] - 1))
                    self.food_dir.set(0, 0)

            head = self.snake[-1]
            # check for self collision
            for body in self.snake[:-1]:
                if body == head:
                    self.winner = 'snake'

            # check for board boundaries
            if head.x < 0 or head.x >= w or head.y < 0 or head.y >= h:
                self.winner = 'snake'

    def get_data(self):
        """Return dict to send data to client"""
        snake = [[v.x, v.y] for v in self.snake]
        food = [self.food.x, self.food.y]
        w, h = self.size
        d = {
            'snake': snake,
            'food': food,
            'width': w,
            'height': h,
            'winner': self.winner
        }
        return d