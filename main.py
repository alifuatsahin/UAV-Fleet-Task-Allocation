import numpy as np
from agent import Agent
from UAV_gym_env import UAVGymEnv

if __name__ == "__main__":
    env = UAVGymEnv(uav_number=5, max_distance=100)
    agent = Agent(alpha=0.0003, beta=0.0003, 
                  input_dims=[env.observation_space.shape[0]], 
                  tau=0.005, scale=2, env=env, gamma=0.99, 
                  n_actions=env.action_space.shape[0], max_size=1000000, 
                  layer1_size=256, layer2_size=256, batch_size=256)
    n_games = 250

    best_score = env.reward_range[0]
    score_history = []
    max_iter = 1000

    for i in range(n_games):
        observation = env.reset()
        done = False
        score = 0
        iter = 0
        while not done and iter < max_iter:
            action = agent.choose_action(observation)
            observation_, reward, done, info = env.step(action)
            score += reward
            agent.remember(observation, action, reward, observation_, done)
            agent.learn()
            observation = observation_
            iter += 1
        score_history.append(score)
        avg_score = np.mean(score_history[-100:])

        if avg_score > best_score:
            best_score = avg_score

        print('episode ', i, 'score %.1f' % score, 'avg_score %.1f' % avg_score)