import sys
import os
directory = '/Users/edisony611/PycharmProjects/VEX-VRSkills-AI/High Stakes/env/'
sys.path.append(os.path.abspath(directory))
from env import Field

from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3 import PPO
import time

models_dir = f"High Stakes/ai/ppo/models/{int(time.time())}"
logdir = f"High Stakes/ai/ppo/logs/{int(time.time())}"


if __name__ == '__main__':
	env = Field(display=False)
	vec_env = SubprocVecEnv([env for _ in range(2)])


	train = True

	if train:
		if not os.path.exists(models_dir):
			os.makedirs(models_dir)

		if not os.path.exists(logdir):
			os.makedirs(logdir)

		model = PPO('MlpPolicy', vec_env, verbose=1, tensorboard_log=logdir, ent_coef=0.01)
		TIMESTEPS = 50000
		iters = 0
		while True:
			iters += 1
			model.learn(total_timesteps=TIMESTEPS, reset_num_timesteps=False, tb_log_name=f"PPO")
			model.save(f"{models_dir}/{TIMESTEPS*iters}")

			# done = False
			# obs = env.reset()
			# actions = []
			# render = False
			# while not done:
			# 	random_action = env.action_space.sample()
			# 	actions.append(random_action)
			# 	obs, reward, done, info = env.step(random_action)
			# 	render = True
			# if render:
			# 	Field(display=True, actions=actions)

	else:
		log_num = 1724957412
		model_num = 700000
		model_path = f"High Stakes/ai/ppo/models/{log_num}/{model_num}.zip"
		model = PPO.load(model_path, env=env)

		episodes = 500

		for episode in range(episodes):
			done = False
			obs = env.reset()
			actions = []
			render = False
			while not done:
				action, _ =	model.predict(obs)
				actions.append(action)
				obs, reward, done, info = env.step(action)
				render = True
				# if reward > 8:
				# 	render = True
			if render:
				Field(display=True, actions=actions)