import pandas as pd
import re
import os

def load_timetable_data(files):
    """Load all timetable CSV files into a single DataFrame"""
    all_data = []
    for file in files:
        try:
            # Check if file exists and is not empty
            if not os.path.exists(file):
                print(f"Warning: File {file} does not exist. Skipping.")
                continue
                
            if os.path.getsize(file) == 0:
                print(f"Warning: File {file} is empty. Skipping.")
                continue
                
            # Try to read the CSV file
            df = pd.read_csv(file)
            print(f"✓ Successfully loaded {file} with {len(df)} rows")
            all_data.append(df)
            
        except pd.errors.EmptyDataError:
            print(f"Warning: File {file} is empty or has no columns. Skipping.")
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    if not all_data:
        raise Exception("No data was loaded from any file")
    
    return pd.concat(all_data, ignore_index=True)

def parse_time_input(time_str):
    """Convert time input like '8:00' to minutes since midnight"""
    try:
        # Handle both HH:MM and H:MM formats
        if ':' in time_str:
            hours, minutes = map(int, time_str.split(':'))
        else:
            # If no colon, assume it's just hours
            hours = int(time_str)
            minutes = 0
        
        return hours * 60 + minutes
    except:
        return None

def parse_slot_time(slot_str):
    """Convert slot string like 'S8:50am - 9:40am' to time range in minutes"""
    # Remove the 'S' prefix if present
    slot_str = slot_str.replace('S', '')
    
    # Extract the time part from the slot string
    match = re.search(r'(\d+:\d+)(am|pm)?\s*-\s*(\d+:\d+)(am|pm)?', slot_str, re.IGNORECASE)
    if not match:
        return None, None
    
    start_time_str, start_period, end_time_str, end_period = match.groups()
    
    # Convert to 24-hour format
    def convert_to_minutes(time_str, period):
        # Handle time format like "8:50"
        if ':' in time_str:
            hours, minutes = map(int, time_str.split(':'))
        else:
            # If no colon, assume it's just hours
            hours = int(time_str)
            minutes = 0
        
        # Convert to 24-hour format based on period
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
    
    # Filter for the requested day
    day_data = df[df['Day'].str.lower() == day.lower()]
    if day_data.empty:
        return f"No data available for {day}.", None
    
    free_classrooms = []
    occupied_classrooms = []
    
    print(f"\nSearching for time: {time_minutes//60}:{time_minutes%60:02d} on {day}")
    
    # Check each classroom for the given time
    for _, row in day_data.iterrows():
        start_minutes, end_minutes = parse_slot_time(row['Slot'])
        
        if start_minutes is None or end_minutes is None:
            continue
            
        # Check if the requested time falls within this slot
        if start_minutes <= time_minutes < end_minutes:
            subject = str(row['Subject'])
            
            # Classroom is free if subject is empty, NaN, or Break/Mentoring
            if (pd.isna(subject) or subject.strip() == '' or subject == 'nan' or 
                subject.lower() == 'break' or subject.lower() == 'mentor hour' or
                subject.lower() == 'mentoring'):
                free_classrooms.append({
                    'Department': row['Department'],
                    'Block': row['Block'],
                    'Classroom': row['Classroom'],
                    'Slot': row['Slot']
                })
            else:
                occupied_classrooms.append({
                    'Department': row['Department'],
                    'Block': row['Block'],
                    'Classroom': row['Classroom'],
                    'Subject': subject,
                    'Slot': row['Slot']
                })
    
    return free_classrooms, occupied_classrooms

def display_timetable_preview(df):
    """Display a preview of the timetable data"""
    print("\n" + "="*60)
    print("TIMETABLE PREVIEW")
    print("="*60)
    print(f"Total entries: {len(df)}")
    print(f"Departments: {df['Department'].unique()}")
    print(f"Days: {df['Day'].unique()}")
    print(f"Blocks: {df['Block'].unique()}")
    print(f"Classrooms: {df['Classroom'].unique()}")
    
    # Show first few entries
    print("\nFirst 5 entries:")
    print(df[['Department', 'Day', 'Slot', 'Subject']].head().to_string(index=False))

def main():
    # List of CSV files to process
<<<<<<< HEAD
    csv_files = ['mech.csv']  # Use your MECHANICAL CSV file
=======
    csv_files = ['civil_timetable_neat.csv', 'datascience.csv', 'eee.csv', 'mech.csv']
>>>>>>> 5c7b288374c7c3def2a7242c4ef20c3c194efb10
    
    try:
        # Load all timetable data
        print("Loading timetable data...")
        df = load_timetable_data(csv_files)
        print("✓ Timetable data loaded successfully!")
        
        # Display preview
        display_timetable_preview(df)
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        print("Please make sure your mech.csv file exists and is properly formatted.")
        print("The file should be in the same directory as this script.")
        return
    
    print("\n" + "="*60)
    print("FREE SLOT FINDER")
    print("="*60)
    
    while True:
        try:
            # Get user input
            print("\nEnter the details to find free classrooms:")
            day = input("Day (e.g., Monday, Tuesday): ").strip()
            
            if day.lower() == 'exit':
                print("Goodbye!")
                break
                
            time_str = input("Time in HH:MM format (e.g., 8:30, 14:45): ").strip()
            
            if time_str.lower() == 'exit':
                print("Goodbye!")
                break
            
            # Find free classrooms
            free_classrooms, occupied_classrooms = find_free_classrooms(day, time_str, df)
            
            if isinstance(free_classrooms, str):  # Error message
                print(f"\n❌ {free_classrooms}")
                continue
            
            # Display results
            print(f"\n{'='*60}")
            print(f"RESULTS FOR {day.upper()} AT {time_str}")
            print(f"{'='*60}")
            
            if free_classrooms:
                print(f"\n✅ FREE CLASSROOMS ({len(free_classrooms)} found):")
                for i, room in enumerate(free_classrooms, 1):
                    print(f"{i}. {room['Department']} - {room['Block']} - {room['Classroom']} ({room['Slot']})")
            else:
                print(f"\n❌ No free classrooms found at {time_str} on {day}")
            
            if occupied_classrooms:
                print(f"\n🚫 OCCUPIED CLASSROOMS ({len(occupied_classrooms)} found):")
                for i, room in enumerate(occupied_classrooms, 1):
                    print(f"{i}. {room['Department']} - {room['Block']} - {room['Classroom']}: {room['Subject']} ({room['Slot']})")
            
            print(f"\n{'='*60}")
            
            # Ask if user wants to continue
            cont = input("\nDo you want to check another time? (yes/no): ").strip().lower()
            if cont not in ['yes', 'y', '']:
                print("Goodbye!")
                break
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please try again with valid inputs.")

if __name__ == "__main__":
    main()