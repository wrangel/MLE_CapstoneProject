#!/usr/bin/python

#!/usr/bin/python

import numpy as np
import gym
from collections import defaultdict
from keras.layers import Dense
from keras.models import Sequential 


D = 7
GAMMA = 0.99
##NEW##
#N_EPISODES = 10
##NEW##
ENV = gym.make("LunarLander-v2")
INPUT_DIM = ENV.reset().shape[0] 
N_ACTIONS = ENV.action_space.n
ACTIONS = np.arange(0, N_ACTIONS)


#https://keras.io/getting-started/functional-api-guide/
def _create_network(D):
	model = Sequential()
	model.add(Dense(200, input_shape=(D*INPUT_DIM,)))
	model.add(Dense(N_ACTIONS, activation='softmax'))
	model.compile(optimizer='rmsprop',
				loss='categorical_crossentropy',
				metrics=['accuracy'])
	return model 


##NEW##
TOTAL_TIME_STEPS = 1e2
TOTAL_EXPLORATION_STEPS = TOTAL_TIME_STEPS / 10
##NEW##
EPSILON_RANGE = [1, 0.01]
epsilon = EPSILON_RANGE[0]
##NEW##

model = _create_network(D)
t = pos_count = finalized_count = 0

##NEW##
#for e in range(N_EPISODES):
while t <= TOTAL_TIME_STEPS:
##NEW##
	x_t = ENV.reset()
	s_t = np.tile(x_t, D)
	done = False
	
	while not done: 
		ENV.render()
			
		# estimate rewards for each action (targets), at s_t (1a)
		q = model.predict(s_t[np.newaxis])[0]
			
		###NEW###
		# Anneal epsilon over exploration timesteps
		epsilon = epsilon - epsilon / TOTAL_EXPLORATION_STEPS if epsilon > EPSILON_RANGE[1] else EPSILON_RANGE[1]
		
		# Take action with highest estimated reward, epsilon greedy
		a_t = np.random.choice(ACTIONS, 1)[0] if np.random.random() <= epsilon else np.argmax(q) #argmax returns index
		##NEW##
			
		# Observe after action a_t
		x_t, r_t, done, info = ENV.step(a_t)
			
		# Create state at t1: Append x observations, throw away the earliest
		s_t1 = np.concatenate((x_t, s_t[:(D-1) * INPUT_DIM,]), axis=0)
			
		# Estimate rewards for each action (targets), at s_t1 (again a forward pass)
		Q_sa = model.predict(s_t1[np.newaxis])[0]
			
		''' Create reference/targets by updating estimated reward for chosen action
			For action taken, replace estimated reward by remaining cumulative lifetime reward
		''' 
		targets = q
		targets[a_t] = r_t + GAMMA * np.max(Q_sa) if not done else r_t
			
		''' Learn!
			 - Again, predict q values for state s_t
			 - Calculate loss by comparing predictions to targets: they will differ only for the action taken
			- backpropagate error for action taken, update weights
		''' 
		model.fit(s_t[np.newaxis], targets[np.newaxis], nb_epoch=10, verbose=0)
			
		# Update states and times
		s_t = s_t1
		t += 1
		
		if r_t > 100: finalized_count += 1
		if r_t > 0: pos_count += 1
	
print D, t, pos_count/float(t+1), finalized_count