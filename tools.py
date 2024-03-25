from dataclasses import dataclass
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