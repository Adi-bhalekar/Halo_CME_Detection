import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Load and prepare data
print("📂 Loading data...")

try:
    # Load datasets
    df = pd.read_csv('data/final_dataset.csv')
    detections = pd.read_csv('data/detected_halo_cmes.csv')
    print("✅ Data loaded successfully")
except FileNotFoundError as e:
    print(f"❌ Error loading data: {e}")
    print("Please ensure both files exist in the data/ folder:")
    print("  - data/final_dataset.csv")
    print("  - data/detected_halo_cmes.csv")
    exit(1)

print("\n🔍 Identifying columns...")

# Find time column
time_candidates = ['Time', 'time', 'datetime', 'date', 'timestamp']
time_col = None
for col in time_candidates:
    if col in df.columns:
        time_col = col
        try:
            df[col] = pd.to_datetime(df[col])
            print(f"  ✅ Converted {col} to datetime")
        except:
            print(f"  ⚠️ Could not convert {col} to datetime")
        break

if not time_col:
    # If no time column found, use the first column that looks like a date
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                pd.to_datetime(df[col].iloc[0])
                time_col = col
                df[col] = pd.to_datetime(df[col])
                print(f"  ✅ Using {col} as time column")
                break
            except:
                continue

# Find score/composite column
score_keywords = ['composite', 'score', 'anomaly', 'metric', 'cme', 'index']
score_col = None
for col in df.columns:
    col_lower = col.lower()
    if any(keyword in col_lower for keyword in score_keywords) and col != time_col:
        score_col = col
        break

# If still no score column, use the first numeric column
if not score_col:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if time_col and time_col in numeric_cols:
        numeric_cols.remove(time_col)
    if numeric_cols:
        score_col = numeric_cols[0]

# Find numeric columns for parameter selection
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
if time_col and time_col in numeric_cols:
    numeric_cols.remove(time_col)

param_options = [{'label': col, 'value': col} for col in numeric_cols[:15]]  # Limit to first 15

# Identify detection columns
start_col = None
end_col = None
duration_col = None
strength_col = None

start_keywords = ['start', 'begin', 'from', 'onset']
end_keywords = ['end', 'stop', 'to', 'finish', 'complete']
duration_keywords = ['duration', 'length', 'hours', 'time_span', 'period']
strength_keywords = ['strength', 'class', 'category', 'type', 'level', 'intensity']

for col in detections.columns:
    col_lower = col.lower()
    if any(keyword in col_lower for keyword in start_keywords):
        start_col = col
        try:
            detections[col] = pd.to_datetime(detections[col])
        except:
            pass
    if any(keyword in col_lower for keyword in end_keywords):
        end_col = col
        try:
            detections[col] = pd.to_datetime(detections[col])
        except:
            pass
    if any(keyword in col_lower for keyword in duration_keywords):
        duration_col = col
    if any(keyword in col_lower for keyword in strength_keywords):
        strength_col = col

# If no duration column but we have start and end, calculate duration
if not duration_col and start_col and end_col:
    try:
        detections['calculated_duration'] = (pd.to_datetime(detections[end_col]) - pd.to_datetime(detections[start_col])).dt.total_seconds() / 3600
        duration_col = 'calculated_duration'
        print("  ✅ Calculated duration from start/end times")
    except:
        pass

# Print summary
print("\n📊 Column Detection Summary:")
print(f"  ✅ Time column: {time_col}")
print(f"  ✅ Score column: {score_col}")
print(f"  ✅ Start column: {start_col}")
print(f"  ✅ End column: {end_col}")
print(f"  ✅ Duration column: {duration_col}")
print(f"  ✅ Strength column: {strength_col}")
print(f"  ✅ Available parameters: {len(param_options)}")

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# App layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("☀️ Halo CME Detection Dashboard", 
                   className="text-center my-4",
                   style={'color': '#2c3e50'}),
            html.Hr(style={'border-top': '2px solid #3498db'})
        ])
    ]),
    
    # Summary stats
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Total CMEs", className="card-title text-muted"),
                    html.H2(f"{len(detections)}", className="text-primary display-4")
                ])
            ], className="shadow-sm")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Date Range", className="card-title text-muted"),
                    html.H6(f"{df[time_col].min().strftime('%Y-%m-%d') if time_col else 'N/A'} to {df[time_col].max().strftime('%Y-%m-%d') if time_col else 'N/A'}", 
                           className="text-info")
                ])
            ], className="shadow-sm")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Avg Duration", className="card-title text-muted"),
                    html.H2(f"{detections[duration_col].mean():.1f}h" if duration_col and duration_col in detections.columns else "N/A", 
                           className="text-success display-4")
                ])
            ], className="shadow-sm")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Max Score", className="card-title text-muted"),
                    html.H2(f"{detections[score_col].max() if score_col and score_col in detections.columns else df[score_col].max():.2f}" if score_col else "N/A", 
                           className="text-warning display-4")
                ])
            ], className="shadow-sm")
        ], width=3),
    ], className="mb-4"),
    
    # Controls
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("🎛️ Filter Controls", className="card-title"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("📅 Date Range", className="fw-bold"),
                            dcc.DatePickerRange(
                                id='date-range',
                                start_date=df[time_col].min() if time_col else None,
                                end_date=df[time_col].max() if time_col else None,
                                display_format='YYYY-MM-DD',
                                className="form-control"
                            )
                        ], width=4),
                        
                        dbc.Col([
                            html.Label("💪 CME Strength", className="fw-bold"),
                            dcc.Dropdown(
                                id='strength-filter',
                                options=[{'label': 'All', 'value': 'all'}] + 
                                        ([{'label': str(s), 'value': s} for s in detections[strength_col].unique()] if strength_col and strength_col in detections.columns else []),
                                value='all',
                                className="form-control"
                            )
                        ], width=4),
                        
                        dbc.Col([
                            html.Label("📊 Parameter", className="fw-bold"),
                            dcc.Dropdown(
                                id='parameter-select',
                                options=param_options,
                                value=score_col if score_col else (param_options[0]['value'] if param_options else None),
                                className="form-control"
                            )
                        ], width=4),
                    ]),
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),
    
    # Main plots
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("📈 Time Series with Detected CMEs", className="mb-0")),
                dbc.CardBody([
                    dcc.Graph(id='time-series-plot', style={'height': '450px'})
                ])
            ], className="shadow-sm")
        ], width=12)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("📅 CME Events Timeline", className="mb-0")),
                dbc.CardBody([
                    dcc.Graph(id='timeline-plot', style={'height': '350px'})
                ])
            ], className="shadow-sm")
        ], width=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("📊 Distribution", className="mb-0")),
                dbc.CardBody([
                    dcc.Graph(id='strength-dist', style={'height': '350px'})
                ])
            ], className="shadow-sm")
        ], width=6),
    ], className="mb-4"),
    
    # Data table
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("📋 Detected CME Events", className="mb-0")),
                dbc.CardBody([
                    html.Div(id='cme-table', style={'maxHeight': '400px', 'overflowY': 'scroll'})
                ])
            ], className="shadow-sm")
        ], width=12)
    ]),
    
    # Footer
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.P(f"Generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                  className="text-center text-muted small")
        ])
    ]),
    
], fluid=True)

# Callbacks
@app.callback(
    [Output('time-series-plot', 'figure'),
     Output('timeline-plot', 'figure'),
     Output('strength-dist', 'figure'),
     Output('cme-table', 'children')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('strength-filter', 'value'),
     Input('parameter-select', 'value')]
)
def update_dashboard(start_date, end_date, strength_filter, parameter):
    # Filter data by date
    if time_col and start_date and end_date:
        try:
            mask = (df[time_col] >= start_date) & (df[time_col] <= end_date)
            filtered_df = df[mask].copy()
        except:
            filtered_df = df.copy()
    else:
        filtered_df = df.copy()
    
    # Filter detections
    detections_filtered = detections.copy()
    
    # Apply strength filter
    if strength_filter != 'all' and strength_col and strength_col in detections_filtered.columns:
        detections_filtered = detections_filtered[detections_filtered[strength_col] == strength_filter]
    
    # Apply date filter to detections
    if start_col and end_col and start_date and end_date:
        try:
            start_mask = pd.to_datetime(detections_filtered[start_col]) >= pd.Timestamp(start_date)
            end_mask = pd.to_datetime(detections_filtered[end_col]) <= pd.Timestamp(end_date)
            detections_filtered = detections_filtered[start_mask & end_mask]
        except:
            pass
    
    # Time series plot
    fig1 = go.Figure()
    
    if time_col and parameter and parameter in filtered_df.columns:
        fig1.add_trace(go.Scatter(
            x=filtered_df[time_col],
            y=filtered_df[parameter],
            mode='lines',
            name=parameter,
            line=dict(color='#3498db', width=2),
            hovertemplate='<b>Time</b>: %{x}<br><b>Value</b>: %{y:.2f}<extra></extra>'
        ))
    
    # Add CME intervals
    if start_col and end_col and len(detections_filtered) > 0:
        colors = {
            'Weak': 'rgba(255, 193, 7, 0.15)',   # Yellow
            'Moderate': 'rgba(52, 152, 219, 0.15)',  # Blue
            'Strong': 'rgba(231, 76, 60, 0.15)',     # Red
            'default': 'rgba(149, 165, 166, 0.15)'   # Gray
        }
        
        for idx, cme in detections_filtered.iterrows():
            # Determine color based on strength
            color = colors['default']
            if strength_col and strength_col in cme.index and pd.notna(cme[strength_col]):
                strength_val = str(cme[strength_col])
                for key in colors:
                    if key.lower() in strength_val.lower():
                        color = colors[key]
                        break
            
            try:
                fig1.add_vrect(
                    x0=cme[start_col], x1=cme[end_col],
                    fillcolor=color,
                    opacity=0.8,
                    line_width=0,
                    annotation_text=f"CME {idx+1}" if idx < 5 else "",
                    annotation_position="top left",
                    annotation_font_size=10
                )
            except:
                pass
    
    fig1.update_layout(
        title=f"{parameter} over Time" if parameter else "Time Series",
        xaxis_title="Time",
        yaxis_title=parameter,
        height=400,
        hovermode='x unified',
        template='plotly_white',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Timeline plot
    fig2 = go.Figure()
    
    if start_col and end_col and len(detections_filtered) > 0:
        colors = {'Weak': '#f39c12', 'Moderate': '#3498db', 'Strong': '#e74c3c'}
        
        for idx, cme in detections_filtered.iterrows():
            # Get strength for color
            color = '#95a5a6'  # Default gray
            strength_text = "Unknown"
            
            if strength_col and strength_col in cme.index and pd.notna(cme[strength_col]):
                strength_val = str(cme[strength_col])
                strength_text = strength_val
                for key, val in colors.items():
                    if key.lower() in strength_val.lower():
                        color = val
                        break
            
            # Get duration
            duration_text = "N/A"
            if duration_col and duration_col in cme.index and pd.notna(cme[duration_col]):
                duration_text = f"{cme[duration_col]:.1f}h"
            
            # Create hover text
            hover_text = f"<b>CME {idx+1}</b><br>"
            hover_text += f"Strength: {strength_text}<br>"
            hover_text += f"Duration: {duration_text}<br>"
            hover_text += f"Start: {cme[start_col]}<br>"
            hover_text += f"End: {cme[end_col]}"
            
            try:
                fig2.add_trace(go.Scatter(
                    x=[cme[start_col], cme[end_col]],
                    y=[idx+1, idx+1],
                    mode='lines+markers',
                    line=dict(color=color, width=8),
                    marker=dict(size=12, color=color, symbol='circle'),
                    name=f"CME {idx+1}",
                    text=hover_text,
                    hoverinfo='text',
                    showlegend=False
                ))
            except:
                pass
    
    fig2.update_layout(
        title="CME Events Timeline",
        xaxis_title="Time",
        yaxis_title="Event Number",
        height=300,
        hovermode='closest',
        template='plotly_white',
        xaxis=dict(rangeslider=dict(visible=True))
    )
    
    # Distribution plot
    fig3 = go.Figure()
    
    if strength_col and strength_col in detections_filtered.columns and len(detections_filtered) > 0:
        strength_counts = detections_filtered[strength_col].value_counts()
        colors_map = {'Weak': '#f39c12', 'Moderate': '#3498db', 'Strong': '#e74c3c'}
        bar_colors = [colors_map.get(s, '#95a5a6') for s in strength_counts.index]
        
        fig3.add_trace(go.Bar(
            x=strength_counts.index,
            y=strength_counts.values,
            marker_color=bar_colors,
            text=strength_counts.values,
            textposition='auto',
            hovertemplate='Strength: %{x}<br>Count: %{y}<extra></extra>'
        ))
        fig3.update_layout(
            title="CME Strength Distribution",
            xaxis_title="Strength",
            yaxis_title="Count",
            height=300,
            template='plotly_white'
        )
    elif duration_col and duration_col in detections_filtered.columns and len(detections_filtered) > 0:
        # If no strength, show duration histogram
        fig3.add_trace(go.Histogram(
            x=detections_filtered[duration_col],
            nbinsx=20,
            marker_color='#3498db',
            hovertemplate='Duration: %{x:.1f}h<br>Count: %{y}<extra></extra>'
        ))
        fig3.update_layout(
            title="CME Duration Distribution",
            xaxis_title="Duration (hours)",
            yaxis_title="Frequency",
            height=300,
            template='plotly_white'
        )
    else:
        fig3.add_annotation(
            text="No distribution data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#95a5a6")
        )
        fig3.update_layout(
            title="Distribution",
            height=300,
            template='plotly_white'
        )
    
    # Data table
    if len(detections_filtered) > 0:
        # Select columns to display
        display_cols = []
        
        if start_col:
            display_cols.append(start_col)
        if end_col:
            display_cols.append(end_col)
        if duration_col and duration_col in detections_filtered.columns:
            display_cols.append(duration_col)
        if strength_col and strength_col in detections_filtered.columns:
            display_cols.append(strength_col)
        if score_col and score_col in detections_filtered.columns:
            display_cols.append(score_col)
        
        # Ensure we have at least some columns
        if not display_cols:
            display_cols = detections_filtered.columns[:5].tolist()
        
        # Create table data
        table_data = detections_filtered[display_cols].head(20).copy()
        
        # Format datetime columns
        for col in display_cols:
            if col in [start_col, end_col] and col:
                try:
                    table_data[col] = pd.to_datetime(table_data[col]).dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
        
        # Format numeric columns
        for col in display_cols:
            if col in [duration_col, score_col] and col:
                try:
                    table_data[col] = table_data[col].round(2)
                except:
                    pass
        
        # Create table
        table = dbc.Table.from_dataframe(
            table_data,
            striped=True,
            bordered=True,
            hover=True,
            size='sm',
            style={'fontSize': '12px'}
        )
        
        if len(detections_filtered) > 20:
            table = html.Div([
                table,
                html.P(f"... and {len(detections_filtered) - 20} more events", 
                      className="text-muted text-center mt-2")
            ])
    else:
        table = html.P("No events match the selected filters", 
                      className="text-center text-muted fs-5 mt-4")
    
    return fig1, fig2, fig3, table

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting interactive dashboard...")
    print("📊 Open http://127.0.0.1:8050 in your browser")
    print("="*60 + "\n")
    
    # FIXED: Use run() instead of run_server()
    app.run(debug=True, host='127.0.0.1', port=8050)