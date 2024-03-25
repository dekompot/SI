import pandas as pd
from typing import List, Dict, Tuple, Callable
import time as tm
from tools import Stop, Route, StopLine, format_time, time_to_minutes, Algorithm, change_minutes
from dataclasses import dataclass
import sys
from geopy.distance import geodesic

@dataclass
class StopRecord():
    f: float
    g: float
    last_stopline: StopLine
    last_route: Route
    time: int

further_charge = 0.1

class AStarChanges(Algorithm):
    def __init__(self, filename="connection_graph (1).csv") -> None:
        super().__init__(filename)

    def _create(self):
        self.graph: Dict[Stop, Dict[Stop, Dict[str,List[Route]]]] = {}
        self.to_graph: Dict[Stop, List[str]] = {}
        for stop in self.data.itertuples():
            start_stop: Stop = Stop(stop.start_stop, stop.start_stop_lat, stop.start_stop_lon) 
            end_stop: Stop = Stop(stop.end_stop, stop.end_stop_lat, stop.end_stop_lon)
            route: Route = Route(line=stop.line, departure_minutes=time_to_minutes(stop.departure_time), arrival_minutes=time_to_minutes(stop.arrival_time))
            if end_stop not in self.to_graph.keys():
                self.to_graph[end_stop] = [stop.line]
            elif stop.line not in self.to_graph[end_stop]:
                self.to_graph[end_stop].append(stop.line)
            if start_stop not in self.graph.keys():
                self.graph[start_stop] = {end_stop: {route.line: [route]}}
            elif end_stop in self.graph[start_stop].keys():
                if route.line in self.graph[start_stop][end_stop].keys():
                    self.graph[start_stop][end_stop][route.line].append(route)
                else:
                    self.graph[start_stop][end_stop][route.line] = [route]
            else:
                self.graph[start_stop][end_stop] = {route.line: [route]}
            if end_stop not in self.graph.keys():
               self.graph[end_stop] = {}
        for stop, neighbors in self.graph.items():
            for _, lines in neighbors.items():
                for _, routes in lines.items():
                    routes.sort(key=lambda rt: rt.arrival_minutes)            
    
    def approaching(prev_node: Stop, next_node: Stop, end_node: Stop) -> float:
        # charge coming further away from target
        prev_dist = geodesic((prev_node.latitude,prev_node.longitude), (end_node.latitude,end_node.longitude)).meters
        next_dist = geodesic((next_node.latitude,next_node.longitude), (end_node.latitude,end_node.longitude)).meters
        return 0 if next_dist < prev_dist else further_charge
    
    def _proceed(self, a_start: Stop, b_end:Stop, start_time: str):
        time = time_to_minutes(start_time)
        self.stops_records: Dict[StopLine, StopRecord] = {} 
        unseen_stoplines = []
        for stop, lines in self.to_graph.items():
            for line in lines:
                self.stops_records[StopLine(stop,line)] = StopRecord(1e10, 1e10, None, None, None)
        self.stops_records[StopLine(a_start,None)] = StopRecord(0, 0, None, None, time)
        unseen_stoplines = list(self.stops_records.keys())
        seen_stoplines = []
        while(len(unseen_stoplines) > 0):
            curr_stopline = unseen_stoplines[0]
            for stopline in unseen_stoplines:
                if self.stops_records[stopline].f < self.stops_records[curr_stopline].f:
                    curr_stopline = stopline
            if curr_stopline.stop == b_end:
                return
            unseen_stoplines.remove(curr_stopline)
            seen_stoplines.append(curr_stopline)
            # normalize arrival time to 24h
            time_partial = self.stops_records[curr_stopline].time % (24*60) 
            for neighbor, lines_to_routes in self.graph[curr_stopline.stop].items():   
                for line, routes in lines_to_routes.items(): 
                    min_arrival_id = -1
                    for i in range(len(routes)):
                        # take time for a change of line
                        change_fine = 0 if self.stops_records[curr_stopline].last_route is not None and routes[i].line == self.stops_records[curr_stopline].last_route.line else change_minutes
                        if time_partial + change_fine <= routes[i].departure_minutes:
                            min_arrival_id = i
                            break
                    time_ = routes[min_arrival_id].arrival_minutes if min_arrival_id > -1 else 24*60+routes[0].arrival_minutes
                    min_arrival_id = max(min_arrival_id,0)
                    time_ += (self.stops_records[curr_stopline].time // (24*60)) * 24*60
                    time_ += 0 if routes[min_arrival_id].arrival_minutes >= routes[min_arrival_id].departure_minutes else 24*60
                    g = self.stops_records[curr_stopline].g
                    g += 0 if self.stops_records[curr_stopline].last_route is None or routes[min_arrival_id] is None or (routes[min_arrival_id].line == self.stops_records[curr_stopline].last_route.line and abs(time_ - routes[min_arrival_id].arrival_minutes + routes[min_arrival_id].departure_minutes  - self.stops_records[curr_stopline].time) < 2) else 1
                    new_node = StopLine(neighbor,routes[min_arrival_id].line)
                    if new_node not in unseen_stoplines and new_node not in seen_stoplines:
                        unseen_stoplines.append(new_node)
                        self.stops_records[new_node].g = g
                        self.stops_records[new_node].f = g + AStarChanges.approaching(curr_stopline.stop, new_node.stop, b_end)
                        self.stops_records[new_node].last_stopline = curr_stopline
                        self.stops_records[new_node].last_route = routes[min_arrival_id]
                        self.stops_records[new_node].time = time_
                    else:
                        if g < self.stops_records[new_node].g:
                            self.stops_records[new_node].g = g
                            self.stops_records[new_node].f = g + AStarChanges.approaching(curr_stopline.stop, new_node.stop, b_end)
                            self.stops_records[new_node].last_stopline = curr_stopline
                            self.stops_records[new_node].last_route = routes[min_arrival_id]
                            self.stops_records[new_node].time = time_
                            if new_node in seen_stoplines:
                                unseen_stoplines.append(new_node)
                                seen_stoplines.remove(new_node)
                    
    def _print(self, a_start: Stop, b_end: Stop, start_time: str) -> None:
        min_g = 1e10
        end = None
        for stopline in self.stops_records.keys():
            if stopline.stop.name == b_end.name and self.stops_records[stopline].g < min_g:
                end = stopline, self.stops_records[stopline]
                min_g = self.stops_records[stopline].g
        temp = end[0], self.stops_records[end[0]]
        route: List[Tuple[StopLine, StopRecord]] = []
        max_length = [0,0,0,0,0]
        while temp[1].last_stopline is not None:
            route.append(temp)
            for i, element in enumerate([temp[1].last_route.line, temp[1].last_stopline.stop.name, format_time(temp[1].last_route.departure_minutes), temp[0].stop.name, format_time(temp[1].last_route.arrival_minutes)]):
                max_length[i] = len(str(element)) if len(str(element)) > max_length[i] else max_length[i]
            temp = temp[1].last_stopline, self.stops_records[temp[1].last_stopline]
        route.reverse()
        print(f"From {a_start.name} at {start_time}:")
        for i, stop in enumerate(route):
            day_info = "Day " +  str(stop[1].time // (24*60) + 1)
            print(f"{str(i+1).rjust(len(str(len(route))))}. \t{str(stop[1].last_route.line).rjust(max_length[0])}) [{format_time(stop[1].last_route.departure_minutes).rjust(max_length[2])}] {stop[1].last_stopline.stop.name.ljust(max_length[1])} - "
                f"[{format_time(stop[1].last_route.arrival_minutes)}] {stop[0].stop.name} ({day_info})")
        print(f'Cost function: {self._cost(a_start, b_end, start_time)}', file=sys.stderr)

    def _cost(self, a_start: Stop, b_end: Stop, start_time: str) -> int:
        min_g = 1e10
        end = None
        for stopline in self.stops_records.keys():
            if stopline.stop.name == b_end.name and self.stops_records[stopline].g < min_g:
                end = stopline, self.stops_records[stopline]
                min_g = self.stops_records[stopline].g
        return self.stops_records[end[0]].g

def run(a_start: Stop, b_end: Stop, start_time: str) -> None:
    a = AStarChanges()
    a.run(a_start, b_end, start_time)
    
if __name__ == '__main__':
    start = Stop("Tramwajowa", 51.10446678,17.08466997)
    end = Stop("Muchobór Wielki", 51.09892535,16.94155277)
    # end = Stop("DWORZEC NADODRZE", 51.12431442,17.03503321)
    start_time = '23:53:00'
    run(start, end, start_time)
    