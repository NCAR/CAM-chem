# Plot a map as Lambert Conformal


```python
# projections-conus.py
# Carl Drews
# July 2020
# Added Lambert Conformal CONUS and Mexican states to Cartopy example 5 at:
# https://scitools.org.uk/cartopy/docs/latest/crs/projections.html#lambertconformal

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import cartopy.io.shapereader


#plt.figure(figsize=(4.2897, 3))
myLambert = ccrs.LambertConformal(central_longitude=-97.0,
   central_latitude=(30.0 + 60.0)/2)
ax = plt.axes(projection=myLambert)
ax.set_extent([-119.90, -73.50, 23.08, 50.00])

# set up line width
width = 1.0

ax.coastlines(resolution='50m', linewidth=width)
ax.add_feature(cfeature.BORDERS.with_scale("50m"), linewidth=width)
ax.add_feature(cfeature.STATES.with_scale("50m"), linewidth=width/2)

# States of Mexico
# download from: https://www.naturalearthdata.com/downloads/10m-cultural-vectors/
shapeFilename = "./ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces.shp"
print("Reading states provinces from {}\n".format(shapeFilename))
reader = cartopy.io.shapereader.Reader(shapeFilename)
statesProvinces = reader.records()

mexicoStates = []
for stateProvince in statesProvinces:
   if (stateProvince.attributes["admin"] == "Mexico"):
      print("State province {}".format(stateProvince.attributes["name"]))
      mexicoStates.append(stateProvince.geometry)

ax.add_geometries(mexicoStates, ccrs.PlateCarree(),
   edgecolor="black", facecolor='none', linewidth=width/2)

ax.gridlines()

savePath = "./images/projection-conus.png"

try:
    print("Saving image to {}\n".format(savePath))
    # trim whitespace but leave a narrow margin
    plt.savefig(savePath,
        bbox_inches="tight", pad_inches=0.04)

except RuntimeError as oops:
    print("{}\n".format(traceback.format_exc()))
```

    Reading states provinces from ./ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces.shp
    
    State province Sonora
    State province Baja California
    State province Chihuahua
    State province Coahuila
    State province Tamaulipas
    State province Nuevo León
    State province Quintana Roo
    State province Campeche
    State province Tabasco
    State province Chiapas
    State province Colima
    State province Nayarit
    State province Baja California Sur
    State province Sinaloa
    State province Yucatán
    State province Veracruz
    State province Jalisco
    State province Michoacán
    State province Guerrero
    State province Oaxaca
    State province 
    State province México
    State province Puebla
    State province Morelos
    State province Querétaro
    State province Hidalgo
    State province Guanajuato
    State province San Luis Potosí
    State province Zacatecas
    State province Aguascalientes
    State province Durango
    State province Tlaxcala
    State province Distrito Federal
    Saving image to ./images/projection-conus.png
    



    ---------------------------------------------------------------------------

    FileNotFoundError                         Traceback (most recent call last)

    <ipython-input-5-f62c9fba70ef> in <module>
         48     # trim whitespace but leave a narrow margin
         49     plt.savefig(savePath,
    ---> 50         bbox_inches="tight", pad_inches=0.04)
         51 
         52 except RuntimeError as oops:


    ~/anaconda3/lib/python3.7/site-packages/matplotlib/pyplot.py in savefig(*args, **kwargs)
        727 def savefig(*args, **kwargs):
        728     fig = gcf()
    --> 729     res = fig.savefig(*args, **kwargs)
        730     fig.canvas.draw_idle()   # need this if 'transparent=True' to reset colors
        731     return res


    ~/anaconda3/lib/python3.7/site-packages/matplotlib/figure.py in savefig(self, fname, transparent, **kwargs)
       2178             self.patch.set_visible(frameon)
       2179 
    -> 2180         self.canvas.print_figure(fname, **kwargs)
       2181 
       2182         if frameon:


    ~/anaconda3/lib/python3.7/site-packages/matplotlib/backend_bases.py in print_figure(self, filename, dpi, facecolor, edgecolor, orientation, format, bbox_inches, **kwargs)
       2089                     orientation=orientation,
       2090                     bbox_inches_restore=_bbox_inches_restore,
    -> 2091                     **kwargs)
       2092             finally:
       2093                 if bbox_inches and restore_bbox:


    ~/anaconda3/lib/python3.7/site-packages/matplotlib/backends/backend_agg.py in print_png(self, filename_or_obj, metadata, pil_kwargs, *args, **kwargs)
        528             renderer = self.get_renderer()
        529             with cbook._setattr_cm(renderer, dpi=self.figure.dpi), \
    --> 530                     cbook.open_file_cm(filename_or_obj, "wb") as fh:
        531                 _png.write_png(renderer._renderer, fh,
        532                                self.figure.dpi, metadata=metadata)


    ~/anaconda3/lib/python3.7/contextlib.py in __enter__(self)
        110         del self.args, self.kwds, self.func
        111         try:
    --> 112             return next(self.gen)
        113         except StopIteration:
        114             raise RuntimeError("generator didn't yield") from None


    ~/anaconda3/lib/python3.7/site-packages/matplotlib/cbook/__init__.py in open_file_cm(path_or_file, mode, encoding)
        445 def open_file_cm(path_or_file, mode="r", encoding=None):
        446     r"""Pass through file objects and context-manage `.PathLike`\s."""
    --> 447     fh, opened = to_filehandle(path_or_file, mode, True, encoding)
        448     if opened:
        449         with fh:


    ~/anaconda3/lib/python3.7/site-packages/matplotlib/cbook/__init__.py in to_filehandle(fname, flag, return_opened, encoding)
        430             fh = bz2.BZ2File(fname, flag)
        431         else:
    --> 432             fh = open(fname, flag, encoding=encoding)
        433         opened = True
        434     elif hasattr(fname, 'seek'):


    FileNotFoundError: [Errno 2] No such file or directory: './images/projection-conus.png'



![png](plot_projection_conus_files/plot_projection_conus_1_2.png)



```python
cartopy.config['data_dir'] 
```




    '/home/buchholz/.local/share/cartopy'




```python

```


```python

```
