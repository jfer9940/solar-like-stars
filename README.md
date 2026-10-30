# A Targeted search for radio flares on solar-like stars: Code repository

Attached is the code written and used during this project. Brief descriptions of all notebooks and scripts are outlined below, although code has been commented for clarity. Many scripts are similar, as tasks like downloading additional data or making extra plots needed to be done for a small sample of stars. The code uploaded here includes additional details that were not used directly in this thesis. Feel free to check them out anyway and see some of the dead ends we ran into :) 

Please note that there may be some package version conflicts. Some of this code was run locally on a Windows machine, while much of it was run remotely on a Linux machine. All personal information has also been removed.

## Notebooks
_Notebooks used to analyse data, create plots, etc_

all_star_stats.ipynb - Calculate the all star flare rate statistics

ASAS_lc.ipynb - Alternative optical data for HD 104919

burst_flux.ipynb - Calculate the drift in the HD 104919 burst	

determine_number_of_files.ipynb - Initial estimates of data volume to be processed

download_visibility_data.ipynb - Download test data and count number of files to download

ECMI_emission.ipynb - Generate radio phase plots and find ECMI parameters

find_detected_observations.ipynb - Identify the SRSC detections in our sample

lightkurve_periods.ipynb - Plot lightcurves and calculate periods for candidate sources

plamsa_emission.ipynb - Determine if emission from HD 104919 is due to plasma emission

plot_cutouts.ipynb - Visualise cutout images for different sources

save_ds_figures.ipynb - Visualise dynamic spectra and create plots

tyc_8927.ipynb - Dynamic spectra and lightcurves from TYC 8927 analysis

solar_like_stars_sample_selection.ipynb - Code used to determine our initial sample


## Scripts
_Scripts used to download data, process data, etc_

auto_ds.py - Run DSTools script to generate a dynamic spectrum from a visibility file

casda_tap_download.py - Download visibility files from CASDA

casda_tap_hd104919_data.py- Download extra data for HD 104919

casda_tap_tyc_data.py- Download extra data for TYC 8927

download_cutouts.py - Download cutouts corresponding to our observations

download_hd104919_cutouts.py - Download additional cutouts for HD 104919

download_hd8558_cutouts.py - Download additional cutouts for HD 8558

download_tyc8927_cutouts.py - Download additional cutouts for TYC 8927

download_detection_visibilities.py - Additional visibility files for SRSC detections


