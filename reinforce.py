import torch
import torchvision
import numpy as np
import torch.nn.init as init
import torch.nn as nn
from collections import namedtuple
from features import *


number_of_actions = 6

actions_of_history = 4

visual_descriptor_size = 25088

reward_movement_action = 1

reward_terminal_action = 3

iou_threshold = 0.5

Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward'))


class ReplayMemory(object):

    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        self.position = 0

    def push(self, *args):
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = Transition(*args)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):
        return np.random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)


def get_state(image, history_vector, model_vgg):
    image_feature = get_conv_feature_for_image(image, model_vgg)
    image_feature = image_feature.view(1, -1)
    history_vector_flatten = history_vector.view(1, -1)
    state = torch.cat((image_feature, history_vector_flatten), 1)
    return state


def update_history_vector(history_vector, action):
    action_vector = torch.zeros(number_of_actions)
    action_vector[action - 1] = 1
    size_history_vector = len(torch.nonzero(history_vector))
    if size_history_vector < actions_of_history:
        history_vector[size_history_vector][action - 1] = 1
    else:
        for i in range(actions_of_history - 1, 0, -1):
            history_vector[i][:] = history_vector[i - 1][:]
        history_vector[0][:] = action_vector[:]
    return history_vector


def get_q_network(weights_path="0"):
    model = nn.Sequential(
        nn.Linear(25112, 1024),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(1024, 1024),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(1024, 6),
    )
    if weights_path != "0":
        model.load_state_dict(torch.load(weights_path))

    def weights_init(m):
        if isinstance(m, nn.Linear):
            init.xavier_normal(m.weight.data)

    model.apply(weights_init)
    return model


def get_reward_movement(iou, new_iou):
    if new_iou > iou:
        reward = reward_movement_action
    else:
        reward = - reward_movement_action
    return reward


def get_reward_trigger(new_iou):
    if new_iou > iou_threshold:
        reward = reward_terminal_action
    else:
        reward = - reward_terminal_action
    return reward