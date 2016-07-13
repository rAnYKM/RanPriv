# Project Name: rAnPrivGP
# Author: rAnYKM (Jiayi Chen)
#
#          ___          ____       _       __________
#    _____/   |  ____  / __ \_____(_)   __/ ____/ __ \
#   / ___/ /| | / __ \/ /_/ / ___/ / | / / / __/ /_/ /
#  / /  / ___ |/ / / / ____/ /  / /| |/ / /_/ / ____/
# /_/  /_/  |_/_/ /_/_/   /_/  /_/ |___/\____/_/
#
# Script Name: test.py
# Date: July. 5, 2016

import numpy as np
import logging
from snap_facebook import FacebookEgoNet


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def experiment(data, secret_cate, ar, dr, e):
    fb = FacebookEgoNet(data)
    # Build secret dict
    secrets = dict()
    epsilon = dict()
    ep2 = dict()
    for node in fb.ran.soc_net.nodes():
        feature = [attr for attr in fb.ran.soc_attr_net.neighbors(node)
                   if attr[0] == 'a']
        secret = [attr for attr in feature if attr.split('-')[0] in secret_cate]
        secrets[node] = secret
        epsilon[node] = [np.log2(e) -
                         np.log2(len(fb.ran.soc_attr_net.neighbors(a))/float(fb.ran.soc_net.number_of_nodes()))
                         for a in secret]
        ep2[node] = [e] * len(secret)
    price = fb.ran.value_of_attribute('common')
    price2 = fb.ran.value_of_relation('equal')
    att_ran = fb.ran.random_sampling(ar)
    def_ran, stat1, _ = fb.ran.adv_random_masking(secrets, ep2)
    greedy, stat2 = fb.ran.d_knapsack_mask(secrets, price, epsilon)
    # greedy2 = greedy.d_knapsack_relation(secrets, price2, epsilon)
    s_good, stat3 = fb.ran.s_knapsack_mask(secrets, price, ep2, 'dp')
    s_greedy, stat4 = fb.ran.s_knapsack_mask(secrets, price, ep2, 'greedy')
    s_dual, stat5= fb.ran.s_knapsack_mask(secrets, price, ep2, 'dual_greedy')
    # s_gual, tp4 = fb.ran.s_knapsack_mask(secrets, ep2, 'dual_dp')
    # def_ran.inference_attack(secrets, def_ran)
    # greedy.inference_attack(secrets, greedy)
    _, res = fb.ran.inference_attack(secrets, att_ran)
    _, res2 = def_ran.inference_attack(secrets, att_ran)
    # _, res4 = def_ran.inference_attack_relation(secrets, att_ran)
    # _, res3 = fb.ran.inference_attack_relation(secrets, att_ran)
    _, res5 = greedy.inference_attack(secrets, att_ran)
    # _, res6 = greedy2.inference_attack_relation(secrets, att_ran)
    _, res7 = s_good.inference_attack(secrets, att_ran, e)
    _, res8 = s_greedy.inference_attack(secrets, att_ran, e)
    _, res9 = s_dual.inference_attack(secrets, att_ran, e)

    _, max_score = fb.ran.utility_measure(secrets, price)
    _, score1 = def_ran.utility_measure(secrets, price)
    _, score2 = greedy.utility_measure(secrets, price)
    _, score3 = s_good.utility_measure(secrets, price)
    _, score4 = s_greedy.utility_measure(secrets, price)
    _, score5 = s_dual.utility_measure(secrets, price)
    # d, res10 = s_gual.inference_attack(secrets, fb.ran, e)
    print res, res2, res5, res7, res8, res9
    # print a, b
    """
    for i in range(len(tp1)):
        if tp1[i][0] != tp2[i][0]:
            print tp1[i], tp2[i]
    """
    stat = [stat1, stat2, stat3, stat4, stat5]
    ress = [res2, res5, res7, res8, res9]
    scos = [score1, score2, score3, score4, score5]
    n_scos = [i/float(max_score) for i in scos]
    reff = res
    return stat, ress, reff, n_scos


def experiment_relation(data, secret_cate, ar, dr, e):
    fb = FacebookEgoNet(data)
    # Build secret dict
    secrets = dict()
    epsilon = dict()
    ep2 = dict()
    for node in fb.ran.soc_net.nodes():
        feature = [attr for attr in fb.ran.soc_attr_net.neighbors(node)
                   if attr[0] == 'a']
        secret = [attr for attr in feature if attr.split('-')[0] in secret_cate]
        secrets[node] = secret
        epsilon[node] = [np.log2(e) -
                         np.log2(len(fb.ran.soc_attr_net.neighbors(a))/float(fb.ran.soc_net.number_of_nodes()))
                         for a in secret]
        ep2[node] = [e] * len(secret)
    price = fb.ran.value_of_attribute('common')
    price2 = fb.ran.value_of_relation('equal')
    att_ran = fb.ran.random_sampling(ar)
    def_ran, stat1, _ = fb.ran.adv_random_masking(secrets, ep2)
    greedy, stat2 = fb.ran.d_knapsack_mask(secrets, price, epsilon)
    greedy2, stat3 = greedy.d_knapsack_relation(secrets, price2, epsilon)
    # s_good, stat3 = fb.ran.s_knapsack_relation(secrets, price2, ep2, 'dp')
    s_greedy, stat4 = fb.ran.s_knapsack_relation(secrets, price2, ep2, 'greedy')
    s_dual, stat5= fb.ran.s_knapsack_relation(secrets, price2, ep2, 'dual_greedy')
    # s_gual, tp4 = fb.ran.s_knapsack_mask(secrets, ep2, 'dual_dp')
    # def_ran.inference_attack(secrets, def_ran)
    # greedy.inference_attack(secrets, greedy)
    # _, res = fb.ran.inference_attack(secrets, att_ran)
    # _, res2 = def_ran.inference_attack(secrets, att_ran)
    _, res4 = def_ran.inference_attack_relation(secrets, att_ran)
    _, res3 = fb.ran.inference_attack_relation(secrets, att_ran)
    # _, res5 = greedy.inference_attack(secrets, att_ran)
    _, res6 = greedy2.inference_attack_relation(secrets, att_ran)
    # _, res7 = s_good.inference_attack(secrets, att_ran, e)
    _, res8 = s_greedy.inference_attack_relation(secrets, att_ran)
    _, res9 = s_dual.inference_attack_relation(secrets, att_ran)
    # d, res10 = s_gual.inference_attack(secrets, fb.ran, e)
    print res3, res4, res6, res8, res9
    # print a, b
    """
    for i in range(len(tp1)):
        if tp1[i][0] != tp2[i][0]:
            print tp1[i], tp2[i]
    """
    stat = [stat1, stat3, stat4, stat5]
    ress = [res4, res6, res8, res9]
    reff = res3
    return stat, ress, reff

def data_record(xs, ys, filename):
    with open(filename, 'w') as fp:
        for x in xs:
            fp.write(' '.join([str(i) for i in x]) + '\n')
        fp.write('\n')
        for y in ys:
            fp.write(' '.join([str(i) for i in y]) + '\n')

if __name__ == '__main__':
    sec = ['aensl', 'aencn']
    s1 = []
    s2 = []
    s3 = []
    for i in np.arange(0.05, 1, 0.05):
        print i
        stat, ress, reff, scos = experiment('0', sec, 1, 1, i)
        s1.append(stat)
        s2.append(ress)
        s3.append(scos)
    data_record([np.arange(0.05, 1, 0.05)], s1, 'edge_reduce3.txt')
    data_record([np.arange(0.05, 1, 0.05)], s2, 'performance3.txt')
    data_record([np.arange(0.05, 1, 0.05)], s3, 'score3.txt')
