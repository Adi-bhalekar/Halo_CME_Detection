import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import base64
from io import BytesIO
from datetime import datetime

class CMEDashboard:
    def __init__(self, data_dir='data', plots_dir='plots'):
        self.data_dir = Path(data_dir)
        self.plots_dir = Path(plots_dir)
        self.load_data()
        self.identify_columns()
        
    def load_data(self):
        """Load all necessary data"""
        print("📂 Loading data...")
        
        # Load detection results
        detections_path = self.data_dir / 'detected_halo_cmes.csv'
        self.detections = pd.read_csv(detections_path)
        
        # Load full dataset
        dataset_path = self.data_dir / 'final_dataset.csv'
        self.full_data = pd.read_csv(dataset_path)
        
        # Try to parse time column
        time_candidates = ['Time', 'time', 'datetime', 'date', 'timestamp']
        self.time_col = None
        for col in time_candidates:
            if col in self.full_data.columns:
                self.time_col = col
                self.full_data[col] = pd.to_datetime(self.full_data[col])
                break
        
        print(f"✅ Loaded {len(self.detections)} CME events")
        print(f"✅ Loaded {len(self.full_data)} time points")
        
    def identify_columns(self):
        """Identify what columns are available"""
        print("\n🔍 Identifying available columns...")
        
        # Look for score/composite columns
        score_keywords = ['composite', 'score', 'anomaly', 'metric']
        self.score_col = None
        for col in self.full_data.columns:
            if any(keyword in col.lower() for keyword in score_keywords):
                self.score_col = col
                break
        
        # Look for detection columns
        self.start_col = None
        self.end_col = None
        self.duration_col = None
        self.strength_col = None
        
        start_keywords = ['start', 'begin']
        end_keywords = ['end', 'stop', 'finish']
        duration_keywords = ['duration', 'length', 'hours']
        strength_keywords = ['strength', 'class', 'category', 'type']
        
        for col in self.detections.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in start_keywords):
                self.start_col = col
            if any(keyword in col_lower for keyword in end_keywords):
                self.end_col = col
            if any(keyword in col_lower for keyword in duration_keywords):
                self.duration_col = col
            if any(keyword in col_lower for keyword in strength_keywords):
                self.strength_col = col
        
        # Print what we found
        print(f"  Time column: {self.time_col}")
        print(f"  Score column: {self.score_col}")
        print(f"  Start column: {self.start_col}")
        print(f"  End column: {self.end_col}")
        print(f"  Duration column: {self.duration_col}")
        print(f"  Strength column: {self.strength_col}")
        
    def create_summary_stats(self):
        """Generate summary statistics"""
        stats = {
            'total_cmes': len(self.detections),
            'date_range': f"{self.full_data[self.time_col].min()} to {self.full_data[self.time_col].max()}" if self.time_col else 'N/A',
        }
        
        if self.duration_col:
            stats['avg_duration'] = self.detections[self.duration_col].mean()
        
        if self.score_col:
            stats['max_score'] = self.detections[self.score_col].max() if self.score_col in self.detections.columns else self.full_data[self.score_col].max()
        
        if self.strength_col:
            stats['strength_dist'] = self.detections[self.strength_col].value_counts().to_dict()
        
        return stats
    
    def plot_timeline(self):
        """Create timeline plot of all CMEs"""
        fig, ax = plt.subplots(figsize=(12, 4))
        
        if self.start_col and self.end_col:
            # Convert time if needed
            starts = pd.to_datetime(self.detections[self.start_col])
            ends = pd.to_datetime(self.detections[self.end_col])
            
            # Define colors for strengths
            colors = {'Weak': 'yellow', 'Moderate': 'orange', 'Strong': 'red', 
                     'low': 'yellow', 'medium': 'orange', 'high': 'red'}
            
            for i, (start, end) in enumerate(zip(starts, ends)):
                # Get strength if available
                color = 'blue'
                if self.strength_col:
                    strength = str(self.detections.iloc[i].get(self.strength_col, '')).lower()
                    for key, value in colors.items():
                        if key.lower() in strength:
                            color = value
                            break
                
                # Calculate duration in hours
                duration_hours = (end - start).total_seconds() / 3600
                ax.barh(i, duration_hours, left=start, height=0.5, 
                       color=color, alpha=0.7, edgecolor='black', linewidth=0.5)
        
        ax.set_xlabel('Time')
        ax.set_ylabel('CME Event #')
        ax.set_title('Detected CME Timeline')
        if self.time_col:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        return fig
    
    def plot_scores(self):
        """Plot scores over time"""
        fig, ax = plt.subplots(figsize=(12, 5))
        
        if self.score_col and self.time_col:
            # Plot full time series
            ax.plot(pd.to_datetime(self.full_data[self.time_col]), 
                    self.full_data[self.score_col], 
                    'b-', alpha=0.6, linewidth=1, label='Score')
            
            # Highlight detected CMEs if we have start/end times
            if self.start_col and self.end_col:
                starts = pd.to_datetime(self.detections[self.start_col])
                ends = pd.to_datetime(self.detections[self.end_col])
                
                for start, end in zip(starts, ends):
                    ax.axvspan(start, end, alpha=0.2, color='red', label='Detected CME' if start == starts[0] else '')
            
            ax.set_xlabel('Time')
            ax.set_ylabel(self.score_col)
            ax.set_title(f'{self.score_col} with Detected CMEs')
            if self.time_col:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.legend()
        
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return fig
    
    def plot_parameter(self, param_col):
        """Plot a specific parameter"""
        fig, ax = plt.subplots(figsize=(12, 4))
        
        if param_col in self.full_data.columns and self.time_col:
            ax.plot(pd.to_datetime(self.full_data[self.time_col]), 
                    self.full_data[param_col], 
                    'g-', alpha=0.6, linewidth=1)
            
            ax.set_xlabel('Time')
            ax.set_ylabel(param_col)
            ax.set_title(f'{param_col} Time Series')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def generate_html_report(self, output_file='cme_dashboard.html'):
        """Generate an HTML dashboard"""
        stats = self.create_summary_stats()
        
        # Create plots
        timeline_fig = self.plot_timeline()
        scores_fig = self.plot_scores()
        
        # Also plot first few parameters if available
        param_figs = []
        param_cols = [col for col in self.full_data.columns 
                     if col not in [self.time_col, self.score_col] 
                     and 'Unnamed' not in col][:3]  # First 3 other parameters
        
        for param in param_cols:
            param_figs.append(self.plot_parameter(param))
        
        # Convert plots to HTML images
        timeline_img = self.fig_to_base64(timeline_fig)
        scores_img = self.fig_to_base64(scores_fig)
        param_imgs = [self.fig_to_base64(fig) for fig in param_figs]
        
        # Create HTML content
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Halo CME Detection Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                .stats-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                                  gap: 20px; margin-bottom: 30px; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 10px; 
                             box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }}
                .stat-value {{ font-size: 36px; font-weight: bold; color: #667eea; }}
                .stat-label {{ font-size: 14px; color: #666; margin-top: 10px; }}
                .plot-container {{ background: white; padding: 20px; border-radius: 10px;
                                 margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .plot-title {{ font-size: 18px; font-weight: bold; margin-bottom: 15px; color: #333; }}
                table {{ width: 100%; border-collapse: collapse; background: white; 
                        border-radius: 10px; overflow: hidden; }}
                th {{ background: #667eea; color: white; padding: 12px; }}
                td {{ padding: 12px; border-bottom: 1px solid #ddd; }}
                tr:hover {{ background-color: #f5f5f5; }}
                .weak {{ color: orange; }}
                .moderate {{ color: #667eea; }}
                .strong {{ color: red; font-weight: bold; }}
                img {{ max-width: 100%; height: auto; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>☀️ Halo CME Detection Dashboard</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="stats-container">
                <div class="stat-card">
                    <div class="stat-value">{stats['total_cmes']}</div>
                    <div class="stat-label">Total CMEs Detected</div>
                </div>
        """
        
        if 'avg_duration' in stats:
            html += f"""
                <div class="stat-card">
                    <div class="stat-value">{stats['avg_duration']:.1f}</div>
                    <div class="stat-label">Avg Duration (hours)</div>
                </div>
            """
        
        if 'max_score' in stats:
            html += f"""
                <div class="stat-card">
                    <div class="stat-value">{stats['max_score']:.2f}</div>
                    <div class="stat-label">Max Score</div>
                </div>
            """
        
        html += """
            </div>
            
            <div class="plot-container">
                <div class="plot-title">📈 Score Timeline</div>
                <img src="data:image/png;base64,{scores_img}" alt="Scores">
            </div>
            
            <div class="plot-container">
                <div class="plot-title">📅 CME Timeline</div>
                <img src="data:image/png;base64,{timeline_img}" alt="CME Timeline">
            </div>
        """
        
        # Add parameter plots
        for i, param_img in enumerate(param_imgs):
            if i < len(param_cols):
                html += f"""
            <div class="plot-container">
                <div class="plot-title">📊 {param_cols[i]}</div>
                <img src="data:image/png;base64,{param_img}" alt="{param_cols[i]}">
            </div>
                """
        
        # Add table
        html += """
            <div class="plot-container">
                <div class="plot-title">📋 Detected CME Events</div>
                <table>
                    <tr>
        """
        
        # Table headers
        headers = []
        if self.start_col:
            headers.append('Start Time')
        if self.end_col:
            headers.append('End Time')
        if self.duration_col:
            headers.append('Duration (hrs)')
        if self.strength_col:
            headers.append('Strength')
        if self.score_col and self.score_col in self.detections.columns:
            headers.append('Score')
        
        for header in headers:
            html += f"<th>{header}</th>"
        
        html += """
                    </tr>
        """
        
        # Table rows
        for idx, row in self.detections.iterrows():
            if idx >= 20:  # Limit to 20 rows
                html += f'<tr><td colspan="{len(headers)}" style="text-align: center;">... and {len(self.detections)-20} more events</td></tr>'
                break
                
            html += "<tr>"
            if self.start_col:
                html += f"<td>{row.get(self.start_col, 'N/A')}</td>"
            if self.end_col:
                html += f"<td>{row.get(self.end_col, 'N/A')}</td>"
            if self.duration_col:
                val = row.get(self.duration_col, 'N/A')
                html += f"<td>{val:.1f if isinstance(val, (int, float)) else val}</td>"
            if self.strength_col:
                strength = str(row.get(self.strength_col, 'N/A'))
                strength_class = strength.lower() if strength in ['Weak', 'Moderate', 'Strong'] else ''
                html += f'<td class="{strength_class}">{strength}</td>'
            if self.score_col and self.score_col in self.detections.columns:
                val = row.get(self.score_col, 'N/A')
                html += f"<td>{val:.2f if isinstance(val, (int, float)) else val}</td>"
            html += "</tr>"
        
        html += """
                </table>
            </div>
            
            <div style="text-align: center; color: #666; margin-top: 20px; font-size: 12px;">
                Generated by Halo CME Detection Pipeline
            </div>
        </body>
        </html>
        """
        
        # Save HTML file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ Dashboard saved to {output_file}")
        return output_file
    
    def fig_to_base64(self, fig):
        """Convert matplotlib figure to base64 string"""
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_str

if __name__ == "__main__":
    # Create dashboard
    dashboard = CMEDashboard()
    
    # Generate HTML report
    html_file = dashboard.generate_html_report()
    
    # Open in browser
    import webbrowser
    webbrowser.open(html_file)
    
    print("\n✨ Dashboard created successfully!")