;=======================================================;
;  combine_qfed_finn_ers.ncl
;=======================================================;
;
; Concepts illustrated:
;   - Load qfed CO2 (or CO) files
;   - Regrid from 0.25 x 0.25 to 1.9 x2.5
;                          or to 0.94 x 1.25
;   - Regrid lon gridding,
;          -180 to 180 qfed : 0 to 360 CAM-chem
;   - Write out to netCDF - one file per tracer per year
;                         - kept at daily time resolution
;   
;   To run type:
;         ncl regrid_qfed.ncl
;
;   Requires:
;         path to qfed files separated into years
;         molecular weights file
;                                  RRB March 06, 2015
;=======================================================;
; load the libraries
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"

begin

;--------------------------------------------
; user input
;--------------------------------------------
  year = 2016
  outres = "0.9x1.25"
  input_species = "oc"
  species = "OC"
  outpath = "/data14b/buchholz/qfed/cam_"+outres+"/regridded/"+year+"/"

  ; -------------------------------
  ; QFED files
  ; -------------------------------
  qfed_dir = "/data14b/buchholz/qfed/orig_0.25/"+input_species+"_"+year+"/"
  qfed_files = systemfunc ("ls "+qfed_dir+"*"+year+"*.nc4")

  ; -------------------------------
  ; MOZART molecular weights
  ; -------------------------------
  molwts = "/home/buchholz/data/species_molwts.txt"

  ;------------
  ; toggles
  ;------------
  netCDF         = True                       ; for netCDF output
  PLOT           = False
;--------------------------------------------
; end user input
;--------------------------------------------

;********************************************
; set up
  ; -------------------------------
  ; names of QFED data structures
  ; determined from an ncl_filedump
  ; -------------------------------
  qfed_tracer        = "biomass"
  qfed_time          = "time"

  ; -------------------------------
  ; plotting parameters
  ; -------------------------------
  if (PLOT) then
    mapType = "x11"
    mapName = "test"
  end if ;PLOT

  ; -------------------------------
  ; constants
  ; -------------------------------
   NAv = 6.022e23              ; Avogadro's number, molecules mole^-1

   re   = 6.37122e06              ; Earth radius
   rad  = 4.0 * atan(1.0) / 180.0 ; For area sums/avg
   con  = re * rad                 

   ; load molecular weights (g/mol) from a MOZART file,
   ; augmented with additional values for:
   ; CO2, OC and BC copied from OC1 and CB1
   mw_dummy  = asciiread(molwts,-1,"string")
   mw_dummy2 = mw_dummy(2:)
   mol_wts = new((/dimsizes(mw_dummy2),2/), string)
   do s = 0,dimsizes(mw_dummy2)-1
     mol_wts(s,:) = str_split(mw_dummy2(s)," ")
   end do


  ; -------------------------------
  ; lat/lon for re-gridding
  ; -------------------------------

  if (outres.eq."0.9x1.25") then
   ; higher res - 1 deg
   newlon  = fspan(0,358.75, 288)
     newlon@units      = "degrees_east"
     newlon@long_name  = "longitude"
     newlon!0          = "lon"
     newlon&lon        = newlon
   newlat  = fspan(-90,90, 192)
     newlat@units      = "degrees_north"
     newlat@long_name  = "latitude"
     newlat!0          = "lat"
     newlat&lat        = newlat
  else
    ; lower res - 2 deg
   newlon  = fspan(0,357.5, 144)
     newlon@units      = "degrees_east"
     newlon@long_name  = "longitude"
     newlon!0          = "lon"
     newlon&lon        = newlon
   newlat  = fspan(-90,90, 96)
     newlat@units      = "degrees_north"
     newlat@long_name  = "latitude"
     newlat!0          = "lat"
     newlat&lat        = newlat
   end if

  ; -------------------------------
  ; CAM-chem res for sums/avgs
  ; -------------------------------
     clat = cos(newlat * rad)        ; cosine of latitude
     dlon = (newlon(2) - newlon(1))  ; assume dlon is constant
     dlat = (newlat(2) - newlat(1))  ; assume dlat is constant
     dx   = con * dlon * clat        ; dx at each latitude
     dy   = con * dlat               ; dy is constant
     dydx = dy * dx                  ; dydx(nlat)
   
     wgt_CAM  = new((/dimsizes(newlat), dimsizes(newlon)/), float)
     wgt_CAM  = conform(wgt_CAM, dydx, 0)


;********************************************
; load files and extract
  ; -------------------------------
  ; QFED load
  ; -------------------------------
    fin = addfiles(qfed_files, "r")            ; read in
    ListSetType (fin, "cat") 
      tracer_all       = fin[:]->$qfed_tracer$

      ; load and convert time format
      time_dummy       = fin[:]->$qfed_time$
      time = cd_convert(time_dummy, "days since 1850-01-01 00:00:00" )
        time@long_name = "Time"
        time@calendar = "Gregorian"
        time!0 = "time"
        time&time = time

      date = cd_calendar(time_dummy,-2)
        date!0 = "time"
        date&time = time
        date@long_name = "Date"
        date@units = "YYYYMMDD"
        delete(date@calendar)

      delete(tracer_all&time )
      tracer_all!0 = "time"
      tracer_all&time = (time)

  ; -------------------------------
  ; QFED res for sums/avgs
  ; -------------------------------
     clat_q = cos(tracer_all&lat * rad) ; cosine of latitude
     dlon_q = (tracer_all&lon(2) - tracer_all&lon(1))  ; assume dlon is constant
     dlat_q = (tracer_all&lat(2) - tracer_all&lat(1))  ; assume dlat is constant
     dx_q   = con * dlon_q * clat_q   ; dx at each latitude
     dy_q   = con * dlat_q            ; dy is constant
     dydx_q = dy_q * dx_q             ; dydx(nlat)

     wgt_QFED  = new((/dimsizes(tracer_all&lat), dimsizes(tracer_all&lon)/), float)
     wgt_QFED  = conform(wgt_QFED, tofloat(dydx_q), 0)


  ;********************************************
  ; Regrid and QFED for CAM-chem input
  ; -------------------------------

    tracer_emiss:= tracer_all
      copy_VarAtts(tracer_all,tracer_emiss)
      copy_VarCoords(tracer_all,tracer_emiss)
    ;printVarSummary(tracer_emiss)

    ; -------------------------------
    ; convert to CAM-Chem units
    ; kg s-1 m-2 to molec. cm-2 s-1
    ; -------------------------------
     print(species)
     mw = tofloat(mol_wts(ind(mol_wts(:,0).eq.species),1))
     print(species+" MW: "+mw)
     tracer_emiss = tracer_emiss/(10000)        ; m-2 -> cm-2
     tracer_emiss = (tracer_emiss*1000/mw)*NAv  ; kg -> g -> mol -> molec
       tracer_emiss@units = "molecules/cm2/s"

    ; -------------------------------
    ; regrid to CAM-chem structure
    ; 1.9 x 2.5 or 0.94 x 1.25
    ; -------------------------------
     opt    = False
     emiss_regrid  = area_conserve_remap_Wrap(tracer_emiss&lon,tracer_emiss&lat, \
                                         tracer_emiss , \
                                         newlon, newlat, opt)  ; (ntim,96,144)
     ;printVarSummary(emiss_regrid)

     ;--- sanity check
     SumOrigGrid = wgt_areasum2 (tracer_emiss , wgt_QFED, 0)
     Sum_Regrid = wgt_areasum2 (emiss_regrid, wgt_CAM, 0)
     SumDiff = SumOrigGrid-Sum_Regrid
     PercDiff = (SumDiff/SumOrigGrid)*100
     MaxDiff = max(PercDiff)
     max_ind = ind(PercDiff.eq.MaxDiff)
   print("Maximum diff: lowres: "+sprintf("%2.2e",SumOrigGrid(max_ind))+\
         "  highres: "+sprintf("%2.2e",Sum_Regrid(max_ind))+   \
         "    diff: "+sprintf("%2.2e",SumDiff(max_ind))+  \
         "   percent diff: "+sprintf("%2.2f",PercDiff(max_ind))+"%")

   print("Maximum percent diff in "+species+\
         " from regridding: "+sprintf("%2.2f",PercDiff(max_ind))+"%"+\
         " on date: " + cd_calendar(tracer_all&time(max_ind),2))
   print("-------------------------------------------------")

    ;--------------------------------------------
    ; Write out to an netCDF file
    ;--------------------------------------------
    if (netCDF) then
      ;-------------------
      ; create file for each 
      ; CAM-chem species
      ;-------------------
      outfilename = "qfed.emis_"+species+"_"+outres+"_mol_"+year+".nc"
      fout = addfile(outpath+outfilename, "c")

      ;------------
      ; File 
      ; Attributes
      ;------------
      setfileoption(fout, "DefineMode",True)
      fAtt                      = True
        fAtt@molecular_weight   = mw
        fAtt@conventions        = "CF"
        fAtt@history            = species+" is from QFED, Level3b v2.5 "+\
                                  "(qfed-2_5_r1) Gridded Emission Estimates"
        fAtt@author             = "R. R. Buchholz"
        fAtt@creation_date      = systemfunc ("date")
        fAtt@source             = "QFED: NASA/GSFC/GMAO GEOS-5 Aerosol Group"
        fAtt@title              = "Emissions of "+ species + " from QFED, daily"

       fileattdef(fout, fAtt)
       setfileoption(fout, "DefineMode",False)

      ;------------
      ; Coordinate Variables
      ;------------
        dimNames = (/"time", "lat", "lon"/)  
	dim_Sizes = (/ -1   ,  dimsizes(emiss_regrid&lat),  dimsizes(emiss_regrid&lon)/) 
	dimUnlim = (/ True , False, False/)   
	filedimdef(fout,dimNames,dim_Sizes,dimUnlim)
      ;------------
      ; Variables
      ;------------
      emiss_regrid@long_name = species +" QFED fire emissions"
      emiss_regrid@vmax      = max(emiss_regrid)
      emiss_regrid@vmin      = min(emiss_regrid)
      delete(emiss_regrid@missing_value)
      delete(emiss_regrid@fmissing_value)

       ;--- date
         fout->date             = date
       ;--- emissions
         fout->bb               = emiss_regrid
    end if ;NetCDF

  tracername := species

  ;********************************************
  ; panel plots for consistency check
  ;-------------------
  ; MAP PLOT
  ;-------------------
  if (PLOT) then
    wks = gsn_open_wks(mapType,mapName)
    gsn_define_colormap(wks,"sunshine_9lev")        ; change colour map
    ;-------------------
    ; define resources 
    ; to use for plotting
    ;-------------------
    mapres = True
    mapres@tiMainString              = ""                  ; changing main large title
    mapres@gsnLeftString             = ""                  ; change left 
    mapres@gsnRightString            = tracer_emiss@units  ; change right title
    mapres@gsnFrame                  = False               ; do not advance frame
    mapres@gsnDraw		     = False	           ; don't draw it yet

    mapres@cnFillOn                  = True
    mapres@cnFillMode                = "CellFill"          ; fill as grid boxes not contours
    mapres@cnLineLabelsOn            = False               ; turn off countour labels
    mapres@cnLinesOn                 = False
    mapres@lbLabelBarOn              = False               ; turn off individual colorbars

    ;mapres@mpLimitMode               ="LatLon"            ; zoom to Australia
    ;  mapres@mpMinLatF               = -45
    ;  mapres@mpMaxLatF               = -10
    ;  mapres@mpMinLonF               = 100
     ; mapres@mpMaxLonF               = 160

    mapres@cnLevelSelectionMode      = "ManualLevels"      ; manually set the contour levels
      mapres@cnMinLevelValF          = 1e09                ; set the minimum contour level
      mapres@cnMaxLevelValF          = 5e10                ; set the maximum contour level
      mapres@cnLevelSpacingF         = 1e10                ; set the interval between contours

    ;-------------------
    ; do the plotting
    ;-------------------
    ;map1 = gsn_csm_contour_map_ce(wks,co2_all(0,:,:),mapres)

    mapres@gsnLeftString            = "spatial sum = "+ SumOrigGrid(0) ; change left title
      map1 = gsn_csm_contour_map_ce(wks,tracer_emiss(0,:,:),mapres)

    mapres@gsnLeftString            = "spatial sum = "+ Sum_Regrid(0) ; change left title
      map2 = gsn_csm_contour_map_ce(wks,emiss_regrid(0,:,:),mapres)

    panel_res                       = True
      panel_res@txString            = "QFED "+ tracername +" emissions"
      panel_res@gsnPanelLabelBar    = True                ; add common colorbar
      panel_res@gsnPanelFigureStrings = (/"qfed high res","qfed low res"/)

    gsn_panel(wks,(/map1,map2/),(/2,1/),panel_res)

  end if    ; PLOT


end

