import numpy as np
import pandas as pd
from scipy.interpolate import Rbf

def read_data(file_path):
    data = pd.read_csv(file_path)
    return data

def interpolate_data(data):
    latitudes = np.linspace(-90, 90, 181)
    longitudes = np.linspace(-180, 180, 361)
    
    # Original data points
    sun_lat = data['Sun_lat'].values
    sun_lon = data['Sun_lon'].values
    acc_X = data['acc_X'].values
    acc_Y = data['acc_Y'].values
    acc_Z = data['acc_Z'].values
    
    # Create RBF interpolators
    rbf_X = Rbf(sun_lat, sun_lon, acc_X, function='thin_plate')
    rbf_Y = Rbf(sun_lat, sun_lon, acc_Y, function='thin_plate')
    rbf_Z = Rbf(sun_lat, sun_lon, acc_Z, function='thin_plate')
    
    lat_grid, lon_grid = np.meshgrid(latitudes, longitudes, indexing='ij')
    
    # Interpolate the data
    acc_X_interp = rbf_X(lat_grid, lon_grid)
    acc_Y_interp = rbf_Y(lat_grid, lon_grid)
    acc_Z_interp = rbf_Z(lat_grid, lon_grid)
    
    return latitudes, longitudes, acc_X_interp, acc_Y_interp, acc_Z_interp

def save_interpolated_data(output_path, latitudes, longitudes, acc_X_interp, acc_Y_interp, acc_Z_interp):
    with open(output_path, 'w') as f:
        f.write('Sun_lat,Sun_lon,acc_X,acc_Y,acc_Z\n')
        for i, lat in enumerate(latitudes):
            for j, lon in enumerate(longitudes):
                f.write(f"{lat},{lon},{acc_X_interp[i, j]},{acc_Y_interp[i, j]},{acc_Z_interp[i, j]}\n")

def main():
    input_file = 'Scratch/AntTest/spiralPoints/outputFiles/combined_output.txt'
    output_file = 'combined_output_interp.txt'
    
    data = read_data(input_file)
    latitudes, longitudes, acc_X_interp, acc_Y_interp, acc_Z_interp = interpolate_data(data)
    save_interpolated_data(output_file, latitudes, longitudes, acc_X_interp, acc_Y_interp, acc_Z_interp)

if __name__ == "__main__":
    main()