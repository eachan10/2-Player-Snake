# game logic

import random
import threading

class Vector:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def set(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if not isinstance(other, Vector):
            raise ValueError('brug')
        return Vector(self.x + other.x, self.y + other.y)

    def __eq__(self, other):
        if not isinstance(other, Vector):
            raise ValueError('brug')
        return self.x == other.x and self.y == other.y


class SnakeGame:
    def __init__(self, size, sid):
        self.size = size  # dimensions of game tuple/list [x, y]
        self.sid = sid  # session id of snake player
        self.food_sid = None  # session id of the food player
        self.lock = threading.Lock()

        # set all variables but don't actually start yet
        self.start()
        self.alive = False

    def start(self):
        if not self.food_sid or not self.sid:
            return False
        # positions of each snake piece
        # last element is head
        self.snake = [Vector()]
        self.snake_dir = Vector(1, 0)  # direction of head movement
        self.snake_last_movement = Vector(self.snake_dir.x, self.snake_dir.y)
        # 2 element list, [x, y] for position of the food
        self.food = Vector(random.randint(0, self.size[0] - 1), random.randint(0, self.size[1] - 1))
        self.alive = True

    def set_snake_dir(self, dir):
        """
        Update direction of movement based on input
        'up' 'down' 'left' 'right'
        """
        with self.lock:
            if dir == 'up' and self.snake_last_movement.y != 1:
                # go up as long as dir isn't down
                self.snake_dir.set(0, -1)
            elif dir == 'down' and self.snake_last_movement.y != -1:
                # go down as long as dir isn't up
                self.snake_dir.set(0, 1)
            elif dir == 'left' and self.snake_last_movement.x != 1:
                # go left as long as dir isn't right
                self.snake_dir.set(-1, 0)
            elif dir == 'right' and self.snake_last_movement.x != -1:
                # go right as long as dir isn't left
                self.snake_dir.set(1, 0)

    def move(self):
        """
        Move snake head in current direction
        Snake tail follows segment ahead
        If food is consumed increase length
        """
        with self.lock:
            # move the head of the snake
            self.snake.append(self.snake[-1] + self.snake_dir)
            self.snake_last_movement.set(self.snake_dir.x, self.snake_dir.y)

            # check if food not at head
            if self.snake[-1] != self.food:
                # remove end from snake
                self.snake.pop(0)
            else:
                # don't remove end if snake ate food
                while self.food in self.snake:
                    self.food = Vector(random.randint(0, self.size[0] - 1), random.randint(0, self.size[1] - 1))

            head = self.snake[-1]
            # check for self collision
            for body in self.snake[:-1]:
                if body == head:
                    self.alive = False # dead

            # check for board boundaries
            w, h = self.size
            if head.x < 0 or head.x > w or head.y < 0 or head.y > h:
                self.alive = False

    def get_data(self):
        """Return dict to send data to client"""
        snake = [[v.x, v.y] for v in self.snake]
        food = [self.food.x, self.food.y]
        w, h = self.size
        d = {
            'snake': snake,
            'food': food,
            'alive': self.alive,  # not implemented yet
            'width': w,
            'height': h,
        }
        return d