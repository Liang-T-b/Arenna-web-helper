# -*- coding: utf-8 -*-
"""
    KingHonour Data production process
"""
import os
import time
import numpy as np
import copy

from rl_framework.common.logging import g_log_time, log_time, log_time_func
from rl_framework.common.logging import logger as LOG

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

target_hero_config_ids_list = [[169, 176, 128], [112, 119, 163],[174, 157, 167]]

######################################################################
# 【原始版本】
# class Actor:
#     def __init__(
#         self,
#         id,
#         agents,
#         env,
#         sample_manager,
#         camp_iter,
#         max_episode=-1,
#         monitor_logger=None,
#         send_sample_frame=963,
#     ):
#         self.m_config_id = id

#         self.agents = agents
#         self.env = env
#         self.sample_manager = sample_manager
#         self.camp_iter = camp_iter

#         self._max_episode = max_episode
#         self.monitor_logger = monitor_logger
#         self.send_sample_frame = send_sample_frame

#         self._episode_num = 0

#     @log_time("one_episode")
#     def _run_episode(self, camp_config):
#         LOG.info("Start a new game")
#         g_log_time.clear()

#         log_time_func("reset")
#         # swap two agents, and re-assign camp
#         self.agents.reverse()

#         for i, agent in enumerate(self.agents):
#             LOG.debug("reset agent {}".format(i))
#             agent.reset()

#         # restart a new game
#         use_common_ai = [agent.is_common_ai() for agent in self.agents]
#         self.env.reset(use_common_ai, camp_config)
#         first_frame_no = -1

#         # reset mem pool and models
#         self.sample_manager.reset()
#         log_time_func("reset", end=True)

#         game_info = {}
#         is_gameover = False
#         frame_state = None
#         reward_game = [[], []]

#         while not is_gameover:
#             log_time_func("one_frame")

#             continue_process = False
#             # while True:
#             is_send = False
#             reward_camp = [[], []]
#             for i, agent in enumerate(self.agents):
#                 if use_common_ai[i]:
#                     LOG.debug(f"agent {i} is common_ai")
#                     continue

#                 continue_process, features, frame_state = self.env.step_feature(i)

#                 if frame_state.frame_no == 90:
#                     print("Test!!!!!!!!!")

#                 if frame_state.gameover:
#                     game_info["length"] = frame_state.frame_no
#                     is_gameover = True

#                 if not continue_process:
#                     continue

#                 if first_frame_no < 0:
#                     first_frame_no = frame_state.frame_no
#                     LOG.info("first_frame_no %d" % first_frame_no)

#                 probs, lstm_info = agent.predict_process(features, frame_state)
#                 ok, results = self.env.step_action(i, probs, features, frame_state)
#                 if not ok:
#                     raise Exception("step action failed")

#                 sample = agent.sample_process(features, results, lstm_info, frame_state)

#                 reward_game[i].append(sample["reward_s"])

#                 # skip save sample if not latest model
#                 if not agent.is_latest_model:
#                     continue

#                 is_send = frame_state.gameover or (
#                     (
#                         (frame_state.frame_no - first_frame_no) % self.send_sample_frame
#                         == 0
#                     )
#                     and (frame_state.frame_no > first_frame_no)
#                 )

#                 if not is_send:
#                     self.sample_manager.save_sample(**sample, agent_id=i)
#                 else:
#                     LOG.info(
#                         f"save_last_sample frame[{frame_state.frame_no}] frame_state.gameover[{frame_state.gameover}]"
#                     )
#                     if frame_state.gameover:
#                         self.sample_manager.save_last_sample(
#                             agent_id=i, reward=sample["reward_s"]
#                         )
#                     else:
#                         self.sample_manager.save_last_sample(
#                             agent_id=i,
#                             reward=sample["reward_s"],
#                             value_s=sample["value_s"],
#                         )

#             if is_send or is_gameover:
#                 LOG.info("send_sample and update model")
#                 self.sample_manager.send_samples()
#                 self.sample_manager.reset()
#                 for i, agent in enumerate(self.agents):
#                     agent.update_model()
#                 LOG.info("send_sample and update model done.")
#         log_time_func("one_frame", end=True)
#         self.env.close_game()

#         if not frame_state:
#             return

#         # process game info
#         loss_camp = None
#         # update camp information.
#         for organ in frame_state.organ_list:
#             if organ.type == 24 and organ.hp <= 0:
#                 loss_camp = organ.camp

#             if organ.type in [21, 24]:
#                 LOG.info(
#                     "Tower {} in camp {}, hp: {}".format(
#                         organ.type, organ.camp, organ.hp
#                     )
#                 )

#         for i, agent in enumerate(self.agents):
#             agent_camp = i + 1
#             agent_win = 0
#             if (loss_camp is not None) and (agent_camp != loss_camp):
#                 agent_win = 1
#             LOG.info("camp%d_agent:%d win:%d" % (agent_camp, i, agent_win))

#             LOG.info("---------- camp%d hero_info ----------" % agent_camp)
#             for hero_state in frame_state.hero_list:
#                 if agent_camp != hero_state.camp:
#                     continue

#                 LOG.info(
#                     "hero:%d moneyCnt:%d killCnt:%d deadCnt:%d assistCnt:%d"
#                     % (
#                         hero_state.config_id,
#                         hero_state.moneyCnt,
#                         hero_state.killCnt,
#                         hero_state.deadCnt,
#                         hero_state.assistCnt,
#                     )
#                 )

#         if self.m_config_id == 0:
#             for i, agent in enumerate(self.agents):
#                 if not agent.keep_latest:
#                     continue

#                 money_per_frame = 0
#                 kill = 0
#                 death = 0
#                 assistCnt = 0
#                 hurt_per_frame = 0
#                 hurtH_per_frame = 0
#                 hurtBH_per_frame = 0
#                 totalHurtToHero = 0

#                 agent_camp = i + 1
#                 agent_win = 0
#                 if (loss_camp is not None) and (agent_camp != loss_camp):
#                     agent_win = 1

#                 hero_idx = 0
#                 for hero_state in frame_state.hero_list:
#                     if agent_camp == hero_state.camp:
#                         hero_idx += 1
#                         money_per_frame += hero_state.moneyCnt / game_info["length"]
#                         kill += hero_state.killCnt
#                         death += hero_state.deadCnt
#                         assistCnt += hero_state.assistCnt
#                         hurt_per_frame += hero_state.totalHurt / game_info["length"]
#                         hurtH_per_frame += (
#                             hero_state.totalHurtToHero / game_info["length"]
#                         )
#                         hurtBH_per_frame += (
#                             hero_state.totalBeHurtByHero / game_info["length"]
#                         )
#                         totalHurtToHero += hero_state.totalHurtToHero

#                 game_info["money_per_frame"] = money_per_frame / hero_idx
#                 game_info["kill"] = kill / hero_idx
#                 game_info["death"] = death / hero_idx
#                 game_info["assistCnt"] = assistCnt / hero_idx
#                 game_info["hurt_per_frame"] = hurt_per_frame / hero_idx
#                 game_info["hurtH_per_frame"] = hurtH_per_frame / hero_idx
#                 game_info["hurtBH_per_frame"] = hurtBH_per_frame / hero_idx
#                 game_info["win"] = agent_win
#                 game_info["reward"] = np.sum(reward_game[i])
#                 game_info["totalHurtToHero"] = totalHurtToHero / hero_idx

#             if self.monitor_logger:
#                 self.monitor_logger.info(game_info)

#     def run(self):
#         self._last_print_time = time.time()
#         self._episode_num = 0
#         MAX_REPEAT_ERR_NUM = 2
#         repeat_num = MAX_REPEAT_ERR_NUM

#         while True:
#             try:
#                 camp_config = next(self.camp_iter)
#                 self._run_episode(camp_config)
#                 self._episode_num += 1
#                 repeat_num = MAX_REPEAT_ERR_NUM
#             except Exception as e:
#                 LOG.exception(
#                     "_run_episode err: {}/{}".format(repeat_num, MAX_REPEAT_ERR_NUM)
#                 )
#                 repeat_num -= 1
#                 if repeat_num == 0:
#                     raise e

#             if 0 < self._max_episode <= self._episode_num:
#                 break


class Actor:
    def __init__(
            self,
            id,
            agents,
            env,
            sample_manager,
            camp_iter,
            max_episode=-1,
            monitor_logger=None,
            send_sample_frame=963,
    ):
        self.m_config_id = id

        self.agents = agents
        self.env = env
        self.sample_manager = sample_manager
        self.camp_iter = camp_iter

        self._max_episode = max_episode
        self.monitor_logger = monitor_logger
        self.send_sample_frame = send_sample_frame

        self._episode_num = 0

######################################################################
    # 【无归一化完整版本】
    # @log_time("one_episode")
    # def _run_episode(self, camp_config):
    #     LOG.info("Start a new game")
    #     g_log_time.clear()

    #     log_time_func("reset")
    #     # swap two agents, and re-assign camp
    #     self.agents.reverse()  # 倒转agents

    #     for i, agent in enumerate(self.agents):
    #         LOG.debug("reset agent {}".format(i))
    #         agent.reset()

    #     # restart a new game
    #     use_common_ai = [agent.is_common_ai() for agent in self.agents]
    #     self.env.reset(use_common_ai, camp_config)
    #     first_frame_no = -1

    #     # reset mem pool and models
    #     self.sample_manager.reset()
    #     log_time_func("reset", end=True)

    #     game_info = {}
    #     is_gameover = False
    #     frame_state = None
    #     reward_game = [[], []]

    #     # 初始化对方的frame_state
    #     frame_state_op = None
    #     features_op = None

    #     while not is_gameover:
    #         log_time_func("one_frame")

    #         continue_process = False
    #         # while True:
    #         is_send = False
    #         reward_camp = [[], []]

    #         # 遍历所有智能体
    #         for i, agent in enumerate(self.agents):
    #             if use_common_ai[i]:
    #                 LOG.debug(f"agent {i} is common_ai")
    #                 continue

    #             # 返回下一帧的状态
    #             continue_process, features, frame_state = self.env.step_feature(i)

    #             # 【获得隐藏信息】
    #             for idx, feature in enumerate(features):

    #                 # 获取当前英雄的信息，用于计算相对位置
    #                 cur_camp_id = feature.camp_id
    #                 cur_runtime_id = feature.hero_runtime_id
    #                 cur_x = 10000
    #                 cur_z = 10000
    #                 for hero_item in frame_state.hero_list:
    #                     if hero_item.runtime_id == cur_runtime_id:
    #                         cur_x = hero_item.location.x
    #                         cur_z = hero_item.location.z

    #                 # 在原本feature的基础上，添加invisible info
    #                 if frame_state_op is None or len(features_op) == 0:  # 39 + 180 = 219
    #                     # 如果为None，则全部重置为0
    #                     feature_invisible = [0] * 219  # TODO 维度需要修改
    #                 elif features_op[0].camp_id == cur_camp_id:
    #                     feature_invisible = [0] * 219  # TODO 维度需要修改
    #                 else:
    #                     feature_invisible = []  # 初始化一下
    #                     # 英雄信息
    #                     for hero_item in frame_state_op.hero_list:
    #                         if hero_item.camp.value != cur_camp_id:  # 敌方 13*3
    #                             hero_item_info = [hero_item.config_id,
    #                                               hero_item.atk_spd,
    #                                               hero_item.crit_effe,
    #                                               hero_item.crit_rate,
    #                                               hero_item.ep,
    #                                               hero_item.ep_recover,
    #                                               hero_item.hp,
    #                                               hero_item.hp_recover,
    #                                               hero_item.mov_spd,
    #                                               hero_item.location.x,
    #                                               hero_item.location.z,
    #                                               hero_item.location.x - cur_x,
    #                                               hero_item.location.z - cur_z,
    #                                               ]
    #                             feature_invisible.extend(hero_item_info)
    #                     # 士兵信息
    #                     soldier_cnt = 0
    #                     for soldier_item in frame_state_op.soldier_list:  # 6*10
    #                         if soldier_item.camp.value != cur_camp_id and soldier_cnt < 10:
    #                             soldier_item_info = [soldier_item.config_id,
    #                                                  soldier_item.hp,
    #                                                  soldier_item.location.x,
    #                                                  soldier_item.location.z,
    #                                                  soldier_item.location.x - cur_x,
    #                                                  soldier_item.location.z - cur_z]
    #                             feature_invisible.extend(soldier_item_info)
    #                             soldier_cnt += 1
    #                     while soldier_cnt < 10:
    #                         feature_invisible.extend([0, 0, 0, 0, 0, 0])
    #                         soldier_cnt += 1
    #                     # 野怪信息
    #                     monster_cnt = 0
    #                     for monster_item in frame_state.monster_list:  # 6*20
    #                         if monster_cnt < 20:
    #                             monster_item_info = [monster_item.config_id,
    #                                                 monster_item.hp,
    #                                                 monster_item.location.x,
    #                                                 monster_item.location.z,
    #                                                 monster_item.location.x - cur_x,
    #                                                 monster_item.location.z - cur_z]
    #                             feature_invisible.extend(monster_item_info)
    #                             monster_cnt += 1
    #                     while monster_cnt < 20:
    #                         feature_invisible.extend([0, 0, 0, 0, 0, 0])
    #                         monster_cnt += 1

    #                 # features[idx].feature = features[idx].feature.extend(feature_invisible) # 给每个英雄进行扩充


    #             # 更新对方的信息，在训练阶段，可以获得对方的信息，在对战测试阶段，无法获得敌方的信息
    #             features_op = features  # 更新对方的features_op
    #             frame_state_op = frame_state  # 更新对方的frame_state_op

    #             if frame_state.gameover:
    #                 game_info["length"] = frame_state.frame_no
    #                 is_gameover = True

    #             if not continue_process:
    #                 continue

    #             if first_frame_no < 0:
    #                 first_frame_no = frame_state.frame_no
    #                 LOG.info("first_frame_no %d" % first_frame_no)

    #             # 智能体预测
    #             probs, lstm_info = agent.predict_process(features, frame_state, feature_invisible)

    #             # 在环境中执行对应动作
    #             ok, results = self.env.step_action(i, probs, features, frame_state)
    #             if not ok:
    #                 raise Exception("step action failed")

    #             # 获取样本
    #             sample = agent.sample_process(features, results, lstm_info, frame_state, feature_invisible)

    #             reward_game[i].append(sample["reward_s"])

    #             # skip save sample if not latest model
    #             if not agent.is_latest_model:
    #                 continue

    #             is_send = frame_state.gameover or (
    #                     (
    #                             (frame_state.frame_no - first_frame_no) % self.send_sample_frame
    #                             == 0
    #                     )
    #                     and (frame_state.frame_no > first_frame_no)
    #             )

    #             if not is_send:
    #                 self.sample_manager.save_sample(**sample, agent_id=i)
    #             else:
    #                 LOG.info(
    #                     f"save_last_sample frame[{frame_state.frame_no}] frame_state.gameover[{frame_state.gameover}]"
    #                 )
    #                 if frame_state.gameover:
    #                     self.sample_manager.save_last_sample(
    #                         agent_id=i, reward=sample["reward_s"]
    #                     )
    #                 else:
    #                     self.sample_manager.save_last_sample(
    #                         agent_id=i,
    #                         reward=sample["reward_s"],
    #                         value_s=sample["value_s"],
    #                     )

    #         if is_send or is_gameover:
    #             LOG.info("send_sample and update model")
    #             self.sample_manager.send_samples()
    #             self.sample_manager.reset()
    #             for i, agent in enumerate(self.agents):
    #                 agent.update_model()
    #             LOG.info("send_sample and update model done.")
    #     log_time_func("one_frame", end=True)
    #     self.env.close_game()

    #     if not frame_state:
    #         return

    #     # process game info
    #     loss_camp = None

    #     # update camp information.
    #     # 塔信息
    #     for organ in frame_state.organ_list:
    #         if organ.type == 24 and organ.hp <= 0:
    #             loss_camp = organ.camp

    #         if organ.type in [21, 24]:
    #             LOG.info(
    #                 "Tower {} in camp {}, hp: {}".format(
    #                     organ.type, organ.camp, organ.hp
    #                 )
    #             )

    #     for i, agent in enumerate(self.agents):
    #         agent_camp = i + 1
    #         agent_win = 0
    #         if (loss_camp is not None) and (agent_camp != loss_camp):
    #             agent_win = 1
    #         LOG.info("camp%d_agent:%d win:%d" % (agent_camp, i, agent_win))

    #         LOG.info("---------- camp%d hero_info ----------" % agent_camp)
    #         for hero_state in frame_state.hero_list:
    #             if agent_camp != hero_state.camp:
    #                 continue

    #             LOG.info(
    #                 "hero:%d moneyCnt:%d killCnt:%d deadCnt:%d assistCnt:%d"
    #                 % (
    #                     hero_state.config_id,
    #                     hero_state.moneyCnt,
    #                     hero_state.killCnt,
    #                     hero_state.deadCnt,
    #                     hero_state.assistCnt,
    #                 )
    #             )

    #     if self.m_config_id == 0:
    #         for i, agent in enumerate(self.agents):
    #             if not agent.keep_latest:  # 最新智能体
    #                 continue

    #             money_per_frame = 0
    #             kill = 0
    #             death = 0
    #             assistCnt = 0
    #             hurt_per_frame = 0
    #             hurtH_per_frame = 0
    #             hurtBH_per_frame = 0
    #             totalHurtToHero = 0

    #             agent_camp = i + 1
    #             agent_win = 0
    #             if (loss_camp is not None) and (agent_camp != loss_camp):
    #                 agent_win = 1

    #             hero_idx = 0
    #             for hero_state in frame_state.hero_list:
    #                 if agent_camp == hero_state.camp:
    #                     hero_idx += 1
    #                     money_per_frame += hero_state.moneyCnt / game_info["length"]
    #                     kill += hero_state.killCnt
    #                     death += hero_state.deadCnt
    #                     assistCnt += hero_state.assistCnt
    #                     hurt_per_frame += hero_state.totalHurt / game_info["length"]
    #                     hurtH_per_frame += (
    #                             hero_state.totalHurtToHero / game_info["length"]
    #                     )
    #                     hurtBH_per_frame += (
    #                             hero_state.totalBeHurtByHero / game_info["length"]
    #                     )
    #                     totalHurtToHero += hero_state.totalHurtToHero

    #             game_info["money_per_frame"] = money_per_frame / hero_idx
    #             game_info["kill"] = kill / hero_idx
    #             game_info["death"] = death / hero_idx
    #             game_info["assistCnt"] = assistCnt / hero_idx
    #             game_info["hurt_per_frame"] = hurt_per_frame / hero_idx
    #             game_info["hurtH_per_frame"] = hurtH_per_frame / hero_idx
    #             game_info["hurtBH_per_frame"] = hurtBH_per_frame / hero_idx
    #             game_info["win"] = agent_win
    #             game_info["reward"] = np.sum(reward_game[i])
    #             game_info["totalHurtToHero"] = totalHurtToHero / hero_idx

    #         if self.monitor_logger:
    #             self.monitor_logger.info(game_info)


######################################################################
    # 【完整版本+修改隐藏信息的bug+适应对战】
    # @log_time("one_episode")
    # def _run_episode(self, camp_config):
    #     LOG.info("Start a new game")
    #     g_log_time.clear()

    #     log_time_func("reset")
    #     # swap two agents, and re-assign camp
    #     self.agents.reverse()  # 倒转agents

    #     for i, agent in enumerate(self.agents):
    #         LOG.debug("reset agent {}".format(i))
    #         agent.reset()

    #     # restart a new game
    #     use_common_ai = [agent.is_common_ai() for agent in self.agents]
    #     self.env.reset(use_common_ai, camp_config)
    #     first_frame_no = -1

    #     # reset mem pool and models
    #     self.sample_manager.reset()
    #     log_time_func("reset", end=True)

    #     game_info = {}
    #     is_gameover = False
    #     frame_state = None
    #     reward_game = [[], []]

    #     # 初始化对方的frame_state
    #     frame_state_op = None
    #     features_op = None

    #     while not is_gameover:
    #         log_time_func("one_frame")

    #         continue_process = False
    #         # while True:
    #         is_send = False
    #         reward_camp = [[], []]

    #         # 遍历所有智能体
    #         for i, agent in enumerate(self.agents):
    #             if use_common_ai[i]:
    #                 LOG.debug(f"agent {i} is common_ai")
    #                 continue

    #             # 返回下一帧的状态
    #             continue_process, features, frame_state = self.env.step_feature(i)

    #             # 【获得隐藏信息】
    #             feature_invisible_list = []
    #             for idx, feature in enumerate(features):

    #                 # 获取当前英雄的信息，用于计算相对位置
    #                 cur_camp_id = feature.camp_id
    #                 cur_runtime_id = feature.hero_runtime_id
    #                 cur_x = 10000
    #                 cur_z = 10000
    #                 for hero_item in frame_state.hero_list:
    #                     if hero_item.runtime_id == cur_runtime_id:
    #                         cur_x = hero_item.location.x
    #                         cur_z = hero_item.location.z

    #                 # 在原本feature的基础上，添加invisible info
    #                 if frame_state_op is None or len(features_op) == 0:  # 39 + 180 = 219
    #                     # 如果为None，则全部重置为0
    #                     feature_invisible = [0] * 219  # TODO 维度需要修改
    #                 elif features_op[0].camp_id == cur_camp_id:
    #                     feature_invisible = [0] * 219  # TODO 维度需要修改
    #                 else:
    #                     feature_invisible = []  # 初始化一下
    #                     # 英雄信息
    #                     for hero_item in frame_state_op.hero_list:
    #                         if hero_item.camp.value != cur_camp_id:  # 敌方 13*3
    #                             hero_item_info = [hero_item.config_id / 300.0,
    #                                               hero_item.atk_spd / 5000.0,
    #                                               hero_item.crit_effe / 50000.0,
    #                                               hero_item.crit_rate / 10000.0,
    #                                               hero_item.ep / 200.0,
    #                                               hero_item.ep_recover / 100.0,
    #                                               hero_item.hp / 5000.0,
    #                                               hero_item.hp_recover / 200.0,
    #                                               hero_item.mov_spd / 10000.0,
    #                                               hero_item.location.x / 20000.0,
    #                                               hero_item.location.z / 20000.0,
    #                                               (hero_item.location.x - cur_x) / 20000.0,
    #                                               (hero_item.location.z - cur_z) / 20000.0,
    #                                               ]
    #                             feature_invisible.extend(hero_item_info)
    #                     # 士兵信息
    #                     soldier_cnt = 0
    #                     for soldier_item in frame_state_op.soldier_list:  # 6*10
    #                         if soldier_item.camp.value != cur_camp_id and soldier_cnt < 10:
    #                             soldier_item_info = [soldier_item.config_id / 300.0,
    #                                                  soldier_item.hp / 5000.0,
    #                                                  soldier_item.location.x / 20000.0,
    #                                                  soldier_item.location.z / 20000.0,
    #                                                  (soldier_item.location.x - cur_x) / 20000.0,
    #                                                  (soldier_item.location.z - cur_z) / 20000.0]
    #                             feature_invisible.extend(soldier_item_info)
    #                             soldier_cnt += 1
    #                     while soldier_cnt < 10:
    #                         feature_invisible.extend([0, 0, 0, 0, 0, 0])
    #                         soldier_cnt += 1
    #                     # 野怪信息
    #                     monster_cnt = 0
    #                     for monster_item in frame_state.monster_list:  # 6*20
    #                         if monster_cnt < 20:
    #                             monster_item_info = [monster_item.config_id / 300.0,
    #                                                  monster_item.hp / 5000.0,
    #                                                  monster_item.location.x / 20000.0,
    #                                                  monster_item.location.z / 20000.0,
    #                                                  (monster_item.location.x - cur_x) / 20000.0,
    #                                                  (monster_item.location.z - cur_z) / 20000.0]
    #                             feature_invisible.extend(monster_item_info)
    #                             monster_cnt += 1
    #                     while monster_cnt < 20:
    #                         feature_invisible.extend([0, 0, 0, 0, 0, 0])
    #                         monster_cnt += 1

    #                 # features[idx].feature = features[idx].feature.extend(feature_invisible) # 给每个英雄进行扩充
    #                 feature_invisible_list.append(feature_invisible)

    #             # 更新对方的信息，在训练阶段，可以获得对方的信息，在对战测试阶段，无法获得敌方的信息
    #             features_op = features  # 更新对方的features_op
    #             frame_state_op = frame_state  # 更新对方的frame_state_op

    #             if frame_state.gameover:
    #                 game_info["length"] = frame_state.frame_no
    #                 is_gameover = True

    #             if not continue_process:
    #                 continue

    #             if first_frame_no < 0:
    #                 first_frame_no = frame_state.frame_no
    #                 LOG.info("first_frame_no %d" % first_frame_no)

    #             # 智能体预测
    #             probs, lstm_info = agent.predict_process(features, frame_state, feature_invisible_list)

    #             # 在环境中执行对应动作
    #             ok, results = self.env.step_action(i, probs, features, frame_state)
    #             if not ok:
    #                 raise Exception("step action failed")

    #             # 获取样本
    #             sample = agent.sample_process(features, results, lstm_info, frame_state, feature_invisible_list)

    #             reward_game[i].append(sample["reward_s"])

    #             # skip save sample if not latest model
    #             if not agent.is_latest_model:
    #                 continue

    #             is_send = frame_state.gameover or (
    #                     (
    #                             (frame_state.frame_no - first_frame_no) % self.send_sample_frame
    #                             == 0
    #                     )
    #                     and (frame_state.frame_no > first_frame_no)
    #             )

    #             if not is_send:
    #                 self.sample_manager.save_sample(**sample, agent_id=i)
    #             else:
    #                 LOG.info(
    #                     f"save_last_sample frame[{frame_state.frame_no}] frame_state.gameover[{frame_state.gameover}]"
    #                 )
    #                 if frame_state.gameover:
    #                     self.sample_manager.save_last_sample(
    #                         agent_id=i, reward=sample["reward_s"]
    #                     )
    #                 else:
    #                     self.sample_manager.save_last_sample(
    #                         agent_id=i,
    #                         reward=sample["reward_s"],
    #                         value_s=sample["value_s"],
    #                     )

    #         if is_send or is_gameover:
    #             LOG.info("send_sample and update model")
    #             self.sample_manager.send_samples()
    #             self.sample_manager.reset()
    #             for i, agent in enumerate(self.agents):
    #                 agent.update_model()
    #             LOG.info("send_sample and update model done.")
    #     log_time_func("one_frame", end=True)
    #     self.env.close_game()

    #     if not frame_state:
    #         return

    #     # process game info
    #     loss_camp = None

    #     # update camp information.
    #     # 塔信息
    #     for organ in frame_state.organ_list:
    #         if organ.type == 24 and organ.hp <= 0:
    #             loss_camp = organ.camp

    #         if organ.type in [21, 24]:
    #             LOG.info(
    #                 "Tower {} in camp {}, hp: {}".format(
    #                     organ.type, organ.camp, organ.hp
    #                 )
    #             )

    #     for i, agent in enumerate(self.agents):
    #         agent_camp = i + 1
    #         agent_win = 0
    #         if (loss_camp is not None) and (agent_camp != loss_camp):
    #             agent_win = 1
    #         LOG.info("camp%d_agent:%d win:%d" % (agent_camp, i, agent_win))

    #         LOG.info("---------- camp%d hero_info ----------" % agent_camp)
    #         for hero_state in frame_state.hero_list:
    #             if agent_camp != hero_state.camp:
    #                 continue

    #             LOG.info(
    #                 "hero:%d moneyCnt:%d killCnt:%d deadCnt:%d assistCnt:%d"
    #                 % (
    #                     hero_state.config_id,
    #                     hero_state.moneyCnt,
    #                     hero_state.killCnt,
    #                     hero_state.deadCnt,
    #                     hero_state.assistCnt,
    #                 )
    #             )

    #     if self.m_config_id == 0:
    #         for i, agent in enumerate(self.agents):
    #             if not agent.keep_latest:  # 最新智能体
    #                 continue

    #             money_per_frame = 0
    #             kill = 0
    #             death = 0
    #             assistCnt = 0
    #             hurt_per_frame = 0
    #             hurtH_per_frame = 0
    #             hurtBH_per_frame = 0
    #             totalHurtToHero = 0

    #             agent_camp = i + 1
    #             agent_win = 0
    #             if (loss_camp is not None) and (agent_camp != loss_camp):
    #                 agent_win = 1

    #             hero_idx = 0
    #             for hero_state in frame_state.hero_list:
    #                 if agent_camp == hero_state.camp:
    #                     hero_idx += 1
    #                     money_per_frame += hero_state.moneyCnt / game_info["length"]
    #                     kill += hero_state.killCnt
    #                     death += hero_state.deadCnt
    #                     assistCnt += hero_state.assistCnt
    #                     hurt_per_frame += hero_state.totalHurt / game_info["length"]
    #                     hurtH_per_frame += (
    #                             hero_state.totalHurtToHero / game_info["length"]
    #                     )
    #                     hurtBH_per_frame += (
    #                             hero_state.totalBeHurtByHero / game_info["length"]
    #                     )
    #                     totalHurtToHero += hero_state.totalHurtToHero

    #             game_info["money_per_frame"] = money_per_frame / hero_idx
    #             game_info["kill"] = kill / hero_idx
    #             game_info["death"] = death / hero_idx
    #             game_info["assistCnt"] = assistCnt / hero_idx
    #             game_info["hurt_per_frame"] = hurt_per_frame / hero_idx
    #             game_info["hurtH_per_frame"] = hurtH_per_frame / hero_idx
    #             game_info["hurtBH_per_frame"] = hurtBH_per_frame / hero_idx
    #             game_info["win"] = agent_win
    #             game_info["reward"] = np.sum(reward_game[i])
    #             game_info["totalHurtToHero"] = totalHurtToHero / hero_idx

    #         if self.monitor_logger:
    #             self.monitor_logger.info(game_info)

######################################################################
    # 【完整版本+修改隐藏信息的bug+适应对战+加强隐藏信息】
    @log_time("one_episode")
    def _run_episode(self, camp_config):
        LOG.info("Start a new game")
        g_log_time.clear()

        log_time_func("reset")
        # swap two agents, and re-assign camp
        self.agents.reverse()  # 倒转agents

        for i, agent in enumerate(self.agents):
            LOG.debug("reset agent {}".format(i))
            agent.reset()

        # restart a new game
        use_common_ai = [agent.is_common_ai() for agent in self.agents]
        self.env.reset(use_common_ai, camp_config)
        first_frame_no = -1

        # reset mem pool and models
        self.sample_manager.reset()
        log_time_func("reset", end=True)

        game_info = {}
        is_gameover = False
        frame_state = None
        reward_game = [[], []]

        # 初始化对方的frame_state
        frame_state_op = None
        features_op = None
        legal_action_dict={}

        while not is_gameover:
            log_time_func("one_frame")

            continue_process = False
            # while True:
            is_send = False
            reward_camp = [[], []]

            # 遍历所有智能体
            for i, agent in enumerate(self.agents):
                if use_common_ai[i]:
                    LOG.debug(f"agent {i} is common_ai")
                    continue

                

                # 返回下一帧的状态
                continue_process, features, frame_state = self.env.step_feature(i)
                


            

                # 【获得隐藏信息】
                feature_invisible = []
                if frame_state_op is None or len(features_op) == 0:  # 39 + 180 = 219
                    # 如果为None，则全部重置为0
                    feature_invisible = [0] * 4821  # TODO 维度需要修改
                elif features_op[0].camp_id == features[0].camp_id:
                    feature_invisible = [0] * 4821  # TODO 维度需要修改
                else:
                    for feature in features_op: # 3 * 1607
                        cur_feature = feature.feature
                        VecFeatureHero = cur_feature[1734: 2487]  # 敌方英雄特征 251*3 = 753
                        MainHeroFeature = cur_feature[3240: 3284]  # 英雄特征 44
                        VecSolider = cur_feature[3284: 3534]  # 士兵特征 10*25 = 250
                        VecMonster = cur_feature[3958: 4518]  # 野怪特征 20*28 = 560
                        feature_invisible.extend(VecFeatureHero)
                        feature_invisible.extend(MainHeroFeature)
                        feature_invisible.extend(VecSolider)
                        feature_invisible.extend(VecMonster)
                feature_invisible_list = [feature_invisible, feature_invisible, feature_invisible]

                # 更新对方的信息，在训练阶段，可以获得对方的信息，在对战测试阶段，无法获得敌方的信息
                features_op = features  # 更新对方的features_op
                frame_state_op = frame_state  # 更新对方的frame_state_op

                if frame_state.gameover:
                    game_info["length"] = frame_state.frame_no
                    is_gameover = True

                if not continue_process:
                    continue

                if first_frame_no < 0:
                    first_frame_no = frame_state.frame_no
                    LOG.info("first_frame_no %d" % first_frame_no)
                
                # 智能体预测
                game_id_value = legal_action_dict.setdefault(frame_state.sgame_id, None)
                probs, lstm_info = agent.predict_process(features, frame_state, feature_invisible_list,legal_action_dict[frame_state.sgame_id])

                # 在环境中执行对应动作
                ok, results = self.env.step_action(i, probs, features, frame_state)
                def handle_results(results):
                    legal_action_list=[]
                    for result in results:
                        action_type=result.actions[0]
                        legal_action=result.legal_action[0]
                        if int(action_type) in range(4,9):
                            legal_action[int(action_type)]=0.0
                        legal_action_list.append(legal_action)
                    return legal_action_list
                legal_action_dict[frame_state.sgame_id]=handle_results(results)

                        
                            

                # k=True
                # if k:
                #     game_id=frame_state.sgame_id
                #     k=False
                # if frame_state.sgame_id== game_id:
                #     print(game_id)
                #     print(results[0].actions)
                #     print(results[0].legal_action[0])
                #     if results[0].actions[0] in range(4,9):
                #         zk=1
                if not ok:
                    raise Exception("step action failed")

                # 获取样本
                sample = agent.sample_process(features, results, lstm_info, frame_state, feature_invisible_list)

                reward_game[i].append(sample["reward_s"])

                # skip save sample if not latest model
                if not agent.is_latest_model:
                    continue

                is_send = frame_state.gameover or (
                        (
                                (frame_state.frame_no - first_frame_no) % self.send_sample_frame
                                == 0
                        )
                        and (frame_state.frame_no > first_frame_no)
                )

                if not is_send:
                    self.sample_manager.save_sample(**sample, agent_id=i)
                else:
                    LOG.info(
                        f"save_last_sample frame[{frame_state.frame_no}] frame_state.gameover[{frame_state.gameover}]"
                    )
                    if frame_state.gameover:
                        self.sample_manager.save_last_sample(
                            agent_id=i, reward=sample["reward_s"]
                        )
                    else:
                        self.sample_manager.save_last_sample(
                            agent_id=i,
                            reward=sample["reward_s"],
                            value_s=sample["value_s"],
                        )

            if is_send or is_gameover:
                LOG.info("send_sample and update model")
                self.sample_manager.send_samples()
                self.sample_manager.reset()
                for i, agent in enumerate(self.agents):
                    agent.update_model()
                LOG.info("send_sample and update model done.")
        log_time_func("one_frame", end=True)
        self.env.close_game()

        if not frame_state:
            return

        # process game info
        loss_camp = None

        # update camp information.
        # 塔信息
        for organ in frame_state.organ_list:
            if organ.type == 24 and organ.hp <= 0:
                loss_camp = organ.camp

            if organ.type in [21, 24]:
                LOG.info(
                    "Tower {} in camp {}, hp: {}".format(
                        organ.type, organ.camp, organ.hp
                    )
                )

        for i, agent in enumerate(self.agents):
            agent_camp = i + 1
            agent_win = 0
            if (loss_camp is not None) and (agent_camp != loss_camp):
                agent_win = 1
            LOG.info("camp%d_agent:%d win:%d" % (agent_camp, i, agent_win))

            LOG.info("---------- camp%d hero_info ----------" % agent_camp)
            for hero_state in frame_state.hero_list:
                if agent_camp != hero_state.camp:
                    continue

                LOG.info(
                    "hero:%d moneyCnt:%d killCnt:%d deadCnt:%d assistCnt:%d"
                    % (
                        hero_state.config_id,
                        hero_state.moneyCnt,
                        hero_state.killCnt,
                        hero_state.deadCnt,
                        hero_state.assistCnt,
                    )
                )

        if self.m_config_id == 0:
            for i, agent in enumerate(self.agents):
                if not agent.keep_latest:  # 最新智能体
                    continue

                money_per_frame = 0
                kill = 0
                death = 0
                assistCnt = 0
                hurt_per_frame = 0
                hurtH_per_frame = 0
                hurtBH_per_frame = 0
                totalHurtToHero = 0

                agent_camp = i + 1
                agent_win = 0
                if (loss_camp is not None) and (agent_camp != loss_camp):
                    agent_win = 1

                hero_idx = 0
                for hero_state in frame_state.hero_list:
                    if agent_camp == hero_state.camp:
                        hero_idx += 1
                        money_per_frame += hero_state.moneyCnt / game_info["length"]
                        kill += hero_state.killCnt
                        death += hero_state.deadCnt
                        assistCnt += hero_state.assistCnt
                        hurt_per_frame += hero_state.totalHurt / game_info["length"]
                        hurtH_per_frame += (
                                hero_state.totalHurtToHero / game_info["length"]
                        )
                        hurtBH_per_frame += (
                                hero_state.totalBeHurtByHero / game_info["length"]
                        )
                        totalHurtToHero += hero_state.totalHurtToHero

                game_info["money_per_frame"] = money_per_frame / hero_idx
                game_info["kill"] = kill / hero_idx
                game_info["death"] = death / hero_idx
                game_info["assistCnt"] = assistCnt / hero_idx
                game_info["hurt_per_frame"] = hurt_per_frame / hero_idx
                game_info["hurtH_per_frame"] = hurtH_per_frame / hero_idx
                game_info["hurtBH_per_frame"] = hurtBH_per_frame / hero_idx
                game_info["win"] = agent_win
                game_info["reward"] = np.sum(reward_game[i])
                game_info["totalHurtToHero"] = totalHurtToHero / hero_idx

            if self.monitor_logger:
                self.monitor_logger.info(game_info)


######################################################################
# 【完整版本+修改隐藏信息的bug+适应对战+加强隐藏信息】
    # @log_time("one_episode")
    # def _run_episode(self, camp_config):
    #     LOG.info("Start a new game")
    #     g_log_time.clear()

    #     log_time_func("reset")
    #     # swap two agents, and re-assign camp
    #     self.agents.reverse()  # 倒转agents

    #     for i, agent in enumerate(self.agents):
    #         LOG.debug("reset agent {}".format(i))
    #         agent.reset()

    #     # restart a new game
    #     use_common_ai = [agent.is_common_ai() for agent in self.agents]
    #     self.env.reset(use_common_ai, camp_config)
    #     first_frame_no = -1

    #     # reset mem pool and models
    #     self.sample_manager.reset()
    #     log_time_func("reset", end=True)

    #     game_info = {}
    #     is_gameover = False
    #     frame_state = None
    #     reward_game = [[], []]

    #     # 初始化对方的frame_state
    #     frame_state_op = None
    #     features_op = None

    #     while not is_gameover:
    #         log_time_func("one_frame")

    #         continue_process = False
    #         # while True:
    #         is_send = False
    #         reward_camp = [[], []]

    #         # 遍历所有智能体
    #         for i, agent in enumerate(self.agents):
    #             if use_common_ai[i]:
    #                 LOG.debug(f"agent {i} is common_ai")
    #                 continue

    #             # 返回下一帧的状态
    #             continue_process, features, frame_state = self.env.step_feature(i)

    #             # 【获得隐藏信息】
    #             feature_invisible = []
    #             if frame_state_op is None or len(features_op) == 0:  # 39 + 180 = 219
    #                 # 如果为None，则全部重置为0
    #                 feature_invisible = [0] * 4821  # TODO 维度需要修改
    #             elif features_op[0].camp_id == features[0].camp_id:
    #                 feature_invisible = [0] * 4821  # TODO 维度需要修改
    #             else:
    #                 for feature in features_op:  # 3 * 1607
    #                     cur_feature = feature.feature
    #                     VecFeatureHero = cur_feature[1734: 2487]  # 敌方英雄特征 251*3 = 753
    #                     MainHeroFeature = cur_feature[3240: 3284]  # 英雄特征 44
    #                     VecSolider = cur_feature[3284: 3534]  # 士兵特征 10*25 = 250
    #                     VecMonster = cur_feature[3958: 4518]  # 野怪特征 20*28 = 560
    #                     feature_invisible.extend(VecFeatureHero)
    #                     feature_invisible.extend(MainHeroFeature)
    #                     feature_invisible.extend(VecSolider)
    #                     feature_invisible.extend(VecMonster)
    #             feature_invisible_list = [feature_invisible, feature_invisible, feature_invisible]

    #             # 更新对方的信息，在训练阶段，可以获得对方的信息，在对战测试阶段，无法获得敌方的信息
    #             features_op = features  # 更新对方的features_op
    #             frame_state_op = frame_state  # 更新对方的frame_state_op

    #             if frame_state.gameover:
    #                 game_info["length"] = frame_state.frame_no
    #                 is_gameover = True

    #             if not continue_process:
    #                 continue

    #             if first_frame_no < 0:
    #                 first_frame_no = frame_state.frame_no
    #                 LOG.info("first_frame_no %d" % first_frame_no)

    #             # 智能体预测
    #             probs, lstm_info = agent.predict_process(features, frame_state, feature_invisible_list)

    #             # 在环境中执行对应动作
    #             ok, results = self.env.step_action(i, probs, features, frame_state)
    #             if not ok:
    #                 raise Exception("step action failed")

    #             # 获取样本
    #             sample = agent.sample_process(features, results, lstm_info, frame_state, feature_invisible_list)

    #             reward_game[i].append(sample["reward_s"])

    #             # skip save sample if not latest model
    #             if not agent.is_latest_model:
    #                 continue

    #             is_send = frame_state.gameover or (
    #                     (
    #                             (frame_state.frame_no - first_frame_no) % self.send_sample_frame
    #                             == 0
    #                     )
    #                     and (frame_state.frame_no > first_frame_no)
    #             )

    #             if not is_send:
    #                 self.sample_manager.save_sample(**sample, agent_id=i)
    #             else:
    #                 LOG.info(
    #                     f"save_last_sample frame[{frame_state.frame_no}] frame_state.gameover[{frame_state.gameover}]"
    #                 )
    #                 if frame_state.gameover:
    #                     self.sample_manager.save_last_sample(
    #                         agent_id=i, reward=sample["reward_s"]
    #                     )
    #                 else:
    #                     self.sample_manager.save_last_sample(
    #                         agent_id=i,
    #                         reward=sample["reward_s"],
    #                         value_s=sample["value_s"],
    #                     )

    #         if is_send or is_gameover:
    #             LOG.info("send_sample and update model")
    #             self.sample_manager.send_samples()
    #             self.sample_manager.reset()
    #             for i, agent in enumerate(self.agents):
    #                 agent.update_model()
    #             LOG.info("send_sample and update model done.")
    #     log_time_func("one_frame", end=True)
    #     self.env.close_game()

    #     if not frame_state:
    #         return

    #     # process game info
    #     loss_camp = None

    #     # update camp information.
    #     # 塔信息
    #     for organ in frame_state.organ_list:
    #         if organ.type == 24 and organ.hp <= 0:
    #             loss_camp = organ.camp

    #         if organ.type in [21, 24]:
    #             LOG.info(
    #                 "Tower {} in camp {}, hp: {}".format(
    #                     organ.type, organ.camp, organ.hp
    #                 )
    #             )

    #     for i, agent in enumerate(self.agents):
    #         agent_camp = i + 1
    #         agent_win = 0
    #         if (loss_camp is not None) and (agent_camp != loss_camp):
    #             agent_win = 1
    #         LOG.info("camp%d_agent:%d win:%d" % (agent_camp, i, agent_win))

    #         LOG.info("---------- camp%d hero_info ----------" % agent_camp)
    #         for hero_state in frame_state.hero_list:
    #             if agent_camp != hero_state.camp:
    #                 continue

    #             LOG.info(
    #                 "hero:%d moneyCnt:%d killCnt:%d deadCnt:%d assistCnt:%d"
    #                 % (
    #                     hero_state.config_id,
    #                     hero_state.moneyCnt,
    #                     hero_state.killCnt,
    #                     hero_state.deadCnt,
    #                     hero_state.assistCnt,
    #                 )
    #             )

    #     if self.m_config_id == 0:
    #         for i, agent in enumerate(self.agents):
    #             if not agent.keep_latest:  # 最新智能体
    #                 continue

    #             money_per_frame = 0
    #             kill = 0
    #             death = 0
    #             assistCnt = 0
    #             hurt_per_frame = 0
    #             hurtH_per_frame = 0
    #             hurtBH_per_frame = 0
    #             totalHurtToHero = 0

    #             agent_camp = i + 1
    #             agent_win = 0
    #             if (loss_camp is not None) and (agent_camp != loss_camp):
    #                 agent_win = 1

    #             agent.update_model_elo_dict(agent_win)  # 更新模型分数

    #             hero_idx = 0
    #             for hero_state in frame_state.hero_list:
    #                 if agent_camp == hero_state.camp:
    #                     hero_idx += 1
    #                     money_per_frame += hero_state.moneyCnt / game_info["length"]
    #                     kill += hero_state.killCnt
    #                     death += hero_state.deadCnt
    #                     assistCnt += hero_state.assistCnt
    #                     hurt_per_frame += hero_state.totalHurt / game_info["length"]
    #                     hurtH_per_frame += (
    #                             hero_state.totalHurtToHero / game_info["length"]
    #                     )
    #                     hurtBH_per_frame += (
    #                             hero_state.totalBeHurtByHero / game_info["length"]
    #                     )
    #                     totalHurtToHero += hero_state.totalHurtToHero

    #             game_info["money_per_frame"] = money_per_frame / hero_idx
    #             game_info["kill"] = kill / hero_idx
    #             game_info["death"] = death / hero_idx
    #             game_info["assistCnt"] = assistCnt / hero_idx
    #             game_info["hurt_per_frame"] = hurt_per_frame / hero_idx
    #             game_info["hurtH_per_frame"] = hurtH_per_frame / hero_idx
    #             game_info["hurtBH_per_frame"] = hurtBH_per_frame / hero_idx
    #             game_info["win"] = agent_win
    #             game_info["reward"] = np.sum(reward_game[i])
    #             game_info["totalHurtToHero"] = totalHurtToHero / hero_idx

    #         if self.monitor_logger:
    #             self.monitor_logger.info(game_info)


######################################################################
    # 【完整版本+修改隐藏信息的bug】
    # @log_time("one_episode")
    # def _run_episode(self, camp_config):
    #     LOG.info("Start a new game")
    #     g_log_time.clear()

    #     log_time_func("reset")
    #     # swap two agents, and re-assign camp
    #     self.agents.reverse()  # 倒转agents

    #     for i, agent in enumerate(self.agents):
    #         LOG.debug("reset agent {}".format(i))
    #         agent.reset()

    #     # restart a new game
    #     use_common_ai = [agent.is_common_ai() for agent in self.agents]
    #     self.env.reset(use_common_ai, camp_config)
    #     first_frame_no = -1

    #     # reset mem pool and models
    #     self.sample_manager.reset()
    #     log_time_func("reset", end=True)

    #     game_info = {}
    #     is_gameover = False
    #     frame_state = None
    #     reward_game = [[], []]

    #     # 初始化对方的frame_state
    #     frame_state_op = None
    #     features_op = None

    #     while not is_gameover:
    #         log_time_func("one_frame")

    #         continue_process = False
    #         # while True:
    #         is_send = False
    #         reward_camp = [[], []]

    #         # 遍历所有智能体
    #         for i, agent in enumerate(self.agents):
    #             if use_common_ai[i]:
    #                 LOG.debug(f"agent {i} is common_ai")
    #                 continue

    #             # 返回下一帧的状态
    #             continue_process, features, frame_state = self.env.step_feature(i)

    #             # 【计算英雄顺序】
    #             hero_runtime_ids = [m_feature.hero_runtime_id for m_feature in features]
    #             hero_config_ids = [0, 0, 0]
    #             hero_config_id_map = {}
    #             inverse_hero_config_id_map = {}
    #             # 获得当前features中英雄的顺序
    #             for m_hero in frame_state.hero_list:
    #                 for idx, hero_runtime_id in enumerate(hero_runtime_ids):
    #                     if m_hero.runtime_id == hero_runtime_id:
    #                         hero_config_ids[idx] = m_hero.config_id
    #             # 获得英雄对应关系
    #             for target_hero_config_ids in target_hero_config_ids_list:  # 判断属于哪个集合
    #                 if sum(target_hero_config_ids) == sum(hero_config_ids):
    #                     for idx, hero_config_id in enumerate(hero_config_ids):  # 遍历现有config_id集合
    #                         for target_idx, target_hero_config_id in enumerate(target_hero_config_ids):
    #                             if hero_config_id == target_hero_config_id:
    #                                 hero_config_id_map[idx] = target_idx
    #                                 inverse_hero_config_id_map[target_idx] = idx
    #                                 break
    #             hero_config_id_maps = [hero_config_id_map, inverse_hero_config_id_map]

    #             feature_invisible_list = []
    #             # 【获得隐藏信息】
    #             for idx, feature in enumerate(features):

    #                 # 获取当前英雄的信息，用于计算相对位置
    #                 cur_camp_id = feature.camp_id
    #                 cur_runtime_id = feature.hero_runtime_id
    #                 cur_x = 10000
    #                 cur_z = 10000
    #                 for hero_item in frame_state.hero_list:
    #                     if hero_item.runtime_id == cur_runtime_id:
    #                         cur_x = hero_item.location.x
    #                         cur_z = hero_item.location.z

    #                 # 在原本feature的基础上，添加invisible info
    #                 if frame_state_op is None or len(features_op) == 0:  # 39 + 180 = 219
    #                     # 如果为None，则全部重置为0
    #                     feature_invisible = [0] * 219  # TODO 维度需要修改
    #                 elif features_op[0].camp_id == cur_camp_id:
    #                     feature_invisible = [0] * 219  # TODO 维度需要修改
    #                 else:
    #                     feature_invisible = []  # 初始化一下
    #                     # 英雄信息
    #                     for hero_item in frame_state_op.hero_list:
    #                         if hero_item.camp.value != cur_camp_id:  # 敌方 13*3
    #                             hero_item_info = [hero_item.config_id / 300.0,
    #                                               hero_item.atk_spd / 5000.0,
    #                                               hero_item.crit_effe / 50000.0,
    #                                               hero_item.crit_rate / 10000.0,
    #                                               hero_item.ep / 200.0,
    #                                               hero_item.ep_recover / 100.0,
    #                                               hero_item.hp / 5000.0,
    #                                               hero_item.hp_recover / 200.0,
    #                                               hero_item.mov_spd / 10000.0,
    #                                               hero_item.location.x / 20000.0,
    #                                               hero_item.location.z / 20000.0,
    #                                               (hero_item.location.x - cur_x) / 20000.0,
    #                                               (hero_item.location.z - cur_z) / 20000.0,
    #                                               ]
    #                             feature_invisible.extend(hero_item_info)
    #                     # 士兵信息
    #                     soldier_cnt = 0
    #                     for soldier_item in frame_state_op.soldier_list:  # 6*10
    #                         if soldier_item.camp.value != cur_camp_id and soldier_cnt < 10:
    #                             soldier_item_info = [soldier_item.config_id / 300.0,
    #                                                  soldier_item.hp / 5000.0,
    #                                                  soldier_item.location.x / 20000.0,
    #                                                  soldier_item.location.z / 20000.0,
    #                                                  (soldier_item.location.x - cur_x) / 20000.0,
    #                                                  (soldier_item.location.z - cur_z) / 20000.0]
    #                             feature_invisible.extend(soldier_item_info)
    #                             soldier_cnt += 1
    #                     while soldier_cnt < 10:
    #                         feature_invisible.extend([0, 0, 0, 0, 0, 0])
    #                         soldier_cnt += 1
    #                     # 野怪信息
    #                     monster_cnt = 0
    #                     for monster_item in frame_state.monster_list:  # 6*20
    #                         if monster_cnt < 20:
    #                             monster_item_info = [monster_item.config_id / 300.0,
    #                                                  monster_item.hp / 5000.0,
    #                                                  monster_item.location.x / 20000.0,
    #                                                  monster_item.location.z / 20000.0,
    #                                                  (monster_item.location.x - cur_x) / 20000.0,
    #                                                  (monster_item.location.z - cur_z) / 20000.0]
    #                             feature_invisible.extend(monster_item_info)
    #                             monster_cnt += 1
    #                     while monster_cnt < 20:
    #                         feature_invisible.extend([0, 0, 0, 0, 0, 0])
    #                         monster_cnt += 1

    #                 # features[idx].feature = features[idx].feature.extend(feature_invisible) # 给每个英雄进行扩充
    #                 feature_invisible_list.append(feature_invisible)

    #             # 更新对方的信息，在训练阶段，可以获得对方的信息，在对战测试阶段，无法获得敌方的信息
    #             features_op = features  # 更新对方的features_op
    #             frame_state_op = frame_state  # 更新对方的frame_state_op

    #             if frame_state.gameover:
    #                 game_info["length"] = frame_state.frame_no
    #                 is_gameover = True

    #             if not continue_process:
    #                 continue

    #             if first_frame_no < 0:
    #                 first_frame_no = frame_state.frame_no
    #                 LOG.info("first_frame_no %d" % first_frame_no)

    #             # 智能体预测
    #             probs, lstm_info = agent.predict_process(features, frame_state, feature_invisible_list, hero_config_id_maps)

    #             # 在环境中执行对应动作
    #             ok, results = self.env.step_action(i, probs, features, frame_state)
    #             if not ok:
    #                 raise Exception("step action failed")

    #             # 获取样本
    #             sample = agent.sample_process(features, results, lstm_info, frame_state, feature_invisible_list, hero_config_id_maps)

    #             reward_game[i].append(sample["reward_s"])

    #             # skip save sample if not latest model
    #             if not agent.is_latest_model:
    #                 continue

    #             is_send = frame_state.gameover or (
    #                     (
    #                             (frame_state.frame_no - first_frame_no) % self.send_sample_frame
    #                             == 0
    #                     )
    #                     and (frame_state.frame_no > first_frame_no)
    #             )

    #             if not is_send:
    #                 self.sample_manager.save_sample(**sample, agent_id=i)
    #             else:
    #                 LOG.info(
    #                     f"save_last_sample frame[{frame_state.frame_no}] frame_state.gameover[{frame_state.gameover}]"
    #                 )
    #                 if frame_state.gameover:
    #                     self.sample_manager.save_last_sample(
    #                         agent_id=i, reward=sample["reward_s"]
    #                     )
    #                 else:
    #                     self.sample_manager.save_last_sample(
    #                         agent_id=i,
    #                         reward=sample["reward_s"],
    #                         value_s=sample["value_s"],
    #                     )

    #         if is_send or is_gameover:
    #             LOG.info("send_sample and update model")
    #             self.sample_manager.send_samples()
    #             self.sample_manager.reset()
    #             for i, agent in enumerate(self.agents):
    #                 agent.update_model()
    #             LOG.info("send_sample and update model done.")
    #     log_time_func("one_frame", end=True)
    #     self.env.close_game()

    #     if not frame_state:
    #         return

    #     # process game info
    #     loss_camp = None

    #     # update camp information.
    #     # 塔信息
    #     for organ in frame_state.organ_list:
    #         if organ.type == 24 and organ.hp <= 0:
    #             loss_camp = organ.camp

    #         if organ.type in [21, 24]:
    #             LOG.info(
    #                 "Tower {} in camp {}, hp: {}".format(
    #                     organ.type, organ.camp, organ.hp
    #                 )
    #             )

    #     for i, agent in enumerate(self.agents):
    #         agent_camp = i + 1
    #         agent_win = 0
    #         if (loss_camp is not None) and (agent_camp != loss_camp):
    #             agent_win = 1
    #         LOG.info("camp%d_agent:%d win:%d" % (agent_camp, i, agent_win))

    #         LOG.info("---------- camp%d hero_info ----------" % agent_camp)
    #         for hero_state in frame_state.hero_list:
    #             if agent_camp != hero_state.camp:
    #                 continue

    #             LOG.info(
    #                 "hero:%d moneyCnt:%d killCnt:%d deadCnt:%d assistCnt:%d"
    #                 % (
    #                     hero_state.config_id,
    #                     hero_state.moneyCnt,
    #                     hero_state.killCnt,
    #                     hero_state.deadCnt,
    #                     hero_state.assistCnt,
    #                 )
    #             )

    #     if self.m_config_id == 0:
    #         for i, agent in enumerate(self.agents):
    #             if not agent.keep_latest:  # 最新智能体
    #                 continue

    #             money_per_frame = 0
    #             kill = 0
    #             death = 0
    #             assistCnt = 0
    #             hurt_per_frame = 0
    #             hurtH_per_frame = 0
    #             hurtBH_per_frame = 0
    #             totalHurtToHero = 0

    #             agent_camp = i + 1
    #             agent_win = 0
    #             if (loss_camp is not None) and (agent_camp != loss_camp):
    #                 agent_win = 1

    #             hero_idx = 0
    #             for hero_state in frame_state.hero_list:
    #                 if agent_camp == hero_state.camp:
    #                     hero_idx += 1
    #                     money_per_frame += hero_state.moneyCnt / game_info["length"]
    #                     kill += hero_state.killCnt
    #                     death += hero_state.deadCnt
    #                     assistCnt += hero_state.assistCnt
    #                     hurt_per_frame += hero_state.totalHurt / game_info["length"]
    #                     hurtH_per_frame += (
    #                             hero_state.totalHurtToHero / game_info["length"]
    #                     )
    #                     hurtBH_per_frame += (
    #                             hero_state.totalBeHurtByHero / game_info["length"]
    #                     )
    #                     totalHurtToHero += hero_state.totalHurtToHero

    #             game_info["money_per_frame"] = money_per_frame / hero_idx
    #             game_info["kill"] = kill / hero_idx
    #             game_info["death"] = death / hero_idx
    #             game_info["assistCnt"] = assistCnt / hero_idx
    #             game_info["hurt_per_frame"] = hurt_per_frame / hero_idx
    #             game_info["hurtH_per_frame"] = hurtH_per_frame / hero_idx
    #             game_info["hurtBH_per_frame"] = hurtBH_per_frame / hero_idx
    #             game_info["win"] = agent_win
    #             game_info["reward"] = np.sum(reward_game[i])
    #             game_info["totalHurtToHero"] = totalHurtToHero / hero_idx

    #         if self.monitor_logger:
    #             self.monitor_logger.info(game_info)


######################################################################
    # 【完整版本】
    # 1030 15:59
    # @log_time("one_episode")
    # def _run_episode(self, camp_config):
    #     LOG.info("Start a new game")
    #     g_log_time.clear()

    #     log_time_func("reset")
    #     # swap two agents, and re-assign camp
    #     self.agents.reverse()  # 倒转agents

    #     for i, agent in enumerate(self.agents):
    #         LOG.debug("reset agent {}".format(i))
    #         agent.reset()

    #     # restart a new game
    #     use_common_ai = [agent.is_common_ai() for agent in self.agents]
    #     self.env.reset(use_common_ai, camp_config)
    #     first_frame_no = -1

    #     # reset mem pool and models
    #     self.sample_manager.reset()
    #     log_time_func("reset", end=True)

    #     game_info = {}
    #     is_gameover = False
    #     frame_state = None
    #     reward_game = [[], []]

    #     # 初始化对方的frame_state
    #     frame_state_op = None
    #     features_op = None

    #     while not is_gameover:
    #         log_time_func("one_frame")

    #         continue_process = False
    #         # while True:
    #         is_send = False
    #         reward_camp = [[], []]

    #         # 遍历所有智能体
    #         for i, agent in enumerate(self.agents):
    #             if use_common_ai[i]:
    #                 LOG.debug(f"agent {i} is common_ai")
    #                 continue

    #             # 返回下一帧的状态
    #             continue_process, features, frame_state = self.env.step_feature(i)

    #             # 【计算英雄顺序】
    #             hero_runtime_ids = [m_feature.hero_runtime_id for m_feature in features]
    #             hero_config_ids = [0, 0, 0]
    #             hero_config_id_map = {}
    #             inverse_hero_config_id_map = {}
    #             # 获得当前features中英雄的顺序
    #             for m_hero in frame_state.hero_list:
    #                 for idx, hero_runtime_id in enumerate(hero_runtime_ids):
    #                     if m_hero.runtime_id == hero_runtime_id:
    #                         hero_config_ids[idx] = m_hero.config_id
    #             # 获得英雄对应关系
    #             for target_hero_config_ids in target_hero_config_ids_list:  # 判断属于哪个集合
    #                 if sum(target_hero_config_ids) == sum(hero_config_ids):
    #                     for idx, hero_config_id in enumerate(hero_config_ids):  # 遍历现有config_id集合
    #                         for target_idx, target_hero_config_id in enumerate(target_hero_config_ids):
    #                             if hero_config_id == target_hero_config_id:
    #                                 hero_config_id_map[idx] = target_idx
    #                                 inverse_hero_config_id_map[target_idx] = idx
    #                                 break
    #             hero_config_id_maps = [hero_config_id_map, inverse_hero_config_id_map]


    #             # 【获得隐藏信息】
    #             for idx, feature in enumerate(features):

    #                 # 获取当前英雄的信息，用于计算相对位置
    #                 cur_camp_id = feature.camp_id
    #                 cur_runtime_id = feature.hero_runtime_id
    #                 cur_x = 10000
    #                 cur_z = 10000
    #                 for hero_item in frame_state.hero_list:
    #                     if hero_item.runtime_id == cur_runtime_id:
    #                         cur_x = hero_item.location.x
    #                         cur_z = hero_item.location.z

    #                 # 在原本feature的基础上，添加invisible info
    #                 if frame_state_op is None or len(features_op) == 0:  # 39 + 180 = 219
    #                     # 如果为None，则全部重置为0
    #                     feature_invisible = [0] * 219  # TODO 维度需要修改
    #                 elif features_op[0].camp_id == cur_camp_id:
    #                     feature_invisible = [0] * 219  # TODO 维度需要修改
    #                 else:
    #                     feature_invisible = []  # 初始化一下
    #                     # 英雄信息
    #                     for hero_item in frame_state_op.hero_list:
    #                         if hero_item.camp.value != cur_camp_id:  # 敌方 13*3
    #                             hero_item_info = [hero_item.config_id / 300.0,
    #                                               hero_item.atk_spd / 5000.0,
    #                                               hero_item.crit_effe / 50000.0,
    #                                               hero_item.crit_rate / 10000.0,
    #                                               hero_item.ep / 200.0,
    #                                               hero_item.ep_recover / 100.0,
    #                                               hero_item.hp / 5000.0,
    #                                               hero_item.hp_recover / 200.0,
    #                                               hero_item.mov_spd / 10000.0,
    #                                               hero_item.location.x / 20000.0,
    #                                               hero_item.location.z / 20000.0,
    #                                               (hero_item.location.x - cur_x) / 20000.0,
    #                                               (hero_item.location.z - cur_z) / 20000.0,
    #                                               ]
    #                             feature_invisible.extend(hero_item_info)
    #                     # 士兵信息
    #                     soldier_cnt = 0
    #                     for soldier_item in frame_state_op.soldier_list:  # 6*10
    #                         if soldier_item.camp.value != cur_camp_id and soldier_cnt < 10:
    #                             soldier_item_info = [soldier_item.config_id / 300.0,
    #                                                  soldier_item.hp / 5000.0,
    #                                                  soldier_item.location.x / 20000.0,
    #                                                  soldier_item.location.z / 20000.0,
    #                                                  (soldier_item.location.x - cur_x) / 20000.0,
    #                                                  (soldier_item.location.z - cur_z) / 20000.0]
    #                             feature_invisible.extend(soldier_item_info)
    #                             soldier_cnt += 1
    #                     while soldier_cnt < 10:
    #                         feature_invisible.extend([0, 0, 0, 0, 0, 0])
    #                         soldier_cnt += 1
    #                     # 野怪信息
    #                     monster_cnt = 0
    #                     for monster_item in frame_state.monster_list:  # 6*20
    #                         if monster_cnt < 20:
    #                             monster_item_info = [monster_item.config_id / 300.0,
    #                                                  monster_item.hp / 5000.0,
    #                                                  monster_item.location.x / 20000.0,
    #                                                  monster_item.location.z / 20000.0,
    #                                                  (monster_item.location.x - cur_x) / 20000.0,
    #                                                  (monster_item.location.z - cur_z) / 20000.0]
    #                             feature_invisible.extend(monster_item_info)
    #                             monster_cnt += 1
    #                     while monster_cnt < 20:
    #                         feature_invisible.extend([0, 0, 0, 0, 0, 0])
    #                         monster_cnt += 1

    #                 # features[idx].feature = features[idx].feature.extend(feature_invisible) # 给每个英雄进行扩充


    #             # 更新对方的信息，在训练阶段，可以获得对方的信息，在对战测试阶段，无法获得敌方的信息
    #             features_op = features  # 更新对方的features_op
    #             frame_state_op = frame_state  # 更新对方的frame_state_op

    #             if frame_state.gameover:
    #                 game_info["length"] = frame_state.frame_no
    #                 is_gameover = True

    #             if not continue_process:
    #                 continue

    #             if first_frame_no < 0:
    #                 first_frame_no = frame_state.frame_no
    #                 LOG.info("first_frame_no %d" % first_frame_no)

    #             # 智能体预测
    #             probs, lstm_info = agent.predict_process(features, frame_state, feature_invisible, hero_config_id_maps)

    #             # 在环境中执行对应动作
    #             ok, results = self.env.step_action(i, probs, features, frame_state)
    #             if not ok:
    #                 raise Exception("step action failed")

    #             # 获取样本
    #             sample = agent.sample_process(features, results, lstm_info, frame_state, feature_invisible, hero_config_id_maps)

    #             reward_game[i].append(sample["reward_s"])

    #             # skip save sample if not latest model
    #             if not agent.is_latest_model:
    #                 continue

    #             is_send = frame_state.gameover or (
    #                     (
    #                             (frame_state.frame_no - first_frame_no) % self.send_sample_frame
    #                             == 0
    #                     )
    #                     and (frame_state.frame_no > first_frame_no)
    #             )

    #             if not is_send:
    #                 self.sample_manager.save_sample(**sample, agent_id=i)
    #             else:
    #                 LOG.info(
    #                     f"save_last_sample frame[{frame_state.frame_no}] frame_state.gameover[{frame_state.gameover}]"
    #                 )
    #                 if frame_state.gameover:
    #                     self.sample_manager.save_last_sample(
    #                         agent_id=i, reward=sample["reward_s"]
    #                     )
    #                 else:
    #                     self.sample_manager.save_last_sample(
    #                         agent_id=i,
    #                         reward=sample["reward_s"],
    #                         value_s=sample["value_s"],
    #                     )

    #         if is_send or is_gameover:
    #             LOG.info("send_sample and update model")
    #             self.sample_manager.send_samples()
    #             self.sample_manager.reset()
    #             for i, agent in enumerate(self.agents):
    #                 agent.update_model()
    #             LOG.info("send_sample and update model done.")
    #     log_time_func("one_frame", end=True)
    #     self.env.close_game()

    #     if not frame_state:
    #         return

    #     # process game info
    #     loss_camp = None

    #     # update camp information.
    #     # 塔信息
    #     for organ in frame_state.organ_list:
    #         if organ.type == 24 and organ.hp <= 0:
    #             loss_camp = organ.camp

    #         if organ.type in [21, 24]:
    #             LOG.info(
    #                 "Tower {} in camp {}, hp: {}".format(
    #                     organ.type, organ.camp, organ.hp
    #                 )
    #             )

    #     for i, agent in enumerate(self.agents):
    #         agent_camp = i + 1
    #         agent_win = 0
    #         if (loss_camp is not None) and (agent_camp != loss_camp):
    #             agent_win = 1
    #         LOG.info("camp%d_agent:%d win:%d" % (agent_camp, i, agent_win))

    #         LOG.info("---------- camp%d hero_info ----------" % agent_camp)
    #         for hero_state in frame_state.hero_list:
    #             if agent_camp != hero_state.camp:
    #                 continue

    #             LOG.info(
    #                 "hero:%d moneyCnt:%d killCnt:%d deadCnt:%d assistCnt:%d"
    #                 % (
    #                     hero_state.config_id,
    #                     hero_state.moneyCnt,
    #                     hero_state.killCnt,
    #                     hero_state.deadCnt,
    #                     hero_state.assistCnt,
    #                 )
    #             )

    #     if self.m_config_id == 0:
    #         for i, agent in enumerate(self.agents):
    #             if not agent.keep_latest:  # 最新智能体
    #                 continue

    #             money_per_frame = 0
    #             kill = 0
    #             death = 0
    #             assistCnt = 0
    #             hurt_per_frame = 0
    #             hurtH_per_frame = 0
    #             hurtBH_per_frame = 0
    #             totalHurtToHero = 0

    #             agent_camp = i + 1
    #             agent_win = 0
    #             if (loss_camp is not None) and (agent_camp != loss_camp):
    #                 agent_win = 1

    #             hero_idx = 0
    #             for hero_state in frame_state.hero_list:
    #                 if agent_camp == hero_state.camp:
    #                     hero_idx += 1
    #                     money_per_frame += hero_state.moneyCnt / game_info["length"]
    #                     kill += hero_state.killCnt
    #                     death += hero_state.deadCnt
    #                     assistCnt += hero_state.assistCnt
    #                     hurt_per_frame += hero_state.totalHurt / game_info["length"]
    #                     hurtH_per_frame += (
    #                             hero_state.totalHurtToHero / game_info["length"]
    #                     )
    #                     hurtBH_per_frame += (
    #                             hero_state.totalBeHurtByHero / game_info["length"]
    #                     )
    #                     totalHurtToHero += hero_state.totalHurtToHero

    #             game_info["money_per_frame"] = money_per_frame / hero_idx
    #             game_info["kill"] = kill / hero_idx
    #             game_info["death"] = death / hero_idx
    #             game_info["assistCnt"] = assistCnt / hero_idx
    #             game_info["hurt_per_frame"] = hurt_per_frame / hero_idx
    #             game_info["hurtH_per_frame"] = hurtH_per_frame / hero_idx
    #             game_info["hurtBH_per_frame"] = hurtBH_per_frame / hero_idx
    #             game_info["win"] = agent_win
    #             game_info["reward"] = np.sum(reward_game[i])
    #             game_info["totalHurtToHero"] = totalHurtToHero / hero_idx

    #         if self.monitor_logger:
    #             self.monitor_logger.info(game_info)




######################################################################
    # 【2】去掉隐藏信息
    # @log_time("one_episode")
    # def _run_episode(self, camp_config):
    #     LOG.info("Start a new game")
    #     g_log_time.clear()

    #     log_time_func("reset")
    #     # swap two agents, and re-assign camp
    #     self.agents.reverse()  # 倒转agents

    #     for i, agent in enumerate(self.agents):
    #         LOG.debug("reset agent {}".format(i))
    #         agent.reset()

    #     # restart a new game
    #     use_common_ai = [agent.is_common_ai() for agent in self.agents]
    #     self.env.reset(use_common_ai, camp_config)
    #     first_frame_no = -1

    #     # reset mem pool and models
    #     self.sample_manager.reset()
    #     log_time_func("reset", end=True)

    #     game_info = {}
    #     is_gameover = False
    #     frame_state = None
    #     reward_game = [[], []]

    #     # 初始化对方的frame_state
    #     frame_state_op = None
    #     features_op = None

    #     while not is_gameover:
    #         log_time_func("one_frame")

    #         continue_process = False
    #         # while True:
    #         is_send = False
    #         reward_camp = [[], []]

    #         # 遍历所有智能体
    #         for i, agent in enumerate(self.agents):
    #             if use_common_ai[i]:
    #                 LOG.debug(f"agent {i} is common_ai")
    #                 continue

    #             # 返回下一帧的状态
    #             continue_process, features, frame_state = self.env.step_feature(i)

    #             # 【计算英雄顺序】
    #             hero_runtime_ids = [m_feature.hero_runtime_id for m_feature in features]
    #             hero_config_ids = [0, 0, 0]
    #             hero_config_id_map = {}
    #             inverse_hero_config_id_map = {}
    #             # 获得当前features中英雄的顺序
    #             for m_hero in frame_state.hero_list:
    #                 for idx, hero_runtime_id in enumerate(hero_runtime_ids):
    #                     if m_hero.runtime_id == hero_runtime_id:
    #                         hero_config_ids[idx] = m_hero.config_id
    #             # 获得英雄对应关系
    #             for target_hero_config_ids in target_hero_config_ids_list:  # 判断属于哪个集合
    #                 if sum(target_hero_config_ids) == sum(hero_config_ids):
    #                     for idx, hero_config_id in enumerate(hero_config_ids):  # 遍历现有config_id集合
    #                         for target_idx, target_hero_config_id in enumerate(target_hero_config_ids):
    #                             if hero_config_id == target_hero_config_id:
    #                                 hero_config_id_map[idx] = target_idx
    #                                 inverse_hero_config_id_map[target_idx] = idx
    #                                 break
    #             hero_config_id_maps = [hero_config_id_map, inverse_hero_config_id_map]

    #             if frame_state.gameover:
    #                 game_info["length"] = frame_state.frame_no
    #                 is_gameover = True

    #             if not continue_process:
    #                 continue

    #             if first_frame_no < 0:
    #                 first_frame_no = frame_state.frame_no
    #                 LOG.info("first_frame_no %d" % first_frame_no)

    #             # 智能体预测
    #             probs, lstm_info = agent.predict_process(features, frame_state, hero_config_id_maps)

    #             # 在环境中执行对应动作
    #             ok, results = self.env.step_action(i, probs, features, frame_state)
    #             if not ok:
    #                 raise Exception("step action failed")

    #             # 获取样本
    #             sample = agent.sample_process(features, results, lstm_info, frame_state, hero_config_id_maps)

    #             reward_game[i].append(sample["reward_s"])

    #             # skip save sample if not latest model
    #             if not agent.is_latest_model:
    #                 continue

    #             is_send = frame_state.gameover or (
    #                     (
    #                             (frame_state.frame_no - first_frame_no) % self.send_sample_frame
    #                             == 0
    #                     )
    #                     and (frame_state.frame_no > first_frame_no)
    #             )

    #             if not is_send:
    #                 self.sample_manager.save_sample(**sample, agent_id=i)
    #             else:
    #                 LOG.info(
    #                     f"save_last_sample frame[{frame_state.frame_no}] frame_state.gameover[{frame_state.gameover}]"
    #                 )
    #                 if frame_state.gameover:
    #                     self.sample_manager.save_last_sample(
    #                         agent_id=i, reward=sample["reward_s"]
    #                     )
    #                 else:
    #                     self.sample_manager.save_last_sample(
    #                         agent_id=i,
    #                         reward=sample["reward_s"],
    #                         value_s=sample["value_s"],
    #                     )

    #         if is_send or is_gameover:
    #             LOG.info("send_sample and update model")
    #             self.sample_manager.send_samples()
    #             self.sample_manager.reset()
    #             for i, agent in enumerate(self.agents):
    #                 agent.update_model()
    #             LOG.info("send_sample and update model done.")
    #     log_time_func("one_frame", end=True)
    #     self.env.close_game()

    #     if not frame_state:
    #         return

    #     # process game info
    #     loss_camp = None

    #     # update camp information.
    #     # 塔信息
    #     for organ in frame_state.organ_list:
    #         if organ.type == 24 and organ.hp <= 0:
    #             loss_camp = organ.camp

    #         if organ.type in [21, 24]:
    #             LOG.info(
    #                 "Tower {} in camp {}, hp: {}".format(
    #                     organ.type, organ.camp, organ.hp
    #                 )
    #             )

    #     for i, agent in enumerate(self.agents):
    #         agent_camp = i + 1
    #         agent_win = 0
    #         if (loss_camp is not None) and (agent_camp != loss_camp):
    #             agent_win = 1
    #         LOG.info("camp%d_agent:%d win:%d" % (agent_camp, i, agent_win))

    #         LOG.info("---------- camp%d hero_info ----------" % agent_camp)
    #         for hero_state in frame_state.hero_list:
    #             if agent_camp != hero_state.camp:
    #                 continue

    #             LOG.info(
    #                 "hero:%d moneyCnt:%d killCnt:%d deadCnt:%d assistCnt:%d"
    #                 % (
    #                     hero_state.config_id,
    #                     hero_state.moneyCnt,
    #                     hero_state.killCnt,
    #                     hero_state.deadCnt,
    #                     hero_state.assistCnt,
    #                 )
    #             )

    #     if self.m_config_id == 0:
    #         for i, agent in enumerate(self.agents):
    #             if not agent.keep_latest:  # 最新智能体
    #                 continue

    #             money_per_frame = 0
    #             kill = 0
    #             death = 0
    #             assistCnt = 0
    #             hurt_per_frame = 0
    #             hurtH_per_frame = 0
    #             hurtBH_per_frame = 0
    #             totalHurtToHero = 0

    #             agent_camp = i + 1
    #             agent_win = 0
    #             if (loss_camp is not None) and (agent_camp != loss_camp):
    #                 agent_win = 1

    #             hero_idx = 0
    #             for hero_state in frame_state.hero_list:
    #                 if agent_camp == hero_state.camp:
    #                     hero_idx += 1
    #                     money_per_frame += hero_state.moneyCnt / game_info["length"]
    #                     kill += hero_state.killCnt
    #                     death += hero_state.deadCnt
    #                     assistCnt += hero_state.assistCnt
    #                     hurt_per_frame += hero_state.totalHurt / game_info["length"]
    #                     hurtH_per_frame += (
    #                             hero_state.totalHurtToHero / game_info["length"]
    #                     )
    #                     hurtBH_per_frame += (
    #                             hero_state.totalBeHurtByHero / game_info["length"]
    #                     )
    #                     totalHurtToHero += hero_state.totalHurtToHero

    #             game_info["money_per_frame"] = money_per_frame / hero_idx
    #             game_info["kill"] = kill / hero_idx
    #             game_info["death"] = death / hero_idx
    #             game_info["assistCnt"] = assistCnt / hero_idx
    #             game_info["hurt_per_frame"] = hurt_per_frame / hero_idx
    #             game_info["hurtH_per_frame"] = hurtH_per_frame / hero_idx
    #             game_info["hurtBH_per_frame"] = hurtBH_per_frame / hero_idx
    #             game_info["win"] = agent_win
    #             game_info["reward"] = np.sum(reward_game[i])
    #             game_info["totalHurtToHero"] = totalHurtToHero / hero_idx

    #         if self.monitor_logger:
    #             self.monitor_logger.info(game_info)



    def run(self):
        self._last_print_time = time.time()
        self._episode_num = 0
        MAX_REPEAT_ERR_NUM = 2
        repeat_num = MAX_REPEAT_ERR_NUM

        while True:
            try:
                camp_config = next(self.camp_iter)  # 生成阵容
                self._run_episode(camp_config)  # 运行一个回合
                self._episode_num += 1
                repeat_num = MAX_REPEAT_ERR_NUM
            except Exception as e:
                LOG.exception(
                    "_run_episode err: {}/{}".format(repeat_num, MAX_REPEAT_ERR_NUM)
                )
                repeat_num -= 1
                if repeat_num == 0:
                    raise e

            if 0 < self._max_episode <= self._episode_num:
                break
