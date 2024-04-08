from dataclasses import dataclass
import pandas as pd
from typing import List, Tuple
import time as tm
from dataclasses import dataclass
import sys
from abc import ABC, abstractmethod

change_minutes = 0

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
class StopLine:
    stop: Stop
    line: str
    def __hash__(self) -> int:
        return hash(str(self.stop.name)+str(self.line))
    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, StopLine) and __value.stop == self.stop and __value.line == self.line
    
def time_to_minutes(time_str: str) -> int:
    time_arr = time_str.split(':')
    hour=int(time_arr[0])
    minute=int(time_arr[1])
    return 60 * (hour % 24) + minute
def format_time(abnormal_time: int) -> str:
    return str(abnormal_time // 60).zfill(2) + ":" + str(abnormal_time % 60).zfill(2)

class Algorithm(ABC):
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
    
    def _proceeding_time(self) -> float:
        for i in range(len(self.logs)):
            label, timestamp = self.logs[i]
            if i % 2 == 0 and label == 'proceeding end':
                return timestamp - self.logs[max(i-1,0)][1]
            
    def _load(self, filename):
        self.data = pd.read_csv(filename, low_memory=False)
        self.data.set_index(keys='Unnamed: 0', inplace=True)
        self.data.drop_duplicates(ignore_index=True, inplace=True)
    
    @abstractmethod
    def _create(self):
        pass
    
    def run(self, a_start: Stop, b_end: Stop, start_time: str, clear_logs: bool= True, debug: bool=True):
        if clear_logs:
            self.logs = [("start", tm.time())]
        self._log("proceeding start")
        self._proceed(a_start, b_end, start_time)
        self._log("proceeding end")
        if debug:
            self._log("printing start")
            self._print(a_start,b_end,start_time)
            self._log("printing end")
            self._print_logs()
        return self._cost(a_start,b_end,start_time), self._proceeding_time()

    @abstractmethod
    def _proceed(self, a_start: Stop, b_end:Stop, start_time: str) -> None:
        pass
    
    @abstractmethod
    def _print(self, a_start: Stop, b_end: Stop, start_time: str) -> None:
        pass
    
    @abstractmethod
    def _cost(self, a_start: Stop, b_end: Stop, start_time: str) -> int:
        pass
    