import tkinter as tk
import numpy as np
import gym
from gym import spaces
import math
import time
from helper import convert_coord, calculate_front_position, calculate_back_position
import keyboard


class Field(gym.Env):
    def __init__(self, display=False, actions=[]):
        super(Field, self).__init__()

        self.action_space = spaces.Discrete(5)  # Forward, Backward, Left, Right, Drop
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(5,), dtype=np.float32)

        self.actions = actions
        self.action = 0
        
        self.score = 0
        self.collided = False
        self.timer = 0
        self.grid_size = [144, 144]
        self.grid = np.zeros(self.grid_size)

        # Initialize Bot
        self.bot = Bot([15, 15], [-48, 0], 0)

        # Initialize Obstacles
        self.obstacles = [(-24, 0), (0, 24), (24, 0), (0, -24)]
        for i in range(len(self.obstacles)):
            self.obstacles[i] = Obstacle(self.obstacles[i], 5)

        # Initialize Rings
        self.rings = []
        red_rings = [(-60, 48), (-48, 60), (-48, 48), (-60, -48), (-48, -60), (-48, -48), (0, 0), (0, 60), (0, -60), (-24, 24), (-24, -24), (24, 24), (24, -24), (-24, 48), (-24, -48), (24, 48), (24, -48), (60, 48), (48, 60), (48, 48), (60, -48), (48, -60), (48, -48)]
        blue_rings = [] # Future Update
        for i in red_rings:
            # coord = convert_coord(self.grid_size, i)
            self.rings.append(Ring(i, 4, "red"))

        # Initialize Stakes
        self.stakes = []
        stakes = [(-48, 24), (-48, -24), (48, 0), (60, 24), (60, -24)]
        for i in stakes:
            self.stakes.append(Stake(i, 6))
        
        self.display = display
        
        if display:
            self.window = tk.Tk()
            self.window.title("VRC Field")

            scale_factor = 5
            # Create a canvas
            self.canvas = tk.Canvas(self.window, width=self.grid_size[1]*scale_factor, height=self.grid_size[0]*scale_factor)
            self.canvas.pack()
            self.status_label = tk.Label(self.window, text="", anchor="w", justify="left")
            self.status_label.pack(fill=tk.X)
            self.render()
        
        else:
            self.window = None
            self.canvas = None
            self.status_label = None

    """
    ML Section
    --------------------------------
    """
    def reset(self):
        self.score = 0
        self.collided = False
        self.timer = 0
        self.grid_size = [144, 144]
        self.grid = np.zeros(self.grid_size)

        # Initialize Bot
        self.bot = Bot([15, 15], [-60, 0], 90)

        # Initialize Obstacles
        self.obstacles = [(-24, 0), (0, 24), (24, 0), (0, -24)]
        for i in range(len(self.obstacles)):
            self.obstacles[i] = Obstacle(self.obstacles[i], 5)

        # Initialize Rings
        self.rings = []
        red_rings = [(-60, 48), (-48, 60), (-48, 48), (-60, -48), (-48, -60), (-48, -48), (0, 0), (0, 60), (0, -60), (-24, 24), (-24, -24), (24, 24), (24, -24), (-24, 48), (-24, -48), (24, 48), (24, -48), (60, 48), (48, 60), (48, 48), (60, -48), (48, -60), (48, -48)]
        blue_rings = [] # Future Update
        for i in red_rings:
            # coord = convert_coord(self.grid_size, i)
            self.rings.append(Ring(i, 4, "red"))

        # Initialize Stakes
        self.stakes = []
        stakes = [(-48, 24), (-48, -24), (48, 0), (60, 24), (60, -24)]
        for i in stakes:
            self.stakes.append(Stake(i, 6))
    
    def step(self, action):
        # Implement action effects
        if action == 0:
            self.bot.drive_forwards()
        elif action == 1:
            self.bot.drive_backwards()
        elif action == 2:
            self.bot.turn_ccw()
        elif action == 3:
            self.bot.turn_cw()
        elif action == 4:
            self.bot.drop()
            
        self.update_position()

        reward = self._calculate_reward()
        done = self._check_done()

        return self._get_obs(), reward, done, {}
    
    def _get_obs(self):
        # Return observation state (you'll need to define what your state representation is)
        return np.array([
            self.bot.position[0], 
            self.bot.position[1], 
            self.bot.heading,
            self.bot.rings_held,
            int(self.bot.has_stake is not None)
        ])

    def _calculate_reward(self):
        reward = 0
        if self.collided:
            reward = -100
        else:
            reward += self.score * 10
            reward += self.bot.rings_held
            if self.bot.has_stake:
                reward += 2
            reward -= self.timer * 0.0001
        return reward
    
    def _check_done(self):
        return (self.timer >= 60000) or (self.collided)
    
    def close(self):
        if self.window is not None:
            self.window.quit()
            print("Game Over")

    """
    Game Section
    --------------------------------
    """
    def update_score(self):
        score = 0
        for stake in self.stakes:
            score += stake.num_rings
            if stake.num_rings > 0:
                score += 2
            if (stake.position[0] <= -66 and stake.position[1] <= -66) or (stake.position[0] >= 66 and stake.position[1] <= -66) or (stake.position[0] <= -66 and stake.position[1] >= 66) or (stake.position[0] >= 66 and stake.position[1] >= 66):
                score += 5
        self.score = score
        return

    def draw_rectangle(self, canvas, x, y, width, height, angle):
        # Convert the angle to radians and adjust for coordinate system
        angle_rad = math.radians(angle+90)

        # Define the corner points of the rectangle relative to its center
        half_width = width / 2
        half_height = height / 2
        corners = [
            (-half_width, -half_height),  # Top-left
            (half_width, -half_height),  # Top-right
            (half_width, half_height),  # Bottom-right
            (-half_width, half_height)  # Bottom-left
        ]
        # Rotate and translate corners
        rotated_corners = []
        for cx, cy in corners:
            # Rotate each corner point around the center (x, y)
            x_rot = cx * math.cos(angle_rad) + cy * math.sin(angle_rad)
            y_rot = -cx * math.sin(angle_rad) + cy * math.cos(angle_rad)

            # Translate the rotated point to the bot's current position
            x_rot += x
            y_rot += y

            new_x, new_y = convert_coord(self.grid_size, (x_rot, y_rot))
            rotated_corners.append((new_x*5, new_y*5))

        # Draw the rotated rectangle
        canvas.create_polygon(rotated_corners, fill="cyan", outline='black', tags="bot")

        x, y = convert_coord(self.grid_size, (x, y))
        front_mid_x = (rotated_corners[3][0] + rotated_corners[0][0]) / 2
        front_mid_y = (rotated_corners[3][1] + rotated_corners[0][1]) / 2

        # Draw a small label or mark on the front side
        canvas.create_text(front_mid_x, front_mid_y, text="F", fill="white", font=("Arial", 12, "bold"), tags="bot")

    def draw_rings(self, canvas):
        for ring in self.rings:
            ring_x, ring_y = convert_coord(self.grid_size, ring.position)
            x1 = (ring_x - ring.size) * 5
            y1 = (ring_y - ring.size) * 5
            x2 = (ring_x + ring.size) * 5
            y2 = (ring_y + ring.size) * 5
            canvas.create_oval(x1, y1, x2, y2, fill="red", outline='red', tags="ring")
    
    def draw_stakes(self, canvas):
        for stake in self.stakes:
            x, y = convert_coord(self.grid_size, stake.position)

            # Hexagon Coordinates
            x1, y1 = x * 5, (y + stake.size) * 5
            x2, y2 = (x + stake.size*math.cos(math.radians(30))) * 5, (y + stake.size*math.sin(math.radians(30))) * 5
            x3, y3 = (x + stake.size*math.cos(math.radians(30))) * 5, (y - stake.size*math.sin(math.radians(30))) * 5
            x4, y4 = x * 5, (y - stake.size) * 5
            x5, y5 = (x - stake.size*math.cos(math.radians(30))) * 5, (y - stake.size*math.sin(math.radians(30))) * 5
            x6, y6 = (x - stake.size*math.cos(math.radians(30))) * 5, (y + stake.size*math.sin(math.radians(30))) * 5

            coords = ((x1, y1), (x2, y2), (x3, y3), (x4, y4), (x5, y5), (x6, y6))
            canvas.create_polygon(coords, fill="gold", outline='black', tags="stake")
            canvas.create_text(x*5, y*5, text=str(stake.num_rings), fill="red", font=("Arial", 12, "bold"), tags="stake")

    
    def check_ring_collision(self):
        for ring in self.rings:
            front_x, front_y = calculate_front_position(self.bot.position, self.bot.heading, self.bot.size[0])

            # Check if the front is near the ring
            distance = math.sqrt((front_x - ring.position[0]) ** 2 + (front_y - ring.position[1]) ** 2)

            # print("ring position:", ring.position)
            # print("bot position:", front_x, front_y)
            # print("distance from ring:", distance)
            
            if distance <= ring.size:  # Assuming ring.size is the radius
                # Pick up the ring
                self.rings.remove(ring)
                self.bot.rings_held += 1
                break

    def check_stake_collision(self):
        for stake in self.stakes:
            x, y = calculate_back_position(self.bot.position, self.bot.heading, self.bot.size[1])

            # Check if the front is near the ring
            distance = math.sqrt((x - stake.position[0]) ** 2 + (y - stake.position[1]) ** 2)

            # print("stake position:", stake.position)
            # print("bot position:", x, y)
            # print("distance from stake:", distance)
            
            if distance < (stake.size):  # Assuming ring.size is the radius
                # Pick up the ring
                self.bot.has_stake = stake
                return
        
    def check_collision(self):
        for obstacle in self.obstacles:
            x = self.bot.position[0]
            y = self.bot.position[1] 

            # Check if the front is near the obstacle
            distance = math.sqrt((x - obstacle.position[0]) ** 2 + (y - obstacle.position[1]) ** 2)

            # print("obstacle position:", obstacle.position)
            # print("bot position:", x, y)
            # print("distance from obstacle:", distance)

            if distance <= (obstacle.size + self.bot.size[0]/2):  # Assuming obstacle.size is the radius
                return True
        
        left_boundary = -self.grid_size[0] / 2 + self.bot.size[0] / 2
        right_boundary = self.grid_size[0] / 2 - self.bot.size[0] / 2
        top_boundary = self.grid_size[1] / 2 - self.bot.size[1] / 2
        bottom_boundary = -self.grid_size[1] / 2 + self.bot.size[1] / 2

        # Check collision with boundaries
        if (self.bot.position[0] <= left_boundary or
            self.bot.position[0] >= right_boundary or
            self.bot.position[1] >= top_boundary or
            self.bot.position[1] <= bottom_boundary):
            return True  # Collision detected
        
        # Check All Other Collisions
        front_x, front_y = calculate_front_position(self.bot.position, self.bot.heading, self.bot.size[0])
        back_x, back_y = calculate_back_position(self.bot.position, self.bot.heading, self.bot.size[1])

        for ring in self.rings:
            distance = math.sqrt((back_x - ring.position[0]) ** 2 + (back_y  - ring.position[1]) ** 2)
            if distance <= ring.size:
                return True
            distance = math.sqrt((front_x - ring.position[0]) ** 2 + (front_y - ring.position[1]) ** 2)
            if distance <= ring.size and self.bot.rings_held >= 3:
                return True

        for stake in self.stakes:
            distance = math.sqrt((front_x - stake.position[0]) ** 2 + (front_y - stake.position[1]) ** 2)
            
            if distance < (stake.size):
                # print(front_x, front_y)
                # print(distance)
                # print(stake.position)
                return True

        return False

    def stake_possession(self, stake):
        angle_rad = math.radians(self.bot.heading + 180)  # 180 degrees to point backward

        # Calculate the position at the back of the robot
        back_x = self.bot.position[0] + (self.bot.size[1] / 2 + stake.size) * math.sin(angle_rad)
        back_y = self.bot.position[1] + (self.bot.size[1] / 2 + stake.size) * math.cos(angle_rad)

        # Update stake possession and position
        stake.is_possessed = True
        self.bot.rings_held = stake.add_rings(self.bot.rings_held)
        stake.position = (back_x, back_y)
    
    def handle_key_press(self, event):
        action = ""
        if event.keysym == "w":
            action = "forward"
        elif event.keysym == "s":
            action = "backward"
        elif event.keysym == "a":
            action = "left"
        elif event.keysym == "d":
            action = "right"
        elif event.keysym == "q":
            action = "drop"
        
        if action == "forward":
            self.bot.drive_forwards()
        elif action == "backward":
            self.bot.drive_backwards()
        elif action == "left":
            self.bot.turn_ccw()
        elif action == "right":
            self.bot.turn_cw()
        elif action == "drop":
            self.bot.drop()

    def update_position(self):
        delay = 100
        # Only for User Testing
        # window.bind("<KeyPress>", self.handle_key_press())

        # Check for collisions
        self.collided = self.check_collision()
        self.check_ring_collision()
        self.check_stake_collision()

        if self.bot.rings_held > 3:
            self.collided = True
        
        if self.collided:
            self.close()
            return

        if self.bot.has_stake:
            self.stake_possession(self.bot.has_stake)
        
        
        self.update_score()

        if self.display:
            self.update_render()
       
        # Schedule the next update
        self.timer += delay
        if self.timer >= 60000:
            self.close()
            return
        
    def update_render(self, delay=100, action="", scale_factor=5):
        canvas = self.canvas
        window = self.window
        status_label = self.status_label

        if self.action >= len(self.actions):
            return

        action = self.actions[self.action]
        self.action += 1

        if action == 0:
            self.bot.drive_forwards()
        elif action == 1:
            self.bot.drive_backwards()
        elif action == 2:
            self.bot.turn_ccw()
        elif action == 3:
            self.bot.turn_cw()
        elif action == 4:
            self.bot.drop()

        self.canvas.delete("bot")
        self.draw_rectangle(
            self.canvas,
            self.bot.position[0],
            self.bot.position[1],
            self.bot.size[0],
            self.bot.size[1],
            self.bot.heading
        )

        self.canvas.delete("ring")
        self.draw_rings(self.canvas)
        self.canvas.delete("stake")
        self.draw_stakes(self.canvas)

        # Update the status label
        status_text = f"Bot Position: {self.bot.position}, Heading: {self.bot.heading}\n"
        status_text += f"Rings Held: {self.bot.rings_held}, Time (s): {self.timer//1000}, Score: {self.score}\n, Reward: {self._calculate_reward()}"
        status_label.config(text=status_text)

        self.window.after(delay, self.update_position)  # Update every 1 ms

    def render(self):
        scale_factor = 5

        # Draw the grid
        for i in range(self.grid_size[0]):
            for j in range(self.grid_size[1]):
                x1 = j * 24 * scale_factor
                y1 = i * 24 * scale_factor
                x2 = x1 + 24 * scale_factor
                y2 = y1 + 24 * scale_factor
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="gray70", outline='black')
        
        # Draw obstacles
        for obstacle in self.obstacles:
            x, y = convert_coord(self.grid_size, obstacle.position)
            radius = obstacle.size
            x1 = (x - radius) * scale_factor
            y1 = (y - radius) * scale_factor
            x2 = (x + radius) * scale_factor
            y2 = (y + radius) * scale_factor
            self.canvas.create_oval(x1, y1, x2, y2, fill="black", outline='black')

        self.update_position()
        self.window.mainloop()


class Bot:
    def __init__(self, size=(15, 15), start_pos=(0,0), heading=0):
        self.size = size

        # Odom Values
        self.position = start_pos
        self.heading = heading

        # Possession
        self.rings_held = 0
        self.has_stake = None

        self.speed = 2

    def drive_forwards(self):
        rad = math.radians(self.heading)
        self.position[0] += self.speed*math.sin(rad)
        self.position[1] += self.speed*math.cos(rad)
        return

    def drive_backwards(self):
        rad = math.radians(self.heading)
        self.position[0] -= self.speed*math.sin(rad)
        self.position[1] -= self.speed*math.cos(rad)
        return

    def turn_cw(self):
        self.heading += 10
        return

    def turn_ccw(self):
        self.heading -= 10
        return

    def drop(self):
        if not self.has_stake:
            return

        self.has_stake.is_possessed = False
        self.has_stake.position = (self.has_stake.position[0] - math.sin(math.radians(self.heading)), self.has_stake.position[1] - math.cos(math.radians(self.heading)))
        self.has_stake = None
        return


class Obstacle:
    def __init__(self, position, size):
        self.position = position
        self.size = size


class Ring:
    def __init__(self, position, size, color):
        self.position = position
        self.size = size
        self.color = color


class Stake:
    def __init__(self, position, size, max_rings=6, mobile=True):
        self.position = position
        self.size = size
        self.is_possessed = False
        self.num_rings = 0

        self.mobile = mobile
        self.max_rings = max_rings

    def add_rings(self, rings):
        self.num_rings += rings
        if self.num_rings > self.max_rings:
            rings = self.num_rings - self.max_rings
            self.num_rings = self.max_rings
            return rings
        return 0

# Testing Purposes Only

# actions = [0 for _ in range(1000)]
# env = Field(display=False, actions=actions)