#####
# this script uses Py6S to model TOA reflectance
# for soil endmembers for use in unmixing models
#
# c. 2016 Christopher Anderson
#####

import numpy as np
import aei as aei
import random
import spectral
from Py6S import *

# load sixs
s = SixS()

#####
# set up output files and processing parameters
#####

# set output file base name (will have _speclib.csv, _speclib.sli, 
#  _speclib.hdr, and _atm_x.sixs appended for the csv, spectral library, 
#  and sixs outputs with x as the atmospheric iteration)
output_base = aei.environ['AEI_GS'] + '/data/tropical_atmosphere_landsat8_soil_bundles'

# set number of random atmospheres to simulate
n_atmospheres = 5

# set number of random veg, woody and soil bundles to simulate
n_bundles = 25

#####
# set up the spectral output parameters
#####

# specify the output sensor configuration for modeled spectra
#  options include ali, aster, er2_mas, gli, landsat_etm, landsat_mss, landsat_oli,
#  landsat_tm, meris, modis, polder, spot_hrv, spot_vgt, vnir, whole_range, and custom
target_sensor = 'landsat_oli'

# set up output wavelengths (in um) if using custom wl range (ignored for pre-defined sensors)
wl_start = 0.4
wl_end = 2.5
wl_interval = 0.01
wl = np.arange(wl_start, wl_end, wl_interval)
wl_sixs = Wavelength(wl_start, wl_end)

# set up output type (an option from s.outputs)
#  examples include pixel_radiance, pixel_reflectance, apparent_radiance, apparent_reflectance, etc.
output_type = 'apparent_reflectance'

#####
# set up atmospheric modeling parameters
#####

# select the atmospheric profile (an option from AtmosProfile)
#  examples include Tropical, MidlatitudeSummer, MidlatitudeWinter, etc.
atmos_profile = [AtmosProfile.Tropical]
atmos_profile_ind = np.random.random_integers(0,len(atmos_profile)-1,n_atmospheres)

# select the aerosol profile to use (an option from AeroProfile)
#  examples include BiomassBurning, Continental, Desert, Maritime, NoAerosols, Urban, etc.
aero_profile = [AeroProfile.Continental, AeroProfile.BiomassBurning]
aero_profile_ind = np.random.random_integers(0,len(aero_profile)-1,n_atmospheres)

# select ground reflectance method (an option from GroundReflectance)
#  examples include GreenVegetation, Hetero(/Homo)geneousLambertian, HotSpot, LeafDistPlanophile, etc
ground_reflectance = [GroundReflectance.HomogeneousLambertian]
ground_reflectance_ind = np.random.random_integers(0,len(ground_reflectance)-1,n_atmospheres)

# set altitudes for sensor (ground) and target (target altitude for modeled reflectance)
#  Landsat 4, 5, 7, 8 altitude - 705 km 
altitudes = Altitudes()
#altitudes.set_sensor_custom_altitude(705)
altitudes.set_sensor_satellite_level()
altitudes.set_target_sea_level()
s.altitudes = altitudes

# set aerosol optical thickness (550 nm)
aot = aei.randomFloats(n_atmospheres, 0.3, 0.7)

# select viewing geometry parameters
geo = Geometry.User()
solar_a = aei.randomFloats(n_atmospheres, 0, 359) 
solar_z = aei.randomFloats(n_atmospheres, 10, 45)
view_a = aei.randomFloats(n_atmospheres, 0, 5) - 2.5
view_z = aei.randomFloats(n_atmospheres, 0, 1)

# convert view azimuth to 0-360 scale
view_a[(view_a < 0)] = view_a[(view_a < 0)] + 360

#####
# set up soil file info
#####

# soil spectra file paths
soil_files = ['/home/cba/cba/global/spectra/joint_fire_science_program/southern_california/soil/privcali.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/southern_california/soil/bigrocks.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/southern_california/soil/parksand.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/southern_california/soil/hillcali.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/southern_california/soil/deepcali.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/southern_california/soil/sand.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/southern_california/soil/bridge.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/southern_california/soil/sandston.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/calib5rd.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/grayrock.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/baresoil.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/redrock.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/site4cal.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/grayrock_hillslope.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/rockycal.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/calibrd.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/whalecal.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/rocksig.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/oldrocky.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/bluesadl.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/roadsoil.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/rockunbu.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/morelcal.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/teepeeca.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/soil_unb.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/sgsaddle.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/cooney_grayrock.txt',
              '/home/cba/cba/global/spectra/joint_fire_science_program/western_montana/soil/hillcal.txt']

# randomly sample # bundles to use
srnd = random.sample(range(len(soil_files)), n_bundles)
soil_spectra = []
for i in srnd:
    soil_spectra.append(soil_files[i])

#####
# set up if statements to set parameters based on sesnsor type
#####
if target_sensor == 'custom':
    run_sixs_params = SixSHelpers.Wavelengths.run_wavelengths
    num_bands = len(wl)
    good_bands = np.arange(num_bands)
elif target_sensor == 'ali':
    run_sixs_params = SixSHelpers.Wavelengths.run_ali
    num_bands = 7
    good_bands = np.arange(num_bands)
elif target_sensor == 'aster':
    run_sixs_params = SixSHelpers.Wavelengths.run_aster
    num_bands = 9
    good_bands = np.arange(num_bands)
elif target_sensor == 'er2_mas':
    run_sixs_params = SixSHelpers.Wavelengths.run_er2_mas
    num_bands = 7
    good_bands = np.arange(num_bands)
elif target_sensor == 'gli':
    run_sixs_params = SixSHelpers.Wavelengths.run_gli
    num_bands = 30
    good_bands = np.arange(num_bands)
elif target_sensor == 'landsat_etm':
    run_sixs_params = SixSHelpers.Wavelengths.run_landsat_etm
    num_bands = 6
    good_bands = np.arange(num_bands)
elif target_sensor == 'landsat_mss':
    run_sixs_params = SixSHelpers.Wavelengths.run_landsat_mss
    num_bands = 4
    good_bands = np.arange(num_bands)
elif target_sensor == 'landsat_oli':
    run_sixs_params = SixSHelpers.Wavelengths.run_landsat_oli
    num_bands = 10
    # use only the 6 traditional optical bands
    good_bands = np.arange(6)+1
elif target_sensor == 'landsat_tm':
    run_sixs_params = SixSHelpers.Wavelengths.run_landsat_tm
    num_bands = 6
    good_bands = np.arange(num_bands)
elif target_sensor == 'meris':
    run_sixs_params = SixSHelpers.Wavelengths.run_meris
    num_bands = 16
    good_bands = np.arange(num_bands)
elif target_sensor == 'modis':
    run_sixs_params = SixSHelpers.Wavelengths.run_modis
    num_bands = 8
    good_bands = np.arange(num_bands)
elif target_sensor == 'polder':
    run_sixs_params = SixSHelpers.Wavelengths.run_polder
    num_bands = 8
    good_bands = np.arange(num_bands)
elif target_sensor == 'spot_hrv':
    run_sixs_params = SixSHelpers.Wavelengths.run_spot_hrv
    num_bands = 4
    good_bands = np.arange(num_bands)
elif target_sensor == 'spot_vgt':
    run_sixs_params = SixSHelpers.Wavelengths.run_spot_vgt
    num_bands = 4
    good_bands = np.arange(num_bands)
elif target_sensor == 'vnir':
    run_sixs_params = SixSHelpers.Wavelengths.run_vnir
    num_bands = 200
    good_bands = np.arange(num_bands)
elif target_sensor == 'whole_range':
    run_sixs_params = SixSHelpers.Wavelengths.run_whole_range
    num_bands = 380
    # use only 400-2500 nm range
    good_bands = np.arange(210)+20
else:
    raise OSError('Unsupported sensor configuration')

nb = len(good_bands)

#####
# set up the output file and band names
#####
output_csv = []
output_sli = []
output_hdr = []
output_sixs = []
output_spec = []

output_csv.append(output_base + '_speclib.csv')
output_sli.append(output_base + '_speclib.sli')
output_hdr.append(output_base + '_speclib.hdr')

for i in range(n_atmospheres):
    output_sixs.append(output_base + '_atm_%02d.sixs' % (i+1))
    
for i in range(n_bundles):
    output_spec.append('Soil bundle %03d' % (i+1))
    
#####
# set up the loop for each atmosphere/canopy model
#####

# first create the output array that will contain all the resulting spectra
output_array = np.zeros([nb, (n_bundles * n_atmospheres) + 1])

for i in range(n_atmospheres):
    
    # set the sixs atmosphere profile
    s.aero_profile = AeroProfile.PredefinedType(aero_profile[aero_profile_ind[i]])
    s.atmos_profile = AtmosProfile.PredefinedType(atmos_profile[atmos_profile_ind[i]])
    s.aot550 = aot[i]
    geo.solar_a = solar_a[i]
    geo.solar_z = solar_z[i]
    geo.view_a = view_a[i]
    geo.view_z = view_z[i]
    s.geometry = geo
    ground_refl = ground_reflectance[ground_reflectance_ind[i]]
    
    # loop through each soil bundle
    for j in range(n_bundles):
        
        # read in the data
        soil = aei.readJFSC(soil_spectra[j])
        
        # remove bad data
        soil.remove_water_bands()
        
        # convert to micrometers if necessary
        if soil.band_unit == 'Nanometers':
            soil.band_centers /= 1000.
        
        # convert to format expected by sixs    
        spectrum = np.array([soil.band_centers, soil.spectra[0]]).transpose()
        s.ground_reflectance = ground_refl(spectrum)
        
        # generate the output spectrum
        if target_sensor == 'custom':
            wavelengths, results = run_sixs_params(s, wl, output_name = output_type)
        else:
            wavelengths, results = run_sixs_params(s, output_name = output_type)
    
        #convert output to array for ease of output
        results = np.asarray(results)
        
        # add the modeled spectrum to the output array
        output_array[0:nb, (i * n_bundles) + j + 1] = results[good_bands]
        
    # write the sixs parameters for this run to output file
    s.write_input_file(output_sixs[i])

# now that the loop has finished we can export our results to a csv file
wavelengths = np.asarray(wavelengths)
output_array[:, 0] = wavelengths[good_bands]
np.savetxt(output_csv[0], output_array.transpose(), delimiter=",")

# output a spectral library
with open(output_sli[0], 'w') as f: 
    output_array[:,1:].transpose().tofile(f)

metadata = {
    'samples' : nb,
    'lines' : n_bundles * n_atmospheres,
    'bands' : 1,
    'data type' : 5,
    'header offset' : 0,
    'interleave' : 'bsq',
    'byte order' : 0,
    'sensor type' : target_sensor,
    'spectra names' : output_spec,
    'wavelength units' : 'micrometers',
    'wavelength' : wavelengths[good_bands]
    }
envi.write_envi_header(output_hdr[0], metadata, is_library=True)
