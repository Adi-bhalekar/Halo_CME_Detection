import os
import shutil
import re

PLOTS_DIR = '../plots'
PARAMS_OVERLAY_DIR = os.path.join(PLOTS_DIR, 'params_overlay')
HEATMAPS_DIR = os.path.join(PLOTS_DIR, 'heatmaps')
BEFORE_AFTER_DIR = os.path.join(PLOTS_DIR, 'before_after')
PLOT_SCORES_DIR = os.path.join(PLOTS_DIR, 'plot_scores')
TIMELINE_DIR = os.path.join(PLOTS_DIR, 'timeline')
CATALOG_OVERLAY_DIR = os.path.join(PLOTS_DIR, 'catalog_overlay')

os.makedirs(PARAMS_OVERLAY_DIR, exist_ok=True)
os.makedirs(HEATMAPS_DIR, exist_ok=True)
os.makedirs(BEFORE_AFTER_DIR, exist_ok=True)
os.makedirs(PLOT_SCORES_DIR, exist_ok=True)
os.makedirs(TIMELINE_DIR, exist_ok=True)
os.makedirs(CATALOG_OVERLAY_DIR, exist_ok=True)

# Move files based on filename patterns
def move_files():
    for fname in os.listdir(PLOTS_DIR):
        fpath = os.path.join(PLOTS_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        # Parameter overlays
        if re.match(r'cme_\d+_params_overlay\\.png$', fname) or re.match(r'cme_\d+_params_overlay\.png$', fname):
            shutil.move(fpath, os.path.join(PARAMS_OVERLAY_DIR, fname))
        # Heatmaps
        elif 'heatmap' in fname:
            shutil.move(fpath, os.path.join(HEATMAPS_DIR, fname))
        # Before/after plots
        elif re.match(r'cme_\d+_event_\d+_composite_before_after\\.png$', fname) or re.match(r'cme_\d+_event_\d+_composite_before_after\.png$', fname):
            shutil.move(fpath, os.path.join(BEFORE_AFTER_DIR, fname))
        # plot_scores.py outputs (e.g., cme_<num>_scores.png or similar)
        elif re.match(r'cme_\d+_scores\\.png$', fname) or re.match(r'cme_\d+_scores\.png$', fname):
            shutil.move(fpath, os.path.join(PLOT_SCORES_DIR, fname))
        # timeline_plot.py outputs (e.g., cme_<num>_timeline.png or similar)
        elif re.match(r'cme_\d+_timeline\\.png$', fname) or re.match(r'cme_\d+_timeline\.png$', fname):
            shutil.move(fpath, os.path.join(TIMELINE_DIR, fname))
        # visualize_with_catalog_overlay.py outputs (e.g., cme_<num>_catalog_overlay.png or similar)
        elif re.match(r'cme_\d+_catalog_overlay\\.png$', fname) or re.match(r'cme_\d+_catalog_overlay\.png$', fname):
            shutil.move(fpath, os.path.join(CATALOG_OVERLAY_DIR, fname))

if __name__ == '__main__':
    move_files()
    print('✅ All plots moved to their respective folders.')
