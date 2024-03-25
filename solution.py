from a_star import AStar
from a_star_changes import AStarChanges
from dijkstra import Dijkstra
import sys
from tools import Stop
from typing import Tuple

class Solution:
    
    def __init__(self) -> None:
        self.dijkstra = Dijkstra()
        self.a_star = AStar()
        self.a_star_changes = AStarChanges()
    
    def find(self, a_start: str, b_end: str, start_time: str, criteria: str, debug: bool = True) -> Tuple[int, float]:
        a = Stop(a_start,0,0)
        b = Stop(b_end,0,0)
        if criteria == 'd':
            return self.dijkstra.run(a,b,start_time, debug=debug)
        elif criteria == 't':
            return self.a_star.run(a,b,start_time, debug=debug)
        elif criteria == 'p':
            return self.a_star_changes.run(a,b,start_time, debug=debug)
        else:
            print("Wrong criteria! It must be 't' or 'p'",file=sys.stderr)
            return None, None
        