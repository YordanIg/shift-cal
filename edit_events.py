"""
Functions that add and delete events from Flo's shift calendar.
"""
from googleapiclient.errors import HttpError
from parse_calendar import parse_calendar_data, parse_default_calendar
from datetime import datetime, timedelta


FLO_ID = '35ff39e798f9acc1fb3904b1372feca82c40d3656cebea11d7335551f8f70e0b@group.calendar.google.com'


def set_all_day_event(service, date, summary, description):
    '''
    Set a single all-day event in Flo's shift calendar, and save the event id in
    a log file.

    Dates must be passed in the format 'YYYY-MM-DD'.
    '''
    event_result = service.events().insert(
        calendarId=FLO_ID,
        body={
            "summary": summary,
            "description": description,
            "start": {"date": date, "timeZone": 'Europe/London'},
            "end": {"date": date, "timeZone": 'Europe/London'},
        }
    ).execute()

    # Save all event id's in a log for easy deletion.
    with open('event_log.txt', 'a') as log:
        log.write(event_result['id']+'\n')

    summary_text = "created event\n"
    summary_text += "id: {}\n".format(event_result['id'])
    summary_text += "summary: {}\n".format(event_result['summary'])
    summary_text += "starts at: {}\n".format(event_result['start']['date'])
    summary_text += "ends at: {}".format(event_result['end']['date'])
    return summary_text


def set_timed_event(service, date, timeStart, timeEnd, summary, description, 
                    color=None):
    '''
    Set a single all-day event in Flo's shift calendar, and save the event id in
    a log file.

    Dates must be passed in the format 'YYYY-MM-DD', and times must be passed in
    24-hour format (HH:MM).
    '''
    datetimeStart = datetime.strptime(date, '%Y-%m-%d') \
                    + timedelta(hours=int(timeStart[:2]), 
                                minutes=int(timeStart[3:]))
    datetimeEnd = datetime.strptime(date, '%Y-%m-%d') \
                    + timedelta(hours=int(timeEnd[:2]), 
                                minutes=int(timeEnd[3:]))
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
        calendarId=FLO_ID,
        body=body
    ).execute()

    # Save all event id's in a log for easy deletion.
    with open('event_log.txt', 'a') as log:
        log.write(event_result['id']+'\n')

    summary_text = "created event\n"
    summary_text += "id: {}\n".format(event_result['id'])
    summary_text += "summary: {}\n".format(event_result['summary'])
    summary_text += "starts at: {}\n".format(event_result['start']['dateTime'])
    summary_text += "ends at: {}".format(event_result['end']['dateTime'])
    return summary_text


def delete_event(service, id):
    """
    Delete an event in Flo's calendar given its event id. Return 0 if succesful,
    else return 1.
    """
    try:
        service.events().delete(
            calendarId=FLO_ID,
            eventId=id,
        ).execute()
        print("Event deleted")
        return 0
    except HttpError as error_message:
        print("HttpError - Event not deleted: " + str(error_message))
        return 1
    


def delete_all_events(service):
    """
    Delete all events in Flo's calendar stored in the event_log file, and clear
    the file.
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


'''
open the log file and store all ids in a list.
go through the list, deleting ids as you pass them to delete_event, and keep them
in the list if you don't.
re-write the file.
'''

def add_to_cal_all_day(service, df):
    """
    Write a series of all-day events to the calendar. They must be passed as a pandas
    dataframe with colums "Date" in the format '%Y-%m-%d' (i.e. YYYY-MM-DD) and 
    "Shift", which will be the event summary.
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
    dataframe with colums "Date" in the format '%Y-%m-%d' (i.e. YYYY-MM-DD), 
    "Shift", which will be the event summary, "Start Time" and "End Time" in the
    format "HH:MM" (24hr clock).
    If "Color" is also passed, will make the event this color.
    """
    for i in range(len(df)):
        set_timed_event(
            service, 
            date=df['Date'][i],
            timeStart=df['Start Time'][i],
            timeEnd=df['End Time'][i],
            summary=df['Shift'][i],
            description='',
            color=df['Color'][i]
        )


if __name__ == '__main__':
    '''
    An example of how to use the code here.
    '''
    from cal_setup import get_calendar_service

    calendar_data = parse_default_calendar()
    service = get_calendar_service()
    add_to_cal(service, calendar_data)

