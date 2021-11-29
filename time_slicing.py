import pandas as pd
from datetime import datetime as dt, timedelta as td, MINYEAR

# Time enums
ALL_Y = 0
FIVE_Y = 10
ONE_Y = 40
THREE_M = 70
ONE_M = 80
ONE_W = 90

# Maps var names to num of days 
time_map = {
    FIVE_Y: 365*5,
    ONE_Y: 365, 
    THREE_M: 30*3, 
    ONE_M: 30,
    ONE_W: 7
}

def get_delta(dif):
    '''
    Only accepts enums defined above as input
    '''
    if dif == 0:
        return None

    now = dt.now() 
    days = time_map[dif]
    delta = td(days=days)

    return now-delta