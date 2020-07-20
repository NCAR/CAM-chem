# Example Map Plotting


```python
# By line: RRB 2020-07-20
# Script aims to:
# - Load a netCDF file
# - Extract one variable: CO
# - Create contour plot of variable as world map with coastlines
# - Add axes labels
# - Add grid lines
```

### At the start of a Jupyter notebook you need to import all modules that you will use


```python
import matplotlib.pyplot as plt
import cartopy.crs as ccrs                 # For plotting maps
import cartopy.feature as cfeature         # For plotting maps
from   pathlib import Path                 # System agnostic paths
import xarray as xr                        # For loading the data arrays
```

### Define the directories and file of interest for your results. This can be shortened to less lines as well.


```python
result_dir = Path("/home/buchholz/Documents/code_database/untracked/my-notebook/CAM_Chem_examples")
file = "CAM_chem_merra2_FCSD_1deg_QFED_monthoutput_CO_201801.nc"
file_to_open = result_dir / file
#the netcdf file is now held in an xarray dataset named 'nc_load' and can be referenced later in the notebook
nc_load = xr.open_dataset(file_to_open)
#to see what the netCDF file contains, uncomment below
#nc_load
```

### Extract the variable of choice at the time and level of choice


```python
#extract grid variables
lat = nc_load['lat']
lon = nc_load['lon']

#extract variable
var_sel = nc_load['CO']
#to see the dimensions and metadata of the variable, uncomment below
#print(var_sel)

#select the surface level and convert to ppbv from vmr
var_srf = var_sel.isel(time=0,lev=55) # MAM chosen
var_srf = var_srf*1e09 # 10-9 to ppb
print(var_srf.shape)
```

    (192, 288)


### Plot the value over a specific region


```python
plt.figure(figsize=(20,8))

#Define projection
ax = plt.axes(projection=ccrs.PlateCarree())

#plot the data
plt.contourf(lon,lat,var_srf,cmap='Spectral_r')

# add coastlines
ax.add_feature(cfeature.COASTLINE)

#add lat lon grids
gl = ax.gridlines(draw_labels=True, color='lightgrey', alpha=0.5, linestyle='--')
gl.xlabels_top = False
gl.ylabels_right = False

# Titles
# Main
plt.title("Global map of CAM-chem CO, January 2018",fontsize=18)

# y-axis
ax.text(-0.04, 0.5, 'Latitude', va='bottom', ha='center',
        rotation='vertical', rotation_mode='anchor',
        transform=ax.transAxes)
# x-axis
ax.text(0.5, -0.08, 'Longitude', va='bottom', ha='center',
        rotation='horizontal', rotation_mode='anchor',
        transform=ax.transAxes)
# legend
ax.text(1.15, 0.5, 'CO (ppb)', va='bottom', ha='center',
        rotation='vertical', rotation_mode='anchor',
        transform=ax.transAxes)

plt.colorbar()
plt.show() 
```


![png](plot_map_basic_co_files/plot_map_basic_co_9_0.png)



```python

```