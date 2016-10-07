######## https://keras.io/getting-started/sequential-model-guide/#training

#!/usr/bin/python

import numpy as np
import gym
###NEW 
from collections import defaultdict, deque
###NEW 
from keras.layers import Dense
from keras.models import Sequential 

import sys
from future import print_function


D = 7
GAMMA = 0.99
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



TOTAL_TIME_STEPS = 1e4
TOTAL_EXPLORATION_STEPS = TOTAL_TIME_STEPS / 10
EPSILON_RANGE = [1, 0.01]
epsilon = EPSILON_RANGE[0]
###NEW### over all timesteps, we have memory
ERM_SIZE = TOTAL_EXPLORATION_STEPS # following the recommendation of dqn paper
ERM = deque(maxlen=ERM_SIZE) # nice use case for deque # If too long, throw away the earliest (latest is ERM[-1])
BATCH_SIZE = 32 # following the recommendation of dqn paper
###NEW###

model = _create_network(D)
t = pos_count = finalized_count = 0

while t <= TOTAL_TIME_STEPS:
	
	x_t = ENV.reset()
	s_t = np.tile(x_t, D)
	done = False
	
	while not done: 
		###ENV.render()
		loss = 0
		
		# Anneal epsilon over exploration timesteps
		epsilon = epsilon - epsilon / TOTAL_EXPLORATION_STEPS if epsilon > EPSILON_RANGE[1] else EPSILON_RANGE[1]
			
		# estimate rewards for each action (targets), at s_t
		q = model.predict(s_t[np.newaxis])[0]
		
		# Take action with highest estimated reward, epsilon greedy
		a_t = np.random.choice(ACTIONS, 1)[0] if np.random.random() <= epsilon else np.argmax(q) #argmax returns index
			
		# Observe after action a_t
		x_t, r_t, done, info = ENV.step(a_t)
			
		# Create state at t1: Append x observations, throw away the earliest
		s_t1 = np.concatenate((x_t, s_t[:(D-1) * INPUT_DIM,]), axis=0)
		
		###NEW### Store transition in experience replay memory
		ERM.append((s_t, a_t, r_t, s_t1)) # maxlen parametrization of deque will do the len cutting
		
		###NEW### Choose a batch of maximum length BATCH_SIZE
		minibatch = np.array([ ERM[i] for i in np.random.choice(np.arange(0, len(ERM)), min(len(ERM), BATCH_SIZE)) ])
		
		###NEW### Compute targets/reference for each transition in minibatch		
		inputs = deque()
		targets = deque()
		for m in minibatch:
			inputs.append(m[0]) # Append s_t of batch transition m to inputs
			m_q    = model.predict(m[0][np.newaxis])[0] # Estimate rewards for each action (targets), at s_t
			m_Q_sa = model.predict(m[3][np.newaxis])[0] # Estimate rewards for each action (targets), at s_t1 (again a forward pass)
			m_targets = m_q
			m_targets[m[1]] = m[2] + GAMMA * np.max(m_Q_sa)
			targets.append(m_targets) # Append target of batch transition m to targets
		###NEW### Train the model by backpropagating the errors and update weights
		loss += model.train_on_batch(np.array(inputs), np.array(targets))[0] # model.metrics_names: ['loss', 'acc']
		
		# Update states and times (the latter for bookkeeping only)
		s_t = s_t1
		t += 1
		
		if r_t > 100: finalized_count += 1
		if r_t > 0: pos_count += 1
		
		print(loss, end=' ')
		sys.stdout.flush()
	
	print D, t, loss, pos_count/float(t+1), finalized_count