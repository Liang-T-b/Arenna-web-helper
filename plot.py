import matplotlib.pyplot as plt
import os
import json
if os.path.exists('elo.json'):
    f2 = open('elo.json', 'r')
    elo_dic = json.load(f2)
for key,value in elo_dic.items():
    plt.scatter(key, value, s=None, c=None, marker=None, cmap=None, norm=None, vmin=None)
plt.show()
