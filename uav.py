from __future__ import annotations
import numpy as np
import random
from typing import List


class UAV:

    def __init__(self, uav_id: int, seed):
        np.random.seed(seed)
        self.uav_id = uav_id

        self.hover_bearing_health = np.zeros(4)
        self.hover_bearing_factors = np.zeros(4)
        self.hover_coil_health = np.zeros(4)
        self.hover_coil_factors = np.zeros(4)

        self.pusher_bearing_health = 0.0
        self.pusher_bearing_factor = 1
        self.pusher_coil_health = 0.0
        self.pusher_coil_factor = 1

        self.hover_bearing_failure_appearance = np.empty(4)
        self.hover_coil_failure_appearance = np.empty(4)

        self.pusher_bearing_failure_appearance = None
        self.pusher_coil_failure_appearance = None

        self.hover_bearing_severity = np.random.uniform(1.004, 1.008, 4)
        self.hover_coil_severity = np.random.uniform(1.008, 1.012, 4)

        self.pusher_bearing_severity = np.random.uniform(1.004, 1.008)
        self.pusher_coil_severity = np.random.uniform(1.008, 1.012)

        self.health_initialization()
        self.failure_detection = False
        
        self._flown_distances: List[float] = []     # distances flown for each mission

    def health_initialization(self) -> None:
        self.flight_mode = 0
        self._flown_distances = []
        healths = self.generate_healths(0.8, 1.0)
        
        for i in range(len(self.hover_bearing_health)):
            self.hover_bearing_health[i] = healths[2*(i-1)]
            self.hover_bearing_factors[i] = 1.0
            self.hover_bearing_failure_appearance[i] = round(random.uniform(0.45, 0.6), 3)

            self.hover_coil_health[i] = healths[2*(i-1)+1]
            self.hover_coil_factors[i] = 1.0
            self.hover_coil_failure_appearance[i] = round(random.uniform(0.45, 0.6), 3)

        self.pusher_bearing_health = healths[8]
        self.pusher_bearing_factor = 1
        self.pusher_bearing_failure_appearance = round(random.uniform(0.45, 0.6), 3)

        self.pusher_coil_health = healths[9]
        self.pusher_coil_factor = 1
        self.pusher_coil_failure_appearance = round(random.uniform(0.45, 0.6), 3)

    def generate_healths(self, min_health: float, max_health:float) -> np.ndarray:
        num_values = 10 

        alpha = 0.1*np.ones(num_values)

        values = np.random.dirichlet(alpha) * (min_health - max_health) + max_health

        return values

    def degrade(self, hover: float, cruise: float) -> None:
        self.flyMinute()    # for stats
        
        if  hover > 0:
            hover_bearing_deg_values = np.empty(len(self.hover_bearing_health))
            for j in range(len(self.hover_bearing_health)):
                if self.hover_bearing_health[j] > self.hover_bearing_failure_appearance[j]:
                    hover_bearing_deg_values[j] = self.hover_bearing_factors[j]*round(random.uniform(1, 5) * 0.0002, 6)
                    self.hover_bearing_factors[j] *= 1.001
                else:
                    hover_bearing_deg_values[j] = self.hover_bearing_factors[j]*round((random.uniform(1, 5) * 0.0002), 6)
                    self.hover_bearing_factors[j] *= self.hover_bearing_severity[j]

            self.hover_bearing_health -= hover*hover_bearing_deg_values

            hover_coil_deg_values = np.empty(len(self.hover_coil_health))
            for j in range(len(self.hover_coil_health)):
                if self.hover_coil_health[j] > self.hover_coil_failure_appearance[j]:
                    hover_coil_deg_values[j] = self.hover_coil_factors[j]*round(random.uniform(1, 4) * 0.0002, 6)
                    self.hover_coil_factors[j] *= 1.001
                else:
                    hover_coil_deg_values[j] = self.hover_coil_factors[j]*round(random.uniform(1, 4) * 0.0002, 6)
                    self.hover_coil_factors[j] *= self.hover_coil_severity[j]
                    
            self.hover_coil_health -= hover*hover_coil_deg_values

        if cruise > 0:
            if self.pusher_bearing_health > self.pusher_bearing_failure_appearance:
                pusher_bearing_deg_rate = self.pusher_bearing_factor*round(random.uniform(1, 5) * 0.0002, 6)
                self.pusher_bearing_factor *= 1.001
            else:
                pusher_bearing_deg_rate = self.pusher_bearing_factor*round(random.uniform(1, 5) * 0.0002, 6)
                self.pusher_bearing_factor *= self.pusher_bearing_severity

            self.pusher_bearing_health -= cruise*pusher_bearing_deg_rate

            if self.pusher_coil_health > self.pusher_coil_failure_appearance:
                pusher_coil_deg_rate = self.pusher_coil_factor*round(random.uniform(1, 4) * 0.0002, 6)
                self.pusher_coil_factor *= 1.001
            else:
                pusher_coil_deg_rate = self.pusher_coil_factor*round(random.uniform(1, 4) * 0.0002, 6)
                self.pusher_coil_factor *= self.pusher_coil_severity

            self.pusher_coil_health -= cruise*pusher_coil_deg_rate

    def detectFailure(self) -> bool:
        component_healths = []
        component_healths.extend(list(self.hover_bearing_health))
        component_healths.extend(list(self.hover_coil_health))
        component_healths.append(float(self.pusher_bearing_health))
        component_healths.append(float(self.pusher_coil_health))
        component_healths = np.asarray(component_healths)

        return any(component_healths < 0)

    def detectComponentFailure(self, component: int, component_index: int = None) -> bool:
        """
        component: among UAVStats.METRICS
        component_index: for multivalue components
        """
        if component == UAVStats.HOVER_BEARING_HEALTH:
            if component_index is None:
                return any(x < 0 for x in self.hover_bearing_health)
            else:
                return self.hover_bearing_health[component_index] < 0
        elif component == UAVStats.HOVER_COIL_HEALTH:
            if component_index is None:
                return any(x < 0 for x in self.hover_coil_health)
            else:
                return self.hover_coil_health[component_index] < 0
        elif component == UAVStats.PUSHER_BEARING_HEALTH:
            return self.pusher_bearing_health < 0
        elif component == UAVStats.PUSHER_COIL_HEALTH:
            return self.pusher_coil_health < 0
        else:
            raise
        
    def startMission(self):
        self._flown_distances.append(0)
        
    def flyMinute(self):
        speed = 1
        self._flown_distances[-1] += speed
    
    def getFlownDistances(self):
        return self._flown_distances
        
    def getStats(self) -> np.ndarray:
        return UAVStats(self).get()


class UAVStats:
    """
    Class for gathering stats encoding and decoding, to make it easier if we want to change those mechanics later 
    (for instance by adding back battery levels to the stats, which they are currently not).
    """
    
    HOVER_BEARING_HEALTH = 0
    HOVER_COIL_HEALTH = 1
    PUSHER_BEARING_HEALTH = 2
    PUSHER_COIL_HEALTH = 3
    BATTERY_LEVEL = 4
    
    METRICS = [HOVER_BEARING_HEALTH, HOVER_COIL_HEALTH, PUSHER_BEARING_HEALTH, PUSHER_COIL_HEALTH]  #, BATTERY_LEVEL]
    MULTIVALUE_METRICS = [HOVER_BEARING_HEALTH, HOVER_COIL_HEALTH]
    
    STAT_NAMES = {
        HOVER_BEARING_HEALTH: "hover bearing%s",
        HOVER_COIL_HEALTH: "hover coil%s",
        PUSHER_BEARING_HEALTH: "pusher bearing",
        PUSHER_COIL_HEALTH: "pusher coil",
        BATTERY_LEVEL: "battery level"
    }
    
    def __init__(self, uav: UAV):
        self._uav = uav
    
    def get(self):
        """get stats encoded as a numpy array"""
        return np.concatenate((
            self._uav.hover_bearing_health,
            self._uav.hover_coil_health,
            np.array([self._uav.pusher_bearing_health]),
            np.array([self._uav.pusher_coil_health]),
            #np.array([self._uav.battery_level])
        ))
    
    @staticmethod
    def get_metric(stats: np.ndarray, metric: int, uav_index: int = None) -> np.ndarray:
        """
        Get a metric of the stats that have been encoded to numpy array.
        args
        ----
        stats:
            a numpy array of shape (<nb metrics>*<nb uavs>) x <nb of steps recorded>
        metric:
            The metric to isolate among UAVStats.METRICS

        returns the value of this metric for the given uav_index across all the steps
        """
        attr_lengths = [4, 4, 1, 1]     # [4, 4, 1, 1, 1] with battery level
        total_length = sum(attr_lengths)
        if uav_index is None:   # TODO: for now only works for attributes of length 1
            start = sum(attr_lengths[:metric])
            return stats[start::total_length]
        start = total_length*uav_index + sum(attr_lengths[:metric])
        length = attr_lengths[metric]
        return stats[start] if length == 1 else stats[start: start+length]

    @classmethod
    def get_metric_name(cls, metric: int, health: bool = True):
        name = cls.STAT_NAMES[metric]
        if health:
            return name + " health"
        return name
        if metric in cls.MULTIVALUE_METRICS:
            name %= "s"
        return name
