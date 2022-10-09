import requests
import os
import json
import matplotlib.pyplot as plt
import matplotlib

TOKEN = os.environ['CHUNIREC_TOKEN']
matplotlib.rc('font', family="M+ 1p")

MAXSCORE = 1010000.0
SSSP = 1009000.0
SSS = 1007500.0
SSP = 1005000.0
SS = 1000000.0
SP = 990000
S = 975000

def score_to_rank_rate(score):
    if score >= SSSP:
        return ('SSSP', 2.15)
    elif score >= SSS:
        return ('SSS', 2.0 + (score - SSS) * 0.0001)
    elif score >= SSP:
        return ('SSP', 1.5 + (score - SSP) * 0.0002)
    elif score >= SS:
        return ('SS', 1.0 + (score - SS) * 0.0001)
    elif score >= S:
        return ('S', 0 + (score - S) * 0.00004)
    else:
        return ('?', 0)

# Music Meta
# id title genre artist release bpm
class MusicMeta:
    def __init__(self, meta):
        self.__dict__.update(meta)

# Music Chart
# diff level const maxcombo is_const_unknown
class MusicChart:
    def __init__(self, data, diff):
        self.__dict__.update(data)
        self.diff = diff
    def note_score(self):
        return MAXSCORE / self.maxcombo

# MusicInfo
# meta charts...{ diff: chart }
class MusicInfo:
    def __init__(self, info):
        self.meta = MusicMeta(info['meta'])
        self.charts = dict()
        for diff, ch in info['data'].items():
            self.charts[diff] = MusicChart(ch, diff)

# Music Dict
# get_info to get music info
class MusicDict:
    def __init__(self):
        payload = {
                'region': 'jp2',
                'token': TOKEN
        }
        r = requests.get('https://api.chunirec.net/2.0/music/showall.json', params=payload)
        data = json.loads(r.text)
        self.musics = dict()
        for d in data:
            self.musics[d['meta']['id']] = MusicInfo(d)
    def get_info(self, id):
        return self.musics[id]

# Music Result
# id diff level title const score rating is_const_unknown is_clear is_fullcombo is_alljustice
# is_fullchain genre updated_at is_played
class MusicResult:
    def __init__(self, data):
        self.__dict__.update(data)
    def __repr__(self):
        return f"({self.title}, {self.score})"

#https://api.chunirec.net/2.0/records/showall.json
class NormalRecord:
    def __init__(self, user_id = None):
        payload = {
                'region': 'jp2',
                'token': TOKEN
        }
        if user_id is not None:
            payload['user_id'] = user_id
        r = requests.get('https://api.chunirec.net/2.0/records/showall.json', params=payload)
        self.records = [MusicResult(data) for data in json.loads(r.text)['records']]

    def bests(self):
        sorted_records = sorted(self.records, key = lambda record: record.rating)
        sorted_records.reverse()
        return sorted_records[0:30]

#https://api.chunirec.net/2.0/records/rating_data.json
class RatingRecord:
    def __init__(self, user_id = None):
        payload = {
                'region': 'jp2',
                'token': TOKEN
        }
        if user_id is not None:
            payload['user_id'] = user_id
        r = requests.get('https://api.chunirec.net/2.0/records/rating_data.json', params=payload)
        self.bests = [MusicResult(data) for data in json.loads(r.text)['best']['entries']]
        self.recent = [MusicResult(data) for data in json.loads(r.text)['recent']['entries']]
        self.best_candidate = [MusicResult(data) for data in json.loads(r.text)['best_candidate']['entries']]
        self.best_candidate_sss = [MusicResult(data) for data in json.loads(r.text)['best_candidate_sss']['entries']]
        self.outside = [MusicResult(data) for data in json.loads(r.text)['best_outside']['entries']]


def draw_chart(music_dict, results, filename):
    N = len(results)
    fig = plt.figure(figsize=(10, 10 / 30 * N))
    fig.subplots_adjust(left=0.35)
    ax = fig.add_subplot(1, 1, 1)
    ratings = [r.rating for r in results]
    max_rate = [r.const + 2.15 for r in results]
    names = [r.title for r in results]
    ax.barh(range(N), max_rate, color="grey", alpha=0.3)
    ax.barh(range(N), ratings, color="salmon", alpha=1.0)
    ax.set_yticks(range(N), names)
    min_rating = min(ratings)
    ax.set_xlim(min_rating - 0.15, max(max_rate) + 0.05)
    ax.invert_yaxis()
    for i, res in enumerate(results):
        ax.text(min_rating - 0.075, i, f"{res.score}", ha='center', va='center')

    for i, res in enumerate(results):
        ax.plot([res.const + 2.0], [i + 0.5], marker='^', color='violet', markersize=3)
        ax.plot([res.const + 1.5], [i + 0.5], marker='^', color='blue', markersize=3)

    for i, res in enumerate(results):
        one = music_dict.get_info(res.id).charts[res.diff].note_score() * 0.5
        sssp = (MAXSCORE - SSSP) / one;
        sss = (MAXSCORE - SSS) / one;
        ssp = (MAXSCORE - SSP) / one;
        ax.text(res.const + 2.15 + 0.01, i + 0.5, f"{sssp:.1f}", color="orange", va='center', size=4)
        ax.text(res.const + 2.0 + 0.01, i + 0.5, f"{sss:.1f}", color="red", va='center', size=4)
        ax.text(res.const + 1.5 + 0.01, i + 0.5, f"{ssp:.1f}", color="blue", va='center', size=4)
    
    for i, res in enumerate(results):
        score = res.score
        diff = res.diff
        one = music_dict.get_info(res.id).charts[diff].note_score()
        while score < SSSP:
            score += one * 0.5
            rank, rate = score_to_rank_rate(score)
            ax.plot([res.const + rate], [i], marker='|', color='green', markersize=10)

    fig.savefig(filename, format='png', dpi=300)

if __name__ == '__main__':
    music_dict = MusicDict()
    record = NormalRecord()
    rating_info = RatingRecord()
    print(record.bests())
    draw_chart(music_dict, record.bests() + rating_info.best_candidate_sss, 'bests.png')


