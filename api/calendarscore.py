import json
import csv
import os
import datetime
from datetime import datetime as dt
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

class BorderCalendarScore:
    """
    A model to analyze border crossing wait times and correlate them with events
    to predict and classify border traffic levels.
    """
    
    # Traffic thresholds for classification (in minutes)
    TRAFFIC_THRESHOLDS = {
        'pv_time_avg': {'green': 60, 'yellow': 120},  # Personal Vehicle
        'ped_time_avg': {'green': 20, 'yellow': 40}   # Pedestrian
    }
    
    def __init__(self, monthly_data_dir, events_file):
        """
        Initialize the BorderCalendarScore model.
        
        Args:
            monthly_data_dir: Directory containing monthly JSON data files
            events_file: CSV file containing event data
        """
        self.monthly_data_dir = monthly_data_dir
        self.events_file = events_file
        self.monthly_data = {}  # Will store monthly data
        self.events = []  # Will store event data
        self.day_of_week_traffic_patterns = {}  # Will store traffic patterns by day of week
        self.date_scores = {}  # Will store traffic scores for specific dates
        
        # Load data
        self.load_monthly_data()
        self.load_events_data()
        self.analyze_traffic_patterns()
    
    def load_monthly_data(self):
        """Load all monthly traffic data files."""
        months = ['january', 'february', 'march', 'april', 'may', 'june',
                 'july', 'august', 'september', 'october', 'november', 'december']
        
        for month in months:
            file_path = os.path.join(self.monthly_data_dir, f"{month}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    self.monthly_data[month] = json.load(file)
                print(f"Loaded {month} data")
            else:
                print(f"Warning: {month}.json not found")
    
    def load_events_data(self):
        """Load events data from CSV."""
        if not os.path.exists(self.events_file):
            print(f"Warning: Events file {self.events_file} not found")
            return
        
        with open(self.events_file, 'r') as file:
            csv_reader = csv.reader(file)
            header = next(csv_reader)  # Skip header
            
            for row in csv_reader:
                if len(row) >= 2:
                    event = {
                        'title': row[0],
                        'date': row[1]
                    }
                    self.events.append(event)
        
        print(f"Loaded {len(self.events)} events")
    
    def analyze_traffic_patterns(self):
        """
        Analyze traffic patterns from monthly data to establish baselines
        for each day of the week and time slot.
        """
        # Initialize data structures
        day_totals = defaultdict(lambda: defaultdict(list))
        
        # Process all monthly data
        for month, data in self.monthly_data.items():
            if 'wait_times' not in data:
                continue
                
            for entry in data['wait_times']:
                # Skip incomplete entries
                if not all(key in entry for key in ['bwt_day', 'time_slot']):
                    continue
                
                try:
                    day = int(entry['bwt_day'])
                    time_slot = int(entry['time_slot'])
                    
                    # Convert string values to numbers, handling missing values
                    pv_time = int(entry.get('pv_time_avg', '0')) if entry.get('pv_time_avg') else 0
                    ped_time = int(entry.get('ped_time_avg', '0')) if entry.get('ped_time_avg') else 0
                    
                    # Store data by day and time slot
                    key = f"{day}_{time_slot}"
                    day_totals[key]['pv'].append(pv_time)
                    day_totals[key]['ped'].append(ped_time)
                except (ValueError, KeyError) as e:
                    # Skip entries with invalid data
                    continue
        
        # Calculate averages
        self.day_of_week_traffic_patterns = {}
        for key, values in day_totals.items():
            day, time_slot = key.split('_')
            day = int(day)
            time_slot = int(time_slot)
            
            if day not in self.day_of_week_traffic_patterns:
                self.day_of_week_traffic_patterns[day] = {}
            
            self.day_of_week_traffic_patterns[day][time_slot] = {
                'pv_time_avg': np.mean(values['pv']) if values['pv'] else 0,
                'ped_time_avg': np.mean(values['ped']) if values['ped'] else 0
            }
        
        print("Traffic patterns analyzed")
    
    def get_event_dates(self, year=2024):
        """
        Get all dates that have events.
        Returns a dictionary with date strings as keys and event titles as values.
        """
        event_dates = defaultdict(list)
        for event in self.events:
            try:
                # Parse the date string (assuming format MM/DD/YYYY or MM/DD/YYYY)
                date_str = event['date']
                if len(date_str.split('/')) == 2:  # If year is missing
                    date_str = f"{date_str}/{year}"
                
                # Store the event title for this date
                event_dates[date_str].append(event['title'])
            except Exception as e:
                print(f"Error processing event date: {e}")
        
        return event_dates
    
    def get_day_of_week(self, date_str):
        """Get the day of week (0-6) for a date string (MM/DD/YYYY)."""
        try:
            date_obj = dt.strptime(date_str, '%m/%d/%Y')
            return date_obj.weekday()
        except ValueError:
            # Try alternate format if the first one fails
            try:
                date_obj = dt.strptime(date_str, '%m/%d/%y')
                return date_obj.weekday()
            except ValueError:
                print(f"Warning: Could not parse date {date_str}")
                return None
    
    def get_month_name(self, date_str):
        """Get the month name for a date string (MM/DD/YYYY)."""
        try:
            date_obj = dt.strptime(date_str, '%m/%d/%Y')
            return date_obj.strftime('%B').lower()
        except ValueError:
            # Try alternate format if the first one fails
            try:
                date_obj = dt.strptime(date_str, '%m/%d/%y')
                return date_obj.strftime('%B').lower()
            except ValueError:
                print(f"Warning: Could not parse date {date_str}")
                return None
    
    def calculate_traffic_score(self, day_of_week, month_name=None, is_event_day=False):
        """
        Calculate a traffic score for a given day of week, optionally considering
        if it's an event day and using month-specific data if available.
        
        Returns a score dictionary with different metrics and time slots.
        """
        if day_of_week is None or day_of_week not in self.day_of_week_traffic_patterns:
            return None
            
        day_patterns = self.day_of_week_traffic_patterns[day_of_week]
        
        # Start with base traffic patterns for that day
        scores = {}
        for time_slot, metrics in day_patterns.items():
            scores[time_slot] = {
                'pv_time': metrics['pv_time_avg'],
                'ped_time': metrics['ped_time_avg']
            }
        
        # Apply event day adjustment (simplified model - increase by 20%)
        if is_event_day:
            for time_slot in scores:
                scores[time_slot]['pv_time'] *= 1.2
                scores[time_slot]['ped_time'] *= 1.2
        
        return scores
    
    def classify_traffic(self, traffic_score):
        """
        Classify traffic levels as green, yellow, or red based on wait times.
        
        Args:
            traffic_score: Dictionary with traffic metrics
            
        Returns:
            Dictionary with traffic classifications for each time slot
        """
        classifications = {}
        
        for time_slot, metrics in traffic_score.items():
            pv_time = metrics['pv_time']
            ped_time = metrics['ped_time']
            
            # Classify PV traffic
            if pv_time < self.TRAFFIC_THRESHOLDS['pv_time_avg']['green']:
                pv_class = 'green'
            elif pv_time < self.TRAFFIC_THRESHOLDS['pv_time_avg']['yellow']:
                pv_class = 'yellow'
            else:
                pv_class = 'red'
                
            # Classify pedestrian traffic
            if ped_time < self.TRAFFIC_THRESHOLDS['ped_time_avg']['green']:
                ped_class = 'green'
            elif ped_time < self.TRAFFIC_THRESHOLDS['ped_time_avg']['yellow']:
                ped_class = 'yellow'
            else:
                ped_class = 'red'
            
            # Overall classification (take the worse of the two)
            if 'red' in [pv_class, ped_class]:
                overall_class = 'red'
            elif 'yellow' in [pv_class, ped_class]:
                overall_class = 'yellow'
            else:
                overall_class = 'green'
            
            classifications[time_slot] = {
                'pv_class': pv_class,
                'ped_class': ped_class,
                'overall_class': overall_class
            }
        
        return classifications
    
    def score_event_dates(self, year=2024):
        """
        Calculate and classify traffic scores for all event dates.
        
        Returns:
            Dictionary with date strings as keys and traffic classifications as values
        """
        event_dates = self.get_event_dates(year)
        date_scores = {}
        
        for date_str, events in event_dates.items():
            day_of_week = self.get_day_of_week(date_str)
            month_name = self.get_month_name(date_str)
            
            if day_of_week is not None:
                traffic_score = self.calculate_traffic_score(
                    day_of_week, month_name, is_event_day=True
                )
                
                if traffic_score:
                    classification = self.classify_traffic(traffic_score)
                    
                    # Store the results
                    date_scores[date_str] = {
                        'events': events,
                        'traffic_score': traffic_score,
                        'classification': classification
                    }
        
        self.date_scores = date_scores
        return date_scores
    
    def get_daily_classification(self, date_scores):
        """
        Get an overall daily classification from hourly classifications.
        
        Args:
            date_scores: Dictionary with traffic scores for a date
            
        Returns:
            Overall classification for the day (green, yellow, or red)
        """
        if 'classification' not in date_scores:
            return 'unknown'
        
        # Count classifications across all time slots
        counts = {'green': 0, 'yellow': 0, 'red': 0}
        
        for time_slot, classes in date_scores['classification'].items():
            counts[classes['overall_class']] += 1
        
        # Determine majority classification with priority to more severe levels
        if counts['red'] > 5:  # If more than 5 hours are red
            return 'red'
        elif counts['yellow'] > 8 or counts['red'] > 2:  # If more than 8 hours yellow or 2+ hours red
            return 'yellow'
        else:
            return 'green'
    
    def generate_calendar_data(self, year=2024):
        """
        Generate calendar data with traffic classifications for all dates in the year.
        
        Returns:
            Dictionary with date strings as keys and classification data as values
        """
        # Score event dates first
        if not self.date_scores:
            self.score_event_dates(year)
        
        # Create calendar data structure
        calendar_data = {}
        
        # Get all days in the year
        start_date = dt(year, 1, 1)
        end_date = dt(year, 12, 31)
        delta = datetime.timedelta(days=1)
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%m/%d/%Y')
            day_of_week = current_date.weekday()
            month_name = current_date.strftime('%B').lower()
            
            # Check if this is an event date
            is_event_day = date_str in self.date_scores
            events = self.date_scores.get(date_str, {}).get('events', []) if is_event_day else []
            
            # Calculate traffic score
            traffic_score = self.calculate_traffic_score(
                day_of_week, month_name, is_event_day=is_event_day
            )
            
            if traffic_score:
                classification = self.classify_traffic(traffic_score)
                daily_class = 'green'  # Default
                
                if is_event_day:
                    # Use the pre-calculated classification for event days
                    daily_class = self.get_daily_classification(self.date_scores[date_str])
                else:
                    # Calculate classification for non-event days
                    counts = {'green': 0, 'yellow': 0, 'red': 0}
                    for _, classes in classification.items():
                        counts[classes['overall_class']] += 1
                    
                    # Determine overall classification
                    if counts['red'] > 5:
                        daily_class = 'red'
                    elif counts['yellow'] > 8 or counts['red'] > 2:
                        daily_class = 'yellow'
                
                calendar_data[date_str] = {
                    'events': events,
                    'classification': daily_class
                }
            
            current_date += delta
        
        return calendar_data
    
    def get_event_impact_analysis(self):
        """
        Analyze the impact of different events on border traffic.
        
        Returns:
            Dictionary with event names as keys and impact analysis as values
        """
        if not self.date_scores:
            self.score_event_dates()
        
        event_impacts = defaultdict(list)
        
        for date_str, data in self.date_scores.items():
            for event in data['events']:
                # Get the overall classification for this date
                classification = self.get_daily_classification(data)
                event_impacts[event].append(classification)
        
        # Calculate percentage of each classification for each event
        event_analysis = {}
        for event, classifications in event_impacts.items():
            total = len(classifications)
            if total > 0:
                counts = {
                    'green': classifications.count('green') / total,
                    'yellow': classifications.count('yellow') / total,
                    'red': classifications.count('red') / total
                }
                
                # Determine overall impact
                if counts['red'] > 0.5:  # If more than half the days are red
                    impact = 'high'
                elif counts['yellow'] + counts['red'] > 0.5:  # If more than half are yellow or red
                    impact = 'medium'
                else:
                    impact = 'low'
                
                event_analysis[event] = {
                    'classifications': counts,
                    'impact': impact
                }
        
        return event_analysis


# Example usage
if __name__ == "__main__":
    # Path to the datasets folder
    base_dir = Path(__file__).parent.parent
    datasets_dir = base_dir / 'datasets'
    events_file = datasets_dir / 'calendar_parsedevents.csv'
    
    # Create the model
    calendar_model = BorderCalendarScore(datasets_dir, events_file)
    
    # Score event dates
    event_scores = calendar_model.score_event_dates()
    
    # Print some sample results
    print("\n--- Sample Event Date Traffic Scores ---")
    sample_count = 0
    for date_str, data in event_scores.items():
        if sample_count >= 3:
            break
        
        daily_class = calendar_model.get_daily_classification(data)
        print(f"\nDate: {date_str}")
        print(f"Events: {', '.join(data['events'])}")
        print(f"Overall Classification: {daily_class.upper()}")
        
        # Print some hourly details
        print("Hourly classifications (sample):")
        for hour in [8, 12, 17]:  # Morning, noon, evening
            if str(hour) in data['classification']:
                cls = data['classification'][str(hour)]['overall_class']
                print(f"  Hour {hour}: {cls.upper()}")
        
        sample_count += 1
    
    # Generate calendar data for the whole year
    calendar_data = calendar_model.generate_calendar_data()
    print(f"\nGenerated calendar data for {len(calendar_data)} dates")
    
    # Event impact analysis
    print("\n--- Event Impact Analysis ---")
    event_analysis = calendar_model.get_event_impact_analysis()
    
    sample_count = 0
    for event, analysis in event_analysis.items():
        if sample_count >= 5:
            break
        
        print(f"\nEvent: {event}")
        print(f"Impact: {analysis['impact'].upper()}")
        print(f"Classification Distribution:")
        for cls, pct in analysis['classifications'].items():
            print(f"  {cls.upper()}: {pct:.1%}")
        
        sample_count += 1