import tkinter as tk
import pygame
import numpy as np
import gym
from gym import spaces
import math
import time
from helper import convert_coord, calculate_front_position, calculate_back_position
import sys

class Field(gym.Env):
    def __init__(self, display=False, actions=[], human=False):
        super(Field, self).__init__()
        pygame.init()

        self.action_space = spaces.Discrete(5)  # Forward, Backward, Left, Right, Drop
        self.observation_space = spaces.Box(low=np.array([-72, -72, 0, 0, 0]), high=np.array([72, 72, 35, 3, 1]), shape=(5,), dtype=np.float32)

        self.actions = actions
        self.action = 0
        self.human = human

        self.grid_size = [144, 144]
        self.grid = np.zeros(self.grid_size)
        
        self.display = display

        self.reset()
        
        if self.display:
            self.scale_factor = 4
            self.cell_size = 24
            self.screen = pygame.display.set_mode((self.grid_size[1] * self.scale_factor, self.grid_size[0] * self.scale_factor))
            pygame.display.set_caption("VRC Field")
            self.font = pygame.font.SysFont("Arial", 12)
            self.render()

    """
    ML Section
    --------------------------------
    """
    def reset(self):
        self.done = False
        self.score = 0
        self.collided = False
        self.timer = 0

        self.prev_reward = 0
        self.prev_num_rings = 0
        self.prev_score = 0
        self.stake_possess_time = 0

        self.visited = set()

        # Initialize Bot
        self.bot = Bot([15, 15], [-48, 0], 0)

        # Initialize Obstacles
        self.obstacles = []# [(-24, 0), (0, 24), (24, 0), (0, -24)]
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
        
        return self._get_obs()
    
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
    
    def distance_to_closest_ring(self):
        lowest = sys.maxsize
        for ring in self.rings:
            distance = math.sqrt((ring.position[0] - self.bot.position[0]) ** 2 + (ring.position[1] - self.bot.position[1]) ** 2)
            if distance < lowest:
                lowest = distance
        return lowest
    
    def _get_obs(self):
        # Return observation state (you'll need to define what your state representation is)
        return [
            self.bot.position[0], 
            self.bot.position[1], 
            (self.bot.heading % 360) // 10,
            int(self.bot.rings_held),
            int(self.bot.has_stake is not None)
        ]

    def _calculate_reward(self):
        reward = 0
        if self.collided:
            reward = -100
        else:

            reward += (self.score - self.prev_score) * 5
            reward += (self.bot.rings_held - self.prev_num_rings) * 2
            if self.bot.has_stake:
                self.stake_possess_time += 0.1
            else:
                self.stake_possess_time = 0
            
            if self.stake_possess_time > 3:
                reward += 2
                self.stake_possess_time = 0

            # Encourage Ring Collection
            # d_score = min(0.5, round(8 * 1 / self.distance_to_closest_ring(), 1))
            # reward += d_score

            # Encourage Exploration
            if (int(self.bot.position[0]), int(self.bot.position[1])) not in self.visited:
                reward += 1
                # print((self.bot.position[0], self.bot.position[1]))
                self.visited.add((int(self.bot.position[0]), int(self.bot.position[1])))

            # Encourage Being Fast
            # reward -= 1 # * self.timer

            # Reward Range
            # reward = np.interp(reward, (-0.1, 50), (0, 1))
        
        # total = reward - self.prev_reward
        # self.prev_reward = reward
        self.prev_num_rings = self.bot.rings_held
        self.prev_score = self.score
        
        return reward   
    
    def _check_done(self):
        return (self.timer >= 60000) or (self.collided) or (self.done)
    
    def close(self):
        if self.display:
            pygame.quit()


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

    def draw_rectangle(self, x, y, width, height, angle):
        angle_rad = math.radians(angle+90)
        half_width = width / 2
        half_height = height / 2
        corners = [
            (-half_width, -half_height),  # Top-left
            (half_width, -half_height),  # Top-right
            (half_width, half_height),  # Bottom-right
            (-half_width, half_height)  # Bottom-left
        ]
        rotated_corners = []
        for cx, cy in corners:
            x_rot = cx * math.cos(angle_rad) + cy * math.sin(angle_rad)
            y_rot = -cx * math.sin(angle_rad) + cy * math.cos(angle_rad)
            x_rot += x
            y_rot += y
            new_x, new_y = convert_coord(self.grid_size, (x_rot, y_rot))
            rotated_corners.append((new_x * self.scale_factor, new_y * self.scale_factor))
        pygame.draw.polygon(self.screen, (0, 255, 255), rotated_corners)
        front_mid_x = (rotated_corners[3][0] + rotated_corners[0][0]) / 2
        front_mid_y = (rotated_corners[3][1] + rotated_corners[0][1]) / 2
        text_surface = self.font.render("F", True, (255, 255, 255))
        self.screen.blit(text_surface, (front_mid_x, front_mid_y))

    def draw_obstacles(self):
        for obstacle in self.obstacles:
            x, y = convert_coord(self.grid_size, obstacle.position)
            x1 = (x - obstacle.size) * self.scale_factor
            y1 = (y - obstacle.size) * self.scale_factor
            x2 = (x + obstacle.size) * self.scale_factor
            y2 = (y + obstacle.size) * self.scale_factor
            pygame.draw.ellipse(self.screen, (0, 0, 0), [x1, y1, x2 - x1, y2 - y1])

    def draw_rings(self):
        for ring in self.rings:
            ring_x, ring_y = convert_coord(self.grid_size, ring.position)
            x1 = (ring_x - ring.size) * self.scale_factor
            y1 = (ring_y - ring.size) * self.scale_factor
            x2 = (ring_x + ring.size) * self.scale_factor
            y2 = (ring_y + ring.size) * self.scale_factor
            pygame.draw.ellipse(self.screen, (255, 0, 0), [x1, y1, x2 - x1, y2 - y1])

    def draw_stakes(self):
        for stake in self.stakes:
            x, y = convert_coord(self.grid_size, stake.position)
            x1, y1 = x * self.scale_factor, (y + stake.size) * self.scale_factor
            x2, y2 = (x + stake.size * math.cos(math.radians(30))) * self.scale_factor, (y + stake.size * math.sin(math.radians(30))) * self.scale_factor
            x3, y3 = (x + stake.size * math.cos(math.radians(30))) * self.scale_factor, (y - stake.size * math.sin(math.radians(30))) * self.scale_factor
            x4, y4 = x * self.scale_factor, (y - stake.size) * self.scale_factor
            x5, y5 = (x - stake.size * math.cos(math.radians(30))) * self.scale_factor, (y - stake.size * math.sin(math.radians(30))) * self.scale_factor
            x6, y6 = (x - stake.size * math.cos(math.radians(30))) * self.scale_factor, (y + stake.size * math.sin(math.radians(30))) * self.scale_factor
            coords = [(x1, y1), (x2, y2), (x3, y3), (x4, y4), (x5, y5), (x6, y6)]
            pygame.draw.polygon(self.screen, (255, 215, 0), coords)
            text_surface = self.font.render(str(stake.num_rings), True, (255, 0, 0))
            self.screen.blit(text_surface, (x * self.scale_factor, y * self.scale_factor))
    
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
    
    def handle_key_press(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.bot.drive_forwards()
        elif keys[pygame.K_s]:
            self.bot.drive_backwards()
        elif keys[pygame.K_a]:
            self.bot.turn_ccw()
        elif keys[pygame.K_d]:
            self.bot.turn_cw()
        elif keys[pygame.K_q]:
            self.bot.drop()

    def update_position(self):
        if self.actions:
            if self.action >= len(self.actions):
                self.done = True
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

        delay = 100
        # self.handle_key_press()
        self.collided = self.check_collision()
        self.check_ring_collision()
        self.check_stake_collision()

        if self.bot.rings_held > 3:
            self.collided = True

        # if self.collided:
        #     self.close()
        #     return

        if self.bot.has_stake:
            self.stake_possession(self.bot.has_stake)

        self.update_score()

        self.timer += delay
        # if self.timer >= 60000:
        #     self.close()
        #     return

    def update_render(self):

        self.screen.fill((169, 169, 169))  # Background color
        for i in range(self.grid_size[0]):
            for j in range(self.grid_size[1]):
                x1 = j * self.cell_size * self.scale_factor
                y1 = i * self.cell_size * self.scale_factor
                rect = pygame.Rect(x1, y1, self.cell_size * self.scale_factor, self.cell_size * self.scale_factor)

                # Draw the filled rectangle
                pygame.draw.rect(self.screen, (190, 190, 190), rect)  # Gray color fill

                # Draw the outline
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)  # Black color outline, 1-pixel thick
        
        self.draw_rectangle(
            self.bot.position[0],
            self.bot.position[1],
            self.bot.size[0],
            self.bot.size[1],
            self.bot.heading
        )
        self.draw_rings()
        self.draw_stakes()
        self.draw_obstacles()
        
        status_text = f"Bot Position: {self.bot.position}, Heading: {self.bot.heading}\n"
        status_text += f"Rings Held: {self.bot.rings_held}, Time (s): {self.timer//1000}, Score: {self.score}\n, Reward: {self._calculate_reward()}"
        text_surface = self.font.render(status_text, True, (0, 0, 0))
        self.screen.blit(text_surface, (10, 10))
        pygame.display.flip()

    def render(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            if self._check_done():
                running = False
            if self.human:
                self.handle_key_press()
            self.update_position()
            self.update_render()
            # print(self._get_obs())
            pygame.time.delay(10)
        self.close()

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
        self.position[0] = round(self.position[0], 1)
        self.position[1] = round(self.position[1], 1)
        return

    def drive_backwards(self):
        rad = math.radians(self.heading)
        self.position[0] -= self.speed*math.sin(rad)
        self.position[1] -= self.speed*math.cos(rad)
        self.position[0] = round(self.position[0], 1)
        self.position[1] = round(self.position[1], 1)
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

if __name__ == "__main__":
    field = Field(display=True, human=True)
    # field = Field(display=True, actions = [1, 2, 0, 0, 0, 2, 3, 2, 4, 0, 0, 2, 3, 0, 0, 0, 3, 1, 3, 1, 4, 4, 1, 0, 4, 4, 3, 0, 3, 3, 1, 1, 1, 1, 3, 2, 3, 2, 3, 2, 3, 3, 3, 1, 1, 1, 0, 1, 4, 4, 0, 1, 4, 0, 1, 4, 4, 0, 1, 4, 0, 1, 4, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 0, 1, 4, 1, 1, 3, 3, 0, 4, 3, 0, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 4, 3, 2, 4, 3, 2, 4, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 4, 2, 4, 3, 4, 2, 4, 3, 4, 2, 4, 3, 4, 2, 4, 3, 4, 2, 4, 3, 4, 2, 4, 3, 4, 2, 4, 3, 4, 2, 4, 3, 4, 2, 4, 1, 3, 2, 3, 2, 3, 1, 1, 0, 4, 4, 4, 4, 1, 0, 4, 4, 4, 3, 4, 4, 4, 4, 4, 3, 3, 3, 1, 0, 2, 2, 2, 1, 3, 0, 2, 1, 3, 0, 2, 1, 3, 0, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 0, 3, 3, 0, 3, 1, 2, 1, 1, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2, 4, 3, 2])
    