;=======================================================;
;  redistribute_emiss.ncl
;=======================================================;
;
; Concepts illustrated:
;   - Currently configured to work with QFED emissions
;   - load CAM emission files
;   Do one of the following processes
;   - split OC or BC into 2 files:       tracer choice
;           OC1 50%, OC2 50%              OC
;           CB1 80%, CB2 20%              BC
;   - create combined species
;           bc_a4       = BC              BC
;           num_bc_a4                     BC
;           pom_a4      = 1.4 * OC        OC
;           num_pom_a4                    OC
;           SVOC        = combined        VBS
;           IVOC        = combined        VBS
;           SOAG        = combined        SOAG
;           so4_a1                        SO4
;           num_so4                       SO4
;   
;   To run type:
;        ncl  year=$year 'tracer="BC"' NRT=True 'outres="0.9x1.25"' \
;             'emiss_type="from_co2"' $codehome/redistribute_emiss.ncl
;
;   Requires:
;         emission file/s
;                                  RRB March 1, 2018
;=======================================================;
; load the libraries
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"

begin

;--------------------------------------------
; user input
;--------------------------------------------
    if (.not. isvar("year")) then      ; is year=<YYYY> from command line?
       year = 2017
    end if

    if (.not. isvar("tracer")) then    ; is tracer=<name> from command line?
       tracer = "OC"
    end if

    if (.not. isvar("NRT")) then        ; is NRT=<boolean> from command line?
         NRT = False
    end if

    if (.not. isvar("outres")) then     ; is outres=<name> from command line?
         outres = "0.9x1.25"
    end if

    if (.not. isvar("emiss_type")) then  ; is emiss_type=<name> from command line?
         emiss_type = "from_co2"         ; from_co, from_co2, regridded
    end if


  ; -------------------------------
  ; input emission files
  ; -------------------------------
  top_dir = "/net/modeling1/data14b/buchholz/"
  if (NRT) then
    emis_dir = top_dir+ "qfed/cam_"+outres+"/"+emiss_type+"/"+"nrt/"
  else
    emis_dir = top_dir+ "qfed/cam_"+outres+"/"+emiss_type+"/v2.5/"+year+"/"
  end if
  
  ; OC/BC
  if (tracer.eq."OC".or.tracer.eq."BC")
    e_file_in = emis_dir+"qfed.emis_"+tracer+"_"+outres+"_mol_"+year+".nc"
  ; VBS
  else if (tracer.eq."VBS") then
    pom_file_in = emis_dir+"qfed.emis_pom_a4_"+outres+"_mol_"+year+".nc"
    specs_ivoc = (/"C3H6", "C3H8", "C2H6", "C2H4", "BIGENE", "BIGALK", "CH3COCH3", \
                   "MEK", "CH3CHO", "CH2O", "BENZ", "TOLUENE", "XYLENE"/)
    e_file_in = new(dimsizes(specs_ivoc), string)
    do i = 0, dimsizes(specs_ivoc)-1
      e_file_in(i) = emis_dir+"qfed.emis_"+specs_ivoc(i)+"_"+outres+"_mol_"+year+".nc"
    end do
  ; SOAG
  else if (tracer.eq."SOAG") then
    specs_soag = (/"BIGALK", "BIGENE", "TOLUENE", "BENZ",  "XYLENE", "ISOP", "C10H16"/)
    e_file_in = new(dimsizes(specs_soag), string)
    do i = 0, dimsizes(specs_soag)-1
      e_file_in(i) = emis_dir+"qfed.emis_"+specs_soag(i)+"_"+outres+"_mol_"+year+".nc"
    end do
  ; SO4
  else if (tracer.eq."SO4") then
    e_file_in = emis_dir+"qfed.emis_SO2_orig_"+outres+"_mol_"+year+".nc"
  end if
  end if
  end if
  end if

  ;------------
  ; toggles
  ;------------
  PLOT           = False
  netCDF         = True                       ; for netCDF output

;--------------------------------------------
; end user input
;--------------------------------------------

;--------------------------------------------
; set up
  ; -------------------------------
  ; names of data structures
  ; -------------------------------
  fire_emiss           = "bb"

  ; -------------------------------
  ; plotting parameters
  ; -------------------------------
  if (PLOT) then
    mapType = "x11"
    mapName = tracer+"_diff"
  end if ;PLOT

  cr = "~C~"

  ; -------------------------------
  ; calculation parameters
  ; -------------------------------
  PI  = get_pi("float" )

  ; OC and BC
  if (tracer.eq."OC") then
    diam = 0.134e-06     ; Table S1 Liu, GMD, 2012
    rho_OC = 1000.
    mw = 12.011
  else if (tracer.eq."BC") then
    diam = 0.134e-06     ; Table S1 Liu, GMD, 2012
    rho_BC = 1700.
    mw = 12.011
  ; VBS
  else if (tracer.eq."VBS") then
    mw_ivoc = 184.36
    mw_svoc = 310.
    ;C3H6,C3H8,C2H6,C2H4,BIGENE,BIGALK,CH3COCH3,MEK,CH3CHO,CH2O,BENZENE,TOLUENE,XYLENES
    mws_voc = (/42., 44., 30., 28., 56., 72., 58., 72., 44., 30., 78., 92., 126./)
    mw_pom = 12.011
  ; SOAG
  else if (tracer.eq."SOAG") then
    mw_soag = 12.
    ;BIGALK,BIGENE,TOLUENE,BENZENE,XYLENES,ISOP,MTERP(C10H16)
    mws_voc = (/72., 56.,  92., 78., 126., 68., 136. /)
    yields = (/0.05, 0.05, 0.15, 0.15, 0.15, 0.04, 0.25/)
  ; SO4
  else if (tracer.eq."SO4") then
    diam = 0.134e-06
    rho_SO4 = 1770.
    mw = 115.   ; CAM-chem reads SO4 as NH4HSO4 in MAM (mw_so4 for BAM is 96)
  end if
  end if
  end if
  end if
  end if

;--------------------------------------------
; load files and extract
    if (tracer.eq."OC".or.tracer.eq."BC")
      fin = addfile(e_file_in, "r")
        emiss_in         = fin->$fire_emiss$
    else if (tracer.eq."VBS") then
      fin = addfile(pom_file_in, "r")
        if (ismissing(fin)) then
          print("POM file not created. Run for OC first.")
          exit
        end if
      emiss_in         = fin->$fire_emiss$
      emiss_in_array = new((/dimsizes(emiss_in(:,0,0)), dimsizes(emiss_in(0,:,0)),\
                            dimsizes(emiss_in(0,0,:)), dimsizes(specs_ivoc)/),float)
      do i = 0, dimsizes(specs_ivoc)-1
        fin := addfile(e_file_in(i), "r")
        emiss_in_array(:,:,:,i) = fin->$fire_emiss$
      end do
    else if (tracer.eq."SOAG") then
      fin = addfile(e_file_in(0), "r")
      emiss_in         = fin->$fire_emiss$
      emiss_in_array = new((/dimsizes(emiss_in(:,0,0)), dimsizes(emiss_in(0,:,0)),\
                            dimsizes(emiss_in(0,0,:)), dimsizes(specs_soag)/),float)
      do i = 0, dimsizes(specs_soag)-1
        fin := addfile(e_file_in(i), "r")
        emiss_in_array(:,:,:,i) = fin->$fire_emiss$
      end do
    else if (tracer.eq."SO4") then
      fin = addfile(e_file_in, "r")
        emiss_in         = fin->$fire_emiss$
    end if
    end if
    end if
    end if

;--------------------------------------------
; Perform calculations
;********************************************
; OC and BC -> split into two files, 
; create VBS species and num_* species
  if (tracer.eq."OC".or.tracer.eq."BC") then
    if (tracer.eq."OC") then
      emiss_split_1 = 0.5 * emiss_in
      emiss_split_2 = 0.5 * emiss_in
      ; Primary organic matter is organic carbon plus
      ; all the other present elements (e.g N, O, H etc.)
      emiss_new = 1.4 * emiss_in
      mass_particle = rho_OC *(PI/6.) *(diam)^3       ;mass per particle (kg/particle)
      ; to write out
      new_names = (/"OC1","OC2", "pom_a4", "num_pom_a4"/)
    else if (tracer.eq."BC") then
      emiss_split_1 = 0.8 * emiss_in
      emiss_split_2 = 0.2 * emiss_in
      emiss_new = emiss_in
      mass_particle = rho_BC *(PI/6.) *(diam)^3       ;mass per particle (kg/particle)
      new_names = (/"CB1","CB2", "bc_a4", "num_bc_a4"/)
    end if
    end if
    ; CESM scales emissions by amufac when read in
    ; (to convert molec/cm2/s to kg/m2/s)
    ; amufac = 1.65979e-23 = (1E-3kg/g)*(1E4cm2/m2)/Avog
    ; therefore number emissions files are also scaled by 1/amufac
    num_emiss = emiss_in * mw /mass_particle        ;(particles/cm2/s)(molecules/mole)(g/kg)
    ; to write out
    new_emiss = (/emiss_split_1, emiss_split_2, emiss_new, num_emiss/)
  end if


;********************************************
; VBS --> IVOC and SVOC
; Jathar et al. [2014, Table 1, https://doi.org/10.1073/pnas.1323740111]
; 0.6 x POA emissions considered as lost by evaporation and equal to SVOC
; and 0.2 x NMVOC emissions for the unspeciated IVOC fraction

  if (tracer.eq."VBS") then
    ; IVOC
      mass_emiss_1 = emiss_in_array*0
    do i = 0, dimsizes(specs_ivoc)-1
      mass_emiss_1(:,:,:,i) = 0.2*emiss_in_array(:,:,:,i) * mws_voc(i) / mw_ivoc
    end do
    emiss_comb_1 = dim_sum_n(mass_emiss_1,3)

    ;SVOC
    emiss_comb_2 = 0.6 * emiss_in *mw_pom/mw_svoc

    ; to write out
    new_names = (/"IVOC","SVOC"/)
    new_emiss = (/emiss_comb_1, emiss_comb_2/)
  end if


;********************************************
; SOAG
  if (tracer.eq."SOAG") then
      mass_emiss_1 = emiss_in_array*0
      hist_dummy = specs_soag
    do i = 0, dimsizes(specs_soag)-1
      mass_emiss_1(:,:,:,i) = yields(i)*emiss_in_array(:,:,:,i)*mws_voc(i) / mw_soag
      hist_dummy(i) = str_join((/sprintf("%4.4g", yields(i)),specs_soag(i)/), " x ")
    end do
    emiss_comb_1 = dim_sum_n(mass_emiss_1,3)
    ; to write out
    new_names = (/"SOAG"/)
    new_emiss = (/emiss_comb_1/)
    hist = str_join(hist_dummy, "  +  ")
  end if


;********************************************
; SO4 created from SO2
; Also create num_* species
  if (tracer.eq."SO4") then
    emiss_so2_new = 0.975 * emiss_in
    emiss_so4 = 0.025 * emiss_in
    mass_particle = rho_SO4 *(PI/6.) *(diam)^3       ;mass per particle (kg/particle)
    ; CESM scales emissions by amufac when read in
    ; (to convert molec/cm2/s to kg/m2/s)
    ; amufac = 1.65979e-23 = (1E-3kg/g)*(1E4cm2/m2)/Avog
    ; therefore number emissions files are also scaled by 1/amufac
    num_emiss = emiss_so4 * mw /mass_particle        ;(particles/cm2/s)(molecules/mole)(g/kg)
    ; to write out
    new_names = (/"SO2", "so4_a1", "num_so4_a1"/)
    new_emiss = (/emiss_so2_new, emiss_so4, num_emiss/)
  end if

;--------------------------------------------
; Write out to an netCDF file
  if (netCDF) then
    do i = 0,dimsizes(new_names)-1
    ;-------------------
    ; create file for each 
    ; split CAM-chem species
    ;-------------------
      outfilename = "qfed.emis_"+new_names(i)+"_"+outres+"_mol_"+year+".nc"
      ; copy file to new file
      system("cp "+e_file_in(0)+" "+emis_dir+outfilename)
      ; open the new file to overwrite
      fout = addfile(emis_dir+outfilename, "w")

      ;------------
      ; File 
      ; Attributes
      ;------------
     ; should have same file attributes as original emission file
     ; overwrite the title and date
        fout@creation_date      = systemfunc ("date")
        fout@title              = "Emissions of "+ new_names(i)+\
                                  " from FINN v1.6 emission x QFED CO2, daily"
        if (new_names(i).eq."num_pom_a4".or.new_names(i).eq."num_bc_a4".or.\
            new_names(i).eq."num_so4_a1") then
          fout@data_summary     = "Number of particles of "+tracer+" aerosol emissions for MAM4. Will be scaled by ((1E-3kg/g)*(1E4cm2/m2)/Avog) when read into in CESM2 because model was originally set up to convert molec/cm2/s to kg/m2/s."
          fout@molecular_weight := 1
        else if (new_names(i).eq."so4_a1") then
          fout@molecular_weight := mw
        else if (new_names(i).eq."SVOC") then
          fout@molecular_weight := mw_svoc
          fout@data_summary     = "Lumped HCs precursor of SOA for VBS scheme. 0.6*pom_a4"
        else if (new_names(i).eq."IVOC") then
          fout@molecular_weight := mw_ivoc
          hist = str_join(specs_ivoc, " + ")
          fout@data_summary     = "Lumped HCs precursor of SOA for VBS scheme. 0.2*("+hist+")"
        else if (new_names(i).eq."SOAG") then
          fout@molecular_weight := mw_soag
          fout@data_summary     = "Lumped HCs precursor of SOA for MAM4 scheme."+hist
        end if
       end if
        end if
        end if
        end if
       setfileoption(fout, "DefineMode",False)

      ;------------
      ; Variables
      ;------------
        if (new_names(i).eq."SOAG") then
           bb_emissions := new_emiss(:,:,:) ; only one output
        else
           bb_emissions := new_emiss(i,:,:,:)
        end if
        copy_VarAtts(emiss_in,bb_emissions)
        copy_VarCoords(emiss_in,bb_emissions)
        bb_emissions@long_name = new_names(i)+" QFED/FINN fire emissions"
        bb_emissions@_FillValue:= 0.
        bb_emissions@vmax      := tofloat(max(bb_emissions))
        bb_emissions@vmin      := tofloat(min(bb_emissions))
        if (new_names(i).eq."num_pom_a4".or.new_names(i).eq."num_bc_a4".or.\
            new_names(i).eq."num_so4_a1") then
          bb_emissions@long_name        := new_names(i)+" QFED/FINN particle number fire emissions"
          bb_emissions@units            := "(particles/cm2/s)(molecules/mole)(g/kg)"
          bb_emissions@molecular_weight :=  1
        end if
      printVarSummary(bb_emissions)

       ;--- emissions
         fout->bb               = bb_emissions
    end do
  end if ;NetCDF

;--------------------------------------------
; MAP PLOT
  if (PLOT) then
    plot_ind = 0
    wks = gsn_open_wks(mapType,mapName)
    gsn_define_colormap(wks,"BlueWhiteOrangeRed")        ; change colour map
    ;-------------------
    ; define resources 
    ; to use for plotting
    ;-------------------
    mapres = True
    mapres@tiMainString              = ""                  ; changing main large title
    mapres@gsnLeftString             = ""                  ; change left 
  ;  mapres@gsnRightString            = emiss_diff@units    ; change right title
    mapres@gsnFrame                  = False               ; do not advance frame
    mapres@gsnDraw		     = False	           ; don't draw it yet

    mapres@cnFillOn                  = True
    mapres@cnFillMode                = "CellFill"          ; fill as grid boxes not contours
    mapres@cnLineLabelsOn            = False               ; turn off countour labels
    mapres@cnLinesOn                 = False
    mapres@lbLabelBarOn              = False               ; turn off individual colorbars


    mapres@cnLevelSelectionMode      = "ManualLevels"      ; manually set the contour levels
      mapres@cnMinLevelValF          = -5e10                ; set the minimum contour level
      mapres@cnMaxLevelValF          = 5e10                ; set the maximum contour level
      mapres@cnLevelSpacingF         = 5e09                ; set the interval between contours

    ;-------------------
    ; do the plotting
    ;-------------------
    panel_res                       = True
      panel_res@txString            = "CAM-chem "+ tracer +" scaled, "+ \
                                      cd_calendar(emiss_in&time(plot_ind),1)
      panel_res@gsnPanelLabelBar    = True                ; add common colorbar

      panel_res@gsnPanelFigureStrings = (/"Original","Scaled"/)
    map1 = gsn_csm_contour_map_ce(wks,emiss_in(plot_ind,:,:),mapres)

    map2 = gsn_csm_contour_map_ce(wks,bb_emissions(plot_ind,:,:),mapres)

   ;   mapres@gsnLeftString            = "global average difference = "+\
   ;                                      sprintf("%2.2f",PercDiff(plot_ind))+"%"   ; change left title
   ; map3 = gsn_csm_contour_map_ce(wks,emiss_diff(plot_ind,:,:),mapres)

    gsn_panel(wks,(/map1,map2/),(/2,1/),panel_res)
  end if    ; PLOT


end

