import pandas as pd
from typing import List, Dict, Tuple, Callable
import time as tm
import sys
from geopy.distance import geodesic
from tools import Stop, Route, format_time, time_to_minutes
from dataclasses import dataclass

@dataclass
class StopRecord():
    f: int
    g: int
    last_stop: Stop
    last_route: Route

class AStar():
    def __init__(self, filename="connection_graph (1).csv") -> None:
        self.logs: List[Tuple[str,float]] = [("start", tm.time())]
        self._log("load start")
        self._load(filename)
        self._log("load end")
        self._log("graph creation start")
        self._create()
        self._log("graph creation end")
        
    def _log(self, label: str) -> None:
        self.logs.append((label, tm.time()))
        
    def _print_logs(self) -> None:
        for i in range(len(self.logs)):
            label, timestamp = self.logs[i]
            if i % 2 == 0:
                print(f"--- {label}: {timestamp - self.logs[0][1]} seconds since start \n\t{timestamp - self.logs[max(i-1,0)][1]} seconds since {self.logs[max(i-1,0)][0]}", file=sys.stderr)
        
    def _load(self, filename):
        self.data = pd.read_csv(filename, low_memory=False)
        self.data.set_index(keys='Unnamed: 0', inplace=True)
        self.data.drop_duplicates(ignore_index=True, inplace=True)

    def _create(self):
        self.graph: Dict[Stop, Dict[Stop, List[Route]]] = {}
        for stop in self.data.itertuples():
            start_stop: Stop = Stop(stop.start_stop, stop.start_stop_lat, stop.start_stop_lon) 
            end_stop: Stop = Stop(stop.end_stop, stop.end_stop_lat, stop.end_stop_lon)
            route: Route = Route(line=stop.line, departure_minutes=time_to_minutes(stop.departure_time), arrival_minutes=time_to_minutes(stop.arrival_time))
            if start_stop not in self.graph.keys():
                self.graph[start_stop] = {end_stop: [route]}
            elif end_stop in self.graph[start_stop].keys():
             self.graph[start_stop][end_stop].append(route)
            else:
                self.graph[start_stop][end_stop] = [route] 
            if end_stop not in self.graph.keys():
                self.graph[end_stop] = {}
        for stop, neighbors in self.graph.items():
            for _, routes in neighbors.items():
                routes.sort(key=lambda rt: rt.arrival_minutes)   
    def run(self, a_start: Stop, b_end: Stop, start_time: str, clear_logs: bool= False):
        if clear_logs:
            self.logs = [("start", tm.time())]
        self._log("proceeding start")
        self._proceed(a_start, b_end, start_time, AStar.euclidean)
        self._log("proceeding end")
        self._log("printing start")
        print(b_end)
        self._print(a_start,b_end,start_time)
        self._log("printing end")
        self._print_logs()
    
    def euclidean(next_node: Stop, end_node: Stop) -> float:
        # distance in kilometers / 60 as optimistic velocity in km/h = optimistic time in hours
        # optimistic time in hours * 60 as minutes in an hour = optimistic time in minutes
        return 60 * geodesic((next_node.latitude,next_node.longitude), (end_node.latitude,end_node.longitude)).kilometers / 60
    
    def _proceed(self, a_start: Stop, b_end:Stop, start_time: str, heuristic: Callable[[Stop,Stop],float]):
        change_minutes = 1
        time = time_to_minutes(start_time)
        self.stops_records: Dict[Stop, StopRecord] = {} 
        for key in self.graph.keys():
            self.stops_records[key] = StopRecord(1e10, 1e10, None, None)
        self.stops_records[a_start] = StopRecord(time, time, None, None)
        unseen_stops = list(self.graph.keys())
        seen_stops = []
        while(len(unseen_stops) > 0):
            curr_stop = unseen_stops[0]
            for stop in unseen_stops:
                if self.stops_records[stop].f < self.stops_records[curr_stop].f:
                    curr_stop = stop
            if curr_stop == b_end:
                return
            unseen_stops.remove(curr_stop)
            seen_stops.append(curr_stop)
            # normalize arrival time to 24h
            g_partial = self.stops_records[curr_stop].g % (24*60) 
            for neighbor, routes in self.graph[curr_stop].items():             
                min_arrival_id = -1
                for i in range(len(routes)):
                    # take time for a change of line
                    change_fine = 0 if self.stops_records[curr_stop].last_route is not None and routes[i].line == self.stops_records[curr_stop].last_route.line else change_minutes
                    if g_partial + change_fine <= routes[i].departure_minutes:
                        min_arrival_id = i
                        break
                # if there are no more this day, take the first one after midnight...
                g = routes[min_arrival_id].arrival_minutes if min_arrival_id > -1 else 24*60+routes[0].arrival_minutes
                # ...therefore, this is the chosen route id
                min_arrival_id = max(min_arrival_id,0)
                # derive real cost including days already travelled (anti-prior-normalization)
                g += (self.stops_records[curr_stop].g // (24*60)) * 24*60
                # derive real cost adding day if you were on a road during midnight
                g += 0 if routes[min_arrival_id].arrival_minutes >= routes[min_arrival_id].departure_minutes else 24*60
                
                if neighbor not in unseen_stops and neighbor not in seen_stops:
                    unseen_stops.append(neighbor)
                    self.stops_records[neighbor].g = g
                    self.stops_records[neighbor].f = g + heuristic(neighbor, b_end)
                    self.stops_records[neighbor].last_stop = curr_stop
                    self.stops_records[neighbor].last_route = routes[min_arrival_id]
                else:
                    if g < self.stops_records[neighbor].g:
                        self.stops_records[neighbor].g = g
                        self.stops_records[neighbor].f = g + heuristic(neighbor, b_end)
                        self.stops_records[neighbor].last_stop = curr_stop
                        self.stops_records[neighbor].last_route = routes[min_arrival_id]
                        if neighbor in seen_stops:
                            unseen_stops.append(neighbor)
                            seen_stops.remove(neighbor)
                    
    def _print(self, a_start: Stop, b_end: Stop, start_time: str) -> None:
        temp = b_end, self.stops_records[b_end]
        route: List[Tuple[Stop, StopRecord]] = []
        max_length = [0,0,0,0,0]
        while temp[1].last_stop is not None:
            route.append(temp)
            for i, element in enumerate([temp[1].last_route.line, temp[1].last_stop.name, format_time(temp[1].last_route.departure_minutes), temp[0].name, format_time(temp[1].last_route.arrival_minutes)]):
                max_length[i] = len(str(element)) if len(str(element)) > max_length[i] else max_length[i]
            temp = temp[1].last_stop, self.stops_records[temp[1].last_stop]
        route.reverse()
        print(f"From {a_start} at {start_time}:")
        for i, stop in enumerate(route):
            day_info = "Day " +  str(stop[1].f // (24*60) + 1)
            print(f"{str(i+1).rjust(len(str(len(route))))}. \t{str(stop[1].last_route.line).rjust(max_length[0])}) [{format_time(stop[1].last_route.departure_minutes).rjust(max_length[2])}] {stop[1].last_stop.name.ljust(max_length[1])} - "
                f"[{format_time(stop[1].last_route.arrival_minutes)}] {stop[0].name} ({day_info})")
        print(f'Cost function: {self.stops_records[end].g - time_to_minutes(start_time)}', file=sys.stderr)


def run(a_start: Stop, b_end: Stop, start_time: str) -> None:
    a = AStar()
    a.run(a_start, b_end, start_time)
    
if __name__ == '__main__':
    start = Stop("Tramwajowa", 51.10446678,17.08466997)
    end = Stop("Muchobór Wielki", 51.09892535,16.94155277)
    # end = Stop("DWORZEC NADODRZE", 51.12431442,17.03503321)
    start_time = '23:53:00'
    run(start, end, start_time)