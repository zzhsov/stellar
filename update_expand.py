# import src.GameMap as GameMap#垃圾python
from GameMap import GameMap


class player_class:  # 格式要求
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.strategy = 'expand'
        self.d = None
        self.turn = 0

    def view(self, node, map_info):
        nextlst = node.get_next()
        nextempty = []
        nextfri = []
        nextenemy = []
        for id in nextlst:
            if map_info[id].belong == -1:
                nextempty.append(map_info[id])
            elif map_info[id].belong == self.player_id:
                nextfri.append(map_info[id])
            elif map_info[id].belong == 1 - self.player_id:
                nextenemy.append(map_info[id])
        # print(nextempty,nextfri,nextenemy)
        return (nextempty, nextfri, nextenemy)  # 以node为元素的列表

    def frontier(self, node, map_info):
        return len(self.view(node, map_info)[2]) > 0

    def expandable(self, node, map_info):
        return len(self.view(node, map_info)[0]) > 0

    def expand(self, node, map_info):  # 返回这个节点为起点的一切指令
        # 读取一个节点的值
        action = []
        if node.belong == self.player_id:
            # print('@')
            info = self.view(node, map_info)
            nextempty = info[0]
            nextfri = info[1]
            nextenemy = info[2]
            if len(nextenemy) == 0:
                if len(nextempty) > 0:
                    free = node.power[self.player_id] - 20  # 可调节的,需保证派出兵力大于1
                    if free - len(nextempty) > 0:
                        for nod in nextempty:
                            action.append((node.number, nod.number, free / len(nextempty)))
                else:
                    free = node.power[self.player_id] - 30
                    less = []
                    for nod in nextfri:
                        if nod.power[self.player_id] < 0.8 * node.power[self.player_id]:  # 可调参
                            less.append(nod)
                    for nod in less:
                        action.append((node.number, nod.number, max(free / len(less), 1)))
            else:
                free = node.power[self.player_id] - 10  # 可调
                action.append((node.number, nextenemy[0].number, free))
                self.strategy = 'invade'
            return action
        else:
            return []

    # 前面的map_info都是列表的意思
    def Bellman_Ford(self, map_info: GameMap):
        # Bellman-Ford求最短路径长度
        self.d = [[999999999 for j in range(1, map_info.N + 11)] for i in range(1, map_info.N + 11)]
        d = self.d
        for i in range(1, map_info.N + 1):
            for j in range(1, map_info.N + 1):
                if i == j:
                    d[i][j] = 0
                elif j in map_info.nodes[i].get_next():
                    d[i][j] = 1
        for i in range(1, map_info.N + 1):
            for j in range(1, map_info.N + 1):
                for k in range(1, map_info.N + 1):
                    d[i][j] = min(d[i][j], d[i][k] + d[k][j])
        # print(self.d)

    def invade(self, map_info):
        action = []
        if self.d == None:
            self.Bellman_Ford(map_info)
            # print(self.d)
        for id in range(len(map_info.nodes)):
            home = None
            if self.player_id == 0:
                home = 1
            else:
                home = map_info.N
            if map_info.nodes[id].belong == self.player_id and self.d[id][home] > 1:
                lst = map_info.nodes[id].get_next()
                # print(lst)
                for jd in range(len(lst)):
                    if self.player_id == 0:
                        # print(self.d[id][-1])
                        if self.d[lst[jd]][map_info.N] == self.d[id][map_info.N] - 1:
                            action.append((id, lst[jd], max(map_info.nodes[id].power[self.player_id] - 10, 0)))
                            break
                    else:
                        if self.d[lst[jd]][1] == self.d[id][1] - 1:
                            action.append((id, lst[jd], max(map_info.nodes[id].power[self.player_id] - 10, 0)))
                            break
            else:  # 京师不动
                action = action + self.expand(map_info.nodes[id], map_info.nodes)
        return action

    def defend(self, map_info):  # 守卫首都，防止偷家
        action = []
        if self.player_id == 0:
            home = 1
        else:
            home = map_info.N
        danger = 0
        for id in map_info.nodes[home].get_next():
            if map_info.nodes[id].belong != self.player_id:
                danger += map_info.nodes[id].power[1 - self.player_id]
        if danger > map_info.nodes[home].power[self.player_id]:
            for id in map_info.nodes[home].get_next():
                if map_info.nodes[id].power[self.player_id] > 10:
                    action.append((id, home, max(map_info.nodes[id].power[self.player_id] - 10, 1)))

    def absolute_defend(self):  # 不动如山
        pass

    def dis_to_front(self, map_info):
        dic = {}
        front = self.get_front(map_info)
        for id in front:
            dic[id] = 0
        key = list(dic.keys())
        value = [0] * len(key)
        for id in key:
            for jd in map_info.nodes[id].get_next():
                if jd not in key and map_info.nodes[jd].belong==self.player_id:
                    key.append(jd)
                    value.append(dic[id] + 1)
                    dic[jd] = value[-1]
        return dic

    def get_front(self, map_info):
        front = []
        for id in range(1,map_info.N+1):#太阴间了
            if map_info.nodes[id].belong == self.player_id:
                for jd in map_info.nodes[id].get_next():
                    if map_info.nodes[jd].belong != self.player_id:  # 这个是包括空点的
                        front.append(id)
                        break
        return front

    def upgrate_expand(self, map_info):
        base_inside = 20  # 生产兵力，初期为20，后期对峙时为50
        base_front_safe = 20  # 前线留守兵力，初期为20，后期对峙为70
        base_front_danger = 30
        front = self.get_front(map_info)
        dis = self.dis_to_front(map_info)

        nodes = map_info.nodes
        action = []
        for id in range(1,map_info.N+1):
            if nodes[id].belong == self.player_id and id not in front:
                jd_lst = []
                for jd in nodes[id].get_next():
                    if dis[jd] == dis[id] - 1:
                        jd_lst.append(jd)
                
                if nodes[id].power[self.player_id] > base_inside + len(jd_lst):
                    for jd in jd_lst:
                        action.append((id, jd, (nodes[id].power[self.player_id] - base_inside) / len(jd_lst)))
        for id in front:
            empty = []
            enemy = []
            # 无敌与有敌区别巨大
            for jd in nodes[id].get_next():
                if nodes[jd].belong == 1 - self.player_id:
                    enemy.append(jd)
                elif nodes[jd].belong == -1:
                    empty.append(jd)
            if len(enemy) == 0 and nodes[id].power[self.player_id] > base_front_safe + len(empty):
                for jd in empty:
                    action.append((id, jd, (nodes[id].power[self.player_id] - base_front_safe) / len(empty)))
            elif nodes[id].power[self.player_id] > base_front_safe + len(enemy):
                for jd in enemy:
                    action.append((id, jd, (nodes[id].power[self.player_id] - base_front_danger) / len(enemy)))
        return action

    def player_func(self, map_info: GameMap):
        return self.upgrate_expand(map_info)