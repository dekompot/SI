import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import time
import time as tm
import sys

class Stop:
    def __init__(self, name: str, latitude: float, longitude: float) -> None:
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
    def __str__(self) -> str:
        return self.name + "[" + str(self.latitude) + ", " + str(self.longitude) + "]"
    def __repr__(self) -> str:
        return self.name + ", " + str(self.latitude) + "," + str(self.longitude)
    def __hash__(self) -> int:
        return hash(str(self.name))
    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, Stop) and str(self.name) == str(__value.name)
    
@dataclass
class Route:
    line: str
    departure_minutes: int
    arrival_minutes: int

@dataclass
class StopRecord():
    min_arrival_minutes: int
    last_stop: Stop
    last_route: Route
    
def time_to_minutes(time_str: str) -> int:
    time_arr = time_str.split(':')
    hour=int(time_arr[0])
    minute=int(time_arr[1])
    return 60 * (hour % 24) + minute
def format_time(abnormal_time: int) -> str:
    return str(abnormal_time // 60).zfill(2) + ":" + str(abnormal_time % 60).zfill(2)

class Dijkstra():
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
        self._proceed(a_start, start_time)
        self._log("proceeding end")
        self._log("printing start")
        self._print(a_start,b_end,start_time)
        self._log("printing end")
        self._print_logs()
    
    def _proceed(self, a_start: Stop, start_time: str):
        change_minutes = 1
        time = time_to_minutes(start_time)
        self.stops_records: Dict[Stop, StopRecord] = {} 
        for key in self.graph.keys():
            self.stops_records[key] = StopRecord(1e10, None, None)
        self.stops_records[a_start] = StopRecord(time, None, None)
        unseen_stops = list(self.graph.keys())
        while(len(unseen_stops) > 0):
            curr_stop = unseen_stops[0]
            for stop in unseen_stops:
                if self.stops_records[stop].min_arrival_minutes < self.stops_records[curr_stop].min_arrival_minutes:
                    curr_stop = stop
            unseen_stops.remove(curr_stop)
            arrival_minutes_modulo = self.stops_records[curr_stop].min_arrival_minutes % (24*60) 
            for neighbor, routes in self.graph[curr_stop].items():
                min_arrival_id = -1
                for i in range(len(routes)):
                    change_fine = 0 if self.stops_records[curr_stop].last_route is not None and routes[i].line == self.stops_records[curr_stop].last_route.line else change_minutes
                    if arrival_minutes_modulo + change_fine <= routes[i].departure_minutes:
                        min_arrival_id = i
                        break
                min_arrival_minutes = routes[min_arrival_id].arrival_minutes if min_arrival_id > -1 else 24*60+routes[0].arrival_minutes
                min_arrival_id = max(min_arrival_id,0)
                min_arrival_minutes += (self.stops_records[curr_stop].min_arrival_minutes // (24*60)) * 24*60 
                min_arrival_minutes += 0 if routes[min_arrival_id].arrival_minutes > routes[min_arrival_id].departure_minutes else 24*60
                if min_arrival_minutes < self.stops_records[neighbor].min_arrival_minutes:
                    self.stops_records[neighbor].min_arrival_minutes = min_arrival_minutes
                    self.stops_records[neighbor].last_stop = curr_stop
                    self.stops_records[neighbor].last_route = routes[min_arrival_id]
                    
    def _print(self, a_start: Stop, b_end: Stop, start_time: str) -> None:
        temp = b_end, self.stops_records[end]
        route: List[Tuple[Stop, StopRecord]] = []
        max_length = [0,0,0,0,0]
        while temp[1].last_stop is not None:
            route.append(temp)
            for i, element in enumerate([temp[1].last_route.line, temp[1].last_stop.name, format_time(temp[1].last_route.departure_minutes), temp[0].name, format_time(temp[1].last_route.arrival_minutes)]):
                max_length[i] = len(str(element)) if len(str(element)) > max_length[i] else max_length[i]
            temp = temp[1].last_stop, self.stops_records[temp[1].last_stop]
        route.reverse()
        for i, stop in enumerate(route):
            day_info = "Day " +  str(stop[1].min_arrival_minutes // (24*60) + 1)
            print(f"{str(i+1).rjust(len(str(len(route))))}. \t{str(stop[1].last_route.line).rjust(max_length[0])}) [{format_time(stop[1].last_route.departure_minutes).rjust(max_length[2])}] {stop[1].last_stop.name.ljust(max_length[1])} - "
                f"[{format_time(stop[1].last_route.arrival_minutes)}] {stop[0].name} ({day_info})")


def run(a_start: Stop, b_end: Stop, start_time: str) -> None:
    d = Dijkstra()
    d.run(a_start, b_end, start_time)
    
if __name__ == '__main__':
    start = Stop("Tramwajowa", 51.10446678,17.08466997)
    end = Stop("Muchobór Wielki", 51.09892535,16.94155277)
    # end = Stop("DWORZEC NADODRZE", 51.12431442,17.03503321)
    start_time = '23:53:00'
    run(start, end, start_time)