import sys
import os
import json

# Specify the path to the directory containing your module
directory = '/Users/edisony611/PycharmProjects/VEX-VRSkills-AI/High Stakes/env/'
sys.path.append(os.path.abspath(directory))

from env import Field

import numpy as np
import random

class QLearning:
    def __init__(self, state_size, action_size, learning_rate=0.1, gamma=0.95, epsilon=0.9, epsilon_decay=0.95, min_epsilon=0.01):
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        self.q_table = np.random.uniform(low=0, high=1, size=(state_size + [action_size]))

    def choose_action(self, state):
        if np.random.rand() < self.epsilon:
            return random.randint(0, self.action_size - 1)  # Explore
        else:
            return np.argmax(self.q_table[state])  # Exploit

    def update_q_table(self, state, action, reward, next_state):
        # print("state:", state)
        # print("next_state:", next_state)
        try:
            best_next_action = np.argmax(self.q_table[next_state])
            td_target = reward + self.gamma * self.q_table[next_state][best_next_action]
            td_error = td_target - self.q_table[state][action]
            self.q_table[state][action] += self.learning_rate * td_error

            # Decay epsilon
            self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        except(IndexError):
            print("state:", state)
            print("action:", action)
            print("reward:", reward)
            print("next_state:", next_state)



def get_discrete_state(x, y, heading, num_rings, stake, grid_size):
    # Convert the continuous position to discrete state
    x, y = int(x), int(y)
    x, y = x + grid_size[0] // 2, grid_size[1] // 2 - y
    # Convert the continuous heading to discrete state
    heading = int(heading)
    heading = heading % 360
    heading = heading // 10

    return tuple([x, y, heading, int(num_rings), int(stake)])

# Example usage
# Assuming your Field environment can be initialized and provides state and action spaces

env = Field(display=False)  # Initialize your environment

# Load the configuration file to get current episode
with open("/Users/edisony611/PycharmProjects/VEX-VRSkills-AI/High Stakes/ai/qlearning/config.json", "r") as f:
    config = json.load(f)
cur_episode = config["cur_episode"]

# Initialize the Q-Learning agent and most recent table
agent = QLearning(state_size=[144, 144, 36, 4, 2], action_size=5)
try:
    agent.q_table = np.load(f"/Users/edisony611/PycharmProjects/VEX-VRSkills-AI/High Stakes/ai/qlearning/qtables/q_table_{cur_episode}.npy")
except FileNotFoundError:
    print("No q_table found, starting from scratch")
    pass

episodes = 10000000

SHOW_EVERY = 1000
LOG_EVERY = 1000
SAVE_EVERY = 10000

for episode in range(cur_episode, episodes+1):
    env.reset()
    done = False
    total_reward = 0
    actions = []
    state = env._get_obs()
    state = get_discrete_state(state[0], state[1], state[2], state[3], state[4], env.grid_size)

    render = False
    
    while not done:
        action = agent.choose_action(state)
        actions.append(action)

        next_state, reward, done, _ = env.step(action)
        new_discrete_state = get_discrete_state(next_state[0], next_state[1], next_state[2], next_state[3], next_state[4], env.grid_size)

        agent.update_q_table(state, action, reward, new_discrete_state)

        state = new_discrete_state
        total_reward += reward

    # print(f"Episode {episode + 1}, Total Reward: {total_reward}")
    if episode % SAVE_EVERY == 0:
        np.save(f"/Users/edisony611/PycharmProjects/VEX-VRSkills-AI/High Stakes/ai/qlearning/qtables/q_table_{episode}.npy", agent.q_table)
        table = json.dumps({"cur_episode": episode})
        with open("/Users/edisony611/PycharmProjects/VEX-VRSkills-AI/High Stakes/ai/qlearning/config.json", "w") as f:
            f.write(table)
    if episode % LOG_EVERY == 0:
        print(new_discrete_state)
        print(f"Episode {episode}, Reward: {reward}, Total Reward: {total_reward}")
        print(actions)
    if render or episode % SHOW_EVERY == 0:
        env.render_env = Field(display=True, actions=actions)