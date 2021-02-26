.. Python collection for CAM-chem documentation functions file, created by
   rrb on Mon Feb 15, 2021.

====================
some.examplefunc
====================

.. container::

   **some.examplefunc** (filename_or_obj, group=None, decode_cf=True, mask_and_scale=None, decode_times=True, autoclose=None, concat_characters=True, decode_coords=True, engine=None, chunks=None, lock=None, cache=None, drop_variables=None, backend_kwargs=None, use_cftime=None, decode_timedelta=None)

Open and decode a dataset from a file or file-like object.

Parameters:
   - filename (str, optional) - (str, Path, file-like or DataStore) – Strings and Path objects are interpreted as a path to a netCDF file or an OpenDAP URL and opened with python-netCDF4, unless the filename ends with .gz, in which case the file is gunzipped and opened with scipy.io.netcdf (only netCDF3 supported). Byte-strings or file-like objects are opened by scipy.io.netcdf (netCDF3) or h5py (netCDF4/HDF).
   - group (str, optional) - Path to the netCDF4 group in the given file to open (only works for netCDF4 files).


.. seealso::

   `open_mfdataset <http://xarray.pydata.org/en/stable/generated/xarray.open_mfdataset.html#xarray.open_mfdataset>`_
