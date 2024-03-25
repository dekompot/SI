from a_star import AStar
from a_star_changes import AStarChanges
from dijkstra import Dijkstra
import sys
from tools import Stop

class Solution:
    
    def __init__(self) -> None:
        self.dijkstra = Dijkstra()
        self.a_star = AStar()
        self.a_star_changes = AStarChanges()
    
    def find(self, a_start: str, b_end: str, start_time: str, criteria):
        a = Stop(a_start,0,0)
        b = Stop(b_end,0,0)
        if criteria == 'd':
            self.dijkstra.run(a,b,start_time)
        elif criteria == 't':
            self.a_star.run(a,b,start_time)
        elif criteria == 'p':
            self.a_star_changes.run(a,b,start_time)
        else:
            print("Wrong criteria! It must be 't' or 'p'",file=sys.stderr)