import pandas as pd
import re
import gradio as gr

def load_timetable_data(files):
    """Load all timetable CSV files into a single DataFrame"""
    all_data = []
    for file in files:
        df = pd.read_csv(file)
        all_data.append(df)
    
    return pd.concat(all_data, ignore_index=True)

def parse_time_input(time_str):
    """Convert time input like '8:00' to minutes since midnight"""
    try:
        if ':' in time_str:
            hours, minutes = map(int, time_str.split(':'))
        else:
            hours = int(time_str)
            minutes = 0
        return hours * 60 + minutes
    except:
        return None

def parse_slot_time(slot_str):
    """Convert slot string like 'S2.05pm - 2.55pm' to time range in minutes"""
    match = re.search(r'S?(\d+\.\d+)(am|pm)?\s*-\s*(\d+\.\d+)(am|pm)?', slot_str, re.IGNORECASE)
    if not match:
        return None, None
    
    start_time_str, start_period, end_time_str, end_period = match.groups()
    
    def convert_to_minutes(time_str, period):
        time_str = time_str.replace('.', ':')
        if ':' in time_str:
            hours, minutes = map(int, time_str.split(':'))
        else:
            hours = int(time_str)
            minutes = 0
        
        if period and period.lower() == 'pm' and 1 <= hours <= 11:
            period = 'am'
        if period and period.lower() == 'pm' and hours != 12:
            hours += 12
        elif period and period.lower() == 'am' and hours == 12:
            hours = 0
        return hours * 60 + minutes
    
    start_minutes = convert_to_minutes(start_time_str, start_period)
    end_minutes = convert_to_minutes(end_time_str, end_period)
    
    return start_minutes, end_minutes

def find_free_classrooms(day, time_str, df):
    """Find free classrooms for a given day and time"""
    time_minutes = parse_time_input(time_str)
    if time_minutes is None:
        return "Invalid time format. Please use HH:MM format.", None
    
    day_data = df[df['Day'].str.lower() == day.lower()]
    if day_data.empty:
        return f"No data available for {day}.", None
    
    free_classrooms = []
    occupied_classrooms = []
    
    for _, row in day_data.iterrows():
        start_minutes, end_minutes = parse_slot_time(row['Slot'])
        if start_minutes is None or end_minutes is None:
            continue
        if start_minutes <= time_minutes < end_minutes:
            subject = str(row['Subject'])
            if (pd.isna(subject) or subject.strip() == '' or subject == 'nan' or 
                subject.lower() == 'break' or subject.lower() == 'mentor hour'):
                free_classrooms.append(f"{row['Department']} - {row['Block']} - {row['Classroom']} ({row['Slot']})")
            else:
                occupied_classrooms.append(f"{row['Department']} - {row['Block']} - {row['Classroom']}: {subject} ({row['Slot']})")
    
    return free_classrooms, occupied_classrooms

# Load all timetable data once
csv_files = ['civil_timetable_neat.csv', 'datascience.csv', 'eee.csv']
df = load_timetable_data(csv_files)

def gradio_interface(day, time_str):
    free_classrooms, occupied_classrooms = find_free_classrooms(day, time_str, df)
    if isinstance(free_classrooms, str):
        return free_classrooms, ""
    free_text = "\n".join(free_classrooms) if free_classrooms else "No free classrooms"
    occupied_text = "\n".join(occupied_classrooms) if occupied_classrooms else "No occupied classrooms"
    return free_text, occupied_text

# Gradio UI
iface = gr.Interface(
    fn=gradio_interface,
    inputs=[
        gr.Dropdown(choices=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], label="Day"),
        gr.Textbox(label="Enter time (e.g., 8:00, 14:45)")
    ],
    outputs=[
        gr.Textbox(label="Free Classrooms"),
        gr.Textbox(label="Occupied Classrooms")
    ],
    title="Classroom Availability Finder",
    description="Select a day and enter a time (HH:MM) to check free and occupied classrooms."
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0",server_port=7860,pwa=True,debug=True)