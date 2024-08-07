import numpy as np
import pyautogui
from PIL import ImageGrab, ImageOps
import os
import time
import random


class SimpleQAgent:
    def __init__(self):
        # Define actions
        self.actions = ['drive', 'turn', 'intake', 'outtake']
        self.q_table = {}  # Q-table for storing state-action values
        self.epsilon = 0.1  # Exploration factor
        self.alpha = 0.5  # Learning rate
        self.gamma = 0.9  # Discount factor
        self.current_state = None

    def get_state(self):
        # Capture the current state (simplified)
        screenshot = ImageGrab.grab()
        screenshot = ImageOps.grayscale(screenshot)
        state = hash(screenshot.tobytes())  # Simplified state representation
        return state

    def choose_action(self, state):
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(self.actions)  # Explore
        else:
            # Exploit: choose the action with the highest Q-value
            return max(self.actions, key=lambda action: self.q_table.get((state, action), 0))

    def update_q_table(self, state, action, reward, next_state):
        current_q = self.q_table.get((state, action), 0)
        max_next_q = max(self.q_table.get((next_state, a), 0) for a in self.actions)
        new_q = (1 - self.alpha) * current_q + self.alpha * (reward + self.gamma * max_next_q)
        self.q_table[(state, action)] = new_q

    def perform_action(self, action):
        """
        Execute the given action by generating and running code in the web environment.
        """
        code_snippet = self.action_to_code(action)
        self.execute_code(code_snippet)

    def action_to_code(self, action):
        """
        Map each action to a code snippet.
        """
        if action == 'drive':
            return "drivetrain.drive_for(FORWARD, 24, INCHES)"
        elif action == 'turn':
            return " drivetrain.turn_for(90, DEGREES)"
        elif action == 'intake':
            return "intake();"
        elif action == 'outtake':
            return "outtake();"

    def execute_code(self, code_snippet):
        """
        Execute the given code snippet in the web environment.
        """
        pyautogui.hotkey('ctrl', 'a')  # Select all existing code
        pyautogui.typewrite(code_snippet)  # Type the new code snippet
        # pyautogui.press('enter')  # Execute the code
        time.sleep(1)  # Allow time for action to be executed

    def get_final_reward(self):
        """
        Extract the final reward (score) from the web environment.
        """
        # Placeholder: Implement method to get the final score from the screen
        return random.randint(0, 100)  # Use a random score for demonstration

    def train(self, num_episodes=100):
        for episode in range(num_episodes):
            self.current_state = self.get_state()
            done = False
            total_reward = 0
            action_count = 0

            while not done:
                action = self.choose_action(self.current_state)
                self.perform_action(action)
                next_state = self.get_state()
                reward = 0  # No intermediate rewards

                # Check if run is finished
                action_count += 1
                if action_count >= 10:  # Example condition
                    done = True
                    reward = self.get_final_reward()

                self.update_q_table(self.current_state, action, reward, next_state)
                self.current_state = next_state
                total_reward += reward

            print(f"Episode {episode + 1} completed with total reward: {total_reward}")

# Example use
if __name__ == '__main__':
    agent = SimpleQAgent()
    agent.train(num_episodes=10)
