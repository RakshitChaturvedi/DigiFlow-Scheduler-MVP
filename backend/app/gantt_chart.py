import plotly.express as px
import pandas as pd
from typing import List
from backend.app import models

def create_gantt_chart(scheduled_tasks: List[models.ScheduledTask]):
    # Takes a list of ScheduledTask ORM objects and generates a Plotly Gantt chart figure. Returns the figure as a JSON string for easy transport to frontend
    if not scheduled_tasks:
        return None
    
    # 1: Define a color map for different statuses
    color_map = {
        "SCHEDULED": "rgb(59, 130, 246)",   # Blue
        "IN_PROGRESS": "rgb(245, 158, 11)", # Amber
        "COMPLETED": "rgb(34, 197, 94)",    # Green
        "PAUSED": "rgb(245, 158, 11)",      # Amber
        "BLOCKED": "rgb(239, 68, 68)",      # Red
        "CANCELLED": "rgb(107, 114, 128)",  # Gray
    }

    # 2: Convert SQLAlchemy objects into pandas DF
    chart_data = []
    for task in scheduled_tasks:
        chart_data.append(dict(
            Task=f"{task.production_order.order_id_code} - {task.process_step_definition.step_name}",
            Start = task.start_time,
            Finish = task.end_time,
            Resource = task.assigned_machine.machine_id_code,
            Status = task.status.value.upper()
        ))
    
    if not chart_data:
        return None
    
    df = pd.DataFrame(chart_data)

    # 3: Create the Gantt chart fig using plotly.express
    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish",
        y="Resource",
        color="Status",
        text="Task",
        color_discrete_map=color_map,
        title="Production Schedule by Machine"
    )

    # 4: Customize the layout for cleaner look
    fig.update_layout(
        xaxis_title="Timeline",
        yaxis_title="Machine",
        legend_title="Status",
        font=dict(family="sans-serif", size=12, color="#4B5563"), # Darker gray text
        hovermode="x unified",
        margin=dict(l=20, r=40, b=20, t=60), 
        
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        modebar=dict(
            orientation='h'
        )
    )
    
    fig.update_traces(
        texttemplate='%{text}', 
        textposition='inside', 
        insidetextanchor='middle',
        textfont=dict(
            family="sans-serif",
            size=10,
            color="white"
        )
    )
    
    fig.update_yaxes(categoryorder='total ascending', autorange="reversed")

    # 5: Return fig as JSON obj
    return fig.to_json()