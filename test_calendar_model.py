#!/usr/bin/env python3

from api.calendarscore import BorderCalendarScore
from pathlib import Path
import datetime

def test_specific_dates(model, dates):
    """Test specific dates with the model and print results."""
    print("\n=== Testing Specific Dates ===")
    
    for date_str in dates:
        # Get day of week and month
        try:
            date_obj = datetime.datetime.strptime(date_str, '%m/%d/%Y')
            day_of_week = date_obj.weekday()
            month_name = date_obj.strftime('%B').lower()
            
            # Check if this is an event date
            is_event_date = date_str in model.date_scores
            events = model.date_scores.get(date_str, {}).get('events', []) if is_event_date else []
            
            print(f"\nDate: {date_str} ({date_obj.strftime('%A')})")
            print(f"Events: {', '.join(events) if events else 'No events'}")
            
            # Get baseline traffic (no event)
            baseline = model.calculate_traffic_score(day_of_week, month_name, is_event_day=False)
            
            # Get event-adjusted traffic if applicable
            if is_event_date:
                traffic_score = model.date_scores[date_str]['traffic_score']
                classification = model.date_scores[date_str]['classification']
                daily_class = model.get_daily_classification(model.date_scores[date_str])
            else:
                traffic_score = model.calculate_traffic_score(day_of_week, month_name, is_event_day=False)
                classification = model.classify_traffic(traffic_score)
                
                # Calculate daily classification
                counts = {'green': 0, 'yellow': 0, 'red': 0}
                for _, classes in classification.items():
                    counts[classes['overall_class']] += 1
                
                if counts['red'] > 5:
                    daily_class = 'red'
                elif counts['yellow'] > 8 or counts['red'] > 2:
                    daily_class = 'yellow'
                else:
                    daily_class = 'green'
            
            print(f"Overall Classification: {daily_class.upper()}")
            
            # Print sample hours (morning, noon, evening)
            print("Traffic by hour (sample):")
            for hour in [8, 12, 17]:  # Morning, noon, evening
                hour_str = str(hour)
                if hour_str in traffic_score and hour_str in classification:
                    baseline_pv = baseline[hour_str]['pv_time'] if hour_str in baseline else 0
                    baseline_ped = baseline[hour_str]['ped_time'] if hour_str in baseline else 0
                    
                    event_pv = traffic_score[hour_str]['pv_time']
                    event_ped = traffic_score[hour_str]['ped_time']
                    
                    impact_factor = event_pv / baseline_pv if baseline_pv > 0 else 1.0
                    
                    cls = classification[hour_str]['overall_class']
                    print(f"  Hour {hour}: {cls.upper()}")
                    print(f"    Baseline: PV {baseline_pv:.1f} min, Ped {baseline_ped:.1f} min")
                    print(f"    With events: PV {event_pv:.1f} min, Ped {event_ped:.1f} min")
                    print(f"    Impact factor: {impact_factor:.2f}x increase")
        except Exception as e:
            print(f"Error processing date {date_str}: {e}")
            

def test_event_impact(model, event_names):
    """Test the impact of specific events."""
    print("\n=== Testing Event Impact ===")
    
    event_analysis = model.get_event_impact_analysis()
    
    for event in event_names:
        if event in event_analysis:
            impact = event_analysis[event]['impact']
            classifications = event_analysis[event]['classifications']
            
            print(f"\nEvent: {event}")
            print(f"Impact: {impact.upper()}")
            print(f"Classification Distribution:")
            for cls, pct in classifications.items():
                print(f"  {cls.upper()}: {pct:.1%}")
            
            # Find dates for this event
            dates = []
            for date_str, data in model.date_scores.items():
                if event in data['events']:
                    dates.append(date_str)
            
            print(f"Occurs on {len(dates)} dates: {', '.join(sorted(dates)[:3])}...")
        else:
            print(f"\nEvent '{event}' not found in analysis")


def main():
    try:
        # Initialize the model
        base_dir = Path(__file__).parent
        datasets_dir = base_dir / 'datasets'
        events_file = datasets_dir / 'calendar_parsedevents.csv'
        
        print("Initializing the BorderCalendarScore model...")
        model = BorderCalendarScore(datasets_dir, events_file)
        
        # Score all event dates
        print("Scoring event dates...")
        model.score_event_dates()
        
        # Test specific dates
        test_dates = [
            "7/4/2024",    # 4th of July events
            "9/14/2024",   # Multiple events
            "12/25/2024",  # Christmas (likely no events)
            "6/15/2024",   # Check if there are events
            "11/28/2024"   # Thanksgiving
        ]
        print(f"Testing {len(test_dates)} specific dates...")
        test_specific_dates(model, test_dates)
        
        # Test specific event impacts
        test_events = [
            "San Diego Bayfair",
            "CONCACAF W Gold Cup",
            "Fleet Week San Diego 2024",
            "Little Italy Summer Film Festival",
            "The Spirit of the Fourth"
        ]
        print(f"Testing {len(test_events)} specific events...")
        test_event_impact(model, test_events)
        
        print("Tests completed successfully")
        
    except Exception as e:
        import traceback
        print(f"Error in main: {e}")
        traceback.print_exc()
    
    # Print overall calendar statistics
    calendar_data = model.generate_calendar_data()
    classifications = {'green': 0, 'yellow': 0, 'red': 0}
    for date_data in calendar_data.values():
        classifications[date_data['classification']] += 1
    
    total = sum(classifications.values())
    print("\n=== Calendar Classification Distribution ===")
    for cls, count in classifications.items():
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"{cls.upper()}: {count} days ({percentage:.1f}%)")


if __name__ == "__main__":
    main()
