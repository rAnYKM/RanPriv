# Project Name: rAnPrivGP
# Author: rAnYKM (Jiayi Chen)
#
#          ___          ____       _
#    _____/   |  ____  / __ \_____(_)   __
#   / ___/ /| | / __ \/ /_/ / ___/ / | / /
#  / /  / ___ |/ / / / ____/ /  / /| |/ /
# /_/  /_/  |_/_/ /_/_/   /_/  /_/ |___/
#
# Script Name: ran_lab.py
# Date: Feb. 5, 2017

from __future__ import division
import os
import logging
import random
import numpy as np
import pandas as pd
import networkx as nx
from snap_fbcomplete import FacebookNetwork
from snap_facebook import FacebookEgoNet
from ran_inference import InferenceAttack, infer_performance, rpg_attr_vector, \
    rpg_labels, RelationAttack, self_cross_val, infer_result

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
RESULT_METRICS = ['precision', 'recall', 'f1']
ML_ALGS = ['dt', 'rf', 'nb', 'lr']
RCLASSIFIERS = ['wvrn', 'cdrn-norm-cos', 'nolb-lr-count']


def single_attribute_test(secret, epsilon, delta):
    a = FacebookNetwork()
    price = dict()
    rprice = dict()
    secrets = dict()
    exp1 = dict()
    exp2 = dict()
    for i in a.rpg.attr_node:
        price[i] = 1
    for n in a.rpg.soc_node:
        if a.rpg.attr_net.has_edge(n, secret):
            secrets[n] = [secret]
        else:
            secrets[n] = []
    # Basic Info Display
    logging.debug('[ran_lab] Single Attribute Test - e=%f, d=%f, threshold=%f, affected attributes=%d'
                  % (epsilon,
                     delta,
                     a.rpg.get_max_weight(secret, epsilon, delta),
                     a.rpg.affected_attribute_number(secrets)))
    # Original Graph
    org = InferenceAttack(a.rpg, secrets)
    clf, fsl, result = org.dt_classifier(secret)
    score = org.score(clf, secret)
    full_att = infer_performance(clf, fsl, rpg_attr_vector(a.rpg, secret, secrets), rpg_labels(a.rpg, secret))
    exp1['origin'] = np.average(score)
    exp2['origin'] = full_att[2]
    logging.info('[ran_lab] Origin %d-fold (f1 score) - average=%f'
                 % (len(score), np.average(score)))
    logging.info('[ran_lab] Origin full graph - precision=%f, recall=%f, f1-score=%f'
                 % (full_att[0], full_att[1], full_att[2]))
    """"
    new_ran = a.rpg.d_knapsack_mask(secrets, price, epsilon, delta, mode='greedy')
    print(time.time() - t0)
    print(a.rpg.cmp_attr_degree_L1_error(new_ran))
    def1 = InferenceAttack(new_ran, secrets)
    clf2, fsl2, result25 = def1.dt_classifier(secret)
    print(result25, def1.score(clf2, secret),
          infer_performance(clf, fsl, rpg_attr_vector(new_ran, secret, secrets), rpg_labels(new_ran, secret)))
    """
    # a.rpg.naive_bayes_mask(secrets, epsilon, delta, 0.1)

    new_ran = a.rpg.entropy_mask(secrets, price, epsilon, delta)
    def1 = InferenceAttack(new_ran, secrets)
    clf2, fsl2, result25 = def1.dt_classifier(secret)
    score = def1.score(clf2, secret)
    full_att = infer_performance(clf, fsl, rpg_attr_vector(new_ran, secret, secrets), rpg_labels(new_ran, secret))
    logging.info('[ran_lab] Origin %d-fold (f1 score) - average=%f'
                 % (len(score), np.average(score)))
    logging.info('[ran_lab] Origin full graph - precision=%f, recall=%f, f1-score=%f'
                 % (full_att[0], full_att[1], full_att[2]))

    exp1['entropy'] = np.average(score)
    exp2['entropy'] = full_att[2]
    new_ran = a.rpg.v_knapsack_mask(secrets, price, epsilon, delta, mode='greedy')
    # weight = {n: [a.rpg.get_max_weight(secret, epsilon, delta)] for n in a.ran.soc_net.nodes()}
    # old_ran = a.ran.s_knapsack_mask(secrets, price, weight, mode='greedy')
    # print(time.time() - t0)
    # print(a.rpg.cmp_attr_degree_L1_error(new_ran))
    def2 = InferenceAttack(new_ran, secrets)
    clf3, fsl3, result35 = def1.dt_classifier(secret)
    score = def2.score(clf3, secret)
    full_att = infer_performance(clf, fsl, rpg_attr_vector(new_ran, secret, secrets), rpg_labels(new_ran, secret))
    logging.info('[ran_lab] Origin %d-fold (f1 score) - average=%f'
                 % (len(score), np.average(score)))
    logging.info('[ran_lab] Origin full graph - precision=%f, recall=%f, f1-score=%f'
                 % (full_att[0], full_att[1], full_att[2]))
    exp1['vkp'] = np.average(score)
    exp2['vkp'] = full_att[2]
    for i in a.rpg.soc_net.edges():
        rprice[i] = 1
    # t0 = time.time()
    # a.ran.s_knapsack_relation_global(secrets, rprice, epsilon)
    # print(time.time() - t0)
    # print('3734' in a.rpg.neighbor_array)
    '''
    t0 = time.time()
    new_ran = a.rpg.d_knapsack_relation(secrets, rprice, epsilon, delta)
    print(time.time() - t0)
    print(a.rpg.cmp_soc_degree_L1_error(new_ran))
    t0 = time.time()
    new_ran = a.rpg.v_knapsack_relation(secrets, rprice, epsilon, delta)
    print(time.time() - t0)
    print(a.rpg.cmp_soc_degree_L1_error(new_ran))
    '''
    return exp1, exp2


class AttackSimulator:
    def self_attack(self, classifier='dt'):
        org = InferenceAttack(self.rpg, self.secrets)
        if classifier == 'dt':
            clf, fsl, result = org.dt_classifier(self.secret)
        elif classifier == 'nb':
            clf, fsl, result = org.nb_classifier(self.secret)
        elif classifier == 'lr':
            clf, fsl, result = org.lr_classifier(self.secret)
        elif classifier == 'rf':
            clf, fsl, result = org.rf_classifier(self.secret)
        else:
            clf, fsl, result = org.svm_classifier(self.secret)
        # score = org.score(clf, secret)
        full_att = infer_performance(clf,
                                     fsl,
                                     rpg_attr_vector(self.rpg, self.secret, self.secrets),
                                     rpg_labels(self.rpg, self.secret))
        return {'classifier': clf,
                'feat_selector': fsl,
                'score': full_att}

    def rpg_attack(self, rpg):
        full_att = infer_performance(self.clf,
                                     self.fsl,
                                     rpg_attr_vector(rpg, self.secret, self.secrets),
                                     rpg_labels(rpg, self.secret))
        logging.info('[ran_lab] Full Graph Attack - precision=%f, recall=%f, f1-score=%f'
                     % (full_att[0], full_att[1], full_att[2]))
        # TODO: Utility Measurement
        total = len(self.rpg.attr_edge)
        remain = len(rpg.attr_edge)
        secs = total - len(self.rpg.attr_net.neighbors(self.secret))
        utility = (total - remain) / secs
        return {'score': full_att,
                'utility': 1 - utility}

    def formatted_rpg_attack(self, rpg):
        full_att = infer_performance(self.clf,
                                     self.fsl,
                                     rpg_attr_vector(rpg, self.secret, self.secrets),
                                     rpg_labels(rpg, self.secret))
        logging.info('[ran_lab] Full Graph Attack - precision=%f, recall=%f, f1-score=%f'
                     % (full_att[0], full_att[1], full_att[2]))
        return {'precision': full_att[0],
                'recall': full_att[1],
                'f1': full_att[2]}

    def select_rpg_attack(self, rpg):
        result = infer_result(self.clf,
                              self.fsl,
                              rpg_attr_vector(rpg, self.secret, self.secrets),
                              rpg_labels(rpg, self.secret))
        nodes = {cate: [rpg.soc_node[index] for index in li] for cate, li in result.items()}
        return nodes

    def formatted_robustness(self, rpg):
        f1 = self_cross_val(rpg_attr_vector(rpg, self.secret, self.secrets),
                            rpg_labels(rpg, self.secret),
                            5)
        average = np.average(f1)
        variance = np.var(f1)
        logging.info('[ran_lab] Robustness(f1) - average=%f, var=%f' % (average, variance))
        return {'average': str(average) + ',' + str(variance)}

    def config(self, secret, epsilon, delta, classifier='dt'):
        self.secret = secret
        self.epsilon = epsilon
        self.delta = delta
        org_settings = self.self_attack(classifier=classifier)
        self.clf = org_settings['classifier']
        self.fsl = org_settings['feat_selector']
        self.score = org_settings['score']

    def __init__(self, rpg, secrets, secret, epsilon=0.1, delta=0.0):
        self.rpg = rpg
        self.secrets = secrets
        self.secret = secret
        self.epsilon = epsilon
        self.delta = delta
        org_settings = self.self_attack()
        self.clf = org_settings['classifier']
        self.fsl = org_settings['feat_selector']
        self.score = org_settings['score']


class AttributeExperiment:
    """
    Attribute disclosure experiment
    INPUT: original RPGraph, secret_settings
    Format:
    secret_settings(dict): {secret name (string) : sampling rate (float)}
    """
    def resampling(self):
        secrets = {node: [] for node in self.rpg.soc_node}
        exposed = {node: [] for node in self.rpg.soc_node}
        for secret, rate in self.secret_settings.items():
            # Select all nodes with the secret
            nodes = np.array([node for node in self.rpg.attr_net.neighbors(secret)])
            # rAnDOM
            indices = np.random.permutation(nodes.shape[0])
            # pool_a: nodes thinking secret, pool_b: nodes not thinking secret
            size = int(nodes.shape[0] * rate)
            pool_a_idx, pool_b_idx = indices[:size], indices[size:]
            # pool_a, pool_b = nodes[pool_a_idx,:], nodes[pool_b_idx,:]
            for idx in pool_a_idx:
                secrets[nodes[idx]] += [secret]
            for idx in pool_b_idx:
                exposed[nodes[idx]] += [secret]
            logging.info('[ran_lab] resampling: %s - s:%d e:%d' % (secret, len(pool_a_idx), len(pool_b_idx)))
        return secrets, exposed

    def auto_attr_price(self, mode='equal'):
        values = dict()
        if mode == 'equal':
            for attr in self.rpg.attr_node:
                values[attr] = 1
        elif mode == 'unique':
            for attr in self.rpg.attr_node:
                values[attr] = 1 / np.log(float(len(self.rpg.attr_net.neighbors(attr))) + 1)
        elif mode == 'common':
            for node in self.rpg.soc_node:
                attrs = [attr for attr in self.rpg.attr_net.neighbors_iter(node)]
                values[node] = dict()
                set_n = set(self.rpg.soc_net.neighbors(node))
                for attr in attrs:
                    set_a = set(self.rpg.attr_net.neighbors(attr))
                    values[node][attr] = (len(set_n & set_a) + 1) / float(len(set_n) + 1)
        return values

    def attr_utility(self, rpg, mode='equal', p_mode='single', affected=None):
        price = self.auto_attr_price(mode)
        if affected is None:
            all_nodes = self.rpg.soc_node
        else:
            all_nodes = affected
        if p_mode == 'single':
            total = sum([sum([price[attr] for attr in self.rpg.attr_net.neighbors(node)])
                         for node in all_nodes])
            score = sum([sum([price[attr] for attr in rpg.attr_net.neighbors(node)])
                         for node in all_nodes])
        else:
            total = sum([sum([price[node][attr] for attr in self.rpg.attr_net.neighbors(node)])
                         for node in all_nodes])
            score = sum([sum([price[node][attr] for attr in rpg.attr_net.neighbors(node)])
                         for node in all_nodes])
        return score / total

    def attack_experiment(self, epsilon, delta_range):
        secrets, _ = self.resampling()
        price = self.auto_attr_price()
        secret_list = [s for s in self.secret_settings.keys()]
        simulator = AttackSimulator(self.rpg, secrets, secret_list[0])
        result_table = {secret: [] 
                        for secret in secret_list}
        for delta in delta_range:
            ran_vkp = self.rpg.v_knapsack_mask(secrets, price, epsilon, delta)
            for secret in secret_list:
                tmp_line = {}
                for alg in ML_ALGS:
                    simulator.config(secret, epsilon, delta, alg)
                    result = simulator.formatted_rpg_attack(ran_vkp)
                    tmp_line[alg] = result['f1']
                    tmp_line[alg + '-o'] = simulator.score[2]
                result_table[secret].append(tmp_line)
        return result_table

    def org_attack_experiment(self):
        secrets, _ = self.resampling()
        price = self.auto_attr_price()
        secret_list = [s for s in self.secret_settings.keys()]
        simulator = AttackSimulator(self.rpg, secrets, secret_list[0])
        result_table = {secret: []
                        for secret in secret_list}
        for secret in secret_list:
            for alg in ML_ALGS:
                simulator.config(secret, epsilon=simulator.epsilon,
                                 delta=simulator.delta, classifier=alg)
                tmp_line = {'Precision': simulator.score[0],
                            'Recall': simulator.score[1],
                            'F-Score': simulator.score[2]}
                result_table[secret].append(tmp_line)
        return result_table

    def delta_experiment(self, epsilon, delta_range, utility_name='equal'):
        secrets, _ = self.resampling()
        if utility_name == 'common':
            p_mode = 'double'
        else:
            p_mode = 'single'
        price = self.auto_attr_price(utility_name)
        price0 = self.auto_attr_price()
        utility_table = []
        secret_list = [s for s in self.secret_settings.keys()]
        result_table = {secret: {metric: [] for metric in RESULT_METRICS + ['robust']}
                        for secret in secret_list}
        simulator = AttackSimulator(self.rpg, secrets, secret_list[0])

        for delta in delta_range:
            affect_nodes = [node for node, secret in secrets.items() if len(secret) != 0]
            ran_random = self.rpg.random_mask(secrets, epsilon, delta)
            ran_nb = self.rpg.naive_bayes_mask(secrets, epsilon, delta)
            ran_ig = self.rpg.entropy_mask(secrets, price, epsilon, delta, p_mode=p_mode)
            ran_vkp = self.rpg.v_knapsack_mask(secrets, price0, epsilon, delta)
            ran_vkp_utility = self.rpg.v_knapsack_mask(secrets, price, epsilon, delta, p_mode=p_mode)
            # Utility Calculate
            all_scores = {
                'Random': self.attr_utility(ran_random, utility_name, p_mode, affected=affect_nodes),
                'NaiveBayes': self.attr_utility(ran_nb, utility_name, p_mode, affected=affect_nodes),
                'InfoGain': self.attr_utility(ran_ig, utility_name, p_mode, affected=affect_nodes),
                'V-KP': self.attr_utility(ran_vkp, utility_name, p_mode, affected=affect_nodes),
                'V-KP-U': self.attr_utility(ran_vkp_utility, utility_name, p_mode, affected=affect_nodes)
            }
            print(all_scores)
            """
            for secret in secret_list:
                simulator.config(secret, epsilon, delta)
                result_random = simulator.formatted_rpg_attack(ran_random)
                result_nb = simulator.formatted_rpg_attack(ran_nb)
                result_ig = simulator.formatted_rpg_attack(ran_ig)
                result_vkp = simulator.formatted_rpg_attack(ran_vkp)
                result_vkp_u = simulator.formatted_rpg_attack(ran_vkp_utility)
                for metric in RESULT_METRICS:
                    metric_row = {
                        'Origin': simulator.score[2],
                        'Random': result_random[metric],
                        'NaiveBayes': result_nb[metric],
                        'InfoGain': result_ig[metric],
                        'V-KP': result_vkp[metric],
                        'V-KP-U': result_vkp_u[metric]
                    }
                    result_table[secret][metric].append(metric_row)
            """
            """ Robustness Skipped
                robust_random = simulator.formatted_robustness(ran_random)
                robust_nb = simulator.formatted_robustness(ran_nb)
                robust_ig = simulator.formatted_robustness(ran_ig)
                robust_vkp = simulator.formatted_robustness(ran_vkp)
                robust_vkp_u = simulator.formatted_robustness(ran_vkp_utility)
                result_table[secret]['robust'].append({
                    'Origin': simulator.formatted_robustness(simulator.rpg),
                    'Random': robust_random,
                    'NaiveBayes': robust_nb,
                    'InfoGain': robust_ig,
                    'V-KP': robust_vkp,
                    'V-KP-U': robust_vkp_u
                })
            """
            utility_table.append(all_scores)
        return pd.DataFrame(utility_table, index=delta_range), result_table

    def toy_example(self, secret, epsilon, delta):
        secrets, exposed = self.resampling()
        price = self.auto_attr_price()
        simulator = AttackSimulator(self.rpg, secrets, secret)
        simulator.config(secret, epsilon, delta, 'nb')
        ran_vkp = self.rpg.v_knapsack_mask(secrets, price, epsilon, delta)
        result_pre = simulator.select_rpg_attack(self.rpg)
        result_vkp = simulator.select_rpg_attack(ran_vkp)
        # Label all the nodes
        prev = {}
        post = {}
        for cate, node_li in result_pre.items():
            for node in node_li:
                prev[node]= cate
        for cate, node_li in result_vkp.items():
            for node in node_li:
                post[node] = cate
        graph = nx.Graph()
        graph.add_nodes_from(self.rpg.soc_node)
        graph.add_edges_from(self.rpg.soc_edge)
        nx.set_node_attributes(graph, 'prev', prev)
        nx.set_node_attributes(graph, 'post', post)
        nx.write_gexf(graph, 'out/toy.gexf')

    def show_result_table(self, result_table, delta_range):
        for secret, table in result_table.items():
            for metric, content in table.items():
                print('========Secret: %s, Metric: %s========' % (secret, metric))
                print(pd.DataFrame(content, index=delta_range))

    def save_result_table(self, result_table, delta_range, output="out"):
        for secret, table in result_table.items():
            for metric, content in table.items():
                pd_table = pd.DataFrame(content, index=delta_range)
                pd_table.to_csv(os.path.join(output, '%s-(%s).csv' % (secret, metric)))
        logging.debug('[ran_lab] Result Output Fin.')

    def save_attack_table(self, result_table, delta_range, output='out'):
        for secret, table in result_table.items():
            pd_table = pd.DataFrame(table, index=delta_range)
            pd_table.to_csv(os.path.join(output, '%s.csv' % (secret)))
        logging.debug('[ran_lab] Result Output Fin.')

    def save_original_attack_table(self, result_table, output='out'):
        for secret, table in result_table.items():
            pd_table = pd.DataFrame(table, index=ML_ALGS)
            pd_table.to_csv(os.path.join(output, '%s.csv' % (secret)))
        logging.debug('[ran_lab] Result Output Fin.')

    def __init__(self, origin_rpg, secret_settings):
        self.rpg = origin_rpg
        self.secret_settings = secret_settings


class RelationExperiment:
    def resampling(self):
        secrets = {node: [] for node in self.rpg.soc_node}
        exposed = {node: [] for node in self.rpg.soc_node}
        for secret, rate in self.secret_settings.items():
            # Select all nodes with the secret
            nodes = np.array([node for node in self.rpg.attr_net.neighbors(secret)])
            # rAnDOM
            indices = np.random.permutation(nodes.shape[0])
            # pool_a: nodes thinking secret, pool_b: nodes not thinking secret
            size = int(nodes.shape[0] * rate)
            pool_a_idx, pool_b_idx = indices[:size], indices[size:]
            # pool_a, pool_b = nodes[pool_a_idx,:], nodes[pool_b_idx,:]
            for idx in pool_a_idx:
                secrets[nodes[idx]] += [secret]
            for idx in pool_b_idx:
                exposed[nodes[idx]] += [secret]
            logging.info('[ran_lab] resampling: %s - s:%d e:%d' % (secret, len(pool_a_idx), len(pool_b_idx)))
        return secrets, exposed

    def generate_test_nodes(self, secret, rate, secrets, exposed):
        non_secret_nodes = np.array([node for node in self.rpg.soc_node
                                     if secret not in secrets[node] and secret not in exposed[node]])
        indices = np.random.permutation(non_secret_nodes.shape[0])
        size = int(non_secret_nodes.shape[0] * rate)

        pool_idx = indices[:size]
        secret_nodes = [node for node, sec in secrets.items() if secret in sec]
        test_nodes = non_secret_nodes[pool_idx].tolist() + secret_nodes
        print(size, size + len(secret_nodes), len(self.rpg.soc_node))
        logging.debug('expected rate = %f ,true rate = %f' % (rate, len(test_nodes)/len(self.rpg.soc_node)))
        return test_nodes

    def auto_edge_price(self, mode='equal'):
        values = dict()
        if mode == 'equal':
            for edge in self.rpg.soc_net.edges():
                values[edge] = 1
        elif mode == 'Jaccard':
            for edge in self.rpg.soc_net.edges():
                u = edge[0]
                v = edge[1]
                u_set = set(self.rpg.attr_net.neighbors(u))
                v_set = set(self.rpg.attr_net.neighbors(v))
                values[edge] = len(u_set & v_set) / float(len(u_set | v_set))
        elif mode == 'AA':
            for edge in self.rpg.soc_net.edges():
                u = edge[0]
                v = edge[1]
                u_set = set(self.rpg.attr_net.neighbors(u))
                v_set = set(self.rpg.attr_net.neighbors(v))
                values[edge] = sum([np.log(len([node for node in self.rpg.attr_net.neighbors(w)]))
                                    for w in u_set & v_set])
        return values

    def edge_utility(self, rpg, mode='equal', p_mode='single', affected=None):
        price = self.auto_edge_price(mode)
        if affected is None:
            all_edges = self.rpg.soc_net.edges()
        else:
            all_edges = affected
        if p_mode == 'single':
            total = sum([price[edge] for edge in all_edges])
            score = sum([price[edge] for edge in all_edges if rpg.soc_net.has_edge(edge[0], edge[1])])
        else:
            total = sum([sum([price[node][attr] for attr in self.rpg.attr_net.neighbors(node)])
                         for node in self.rpg.soc_node])
            score = sum([sum([price[node][attr] for attr in rpg.attr_net.neighbors(node)])
                         for node in rpg.soc_node])
        return score / total

    def delta_experiment(self, epsilon, delta_range, rate=0.5, utility_name='equal'):
        secrets, exposed = self.resampling()
        if utility_name == 'common':
            p_mode = 'double'
        else:
            p_mode = 'single'
        price = self.auto_edge_price(utility_name)
        utility_table = []
        secret_list = [s for s in self.secret_settings.keys()]
        result_table = {secret: {metric: [] for metric in RESULT_METRICS}
                        for secret in secret_list}
        simulator = RelationAttackSimulator(self.rpg, secrets, secret_list[0])
        test_set = {}
        for secret in secret_list:
            test_set[secret] = self.generate_test_nodes(secret, rate, secrets, exposed)
        affected_node = [node for node, secret in secrets.items() if len(secret) > 0]
        affected = [edge for edge in self.rpg.soc_net.edges()
                    if edge[0] in affected_node or edge[1] in affected_node]
        print(len(affected))
        for delta in delta_range:
            ran_random = self.rpg.random_mask(secrets, epsilon, delta, mode='on')
            ran_nb = self.rpg.naive_bayes_relation(secrets, epsilon, delta, factor=0.5)
            ran_ig = self.rpg.entropy_relation(secrets, price, epsilon, delta)
            ran_vkp = self.rpg.eppd_relation(secrets, price, epsilon, delta, True)
            # ran_vkp_utility = self.rpg.v_knapsack_mask(secrets, price, epsilon, delta, p_mode=p_mode)
            # Utility Calculate
            all_scores = {
                'Random': self.edge_utility(ran_random, utility_name, p_mode, affected=affected),
                'NaiveBayes': self.edge_utility(ran_nb, utility_name, p_mode, affected=affected),
                'InfoGain': self.edge_utility(ran_ig, utility_name, p_mode, affected=affected),
                'V-KP': self.edge_utility(ran_vkp, utility_name, p_mode, affected=affected),
                # 'V-KP-U': self.attr_utility(ran_vkp_utility, utility_name, p_mode)
            }
            print(all_scores)
            """
            for secret in secret_list:
                simulator.config(secret, epsilon, delta)
                result_org = simulator.test_attack(test_set[secret], secret)
                result_random = simulator.new_rpg_attack(ran_random, test_set[secret], secret)
                result_nb = simulator.new_rpg_attack(ran_nb, test_set[secret], secret)
                result_ig = simulator.new_rpg_attack(ran_ig, test_set[secret], secret)
                result_vkp = simulator.new_rpg_attack(ran_vkp, test_set[secret], secret)
                # esult_vkp_u = simulator.formatted_rpg_attack(ran_vkp_utility)
                for metric in RESULT_METRICS:
                    metric_row = {
                        'Origin': result_org[metric],
                        'Random': result_random[metric],
                        'NaiveBayes': result_nb[metric],
                        'InfoGain': result_ig[metric],
                        'V-KP': result_vkp[metric],
                        # 'V-KP-U': result_vkp_u[metric]
                    }
                    result_table[secret][metric].append(metric_row)
            """
            utility_table.append(all_scores)
        return pd.DataFrame(utility_table, index=delta_range), result_table

    def delta_directed(self, epsilon, delta_range, rate=0.5, utility_name='equal'):
        secrets, exposed = self.resampling()
        if utility_name == 'common':
            p_mode = 'double'
        else:
            p_mode = 'single'
        price = self.auto_edge_price(utility_name)
        utility_table = []
        secret_list = [s for s in self.secret_settings.keys()]
        test_set = {}
        for secret in secret_list:
            test_set[secret] = self.generate_test_nodes(secret, rate, secrets, exposed)
        affected_node = [node for node, secret in secrets.items() if len(secret) > 0]
        affected = []
        for node in affected_node:
            affected += self.rpg.soc_net.edges(node)
        logging.debug('out edge number = %d' % len(affected))
        for delta in delta_range:
            ran_random = self.rpg.random_directed(secrets, epsilon, delta)
            ran_nb = self.rpg.naive_bayes_directed(secrets, epsilon, delta, factor=0.5)
            ran_ig = self.rpg.entropy_directed(secrets, price, epsilon, delta)
            ran_vkp = self.rpg.eppd_directed(secrets, price, epsilon, delta)
            # ran_vkp_utility = self.rpg.v_knapsack_mask(secrets, price, epsilon, delta, p_mode=p_mode)
            # Utility Calculate
            all_scores = {
                'Random': self.edge_utility(ran_random, utility_name, p_mode, affected=affected),
                'NaiveBayes': self.edge_utility(ran_nb, utility_name, p_mode, affected=affected),
                'InfoGain': self.edge_utility(ran_ig, utility_name, p_mode, affected=affected),
                'V-KP': self.edge_utility(ran_vkp, utility_name, p_mode, affected=affected),
                # 'V-KP-U': self.attr_utility(ran_vkp_utility, utility_name, p_mode)
            }
            print(all_scores)
            utility_table.append(all_scores)
        return pd.DataFrame(utility_table, index=delta_range)

    def attack_experiment(self, epsilon, delta_range, rate=0.5):
        secrets, exposed = self.resampling()
        price = self.auto_edge_price()
        test_set = {}
        secret_list = [s for s in self.secret_settings.keys()]
        simulator = RelationAttackSimulator(self.rpg, secrets, secret_list[0])
        result_table = {secret: []
                        for secret in secret_list}
        for secret in secret_list:
            test_set[secret] = self.generate_test_nodes(secret, rate, secrets, exposed)
        for delta in delta_range:
            ran_vkp = self.rpg.eppd_relation(secrets, price, epsilon, delta, True)
            for secret in secret_list:
                tmp_line = {}
                simulator.config(secret, epsilon, delta)
                for alg in RCLASSIFIERS:
                    result_vkp = simulator.new_rpg_attack(ran_vkp, test_set[secret], secret, alg)
                    result_org = simulator.test_attack(test_set[secret], secret, alg)
                    tmp_line[alg] = result_vkp['f1']
                    tmp_line[alg + '-o'] = result_org['f1']
                print(tmp_line)
                result_table[secret].append(tmp_line)
        return result_table

    def origin_attack_experiment(self, rate=0.5):
        secrets, exposed = self.resampling()
        test_set = {}
        secret_list = [s for s in self.secret_settings.keys()]
        simulator = RelationAttackSimulator(self.rpg, secrets, secret_list[0])
        result_table = {secret: []
                        for secret in secret_list}
        for secret in secret_list:
            test_set[secret] = self.generate_test_nodes(secret, rate, secrets, exposed)
        for secret in secret_list:
            for alg in RCLASSIFIERS:
                result_org = simulator.test_attack(test_set[secret], secret, alg)
                tmp_line = result_org
                result_table[secret].append(tmp_line)
        return result_table

    def attack_cross_experiment(self, epsilon, delta_range, rate=0.5):
        secrets, exposed = self.resampling()
        price = self.auto_edge_price()
        secret_list = [s for s in self.secret_settings.keys()]
        simulator = RelationAttackSimulator(self.rpg, secrets, secret_list[0])
        result_table = {secret: []
                        for secret in secret_list}
        for delta in delta_range:
            ran_vkp = self.rpg.eppd_relation(secrets, price, epsilon, delta, True)
            for secret in secret_list:
                tmp_line = {}
                simulator.config(secret, epsilon, delta)
                for alg in RCLASSIFIERS:
                    sub_sim = RelationAttackSimulator(ran_vkp, secrets, secret)
                    result_vkp = sub_sim.attack(rate)
                    result_org = simulator.attack(rate)
                    tmp_line[alg] = result_vkp
                    tmp_line[alg + '-o'] = result_org
                print(tmp_line)
                result_table[secret].append(tmp_line)
        return result_table

    def org_attack(self, epsilon, delta, rate=0.5):
        secrets, exposed = self.resampling()
        test_set = {}
        secret_list = [s for s in self.secret_settings.keys()]
        simulator = RelationAttackSimulator(self.rpg, secrets, secret_list[0])
        result_table = {secret: []
                        for secret in secret_list}
        for secret in secret_list:
            test_set[secret] = self.generate_test_nodes(secret, rate, secrets, exposed)
        for secret in secret_list:
            tmp_line = {}
            simulator.config(secret, epsilon, delta)
            for alg in RCLASSIFIERS:
                result_org = simulator.test_attack(test_set[secret], secret, alg)
                tmp_line[alg] = result_org['f1']
            print(tmp_line)
            result_table[secret].append(tmp_line)
        return result_table

    def small_test_expr(self, secret, rate):
        secrets, exposed = self.resampling()
        test_set = self.generate_test_nodes(secret, rate, secrets, exposed)
        simulator = RelationAttackSimulator(self.rpg, secrets, secret)
        result = simulator.test_attack(test_set, secret)
        return result

    def relation_attack(self, rpg, secret, rate, secrets, exposed):
        # secrets, exposed = self.resampling()
        test_set = self.generate_test_nodes(secret, rate, secrets, exposed)
        simulator = RelationAttackSimulator(rpg, secrets, secret)
        result = simulator.test_attack(test_set, secret)
        return result

    def plain_attack(self, epsilon, delta, rate=0.5):
        secrets, exposed = self.resampling()
        secret_list = [s for s in self.secret_settings.keys()]
        simulator = RelationAttackSimulator(self.rpg, secrets, secret_list[0])
        result_table = {secret: []
                        for secret in secret_list}
        for secret in secret_list:
            simulator.config(secret, epsilon, delta)
            result_org = simulator.attack(rate)
            print(result_org)
            result_table[secret].append(result_org)
        return result_table

    def save_attack_table(self, result_table, delta_range, output='out'):
        for secret, table in result_table.items():
            pd_table = pd.DataFrame(table, index=delta_range)
            pd_table.to_csv(os.path.join(output, '%s.csv' % (secret)))
        logging.debug('[ran_lab] Result Output Fin.')

    def save_original_attack_table(self, result_table, output='out'):
        for secret, table in result_table.items():
            pd_table = pd.DataFrame(table, index=RCLASSIFIERS)
            pd_table.to_csv(os.path.join(output, '%s.csv' % (secret)))
        logging.debug('[ran_lab] Result Output Fin.')

    def save_result_table(self, result_table, delta_range, output="out"):
        for secret, table in result_table.items():
            for metric, content in table.items():
                pd_table = pd.DataFrame(content, index=delta_range)
                pd_table.to_csv(os.path.join(output, '%s-(%s).csv' % (secret, metric)))
        logging.debug('[ran_lab] Result Output Fin.')

    def __init__(self, origin_rpg, secret_settings):
        self.rpg = origin_rpg
        self.secret_settings = secret_settings


def single_attack_test_ver2(simulator, price, secret, epsilon, delta):
    simulator.config(secret, epsilon, delta)
    # Entropy Masking
    new_ran = simulator.rpg.entropy_mask(simulator.secrets, price, epsilon, delta)
    result = simulator.rpg_attack(new_ran)
    etp_res = {'precision': result['score'][0],
               'recall': result['score'][1],
               'f1': result['score'][2],
               'utility': result['utility']}

    # VKP Masking
    new_ran = simulator.rpg.v_knapsack_mask(simulator.secrets, price, epsilon, delta, mode='greedy')
    result = simulator.rpg_attack(new_ran)
    vkp_res = {'precision': result['score'][0],
               'recall': result['score'][1],
               'f1': result['score'][2],
               'utility': result['utility']}
    return etp_res, vkp_res


def single_attribute_batch(secret, epsilon, delta_range):
    exp1 = list()
    exp2 = list()
    for delta in delta_range:
        e1, e2 = single_attribute_test(secret, epsilon, delta)
        exp1.append(e1)
        exp2.append(e2)
    df1 = pd.DataFrame(exp1, index=delta_range)
    df2 = pd.DataFrame(exp2, index=delta_range)
    df1.to_csv('out/%s-exp1.csv' % secret)
    df2.to_csv('out/%s-exp2.csv' % secret)


def single_attribute_batch_ver2(secret, epsilon, delta_range):
    a = FacebookNetwork()
    price = dict()
    secrets = dict()
    for i in a.rpg.attr_node:
        price[i] = 1
    for n in a.rpg.soc_node:
        if a.rpg.attr_net.has_edge(n, secret):
            secrets[n] = [secret]
        else:
            secrets[n] = []
    # Basic Info Display
    logging.debug('[ran_lab] Single Attribute Test - affected attributes=%d'
                  % (a.rpg.affected_attribute_number(secrets)))
    rpg = a.rpg
    # performance - utility
    simulator = AttackSimulator(rpg, secrets, secret)
    res1 = []
    res2 = []
    for delta in delta_range:
        etp_res, vkp_res = single_attack_test_ver2(simulator, price, secret, epsilon, delta)
        res1.append(etp_res)
        res2.append(vkp_res)
    df1 = pd.DataFrame(res1, index=delta_range)
    df2 = pd.DataFrame(res2, index=delta_range)
    df1.to_csv('out/%s-res1.csv' % secret)
    df2.to_csv('out/%s-res2.csv' % secret) 


class RelationAttackSimulator:
    def attack(self, sample_rate):
        result = self.attacker.cross_validation(10, sample_rate)
        formatted = self.attacker.result_formatter(result, self.secret)
        f1_list = [item['f1'] for item in formatted]
        return np.average(f1_list)

    def test_attack(self, test_set, secret, classifier='wvrn'):
        self.attacker.generate_data_set_relation_only(secret)
        result = self.attacker.run_test(test_set, secret, classifier=classifier)
        return self.attacker.result_formatter(result, secret)[0]

    def new_rpg_attack(self, rpg, test_set, secret, classifier='wvrn'):
        self.attacker.rpg_generate_data_set(rpg, secret)
        result = self.attacker.run_test(test_set, secret, classifier=classifier)
        return self.attacker.result_formatter(result, secret)[0]

    def config(self, secret, epsilon, delta):
        self.secret = secret
        self.epsilon = epsilon
        self.delta = delta
        self.attacker.generate_data_set(secret)

    def __init__(self, rpg, secrets, secret, filename='ranykm', epsilon=0.1, delta=0.0):
        self.rpg = rpg
        self.secrets = secrets
        self.secret = secret
        self.epsilon = epsilon
        self.delta = delta
        self.filename = filename
        self.attacker = RelationAttack(self.rpg, self.secrets, self.filename)
        self.attacker.generate_data_set(secret)


def tmp_relation_test():
    a = FacebookNetwork()
    price = dict()
    rprice = dict()
    secrets = dict()
    secret = 'aenslid-50'
    epsilon = 0.1
    delta = 0.00001
    for i in a.rpg.attr_node:
        price[i] = 1
    for n in a.rpg.soc_node:
        if a.rpg.attr_net.has_edge(n, secret):
            secrets[n] = [secret]
        else:
            secrets[n] = []
    simulator = RelationAttackSimulator(a.rpg, secrets, secret, 'origin', epsilon, delta)
    print(simulator.attack(0.8))
    for i in a.rpg.soc_net.edges():
        rprice[i] = 1
    new_ran = a.rpg.d_knapsack_relation(secrets, rprice, epsilon, delta)
    simulator = RelationAttackSimulator(new_ran, secrets, secret, 'dkp', epsilon, delta)
    print(simulator.attack(0.8))

 
def attr_statistics(rpg) :
    stat = [{'name': attr, 'number': len(rpg.attr_net.neighbors(attr))} for attr in rpg.attr_node]
    stat_pd = pd.DataFrame(stat)
    stat_pd = stat_pd.sort_values(by='number', ascending=False)
    print(stat_pd.head(50))


def attr_lab_0223():
    a = FacebookNetwork()
    rate = 1.0
    expr_settings = {
        'aenslid-538': rate,
        'aby-5': rate,
        'ahnid-84': rate,
        # 'alnid-617': rate,
        'aencnid-14': rate
    }
    output_dir = "/Users/jiayichen/ranproject/res317-attr/"
    expr = AttributeExperiment(a.rpg, expr_settings)
    utility, result_table = expr.delta_experiment(0.5, np.arange(0, 0.31, 0.03), 'common')
    utility.to_csv(os.path.join(output_dir, 'utility-c.csv'))
    # expr.save_result_table(result_table, np.arange(0, 0.21, 0.02), output_dir)


def attack_lab_0226():
    a = FacebookNetwork()
    rate = 1.0
    expr_settings = {
        'aenslid-538': rate,
        'aby-5': rate,
        'ahnid-84': rate,
        # 'alnid-617': rate,
        'aencnid-14': rate
    }
    output_dir = "/Users/jiayichen/ranproject/res317-2/"
    expr = AttributeExperiment(a.rpg, expr_settings)
    # result_table = expr.attack_experiment(0.5, np.arange(0, 0.31, 0.03))
    # expr.save_attack_table(result_table, np.arange(0, 0.31, 0.03), output_dir)
    result_table = expr.org_attack_experiment()
    expr.save_original_attack_table(result_table, output_dir)

def script_to_del():
    # a = FacebookNetwork()
    a = FacebookEgoNet('0')
    rate = 0.5
    """
    expr_settings = {
        'aenslid-538': rate,
        'aby-5': rate,
        'ahnid-84': rate,
        # 'alnid-617': rate,
        'aencnid-14': rate
    }
    """
    expr_settings = {
        'aensl-50': rate
    }

    rprice = {}
    epsilon = 0.1
    delta = 0.12
    for i in a.rpg.soc_net.edges():
        rprice[i] = 1
    expr = AttributeExperiment(a.rpg, expr_settings)
    secrets, _ = expr.resampling()
    new_ran = a.rpg.entropy_relation(secrets, rprice, epsilon, delta)
    print(a.rpg.exceed_limits(new_ran, secrets, epsilon, delta))
    new_ran1_5 = a.rpg.naive_bayes_relation(secrets, epsilon, delta, 0.5)
    print(a.rpg.exceed_limits(new_ran1_5, secrets, epsilon, delta))
    shan_bian = []
    for i in range(10):
        new_ran2 = a.rpg.random_relation(secrets, epsilon, delta)
        shan_bian.append(new_ran2.soc_net.number_of_edges() - a.rpg.soc_net.number_of_edges())
        print(a.rpg.exceed_limits(new_ran2, secrets, epsilon, delta))
    print(np.average(shan_bian))

    # new_ran3 = a.rpg.v_knapsack_relation(secrets, rprice, epsilon, delta)
    new_ran3 = a.rpg.eppd_relation(secrets, rprice, epsilon, delta)
    print(a.rpg.exceed_limits(new_ran3, secrets, epsilon, delta))
    new_ran4 = a.rpg.eppd_relation(secrets, rprice, epsilon, delta, True)
    print(a.rpg.exceed_limits(new_ran4, secrets, epsilon, delta))


def nice_figure():
    a = FacebookEgoNet('0')
    rate = 1.0
    expr_settings = {
        'aensl-50': rate
    }
    expr = AttributeExperiment(a.rpg, expr_settings)
    expr.toy_example('aensl-50', 0.1, 0.3)

def relation_lab_0308():

    a = FacebookNetwork()
    rate = 0.5
    expr_settings = {
        'aenslid-538': rate,
        'aby-5': rate,
        'ahnid-84': rate,
        # 'alnid-617': rate,
        'aencnid-14': rate
    }
    expr = RelationExperiment(a.rpg, expr_settings)
    output_dir = "/Users/jiayichen/ranproject/res326-edge/"
    utility, result_table = expr.delta_experiment(0.5, np.arange(0, 0.31, 0.03), rate, utility_name='equal')
    utility.to_csv(os.path.join(output_dir, 'utility.csv'))
    # expr.save_result_table(result_table, np.arange(0, 0.31, 0.03), output_dir)



def relation_small_test():
    a = FacebookEgoNet('0')
    rate = 0.5
    expr_settings = {
        'aensl-50': rate
    }
    expr = RelationExperiment(a.rpg, expr_settings)
    output_dir = "/Users/jiayichen/ranproject/res308/"
    utility, result_table = expr.delta_experiment(0.1, np.arange(0, 0.21, 0.02), rate, utility_name='AA')
    # utility.to_csv(os.path.join(output_dir, 'utility-a.csv'))
    # expr.save_result_table(result_table, np.arange(0, 0.21, 0.02), output_dir)


def attack_lab_0306():
    a = FacebookEgoNet('0')
    rate = 0.5
    rprice = {}
    for i in a.rpg.soc_net.edges():
        rprice[i] = 1
    expr_settings = {
        'aensl-50': rate
    }
    expr = RelationExperiment(a.rpg, expr_settings)
    output_dir = "/Users/jiayichen/ranproject/res314/"
    result_table = expr.attack_experiment(0.1, np.arange(0, 0.21, 0.02), rate)
    expr.save_attack_table(result_table, np.arange(0, 0.21, 0.02), output_dir)


def attack_lab_0313():
    a = FacebookNetwork()
    rate = 0.5
    expr_settings = {
        'aenslid-538': rate,
        'aby-5': rate,
        'ahnid-84': rate,
        # 'alnid-617': rate,
        'aencnid-14': rate
    }
    expr = RelationExperiment(a.rpg, expr_settings)
    output_dir = "/Users/jiayichen/ranproject/res313/"
    result_table = expr.attack_experiment(0.1, np.arange(0, 0.51, 0.1))
    expr.save_attack_table(result_table, np.arange(0, 0.51, 0.1), output_dir)


def original_attack():
    a = FacebookNetwork()
    for rate in np.arange(0.1, 1.0, 0.1):
        print('current rate : %f' % rate)
        expr_settings = {
            'aenslid-538': rate,
            # 'aby-5': rate,
            # 'ahnid-84': rate,
            # 'alnid-617': rate,
            # 'aencnid-14': rate
        }
        expr = RelationExperiment(a.rpg, expr_settings)

        print(expr.org_attack(0.1, 0.2, rate))
    # print(expr.plain_attack(0.1, 0.2, rate=0.5))



if __name__ == '__main__':
    # single_attribute_test('aenslid-538', 0.1, 0)
    # single_attribute_batch_ver2('aenslid-52', 0.1, np.arange(0, 1.0, 0.1))
    # tmp_relation_test()
    """
    a = FacebookNetwork()
    expr = AttributeExperiment(a.rpg, {'aenslid-538': 1.0, 'aenslid-52': 1.0})
    utility, result_table = expr.delta_experiment(0.1, np.arange(0, 0.4, 0.1))
    print(utility)
    expr.show_result_table(result_table, np.arange(0, 0.4, 0.1))
    """
    # attr_statistics(FacebookNetwork().rpg)
    # attr_lab_0223()
    # attack_lab_0226()
    # script_to_del()
    # nice_figure()
    # relation_small_test()
    # attack_lab_0306()
    relation_lab_0308()
    # attack_lab_0313()
    # original_attack()
