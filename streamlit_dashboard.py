# save this as streamlit_dashboard_fixed.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import os

# Page config - MUST BE FIRST
st.set_page_config(
    page_title="Halo CME Detection Dashboard",
    page_icon="☀️",
    layout="wide"
)

# Title
st.title("☀️ Halo CME Detection using Aditya-L1 SWIS-ASPEX Data")
st.markdown("---")

# Function to auto-detect column types
def detect_columns(df):
    """Automatically detect what kind of columns we have"""
    col_types = {
        'time': [],
        'start': [],
        'end': [],
        'duration': [],
        'strength': [],
        'score': [],
        'numeric': []
    }
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Time column detection
        if any(word in col_lower for word in ['time', 'date', 'datetime']):
            col_types['time'].append(col)
        
        # Start time detection
        if any(word in col_lower for word in ['start', 'begin', 'from', 'onset']):
            col_types['start'].append(col)
        
        # End time detection
        if any(word in col_lower for word in ['end', 'stop', 'to', 'finish', 'complete']):
            col_types['end'].append(col)
        
        # Duration detection
        if any(word in col_lower for word in ['duration', 'length', 'hours', 'period', 'span']):
            col_types['duration'].append(col)
        
        # Strength detection
        if any(word in col_lower for word in ['strength', 'class', 'type', 'category', 'level']):
            col_types['strength'].append(col)
        
        # Score detection
        if any(word in col_lower for word in ['score', 'composite', 'anomaly', 'metric', 'index']):
            col_types['score'].append(col)
        
        # Numeric columns
        if pd.api.types.is_numeric_dtype(df[col]):
            col_types['numeric'].append(col)
    
    return col_types

# Function to safely convert to datetime
def safe_to_datetime(series):
    try:
        return pd.to_datetime(series)
    except:
        return series

# Load data with caching
@st.cache_data
def load_data():
    """Load and prepare data with auto-detection"""
    
    # Check if files exist
    if not os.path.exists('data/detected_halo_cmes.csv'):
        st.error("❌ Could not find data/detected_halo_cmes.csv")
        st.stop()
    
    if not os.path.exists('data/final_dataset.csv'):
        st.error("❌ Could not find data/final_dataset.csv")
        st.stop()
    
    # Load data
    detections = pd.read_csv('data/detected_halo_cmes.csv')
    full_data = pd.read_csv('data/final_dataset.csv')
    
    # Detect column types
    det_cols = detect_columns(detections)
    data_cols = detect_columns(full_data)
    
    return full_data, detections, det_cols, data_cols

# Load data
with st.spinner("Loading CME data..."):
    full_data, detections, det_cols, data_cols = load_data()

# Sidebar - Show detected columns
with st.sidebar:
    st.header("📋 Detected Columns")
    
    with st.expander("Detection File Columns"):
        for col_type, cols in det_cols.items():
            if cols:
                st.write(f"**{col_type.title()}**: {', '.join(cols[:3])}")
    
    with st.expander("Main Data Columns"):
        for col_type, cols in data_cols.items():
            if cols:
                st.write(f"**{col_type.title()}**: {', '.join(cols[:3])}")
    
    st.markdown("---")
    st.header("🎛️ Filters")
    
    # Time filter - try to find time column
    time_col = None
    if data_cols['time']:
        time_col = data_cols['time'][0]
        try:
            full_data[time_col] = pd.to_datetime(full_data[time_col])
            min_date = full_data[time_col].min().date()
            max_date = full_data[time_col].max().date()
            
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
        except:
            st.warning("Could not parse dates")
            date_range = (None, None)
    else:
        st.warning("No time column found")
        date_range = (None, None)
    
    # Strength filter
    strength_col = det_cols['strength'][0] if det_cols['strength'] else None
    if strength_col:
        strength_options = ['All'] + list(detections[strength_col].unique())
        selected_strength = st.selectbox("CME Strength", strength_options)
    else:
        selected_strength = 'All'
    
    # Parameter selector (use numeric columns from main data)
    param_options = data_cols['numeric']
    if param_options:
        # Try to find a good default
        default_param = None
        for score_col in data_cols['score']:
            if score_col in param_options:
                default_param = score_col
                break
        if not default_param:
            default_param = param_options[0]
        
        selected_param = st.selectbox(
            "Select Parameter",
            param_options,
            index=param_options.index(default_param) if default_param in param_options else 0
        )
    else:
        st.error("No numeric columns found!")
        st.stop()

# Main content
st.header("📊 CME Detection Results")

# Summary metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total CMEs", len(detections))

with col2:
    if det_cols['duration']:
        duration_col = det_cols['duration'][0]
        avg_duration = detections[duration_col].mean()
        st.metric("Avg Duration", f"{avg_duration:.1f}h")
    else:
        st.metric("Avg Duration", "N/A")

with col3:
    if det_cols['score'] and det_cols['score'][0] in detections.columns:
        score_col = det_cols['score'][0]
        max_score = detections[score_col].max()
        st.metric("Max Score", f"{max_score:.2f}")
    elif selected_param in full_data.columns:
        st.metric("Max Value", f"{full_data[selected_param].max():.2f}")
    else:
        st.metric("Max Score", "N/A")

with col4:
    st.metric("Data Points", f"{len(full_data):,}")

st.markdown("---")

# Time series plot
st.subheader(f"📈 Time Series with CME Intervals")

fig1 = go.Figure()

# Add main time series
if time_col and selected_param:
    fig1.add_trace(go.Scatter(
        x=full_data[time_col],
        y=full_data[selected_param],
        mode='lines',
        name=selected_param,
        line=dict(color='#3498db', width=2)
    ))

# Add CME intervals if we have start/end columns
if det_cols['start'] and det_cols['end']:
    start_col = det_cols['start'][0]
    end_col = det_cols['end'][0]
    
    # Convert to datetime
    detections[start_col] = safe_to_datetime(detections[start_col])
    detections[end_col] = safe_to_datetime(detections[end_col])
    
    # Colors for strength
    colors = {
        'Weak': 'rgba(255, 193, 7, 0.2)',
        'Moderate': 'rgba(52, 152, 219, 0.2)',
        'Strong': 'rgba(231, 76, 60, 0.2)'
    }
    
    for idx, cme in detections.iterrows():
        # Get strength if available
        color = 'rgba(149, 165, 166, 0.2)'
        if strength_col and strength_col in cme:
            strength_val = str(cme[strength_col])
            for key in colors:
                if key.lower() in strength_val.lower():
                    color = colors[key]
                    break
        
        try:
            fig1.add_vrect(
                x0=cme[start_col], 
                x1=cme[end_col],
                fillcolor=color,
                opacity=0.8,
                line_width=0,
                annotation_text=f"CME {idx+1}" if idx < 10 else "",
                annotation_position="top left"
            )
        except:
            pass

fig1.update_layout(
    height=500,
    hovermode='x unified',
    template='plotly_white',
    showlegend=True
)

st.plotly_chart(fig1, use_container_width=True)

# Two column layout
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📅 CME Timeline")
    
    if det_cols['start'] and det_cols['end']:
        fig2 = go.Figure()
        
        start_col = det_cols['start'][0]
        end_col = det_cols['end'][0]
        
        for idx, cme in detections.iterrows():
            # Color by strength
            color = '#95a5a6'
            if strength_col and strength_col in cme:
                strength_val = str(cme[strength_col])
                if 'weak' in strength_val.lower():
                    color = '#f39c12'
                elif 'moderate' in strength_val.lower():
                    color = '#3498db'
                elif 'strong' in strength_val.lower():
                    color = '#e74c3c'
            
            # Build hover text
            hover_text = f"<b>CME {idx+1}</b><br>"
            if strength_col and strength_col in cme:
                hover_text += f"Strength: {cme[strength_col]}<br>"
            if det_cols['duration']:
                duration_col = det_cols['duration'][0]
                hover_text += f"Duration: {cme[duration_col]:.1f}h<br>"
            hover_text += f"Start: {cme[start_col]}<br>"
            hover_text += f"End: {cme[end_col]}"
            
            fig2.add_trace(go.Scatter(
                x=[cme[start_col], cme[end_col]],
                y=[idx+1, idx+1],
                mode='lines+markers',
                line=dict(color=color, width=8),
                marker=dict(size=10, color=color),
                name=f"CME {idx+1}",
                hovertext=hover_text,
                hoverinfo='text',
                showlegend=False
            ))
        
        fig2.update_layout(
            height=400,
            xaxis_title="Time",
            yaxis_title="Event Number",
            template='plotly_white'
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Timeline visualization requires start and end time columns")

with col_right:
    st.subheader("📊 Distribution")
    
    if strength_col and strength_col in detections.columns:
        # Strength distribution
        strength_counts = detections[strength_col].value_counts()
        
        fig3 = go.Figure(data=[
            go.Bar(
                x=strength_counts.index,
                y=strength_counts.values,
                marker_color=['#f39c12' if 'weak' in str(s).lower() 
                             else '#3498db' if 'moderate' in str(s).lower()
                             else '#e74c3c' for s in strength_counts.index],
                text=strength_counts.values,
                textposition='auto',
            )
        ])
        
        fig3.update_layout(
            height=400,
            xaxis_title="Strength",
            yaxis_title="Count",
            template='plotly_white'
        )
        
        st.plotly_chart(fig3, use_container_width=True)
        
    elif det_cols['duration']:
        # Duration histogram
        duration_col = det_cols['duration'][0]
        fig3 = px.histogram(
            detections, 
            x=duration_col,
            nbins=20,
            title="Duration Distribution"
        )
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No distribution data available")

# Data table
st.markdown("---")
st.subheader("📋 Detected CME Events")

# Select columns for display
display_cols = []
if det_cols['start']:
    display_cols.append(det_cols['start'][0])
if det_cols['end']:
    display_cols.append(det_cols['end'][0])
if det_cols['duration']:
    display_cols.append(det_cols['duration'][0])
if det_cols['strength']:
    display_cols.append(det_cols['strength'][0])
if det_cols['score']:
    display_cols.append(det_cols['score'][0])

if display_cols:
    table_df = detections[display_cols].copy()
    
    # Format datetime columns
    for col in table_df.columns:
        if any(word in col.lower() for word in ['time', 'date', 'start', 'end']):
            try:
                table_df[col] = pd.to_datetime(table_df[col]).dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        # Round numeric columns
        if table_df[col].dtype in ['float64', 'int64']:
            try:
                table_df[col] = table_df[col].round(2)
            except:
                pass
    
    st.dataframe(
        table_df,
        use_container_width=True,
        height=400
    )
else:
    st.info("No CME events to display")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
with col2:
    st.markdown(f"*{len(detections)} CME Events*")
with col3:
    st.markdown("*Data: Aditya-L1 SWIS-ASPEX*")

# Debug info in expander
with st.expander("🔧 Debug Info - Click to see column details"):
    st.write("**Detection File Columns:**")
    for col_type, cols in det_cols.items():
        if cols:
            st.write(f"- {col_type}: {cols}")
    
    st.write("\n**Main Data Columns:**")
    for col_type, cols in data_cols.items():
        if cols:
            st.write(f"- {col_type}: {cols[:5]}")