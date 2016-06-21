


import networkx as nx
import numpy as np
from random import Random
from ran_knapsack import knapsack


class RanGraph:
    """
    A Ran Social Network Graph Involves the following three sub-graphs:
    social network graph (social nodes, also actors)
    social attribute network graph (social nodes with attribute nodes)
    attribute network graph (attribute nodes)

    *ATTENTION: PLEASE AVOID DUPLICATE SOCIAL NODE AND ATTRIBUTE NAME*

    Social Node Naming:
    Simply use its original ID

    Attribute Naming:
    'a' + ABBR. of PATH + feature name
        Facebook example:
        education start_date 30 => aes30
        Google+ example:
        job_title software => ajsoftware
    """
    @staticmethod
    def __conditional_prob(set_a, set_b):
        """
        return the conditional probability of two sets P(a|b)
        :param set_a: set
        :param set_b: set
        :return: float
        """
        if len(set_b) == 0:
            return 0
        return len(set_a & set_b) / float(len(set_b))

    @staticmethod
    def __joint_prob(set_a, set_b, set_u):
        """
        return the joint probability of two sets P(a,b) in the set_u where the elements in set_a
        and set_b are supposed to be in the set_u. Otherwise, return 0.
        :param set_a: set
        :param set_b: set
        :param set_u: set
        :return: float
        """
        if set_a <= set_u and set_b <= set_u:
            return len(set_a & set_b) / float(len(set_u))
        else:
            return 0

    @staticmethod
    def __conditional_entropy(set_a, set_b):
        """
        return the conditional entropy of two sets H(a|b). It means the uncertainty of a given b.
        :param set_a: set
        :param set_b: set
        :return: float
        """
        return np.log2(len(set_a & set_b) / float(len(set_b)))

    def __build_soc_net(self, soc_node, soc_edge):
        if self.is_directed:
            net = nx.DiGraph()
        else:
            net = nx.Graph()
        net.add_nodes_from(soc_node)
        net.add_edges_from(soc_edge)
        return net

    def __build_attr_net(self):
        attr_net = nx.Graph()
        nodes = [node for node in self.soc_attr_net.nodes() if node[0] == 'a']
        attr_net.add_nodes_from(nodes)
        for ns in nodes:
            for nd in nodes:
                if ns == nd:
                    continue
                elif not attr_net.has_edge(ns, nd):
                    # Calculate the correlation between two attribute nodes
                    # Jaccard Coefficient
                    neighbor_s = set(self.soc_attr_net.neighbors(ns))
                    neighbor_d = set(self.soc_attr_net.neighbors(nd))
                    if len(neighbor_s | neighbor_d) == 0:
                        cor = 0
                    else:
                        cor = len(neighbor_s & neighbor_d) / float(len(neighbor_s | neighbor_d))
                    if cor > 0.0:
                        attr_net.add_edge(ns, nd, {'weight': cor})
        return attr_net

    def __build_di_attr_net(self):
        attr_net = nx.DiGraph()
        nodes = [node for node in self.soc_attr_net.nodes() if node[0] == 'a']
        attr_net.add_nodes_from(nodes)
        for ns in nodes:
            for nd in nodes:
                if ns == nd:
                    continue
                elif not attr_net.has_edge(ns, nd):
                    # Calculate the correlation between two attribute nodes
                    # Conditional Probability
                    neighbor_s = set(self.soc_attr_net.neighbors(ns))
                    neighbor_d = set(self.soc_attr_net.neighbors(nd))
                    cor1 = self.__conditional_prob(neighbor_d, neighbor_s)
                    cor2 = self.__conditional_prob(neighbor_s, neighbor_d)
                    if cor1 > 0.0:
                        attr_net.add_edge(ns, nd, {'weight': cor1})
                    if cor2 > 0.0:
                        attr_net.add_edge(nd, ns, {'weight': cor2})
        return attr_net

    def __build_soc_attr_net(self, soc_node, attr_node, soc_edge, attr_edge):
        if self.is_directed:
            net = nx.DiGraph()
        else:
            net = nx.Graph()
        net.add_nodes_from(soc_node + attr_node)
        net.add_edges_from(soc_edge + attr_edge)
        return net

    def attribute_correlation(self, source, destination):
        """
        Calculate the correlation between source and destination attributes
        :param source: string
        :param destination: string
        :return: float
        """
        neighbor_s = set(self.soc_attr_net.neighbors(source))
        neighbor_d = set(self.soc_attr_net.neighbors(destination))
        return len(neighbor_s & neighbor_d)/float(len(neighbor_s | neighbor_d))

    def obtain_set(self, features):
        set_r = set(self.soc_net.nodes())
        for f in features:
            set_r &= set([n for n in self.soc_attr_net.neighbors(f)])
        return set_r

    def random_mask(self, secret, mask_ratio=0.1):
        """
        return a sub graph with random mask algorithm
        :param secret: string
        :param mask_ratio: float
        :return: RanGraph
        """
        soc_node = self.soc_net.nodes()
        attr_node = self.attr_net.nodes()
        a = Random()
        soc_edge = [edge for edge in self.soc_edge if a.random() >= mask_ratio]
        attr_edge = [edge for edge in self.attr_edge
                     if edge[1] == secret or a.random() >= mask_ratio]
        new_ran = RanGraph(soc_node, attr_node, soc_edge, attr_edge)
        print new_ran.secret_disclosure_rate(secret)
        return new_ran

    def knapsack_mask(self, secret, epsilon=0.5):
        soc_node = self.soc_net.nodes()
        attr_node = self.attr_net.nodes()
        soc_edge = self.soc_edge
        attr_edge = []
        ctr = 0
        w_set = set([n for n in self.soc_attr_net.neighbors(secret)])
        print len(w_set)
        for n in soc_node:
            if not self.soc_attr_net.has_edge(n, secret):
                attr_edge += [(n, attr) for attr in self.soc_attr_net.neighbors(n) if attr[0] == 'a']
            else:
                fn = [i for i in self.soc_attr_net.neighbors(n)
                        if i[0] == 'a']
                feat = [(1, set(self.soc_attr_net.neighbors(i))) for i in self.soc_attr_net.neighbors(n)
                        if i[0] == 'a']
                val, sel = knapsack(feat, epsilon, w_set, set(self.soc_net.nodes()))
                attr_edge += [(n, fn[i]) for i in sel]
                attr_edge.append((n, secret))
                ctr += 1
                if ctr % 10 == 0:
                    print ctr
        new_ran = RanGraph(soc_node, attr_node, soc_edge, attr_edge)
        print new_ran.secret_disclosure_rate(secret)
        return new_ran

    def secret_analysis(self, secret):
        """
        return the correlations dict of a given secret (private attribute)
        :param secret: string
        :return: dict
        """
        secret_related = self.di_attr_net.successors(secret)
        return {i: self.attribute_correlation(i, secret) for i in secret_related}

    def secret_disclosure_rate(self, secret):
        """
        compare the new ran graph with the original one to obtain the disclosure_rate
        :return: float
        """
        # TODO: finish the complete disclosure rate calculation
        pgf = []
        for soc in self.soc_net.nodes_iter():
            feature = [node for node in self.soc_attr_net.neighbors_iter(soc)
                       if node[0] == 'a' and node != secret]
            rate = self.prob_given_feature(secret, feature)
            if self.soc_attr_net.has_edge(soc, secret):
                # print soc
                pgf.append(rate)
        print pgf

        pgn = []
        for soc in self.soc_net.nodes_iter():
            neighbor = [node for node in self.soc_net.neighbors_iter(soc)]
            rate = self.prob_given_feature(secret, neighbor)
            if self.soc_attr_net.has_edge(soc, secret):
                pgn.append(rate)
        print pgn
        return 1

    def secret_attack(self, secret, attack_graph):
        pgf = []
        for soc in self.soc_net.nodes_iter():
            feature = [node for node in self.soc_attr_net.neighbors_iter(soc)
                       if node[0] == 'a' and node != secret]
            att_feature = [node for node in feature if attack_graph.soc_attr_net.has_edge(soc, node)]
            rate = self.prob_given_feature(secret, feature)
            att_rate = attack_graph.prob_given_feature(secret, att_feature)
            if self.soc_attr_net.has_edge(soc, secret):
                pgf.append(att_rate)
        print pgf
        return np.average(pgf)

    def prob_given_feature(self, secret, feature):
        """
        Given a feature list, return the probability of owning a secret.
        :param secret: string
        :param feature: list
        :return: float
        """
        set_f = set(self.soc_net.nodes())
        first = True
        for f in feature:
            if first:
                set_f = set(self.soc_attr_net.neighbors(f))
                first = False
            else:
                set_f &= set(self.soc_attr_net.neighbors(f))
                if len(set_f) == 0:
                    return 0
        set_s = set(self.soc_attr_net.neighbors(secret))
        return self.__conditional_prob(set_s, set_f)

    def prob_given_neighbor(self, secret, neighbor):
        """
        Given a feature list, return the probability of owning a secret.
        :param secret: string
        :param neighbor: list
        :return: float
        """
        set_f = set(self.soc_net.nodes())
        first = True
        for f in neighbor:
            if first:
                set_f = set(self.soc_net.neighbors(f))
                first = False
            else:
                set_f &= set(self.soc_net.neighbors(f))
                if len(set_f) == 0:
                    return 0
        set_s = set(self.soc_attr_net.neighbors(secret))
        return self.__conditional_prob(set_s, set_f)

    def __init__(self, soc_node, attr_node, soc_edge, attr_edge, is_directed=False):
        if is_directed:
            self.is_directed = True
        else:
            self.is_directed = False
        self.soc_node = soc_node
        self.attr_node = attr_node
        self.soc_edge = soc_edge
        self.attr_edge = attr_edge
        self.soc_net = self.__build_soc_net(soc_node, soc_edge)
        self.soc_attr_net = self.__build_soc_attr_net(soc_node, attr_node, soc_edge, attr_edge)
        """
        Attribute Network is built from Social Attribute Network
        Edges in Attribute Network represent the correlation
        Directed and Undirected attribute networks are both provided
        """
        self.attr_net = self.__build_attr_net()
        self.di_attr_net = self.__build_di_attr_net()
