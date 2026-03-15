"""
Halo CME Detection Main Pipeline
Windows-optimized version
"""

import os
import sys
import logging
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
import time

# Windows-specific setup
if sys.platform == 'win32':
    # Fix console encoding
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')
    
    # Use simpler characters for Windows console
    CHECK_MARK = '+'
    X_MARK = 'x'
    ARROW = '>'
else:
    CHECK_MARK = '✓'
    X_MARK = '✗'
    ARROW = '▶'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_execution.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HaloCMEPipeline:
    def __init__(self, root_dir=None):
        self.root_dir = Path(root_dir) if root_dir else Path(__file__).parent.absolute()
        self.scripts_dir = self.root_dir / 'scripts'
        self.data_dir = self.root_dir / 'data'
        self.raw_data_dir = self.root_dir / 'Data'
        self.plots_dir = self.root_dir / 'plots'
        self.cactus_dir = self.data_dir / 'cactus'
        
        # Create necessary directories
        for dir_path in [self.data_dir, self.plots_dir, self.cactus_dir, self.raw_data_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        logger.info(f"Root directory: {self.root_dir}")
        logger.info(f"Data directory: {self.data_dir}")
    
    def fix_script_paths(self, script_content):
        """Fix path issues in script content for Windows"""
        # Replace Unix-style paths
        script_content = script_content.replace('../data/', 'data/')
        script_content = script_content.replace('"../data/', '"data/')
        script_content = script_content.replace("'../data/", "'data/")
        
        # Replace Windows-style paths
        script_content = script_content.replace('..\\data\\', 'data\\')
        script_content = script_content.replace('"..\\data\\', '"data\\')
        script_content = script_content.replace("'..\\data\\", "'data\\")
        
        # Fix os.path.join patterns
        script_content = script_content.replace(
            "os.path.join('..', 'data'", 
            "os.path.join('data'"
        )
        script_content = script_content.replace(
            'os.path.join("..", "data"', 
            'os.path.join("data"'
        )
        
        return script_content
    
    def run_script_direct(self, script_name, description):
        """Run a Python script directly with Windows fixes"""
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return False
        
        logger.info(f"{ARROW} {description}...")
        
        try:
            # Save original directory
            original_dir = os.getcwd()
            
            # Change to root directory
            os.chdir(self.root_dir)
            logger.debug(f"Changed to directory: {os.getcwd()}")
            
            # Verify data file exists before running
            if script_name == 'halo_cme_detection.py':
                dataset_path = self.data_dir / 'final_dataset.csv'
                if not dataset_path.exists():
                    logger.error(f"Dataset not found at: {dataset_path}")
                    logger.info(f"Files in data directory: {list(self.data_dir.glob('*.csv'))}")
                    return False
                logger.info(f"Found dataset: {dataset_path} ({dataset_path.stat().st_size} bytes)")
            
            # Read script with UTF-8 encoding
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # Fix paths in the script
            script_content = self.fix_script_paths(script_content)
            
            # Create namespace with necessary modules
            namespace = {
                '__name__': '__main__',
                '__file__': str(script_path),
                'pd': __import__('pandas'),
                'np': __import__('numpy'),
                'plt': __import__('matplotlib.pyplot'),
                'os': __import__('os'),
                'Path': __import__('pathlib').Path,
                'datetime': __import__('datetime'),
                'timedelta': __import__('datetime').timedelta,
                'find_peaks': __import__('scipy.signal').find_peaks,
            }
            
            # Execute the fixed script
            exec(script_content, namespace)
            
            # Change back to original directory
            os.chdir(original_dir)
            
            logger.info(f"{CHECK_MARK} {description} - Completed successfully")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"{X_MARK} {description} - File not found: {str(e)}")
            logger.info(f"Current directory: {os.getcwd()}")
            logger.info(f"Data directory contents: {list(self.data_dir.glob('*'))}")
            os.chdir(original_dir)
            return False
            
        except Exception as e:
            logger.error(f"{X_MARK} {description} - Failed: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            os.chdir(original_dir)
            return False
    
    def step3_detect_cmes(self):
        """Step 3: Run Halo CME detection with Windows path fixes"""
        # Check if final dataset exists
        final_dataset = self.data_dir / 'final_dataset.csv'
        if not final_dataset.exists():
            logger.error(f"Final dataset not found at: {final_dataset}")
            logger.info(f"Please run: python main.py --step 2 first")
            logger.info(f"Files found in data: {list(self.data_dir.glob('*.csv'))}")
            return False
        
        # Check cactus catalog
        cactus_file = self.cactus_dir / 'halo_cmes.csv'
        if not cactus_file.exists():
            logger.warning(f"CACTus catalog not found at: {cactus_file}")
            logger.info("Creating empty catalog file for testing...")
            # Create an empty catalog file to prevent errors
            import pandas as pd
            empty_catalog = pd.DataFrame(columns=['Launch_Time', 'Expected_Start', 'Expected_End'])
            empty_catalog.to_csv(cactus_file, index=False)
        
        return self.run_script_direct(
            'halo_cme_detection.py',
            'Detecting Halo CMEs'
        )
    
    # ... (rest of the methods remain the same)

def main():
    print("\n" + "="*60)
    print(" HALO CME DETECTION PIPELINE (Windows Edition)")
    print("="*60 + "\n")
    
    parser = argparse.ArgumentParser(description='Halo CME Detection Pipeline')
    parser.add_argument('--step', choices=['1', '2', '3', '4', '5', 'all'],
                       default='all', help='Which step to run')
    parser.add_argument('--skip-viz', action='store_true',
                       help='Skip visualization generation')
    parser.add_argument('--check', action='store_true',
                       help='Check environment and data files only')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = HaloCMEPipeline()
    
    # Quick check mode
    if args.check:
        print("\n📋 Checking data files...")
        print(f"Data directory: {pipeline.data_dir}")
        print(f"Files found: {list(pipeline.data_dir.glob('*.csv'))}")
        print(f"\nData/ directory: {pipeline.raw_data_dir}")
        print(f"CDF files: {list(pipeline.raw_data_dir.glob('*.cdf'))}")
        return
    
    # Run requested step
    if args.step == '3':
        # Special handling for step 3
        success = pipeline.step3_detect_cmes()
    elif args.step == 'all':
        # Run full pipeline
        print("\n⚠️  Note: You need CDF files in Data/ folder for steps 1-2")
        response = input("Continue with step 3 only? (y/n): ")
        if response.lower() == 'y':
            success = pipeline.step3_detect_cmes()
        else:
            return
    else:
        print(f"\nRunning step {args.step}...")
        # Map steps to functions (simplified)
        step_map = {
            '1': lambda: pipeline.run_script_direct('cdf_to_csv.py', 'Converting CDF'),
            '2': lambda: pipeline.run_script_direct('data_preparation.py', 'Preparing data'),
            '4': lambda: pipeline.run_script_direct('plot_params_overlay.py', 'Generating plots'),
            '5': lambda: pipeline.run_script_direct('organize_plots.py', 'Organizing plots'),
        }
        success = step_map.get(args.step, lambda: False)()
    
    if success:
        print(f"\n{CHECK_MARK} Pipeline step completed successfully!")
    else:
        print(f"\n{X_MARK} Pipeline step failed. Check pipeline_execution.log for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()