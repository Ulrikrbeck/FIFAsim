

# FIFA 2022 world cup simulation
# Code by Ulrik Beck 14. nov 2022

import numpy as np
import operator as op
from copy import deepcopy
import pandas as pd
import random

np.random.seed = 90686


class Match:
    no_matchdb = 0
    no_draws = 0

    def __init__(self, team1, team2, matchdb, stage, detail="N/A"):
        self.team1 = team1
        self.team2 = team2
        self.stage = stage
        self.detail = detail
        self.matchdb = matchdb
        self.winner = None
        self.simulated = True
        self.team1won = 0
        self.team2won = 0
        self.wasdraw = 0
        if self.stage == 'group':
            self.draw_elo = 1710 # This number is calibrated in order to hit approx 2018 draw chance in group stage
            Match.no_matchdb += 1
        else:
            self.draw_elo = 0
        self.find_played_match()
        self.play_match(self.team1won, self.team2won, self.wasdraw)
        matchdb.add_match(self.team1.name, self.team2.name, self.winnername, self.stage, self.detail, simulated=self.simulated)

    def find_played_match(self):
        if self.matchdb.exist(self.team1.name, self.team2.name, self.stage):
            self.winner = self.matchdb.findwinner(self.team1.name, self.team2.name, self.stage)
            self.simulated = False
            if self.team1.name == self.winner:
                self.team1won = 1
            elif self.team2.name == self.winner:
                self.team2won = 1
            elif self.winner == 'draw':
                self.wasdraw = 1

    def play_match(self, team1won=0, team2won=0, wasdraw=0):
        self.team1_eloQ = (1 - team2won) * (1 - wasdraw) * 10**(self.team1.elo / 400)
        self.team2_eloQ = (1 - team1won) * (1 - wasdraw) * 10**(self.team2.elo / 400)
        self.draw_eloQ = (1 - team1won) * (1 - team2won) * (10**(self.draw_elo / 400) - 1)
        self.tot_eloQ = self.team1_eloQ + self.team2_eloQ + self.draw_eloQ
        self.winno = np.random.uniform(0, 1)
        # Expected win rates (based on https://www.eloratings.net/about)
        self.dr = self.team1.elo - self.team2.elo
        self.team1_we = 1 / (10**(self.dr / 400) + 1)
        self.team2_we = 1 / (10**(-self.dr / 400) + 1)
        if (self.team1_eloQ / self.tot_eloQ) >= self.winno:
            self.team1.points += 3
            self.team1.won += 1
            self.team2.lost += 1
            self.winner = self.team1
            self.winnername = self.team1.name
            self.draw = 0
            self.team1won = 1
            self.team2won = 0
        elif ((self.team1_eloQ + self.team2_eloQ) / self.tot_eloQ) >= self.winno:
            self.team2.points += 3
            self.team2.won += 1
            self.team1.lost += 1
            self.winner = self.team2
            self.winnername = self.team2.name
            self.draw = 0
            self.team1won = 0
            self.team2won = 1
        else:
            if self.stage == 'group':
                self.team1.points += 1
                self.team2.points += 1
                self.team1.drawn += 1
                self.team2.drawn += 1
                self.winnername = "is_draw"
                self.draw = 1
                Match.no_draws += 1
                self.team1won = 0.5
                self.team2won = 0.5
            else:
                print('error - no winner was determined')
        # Update ELO ratings (based on https://www.eloratings.net/about)
        self.team1.elo += 40 * (self.team1won - self.team1_we)
        self.team2.elo += 40 * (self.team2won - self.team2_we)

    def printMatchWinner(self):
        print(self.team1.name + " - " + self.team2.name + " : Winner is " + self.winnername)


class Team:
    def __init__(self, name, elo_data):
        self.points = 0
        self.won = 0
        self.lost = 0
        self.drawn = 0
        self.name = name.lower()
        self.elo = elo_data[self.name]
        self.randomnumber = np.random.uniform()

    def displayTeam(self):
        print(self.name, "\t(%0.2f,"%self.elo,"%0.2f)")


class DoneMatches:
    def __init__(self):
        self.db = {}
        self.i = np.nan

    def add_match(self, team1, team2, winner, stage, detail="N/A", simulated=False):
        if winner not in [team1, team2, 'is_draw']:
            print("error " + winner + " is not a team")
        if stage not in ['group', '8th', 'quarter', 'semi', 'final']:
            print("error " + stage + " is not a stage")
        self.db[frozenset([team1, team2, stage])] = {}
        self.db[frozenset([team1, team2, stage])]['team1'] = team1
        self.db[frozenset([team1, team2, stage])]['team2'] = team2
        self.db[frozenset([team1, team2, stage])]['winner'] = winner
        self.db[frozenset([team1, team2, stage])]['stage'] = stage
        self.db[frozenset([team1, team2, stage])]['detail'] = detail
        self.db[frozenset([team1, team2, stage])]['simulated'] = simulated
        self.db[frozenset([team1, team2, stage])]['i'] = self.i

    def exist(self, team1, team2, stage):
        if frozenset([team1, team2, stage]) in self.db.keys():
            return True

    def findwinner(self, team1, team2, stage):
        return self.db[frozenset([team1, team2, stage])]['winner']

    def showmatches(self):
        print(self.db.keys())

    def set_iteration(self, i):
        self.i = i

    def unload(self):
        return pd.DataFrame.from_dict(self.db, orient='index', columns=['team1','team2','winner', 'stage', 'detail', 'simulated', 'i'])


class Group:

    def __init__(self, teams, matchdb):
        self.group_winner = None
        self.group_second = None
        self.teams = teams
        self.matchdb = matchdb
        self.reset()

        # 1st round
        Match(self.teams[0], self.teams[1], self.matchdb, 'group')
        Match(self.teams[2], self.teams[3], self.matchdb, 'group')
        # 2nd round
        Match(self.teams[0], self.teams[2], self.matchdb, 'group')
        Match(self.teams[1], self.teams[3], self.matchdb, 'group')
        # 3rd round
        Match(self.teams[0], self.teams[3], self.matchdb, 'group')
        Match(self.teams[1], self.teams[2], self.matchdb, 'group')
        # Find qualified
        # The winner of the group stage is based on
        # 1 - points
        # 2 - random draw
        # (nothing else considered at the moment))
        self.teams = sorted(self.teams, key=op.attrgetter('points', 'randomnumber'))
        self.group_winner = self.teams[len(self.teams) - 1]
        self.group_second = self.teams[len(self.teams) - 2]

    def reset(self):
        for team in self.teams:
            team.points = 0
            team.won = 0
            team.lost = 0
            team.drawn = 0
            team.scored = 0
            team.conceded = 0
            team.difference = 0


def run_mc(no_iterations=10000,randomize_group_stage=False):

    data = []
    winners = {}
    dkstats={}
    dkstats['DenmarkWinsGroup'] = 0
    dkstats['DenmarkSecondInGroup'] = 0
    dkstats['DenmarkwinsAmatch'] = 0
    dkstats['DenmarkwinsBmatch'] = 0

    # Elo data is from eloratings.net 13 nov 2022
    elo_data = {}
    elo_data['qatar'] = 1680 + 100  #qatar gets 100 extra elo points due to home court advantage (https://www.eloratings.net/about)
    elo_data['ecuador'] = 1833
    elo_data['senegal'] = 1687
    elo_data['netherlands'] = 2040  
    elo_data['england'] = 1920
    elo_data['iran'] = 1817
    elo_data['usa'] = 1798
    elo_data['wales'] = 1790
    elo_data['argentina'] = 2141
    elo_data['saudi_arabia'] = 1640
    elo_data["mexico"] = 1821
    elo_data['poland'] = 1809
    elo_data['france'] = 2005
    elo_data['australia'] = 1719
    elo_data['denmark'] = 1971
    elo_data['tunisia'] = 1687
    elo_data['spain'] = 2045
    elo_data['costa_rica'] = 1743
    elo_data['germany'] = 1960
    elo_data['japan'] = 1798
    elo_data['belgium'] = 2025
    elo_data['canada'] = 1765
    elo_data['morocco'] = 1753
    elo_data['croatia'] = 1922
    elo_data['brazil'] = 2169
    elo_data['serbia'] = 1892
    elo_data['switzerland'] = 1929
    elo_data['cameroun'] = 1609
    elo_data['portugal'] = 2004
    elo_data['ghana'] = 1540
    elo_data['uruguay'] = 1936
    elo_data['south_korea'] = 1786

    # Don't care for issues with capital letters so duplicate with entries in all lower cases
    country_list = tuple(elo_data.keys())
    for i in country_list:
        elo_data[i.lower()] = elo_data[i]

    for i in range(0, no_iterations):
        matchdb = deepcopy(played_matches)
        matchdb.set_iteration(i)

        qatar = Team("qatar", elo_data)
        ecuador = Team("ecuador", elo_data)
        senegal = Team("senegal", elo_data)
        netherlands = Team("netherlands", elo_data)
        england = Team("england", elo_data)
        iran = Team("iran", elo_data)
        usa = Team("usa", elo_data)
        wales = Team("wales", elo_data)
        argentina = Team("argentina", elo_data)
        saudi_arabia = Team("saudi_arabia", elo_data)
        mexico = Team("mexico", elo_data)
        poland = Team("poland", elo_data)
        france = Team("france", elo_data)
        australia = Team("australia", elo_data)
        denmark = Team("denmark", elo_data)
        tunisia = Team("tunisia", elo_data)
        spain = Team("spain", elo_data)
        costa_rica = Team("costa_rica", elo_data)
        germany = Team("germany", elo_data)
        japan = Team("japan", elo_data)
        belgium = Team("belgium", elo_data)
        canada = Team("canada", elo_data)
        morocco = Team("morocco", elo_data)
        croatia = Team("croatia", elo_data)
        brazil = Team("brazil", elo_data)
        serbia = Team("serbia", elo_data)
        switzerland = Team("switzerland", elo_data)
        cameroun = Team("cameroun", elo_data)
        portugal = Team("portugal", elo_data)
        ghana = Team("ghana", elo_data)
        uruguay = Team("uruguay", elo_data)
        south_korea = Team("south_korea", elo_data)

        if randomize_group_stage==False:
            # Play group stage with actual groups
            groupA = Group([qatar, ecuador, senegal, netherlands], matchdb)
            groupB = Group([england, iran, usa, wales], matchdb)
            groupC = Group([argentina, saudi_arabia, mexico, poland], matchdb)
            groupD = Group([france, australia, denmark, tunisia], matchdb)
            groupE = Group([spain, costa_rica, germany, japan], matchdb)
            groupF = Group([belgium, canada, morocco, croatia], matchdb)
            groupG = Group([brazil, serbia, switzerland, cameroun], matchdb)
            groupH = Group([portugal, ghana, uruguay, south_korea], matchdb)

        if randomize_group_stage==True:
            #Play group stage - randomize over groups
            seed1=random.sample([qatar,england,argentina,france,spain,belgium,brazil,portugal],8)
            seed2=random.sample([netherlands,usa,mexico,denmark,germany,croatia,switzerland,uruguay],8)
            seed3=random.sample([senegal,iran,poland,tunisia,japan,morocco,serbia,south_korea],8)
            seed4=random.sample([ecuador,wales,saudi_arabia,australia,costa_rica,canada,cameroun,ghana],8)

            groupA = Group([seed1[0],seed2[0],seed3[0],seed4[0]], matchdb)
            groupB = Group([seed1[1],seed2[1],seed3[1],seed4[1]], matchdb)
            groupC = Group([seed1[2],seed2[2],seed3[2],seed4[2]], matchdb)
            groupD = Group([seed1[3],seed2[3],seed3[3],seed4[3]], matchdb)
            groupE = Group([seed1[4],seed2[4],seed3[4],seed4[4]], matchdb)
            groupF = Group([seed1[5],seed2[5],seed3[5],seed4[5]], matchdb)
            groupG = Group([seed1[6],seed2[6],seed3[6],seed4[6]], matchdb)
            groupH = Group([seed1[7],seed2[7],seed3[7],seed4[7]], matchdb)


        # Play second stage
        quarter1 = Match(groupA.group_winner, groupB.group_second, matchdb, '8th','8th1')
        quarter2 = Match(groupC.group_winner, groupD.group_second, matchdb, '8th','8th2')
        quarter3 = Match(groupE.group_winner, groupF.group_second, matchdb, '8th','8th3')
        quarter4 = Match(groupG.group_winner, groupH.group_second, matchdb, '8th','8th4')
        quarter5 = Match(groupB.group_winner, groupA.group_second, matchdb, '8th','8th5')
        quarter6 = Match(groupD.group_winner, groupC.group_second, matchdb, '8th','8th6')
        quarter7 = Match(groupF.group_winner, groupE.group_second, matchdb, '8th','8th7')
        quarter8 = Match(groupH.group_winner, groupG.group_second, matchdb, '8th','8th8')

        # Quarters
        semifinalist1 = Match(quarter1.winner, quarter2.winner, matchdb, 'quarter','q1')
        semifinalist2 = Match(quarter3.winner, quarter4.winner, matchdb, 'quarter','q2')
        semifinalist3 = Match(quarter5.winner, quarter6.winner, matchdb, 'quarter','q3')
        semifinalist4 = Match(quarter7.winner, quarter8.winner, matchdb, 'quarter','q4')

        # Semifinals
        finalist1 = Match(semifinalist1.winner, semifinalist3.winner, matchdb, 'semi','s1')
        finalist2 = Match(semifinalist2.winner, semifinalist4.winner, matchdb, 'semi','s2')

        # Final
        winner = Match(finalist1.winner, finalist2.winner, matchdb, 'final').winner

        if winner.name in winners:
            winners[winner.name] += 1
        else:
            winners[winner.name] = 1

        if groupD.group_winner == denmark:
            dkstats['DenmarkWinsGroup'] += 1  
        if groupD.group_second == denmark:
             dkstats['DenmarkSecondInGroup'] += 1  
        if quarter6.winner == denmark: 
            dkstats['DenmarkwinsAmatch'] += 1
        if quarter2.winner == denmark: 
            dkstats['DenmarkwinsBmatch'] += 1

        data = data + [matchdb.unload()]

    for key in sorted(winners, key=winners.get, reverse=True):
        print(key + ": {:.2f}".format(winners[key]/no_iterations*100) +"%")

    # Count share of group matches that end in draws
    print("\nShare of group matches ending in draws: {:.2f}".format(Match.no_draws/Match.no_matchdb*100) + "%. Compare to 2018 world cup where 8/48=17% of matches ended in draw")

    return pd.concat(data)

played_matches = DoneMatches()


no_its=10000

data_pre = run_mc(no_its,randomize_group_stage=False)





