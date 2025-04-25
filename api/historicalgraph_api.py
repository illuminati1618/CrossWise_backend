from flask import Blueprint, jsonify, Response
from flask_restful import Api, Resource
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Create the Blueprint
historicalgraph_api = Blueprint('historicalgraph_api', __name__, url_prefix='/api')
api = Api(historicalgraph_api)

class BorderWaitAPI:
    class _GetVisualization(Resource):
        def get(self):
            try:
                # Path to the JSON data file
                # Adjust this path to where your JSON data is stored in your project
                data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'datasets/april.json')
                
                # Load the JSON data
                with open(data_path, 'r') as file:
                    data = json.load(file)

                # Extract wait times data
                wait_times = data['wait_times']

                # Convert to DataFrame
                df = pd.DataFrame(wait_times)

                # Convert data types
                for col in df.columns:
                    if col != 'bwt_day' and col != 'time_slot':
                        df[col] = pd.to_numeric(df[col])

                # Map day numbers to day names
                day_map = {
                    '0': 'Sunday',
                    '1': 'Monday',
                    '2': 'Tuesday',
                    '3': 'Wednesday',
                    '4': 'Thursday',
                    '5': 'Friday',
                    '6': 'Saturday'
                }

                # Map time slots to human-readable times
                time_map = {
                    '0': 'Midnight',
                    '1': '1 am',
                    '2': '2 am',
                    '3': '3 am',
                    '4': '4 am',
                    '5': '5 am',
                    '6': '6 am',
                    '7': '7 am',
                    '8': '8 am',
                    '9': '9 am',
                    '10': '10 am',
                    '11': '11 am',
                    '12': 'Noon',
                    '13': '1 pm',
                    '14': '2 pm',
                    '15': '3 pm',
                    '16': '4 pm',
                    '17': '5 pm',
                    '18': '6 pm',
                    '19': '7 pm',
                    '20': '8 pm',
                    '21': '9 pm',
                    '22': '10 pm',
                    '23': '11 pm'
                }

                # Add day names and human-readable times
                df['day_name'] = df['bwt_day'].map(day_map)
                df['time_label'] = df['time_slot'].map(time_map)

                # Create figure
                fig = go.Figure()

                # Add traces for each day of the week, focusing on pedestrian wait times (ped_time_avg)
                for day in sorted(df['bwt_day'].unique()):
                    day_data = df[df['bwt_day'] == day].sort_values('time_slot')
                    day_name = day_map[day]
                    
                    # Add line for standard vehicle crossing (pv_time_avg)
                    fig.add_trace(go.Scatter(
                        x=day_data['time_label'],
                        y=day_data['pv_time_avg'],
                        mode='lines+markers',
                        name=f'{day_name}',
                        hovertemplate='<b>%{text}</b><br>Time: %{x}<br>Wait Time: %{y} min<extra></extra>',
                        text=[f"{day_name}" for _ in range(len(day_data))],
                        visible=True if day == '0' else 'legendonly'  # Only show Sunday by default
                    ))

                # Update layout
                fig.update_layout(
                    title={
                        'text': "Average Wait Times for January",
                        'y':0.95,
                        'x':0.5,
                        'xanchor': 'center',
                        'yanchor': 'top'
                    },
                    xaxis_title="Time of Day",
                    yaxis_title="Wait Time (min)",
                    hovermode="closest",
                    legend_title="Day of Week",
                    height=600,
                    width=1000,
                    margin=dict(l=50, r=50, t=100, b=100),
                    annotations=[
                        dict(
                            x=0.5,
                            y=1.05,
                            xref="paper",
                            yref="paper",
                            text="(Averages are based on data from previous year)",
                            showarrow=False,
                            font=dict(
                                size=12,
                                color="green"
                            )
                        )
                    ]
                )

                # Add a vertical line at 11 am for Sunday with an annotation
                sunday_data = df[(df['bwt_day'] == '0')].sort_values('time_slot')
                eleven_am_index = sunday_data[sunday_data['time_slot'] == '11'].index[0]
                eleven_am_value = sunday_data.loc[eleven_am_index, 'pv_time_avg']

                fig.add_shape(
                    type="line",
                    x0='11 am', x1='11 am',
                    y0=0, y1=50,
                    line=dict(color="black", width=1, dash="solid"),
                    visible=True
                )

                fig.add_annotation(
                    x='11 am',
                    y=eleven_am_value + 10,
                    text=f"At 11 am<br>Sunday: {int(eleven_am_value)} min",
                    showarrow=False,
                    font=dict(size=12),
                    bgcolor="rgba(200, 200, 200, 0.5)",
                    bordercolor="gray",
                    borderwidth=1,
                    borderpad=4,
                    visible=True
                )

                # Generate HTML representation
                html_content = fig.to_html(include_plotlyjs=True, full_html=True)
                
                # Return the HTML content with proper content type
                return Response(html_content, mimetype='text/html')
                
            except Exception as e:
                return {"error": str(e)}, 500

    # Add the resource to the API
    api.add_resource(_GetVisualization, '/visualization')