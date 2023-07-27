"""
Functions that add and delete events from the shift calendar.
"""
import re
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta


CAL_ID = '35ff39e798f9acc1fb3904b1372feca82c40d3656cebea11d7335551f8f70e0b@group.calendar.google.com'


def extract_hours_minutes(time_str):
    """
    Parse the time string and return the hours and minutes as a tuple of
    integers. Handles times of format H:MM, HH:MM, H, HH, HMM, HHMM. 
    """
    # Define the invalid time error message in advance.
    errormsg = f"time string '{time_str}' does not match expected " \
             +  "formats: H:MM, HH:MM, HMM, HHMM, H, HH."
    
    # Define the regular expression pattern for the formats H:MM and HH:MM.
    colon_pattern = r'(\d+):(\d+)'
    colon_match = re.match(colon_pattern, time_str)
    
    if colon_match:
        hour_str, minute_str = colon_match.group(1), colon_match.group(2)
        if len(hour_str) not in (1, 2) or len(minute_str) != 2:
            raise ValueError(errormsg)
        hours, minutes = int(hour_str), int(minute_str)
    else:
        if len(time_str) == 1:
            hours   = int(time_str)
            minutes = 0
        elif len(time_str) == 2:
            hours   = int(time_str)
            minutes = 0
        elif len(time_str) == 3:
            hours   = int(time_str[0])
            minutes = int(time_str[1:])
        elif len(time_str) == 4:
            hours   = int(time_str[:2])
            minutes = int(time_str[2:])
        else:
            raise ValueError(errormsg)
    
    if hours > 24 or minutes > 60:
        raise ValueError(f"{hours}:{minutes} is not a time.")
    return hours, minutes


def set_all_day_event(service, date, summary, description, color=None):
    '''
    Set a single all-day event in the shift calendar, and save the event id in
    a log file.

    Dates must be passed in the format 'YYYY-MM-DD'.
    '''

    body = {
        "summary": summary,
        "description": description,
        "start": {"date": date, "timeZone": 'Europe/London'},
        "end": {"date": date, "timeZone": 'Europe/London'},
    }
    if color is not None:
        body["colorId"] = color

    event_result = service.events().insert(
        calendarId=CAL_ID,
        body=body
    ).execute()

    # Save all event id's in a log for easy deletion.
    with open('event_log.txt', 'a') as log:
        log.write(event_result['id']+'\n')


def set_timed_event(service, date, timeStart, timeEnd, summary, description, 
                    color=None):
    '''
    Set a single all-day event in the shift calendar, and save the event id in a
    log file.

    Dates must be passed in the format 'YYYY-MM-DD', and times must be passed in
    24-hour format (HH:MM).
    '''
    start_hours, start_mins = extract_hours_minutes(timeStart)
    end_hours, end_mins = extract_hours_minutes(timeEnd)

    datetimeStart = datetime.strptime(date, '%Y-%m-%d') \
                    + timedelta(hours=start_hours, 
                                minutes=start_mins)
    datetimeEnd = datetime.strptime(date, '%Y-%m-%d') \
                    + timedelta(hours=end_hours, 
                                minutes=end_mins)
    datetimeStart = datetimeStart.isoformat()
    datetimeEnd   = datetimeEnd.isoformat()

    body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": datetimeStart, "timeZone": 'Europe/London'},
        "end": {"dateTime": datetimeEnd, "timeZone": 'Europe/London'},
    }
    if color is not None:
        body["colorId"] = color

    event_result = service.events().insert(
        calendarId=CAL_ID,
        body=body
    ).execute()

    # Save all event id's in a log for easy deletion.
    with open('event_log.txt', 'a') as log:
        log.write(event_result['id']+'\n')


def delete_event(service, id):
    """
    Delete an event in the shift calendar given its event id. Return 0 if 
    succesful, else return 1.
    """
    try:
        service.events().delete(
            calendarId=CAL_ID,
            eventId=id,
        ).execute()
        print("Event deleted")
        return 0
    except HttpError as error_message:
        print("HttpError - Event not deleted: " + str(error_message))
        return 1
    

def delete_all_events(service):
    """
    Delete all events in the shift calendar stored in the event_log file, and 
    clear the file.
    Raise FileNotFoundError if event_log.txt has not been created by one of the
    set_event functions.
    """
    with open('event_log.txt', 'r') as log:
        all_ids = log.readlines()
        all_ids = [id.rstrip('\n') for id in all_ids]  # Remove newline characters.
        all_ids = [id.rstrip('\r') for id in all_ids]  # Remove return characters.
    
    undeleted_ids = []  # Store ids that fail to delete.
    for id in all_ids:
        if delete_event(service, id):
            undeleted_ids.append(id)
        else:
            continue

    # Store any non-deleted ids in a clean log.
    open('event_log.txt', 'w').close()
    with open('event_log.txt', 'a') as log:
        for id in undeleted_ids:
            log.write(id+'\n')


def add_to_cal_all_day(service, df):
    """
    Write a series of all-day events to the calendar. They must be passed as a 
    pandas dataframe with colums "Date" in the format '%Y-%m-%d' 
    (i.e. YYYY-MM-DD) and "Shift", which will be the event summary.
    """
    for i in range(len(df)):
        set_all_day_event(
            service, 
            date=df['Date'][i], 
            summary=df['Shift'][i],
            description=''
        )

def add_to_cal(service, df):
    """
    Write a series of events to the calendar. They must be passed as a pandas
    dataframe, with dtype=str, with colums "date" in the format '%Y-%m-%d' 
    (i.e. YYYY-MM-DD), "name", which will be the event summary, "start_time" and 
    "end_time" in the format "HH:MM" (24hr clock). If start_time is nan, the 
    event will be added as an all-day event.
    If "Color" is also passed, will make the event this color.
    Return the indexes in the dataframe of any events that were not added 
    sucessfully.
    """
    unsucessful_index = []
    for i in range(len(df)):
        try:
            if df['start_time'][i] == 'nan':
                set_all_day_event(
                    service, 
                    date=df['date'][i],
                    summary=df['name'][i],
                    description='',
                    color=df['color'][i]
                )
            else:
                set_timed_event(
                    service, 
                    date=df['date'][i],
                    timeStart=df['start_time'][i],
                    timeEnd=df['end_time'][i],
                    summary=df['name'][i],
                    description='',
                    color=df['color'][i]
                )
        except Exception as e:
            print('Error: '+str(e))
            unsucessful_index.append(i)
    return unsucessful_index



if __name__ == '__main__':
    '''
    An example of how to use the code here.
    '''
    from cal_setup import get_calendar_service
    from parse_calendar import parse_default_calendar

    calendar_data = parse_default_calendar()
    service = get_calendar_service()
    add_to_cal(service, calendar_data)

