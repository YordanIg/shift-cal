import tkinter as tk
from tkinter import ttk
import calendar
import datetime
import csv
import pandas as pd
from parse_calendar import parse_default_calendar
from cal_setup import get_calendar_service
from edit_events import add_to_cal

class CalendarApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Event Calendar")
        self.geometry("800x600")

        self.style = ttk.Style()
        self.style.configure("TButton", background="white")  # Default background color
        self.style.configure("Highlighted.TButton", background="light gray")  # Darkened background color

        self.calendar_frame = ttk.Frame(self)
        self.calendar_frame.pack(side=tk.LEFT, expand=True, fill="both")

        self.side_panel = ttk.Frame(self, width=250)
        self.side_panel.pack(side=tk.RIGHT, fill="y")

        self.date = ttk.Label(self.calendar_frame, text="", font=("Helvetica", 16))
        self.date.pack()

        self.calendar_grid = ttk.Frame(self.calendar_frame)
        self.calendar_grid.pack()

        self.event_types = []  # List to store event types
        self.events = []  # List to store events added to the calendar

        self.current_date = datetime.date.today()
        self.update_calendar()

        # Buttons to toggle months and years
        self.prev_month_btn = ttk.Button(self.calendar_frame, text="Prev Month", command=self.previous_month)
        self.prev_month_btn.pack(side=tk.LEFT, padx=10)
        self.next_month_btn = ttk.Button(self.calendar_frame, text="Next Month", command=self.next_month)
        self.next_month_btn.pack(side=tk.LEFT, padx=10)

        self.prev_year_btn = ttk.Button(self.calendar_frame, text="Prev Year", command=self.previous_year)
        self.prev_year_btn.pack(side=tk.LEFT, padx=10)
        self.next_year_btn = ttk.Button(self.calendar_frame, text="Next Year", command=self.next_year)
        self.next_year_btn.pack(side=tk.LEFT, padx=10)

        # Side panel widgets for creating custom events
        self.event_name = ttk.Entry(self.side_panel)
        self.event_name_label = ttk.Label(self.side_panel, text="Shift Name:")
        self.event_name_label.pack()
        self.event_name.pack()

        self.start_time = ttk.Entry(self.side_panel)
        self.start_time_label = ttk.Label(self.side_panel, text="Start Time:")
        self.start_time_label.pack()
        self.start_time.pack()

        self.end_time = ttk.Entry(self.side_panel)
        self.end_time_label = ttk.Label(self.side_panel, text="End Time:")
        self.end_time_label.pack()
        self.end_time.pack()

        # Color buttons for the user to choose from
        self.color_frame = ttk.Frame(self.side_panel)
        self.color_frame.pack(pady=10)
        self.color_label = ttk.Label(self.color_frame, text="Select Color:")
        self.color_label.pack()

        # Define three color options
        colors = ["1", "2", "3", "4", "5", "6"]
        self.selected_color = tk.StringVar()

        for color in colors:
            row_frame = ttk.Frame(self.color_frame)
            row_frame.pack()

            color_btn = ttk.Button(
                row_frame,
                text=color.capitalize(),
                command=lambda c=color: self.select_color(c),
                width=10,
                style="Color.TButton"  # Apply a custom style for the buttons
            )
            color_btn.pack(side=tk.LEFT, padx=5, pady=5)
            color_btn.bind("<Enter>", lambda event, btn=color_btn: self.highlight_color_btn(btn))
            color_btn.bind("<Leave>", lambda event, btn=color_btn: self.reset_color_btn(btn))

        self.create_event_type_btn = ttk.Button(self.side_panel, text="Create Event Type", command=self.create_event_type)
        self.create_event_type_btn.pack()

        # List to display added event types below the calendar
        self.added_event_types_list = tk.Listbox(self.side_panel, height=8, width=40)
        self.added_event_types_list.pack(pady=10)
        self.added_event_types_list.bind("<<ListboxSelect>>", self.select_event_type)

        # Variable to store the selected event type
        self.selected_event_type = None

        # List to display added events below the calendar
        self.added_events_list = tk.Listbox(self.side_panel, height=8, width=40)
        self.added_events_list.pack(pady=10)

        # Save button
        self.save_btn = ttk.Button(self.side_panel, text="Save", 
                                   command=self.save_events_to_csv)
        self.save_btn.pack()

        # Upload button
        self.upload_btn = ttk.Button(self.side_panel, text="Upload", 
                                   command=self.upload_events_to_gcal)
        self.upload_btn.pack()

    def update_calendar(self):
        self.date.config(text=self.current_date.strftime("%B %Y"))

        year = self.current_date.year
        month = self.current_date.month
        cal = calendar.monthcalendar(year, month)

        for widget in self.calendar_grid.winfo_children():
            widget.destroy()

        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day != 0:
                    day_btn = ttk.Button(
                        self.calendar_grid,
                        text=str(day),
                        command=lambda day=day: self.add_event(day),
                    )
                    day_btn.grid(row=week_num, column=day_num, ipady=10, ipadx=10)

    def create_event_type(self):
        name = self.event_name.get()
        start_time = self.start_time.get()
        end_time = self.end_time.get()
        color = self.selected_color.get()  # Use the selected color

        event_type = {
            "name": name,
            "start_time": start_time,
            "end_time": end_time,
            "color": color,
            "dates": []  # List to store assigned dates
        }

        self.event_types.append(event_type)
        self.event_name.delete(0, tk.END)
        self.start_time.delete(0, tk.END)
        self.end_time.delete(0, tk.END)
        self.selected_color.set(None)

        # Add the created event type to the list for selection
        self.added_event_types_list.insert(tk.END, name)

    def add_event(self, day):
        if self.selected_event_type:
            selected_event_type = self.selected_event_type

            # Calculate the clicked date based on the current month and year, and the selected day
            clicked_date = self.current_date.replace(day=day)

            # Check if the event is already assigned to this date
            if clicked_date.strftime("%Y-%m-%d") in selected_event_type["dates"]:
                selected_event_type["dates"].remove(clicked_date.strftime("%Y-%m-%d"))
            else:
                selected_event_type["dates"].append(clicked_date.strftime("%Y-%m-%d"))

            # Update event list with the correct dates
            self.create_event(clicked_date)

    def select_event_type(self, event):
        selected_index = self.added_event_types_list.curselection()
        if selected_index:
            selected_event_name = self.added_event_types_list.get(selected_index[0])
            self.selected_event_type = self.get_event_type_by_name(selected_event_name)

    def get_event_type_by_name(self, event_name):
        for event_type in self.event_types:
            if event_type["name"] == event_name:
                return event_type
        return None

    def create_event(self, clicked_date):
        if self.selected_event_type:
            selected_event_type = self.selected_event_type

            # Create a new event using the clicked date instead of self.current_date
            new_event = {
                "date": clicked_date.strftime("%Y-%m-%d"),
                "name": selected_event_type["name"],
                "start_time": selected_event_type["start_time"],
                "end_time": selected_event_type["end_time"],
                "color": selected_event_type["color"]
            }
            self.events.append(new_event)
            self.update_added_events_list()

    def update_added_events_list(self):
        self.added_events_list.delete(0, tk.END)
        for event in self.events:
            event_name = event["name"]
            event_date = event["date"]
            self.added_events_list.insert(tk.END, f"{event_name} - Date: {event_date}")

    def previous_month(self):
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self.update_calendar()

    def next_month(self):
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self.update_calendar()

    def previous_year(self):
        self.current_date = self.current_date.replace(year=self.current_date.year - 1)
        self.update_calendar()

    def next_year(self):
        self.current_date = self.current_date.replace(year=self.current_date.year + 1)
        self.update_calendar()

    def select_color(self, color):
        self.selected_color.set(color)

    def highlight_color_btn(self, btn):
        # Toggle the style to "Highlighted.TButton" when the button is entered
        self.style.configure(btn["style"], background="light gray")

    def reset_color_btn(self, btn):
        # Toggle the style back to "TButton" when the button is left
        self.style.configure(btn["style"], background="white")

    def save_events_to_csv(self):
        pd.DataFrame(self.events).to_csv("new_cal_data.csv")
    
    def upload_events_to_gcal(self):
        """
        Upload the events saved in the file new_cal_data.csv to Google Calendar,
        and erase the contents of new_cal_data.csv if successful.
        """
        calendar_data = parse_default_calendar()
        service = get_calendar_service()
        unsucessful_index = add_to_cal(service, calendar_data)

        unsucessful_event_calendar_data = calendar_data.iloc[unsucessful_index]
        unsucessful_event_calendar_data.to_csv("new_cal_data.csv", index=False)
        

def main():
    app = CalendarApp()
    app.mainloop()

if __name__ == "__main__":
    main()
