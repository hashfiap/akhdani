import math
from datetime import datetime

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat / 2)**2 + \
        math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2)**2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_duration(start_date, end_date):
    delta = end_date - start_date
    return delta.days + 1

def get_daily_allowance(origin, destination, distance_km):
    if destination.is_luar_negeri:
        return 50.0, "USD"
    
    if distance_km <= 60:
        return 0.0, "IDR"
    
    if origin.provinsi == destination.provinsi:
        return 200000.0, "IDR"
    
    if origin.pulau == destination.pulau:
        return 250000.0, "IDR"
    
    return 300000.0, "IDR"