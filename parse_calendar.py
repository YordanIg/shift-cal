import pandas as pd
from datetime import datetime

def parse_calendar_data():
    """
    Return calendar data as a pandas dataframe with the first column "Date" in
    the format '%Y-%m-%d' (i.e. YYYY-MM-DD) and the second "Shift".

    This parsing will have to change depending on the calendar format provided.
    """
    calendar_data = pd.read_csv('calendar_data_oct-dec_2023.csv')
    calendar_data = pd.DataFrame(calendar_data, dtype=str)
    # Formatted weirdly - drop rows which just say what day of the week it is.
    evens  = [i for i in range(len(calendar_data)) if i%2==0]
    calendar_data = calendar_data.drop(evens)
    calendar_data.index = range(len(calendar_data))  # Have to re-index after dropping values.

    # Drop rows that don't contain shifts.
    drop_indexes = [i for i in range(len(calendar_data)) if calendar_data.iloc[i]['name'] == 'nan']
    calendar_data = calendar_data.drop(drop_indexes)
    calendar_data.index = range(len(calendar_data))  # Have to re-index after dropping values.
    
    # Convert date format from DD/MM/YYYY to YYYY-MM-DD.
    datetimes = [datetime.strptime(calendar_data['date'][i], '%d/%m/%Y') for i in range(len(calendar_data))]
    datetimes = [dt.strftime('%Y-%m-%d') for dt in datetimes]
    calendar_data['date'] = datetimes

    # Set the time properties & event colors depending on whether it's a short
    # or a long shift.
    calendar_data['start_time'] = '08:00'
    calendar_data['end_time'] = '0'
    calendar_data['color'] = '0'

    for i in range(len(calendar_data)):
        if calendar_data.iloc[i]['name'][-1] == 'L':
            calendar_data.loc[i, 'end_time'] = '20:30'
            calendar_data.loc[i, 'color'] = '1'
        elif calendar_data.iloc[i]['name'][-1] == 'S':
            calendar_data.loc[i, 'end_time'] = '16:30'
            calendar_data.loc[i, 'color'] = '2'
        else:
            raise ValueError

    return calendar_data

def parse_default_calendar():
    """
    Return calendar data as a pandas dataframe.
    """
    calendar_data = pd.read_csv('new_cal_data.csv', dtype=str)
    return calendar_data
