# Timeseries - customize


```python
# By line: RRB 2020-07-29
# Script aims to:
# - Load multiple netCDF files
# - Extract one variable: CO
# - Choose a specific location from model grid
# - Plot timeseries
# - Customize visualization
```

### Load python packages


```python
import pandas as pd
from pandas.tseries.offsets import DateOffset
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata
import datetime
```

### Create reusable functions


```python
# Find nearest index
def find_index(array,x):
    idx = np.argmin(np.abs(array-x))
    return idx
```

### Load model Data:
Define the directories and file of interest for your results.


```python
result_dir = "/home/buchholz/Documents/code_database/untracked/my-notebook/CAM_Chem_examples/"
files_to_open = "CAM_chem_merra2_FCSD_1deg_QFED_monthly_*.nc"
#the netcdf files will be held in an xarray dataset named 'nc_load' and can be referenced later in the notebook
nc_load = xr.open_mfdataset(result_dir+files_to_open,combine='by_coords',concat_dim='time')
#to see what the netCDF file contains, just call the variable you read it into
#nc_load
```

### Extract the variable at the time and level and location of choice


```python
#extract variable
var_sel = nc_load['CO']

#extract grid variables
lat = nc_load['lat']
lon = nc_load['lon']
time = nc_load['time']

# CAM-chem writes the month average at midnight - i.e. the start of the next month.
# Reconfigure the time variable
time2 = pd.to_datetime(time.values,format='%Y-%m-%dT%H:%M:%S')+DateOffset(months=-1,days=+14)
print("file time: ", time[0].values, "---> converted time: ", time2[0])
```

    file time:  2018-02-01T00:00:00.000000000 ---> converted time:  2018-01-15 00:00:00


### Select and extract the location.


```python
name_select = "Boulder"
lat_select = 40.0150
lon_select = 360-105.2705 # model longitude is from 0 to 360

lat_i = find_index(lat,lat_select)
lon_i = find_index(lon,lon_select)

print(name_select, " latitude: ", lat_select, "---> nearest: ", lat[lat_i].values)
print(name_select, " longitude: ", lon_select, "---> nearest: ", lon[lon_i].values)

# extract location surface value and convert to ppb
var_srf = var_sel.isel(lev=55, lat=lat_i,lon=lon_i)*1e09
```

    Boulder  latitude:  40.015 ---> nearest:  40.0523560209424
    Boulder  longitude:  254.7295 ---> nearest:  255.0


### Plot the value versus time.


```python
plt.figure(figsize=(20,10),facecolor='whitesmoke')
ax = plt.axes(facecolor='whitesmoke')

plt.plot(time2, var_srf, '-o', label='CAM-chem CO',
         color='darkslateblue',
         markersize=12, linewidth=5,
         markerfacecolor='darkslateblue',
         markeredgecolor='grey',
         markeredgewidth=1)

#resources: named colors - https://matplotlib.org/examples/color/named_colors.html
#           default markers and lines list - https://matplotlib.org/2.1.2/api/_as_gen/matplotlib.pyplot.plot.html

# axes format
plt.xticks(fontsize=18)
ax.set_ylim(90, 200)
plt.yticks(np.arange(100, 220, step=20), fontsize=18)

# tickmarks direction
ax.tick_params(direction='in', length=8, width=3)

# adjust border
ax.spines["left"].set_linewidth(2.5)
ax.spines["bottom"].set_linewidth(2.5)
ax.spines["right"].set_visible(False)
ax.spines["top"].set_visible(False)

# titles
plt.title('CO at ' + name_select,fontsize=24)        
plt.xlabel('Time',fontsize=18)
plt.ylabel('CO (ppb)',fontsize=18)

# legend
plt.legend(bbox_to_anchor=(0.23, 0.08),loc='lower right')

# write to show the whole plot
plt.show() 
```


![png](plot_timeseries_customize_files/plot_timeseries_customize_13_0.png)



```python

```
