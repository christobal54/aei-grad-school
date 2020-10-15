#
# script to apply species ID models from NEON reflectance data
#####

# package imports
import aei
import copy
#import plotly
import pickle
import numpy as np
import pandas as pd
from sklearn import svm
from sklearn import metrics
from sklearn import ensemble
from sklearn import preprocessing
from sklearn import model_selection
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA

# set the seed
np.random.seed(1985)

# set the path to the ECODSEdataset files
path_sep = '/'
path_base = '/home/cba/Downloads/ECODSEdataset'
path_train_hyp = path_sep.join([path_base, 'Task3', 'GroundData', 'hyper_bands_train.csv'])
path_train_bands = path_sep.join([path_base, 'Task3', 'hyper_bands.csv'])
path_train_spp = path_sep.join([path_base, 'Task3', 'GroundData', 'species_id_train.csv'])
path_test_hyp = path_sep.join([path_base, 'Task3', 'GroundData', 'hyper_bands_test.csv'])

# select the classifier settings
color_options = {'RFC': 'Orange', 'GBC': 'Blue', 'SVC': 'Green'}

# set paths to new output files
path_plots = path_sep.join([path_base, 'plots'])
path_scratch = path_sep.join([path_base, 'scratch'])
path_outputs = path_sep.join([path_base, 'outputs'])
path_ova = path_sep.join([path_outputs, 'one_vs_all'])
path_ovo = path_sep.join([path_outputs, 'one_vs_one'])
pred_spp = path_sep.join([path_outputs, 'species_id_subm_new.csv'])
pred_gen = path_sep.join([path_outputs, 'genus_id_subm.csv'])

# load the final models
gbc_file = path_sep.join([path_ova, 'Multiclass-GBC.pickle'])
with open(gbc_file, 'rb') as f:
    gbc = pickle.load(f)

rfc_file = path_sep.join([path_ova, 'Multiclass-RFC.pickle'])
with open(rfc_file, 'rb') as f:
    rfc = pickle.load(f)
    
# and the genus-level models
gbc_ge_file = path_sep.join([path_ova, 'Multiclass-GBC-genus.pickle'])
with open(gbc_ge_file, 'rb') as f:
    gbc_ge = pickle.load(f)

rfc_ge_file = path_sep.join([path_ova, 'Multiclass-RFC-genus.pickle'])
with open(rfc_ge_file, 'rb') as f:
    rfc_ge = pickle.load(f)
    
# load other misc. variables from the classification script
misc_var_file = path_sep.join([path_outputs, 'misc_variables.pickle'])
with open(misc_var_file, 'r') as f:
    misc_vars = pickle.load(f)
    
sp_unique = misc_vars['sp_unique']
ge_unique = misc_vars['ge_unique']
n_species = len(sp_unique)
n_genera = len(ge_unique)

# load the data reducer
reducer_file = path_sep.join([path_outputs, 'Data_transformer.pickle'])
with open(reducer_file, 'r') as f:
    reducer = pickle.load(f)
    
# load the one-vs-all models and the  one-vs-one models (again, just RF)
#ova_models = []
#ovo_models = {}
#for i in range(n_species):
#    
#    # first, load the one-vs-all
#    rfc_ova = path_sep.join([path_ova, '{} {}.pickle'.format(sp_unique[i], classifier)])
#    with open(rfc_ova, 'r') as f:
#        ova_models.append(pickle.load(f))
#    
#    # then loop through the other species for the one-vs-one
#    non_target_species = np.arange(n_species - (i + 1)) + (i + 1)
#    for j in non_target_species:
#        # set the path for the input files
#        sp_pair = "{}-{}".format(sp_unique[i], sp_unique[j])
#        rfc_ovo = path_sep.join([path_ovo, "{} {} model.pickle".format(sp_pair, classifier)])
#        with open(rfc_ovo, 'r') as f:
#            ovo_models[sp_pair] = pickle.load(f)

# set various options for saving / printing outputs
verbose = True
remove_outliers = False
plot_hist = False
plot_ova_cv = False
plot_ovo_cv = False
reduce_dims = True
tune_params = False
tune_ovo = False
use_transformed = True

#####
#
# Reading and preprocessing data
#
#####

test_hyp = pd.read_csv(path_test_hyp)
refl = np.array(test_hyp.loc[:,'band_1':])
crid = np.array(test_hyp.loc[:,'crown_id'])
hght = np.array(test_hyp.loc[:,'chm'])

# subset the reflectance data and transform it to the original data space
gb = misc_vars['gb']
refl = refl[:, gb]

if use_transformed:
    
    # transform the input data
    transformed = reducer.transform(refl)
    
    # then, remove outliers from these predictions
    if remove_outliers:
        
        if verbose:
            print("[ STATUS ]: Removing outliers from dataset")
        
        # we'll perform a PCA, just look through the first 20 or so components, and remove
        #  data points more than 3 stdv outside the mean
        mask = np.repeat(True, len(crid))
        n_components = transformed.shape[1]
        
        # since the data was whitened to unit variance, the stdv will be just 1
        std = 1
        
        # loop through each PC and maks out values > 4x std
        for i in range(n_components):
            outliers = np.where(abs(transformed[:, i]) > 4 * std)
            mask[outliers[0]] = False
            
        # finally, cull the data
        transformed = transformed[mask]
        crid = crid[mask]
        hght = hght[mask]
        
# ok, we should have (an outlier-removed set of) transformed spectra

#####
#
# Applying the final models
#
#####

# predict for the gbc and rfc models
pred_gbc = ovr_gbc.predict(transformed)
pred_rfc = ovr_rfc.predict(transformed)

# and for genus-level
pred_gbc_ge = gbc_ge.predict(transformed)
pred_rfc_ge = rfc_ge.predict(transformed)

# get the probabilities for each prediction
prob_gbc = ovr_gbc.predict_proba(transformed)
prob_rfc = ovr_rfc.predict_proba(transformed)

# and for genus-level
prob_gbc_ge = gbc_ge.predict_proba(transformed)
prob_rfc_ge = rfc_ge.predict_proba(transformed)

# plot the outputs
xbins = np.arange(n_species+1)
plt.hist(pred_gbc, bins=xbins -0.5, color = color_options['GBC'], 
    edgecolor='black', linewidth=1, orientation='horizontal', alpha=0.5, label='GBC')
plt.hist(pred_rfc, bins=xbins -0.5, color = color_options['RFC'], 
    edgecolor='black', linewidth=1, orientation='horizontal', alpha=0.5, label='RFC')
plt.yticks(xbins, sp_unique)#, rotation = 'vertical')
plt.xlabel('Count')
#plt.ylabel('Species')
plt.title('Number of samples identified per species')
plt.legend()
plt.tight_layout()
path_count = path_sep.join([path_plots, 'One-vs-one species counts.png'])
plt.savefig(path_count, dpi=300)
plt.close()

xbins = np.arange(n_genera+1)
plt.hist(pred_gbc_ge, bins=xbins -0.5, color = color_options['GBC'], 
    edgecolor='black', linewidth=1, orientation='horizontal', alpha=0.5, label='GBC')
plt.hist(pred_rfc_ge, bins=xbins -0.5, color = color_options['RFC'], 
    edgecolor='black', linewidth=1, orientation='horizontal', alpha=0.5, label='RFC')
plt.yticks(xbins, ge_unique)#, rotation = 'vertical')
plt.xlabel('Count')
plt.ylabel('Genus')
plt.title('Number of pixels identified per genus')
plt.legend()
plt.tight_layout()
path_count = path_sep.join([path_plots, 'One-vs-one genus counts.png'])
plt.savefig(path_count, dpi=300)
plt.close()

# plot out per-crown sp ID guesses
cr_unique = np.unique(crid)
for i in range(len(cr_unique)):
    cr_ind = np.where(crid == cr_unique[i])
    
    xbins = np.arange(n_species+1)
    plt.hist(pred_gbc[cr_ind[0]], bins=xbins -0.5, color = color_options['GBC'], 
        edgecolor='black', linewidth=1, orientation='horizontal', alpha=0.5, label='GBC')
    plt.hist(pred_rfc[cr_ind[0]], bins=xbins -0.5, color = color_options['RFC'], 
        edgecolor='black', linewidth=1, orientation='horizontal', alpha=0.5, label='RFC')
    plt.yticks(xbins, sp_unique)#, rotation = 'vertical')
    plt.xlabel('Count')
    plt.title('Crown ID: {:03d}'.format(cr_unique[i]))
    plt.legend()
    plt.tight_layout()
    
    # save the output
    path_crowns = path_sep.join([path_plots, 'crowns', 'crown-{:03d}.png'.format(cr_unique[i])])
    plt.savefig(path_crowns, dpi=300)
    plt.close()
    
    xbins = np.arange(n_genera+1)
    plt.hist(pred_gbc_ge[cr_ind[0]], bins=xbins -0.5, color = color_options['GBC'], 
        edgecolor='black', linewidth=1, orientation='horizontal', alpha=0.5, label='GBC')
    plt.hist(pred_rfc_ge[cr_ind[0]], bins=xbins -0.5, color = color_options['RFC'], 
        edgecolor='black', linewidth=1, orientation='horizontal', alpha=0.5, label='RFC')
    plt.yticks(xbins, ge_unique)#, rotation = 'vertical')
    plt.xlabel('Count')
    plt.title('Crown ID: {:03d}'.format(cr_unique[i]))
    plt.legend()
    plt.tight_layout()
    
    # save the output
    path_crowns = path_sep.join([path_plots, 'crowns', 'crown-{:03d}-genus.png'.format(cr_unique[i])])
    plt.savefig(path_crowns, dpi=300)
    plt.close()
    
# merge the results into a single array
crid_merged = np.append(crid, crid)
pred_merged = np.append(pred_gbc, pred_rfc)
prob_merged = np.append(prob_gbc, prob_rfc, axis=0)

# output per-crown guesses
cr_unique = np.unique(crid)
output_nr = len(cr_unique) * n_species
output_cr = np.zeros(output_nr, dtype=np.int16)
#output_id = np.zeros(output_nr, dtype=np.string0)
output_id = []
output_pr = np.zeros(output_nr, dtype=np.float32)

# just manually ad the species codes
sp_code = ['ACRU', 'LIST', 'OTHER', 'PIEL', 'PIPA', 'PITA', 'QUGE', 'QULA', 'QUNI']
for i in range(len(cr_unique)):
    cr_ind = np.where(crid_merged == cr_unique[i])
    
    # subset the crown predictions and probabilities
    cr_pred = pred_merged[cr_ind[0]]
    cr_prob = prob_merged[cr_ind[0]]
    
    # output the results to each array 
    output_cr[i * n_species:(i+1) * n_species] = np.repeat(cr_unique[i], n_species)
    #output_id[i * n_species:(i+1) * n_species] = sp_unique
    output_pr[i * n_species:(i+1) * n_species] = cr_prob.mean(axis=0)
    for sp in sp_code:
        output_id.append(sp)
        
# convert the output to a pandas dataframe and output
final_df = pd.DataFrame.from_items((('crown_id', output_cr), ('ID', output_id), 
    ('probability', output_pr)))
final_df.to_csv(pred_spp, index=False)

# and do for genus
# merge the results into a single array
crid_merged = np.append(crid, crid)
pred_merged = np.append(pred_gbc_ge, pred_rfc_ge)
prob_merged = np.append(prob_gbc_ge, prob_rfc_ge, axis=0)

# output per-crown guesses
cr_unique = np.unique(crid)
output_nr = len(cr_unique) * n_genera
output_cr = np.zeros(output_nr, dtype=np.int16)
#output_id = np.zeros(output_nr, dtype=np.string0)
output_id = []
output_pr = np.zeros(output_nr, dtype=np.float32)

# just manually ad the species codes
for i in range(len(cr_unique)):
    cr_ind = np.where(crid_merged == cr_unique[i])
    
    # subset the crown predictions and probabilities
    cr_pred = pred_merged[cr_ind[0]]
    cr_prob = prob_merged[cr_ind[0]]
    
    # output the results to each array 
    output_cr[i * n_genera:(i+1) * n_genera] = np.repeat(cr_unique[i], n_genera)
    #output_id[i * n_species:(i+1) * n_species] = sp_unique
    output_pr[i * n_genera:(i+1) * n_genera] = cr_prob.mean(axis=0)
    for ge in ge_unique:
        output_id.append(ge)
        
# convert the output to a pandas dataframe and output
final_df = pd.DataFrame.from_items((('crown_id', output_cr), ('ID', output_id), 
    ('probability', output_pr)))
final_df.to_csv(pred_gen, index=False)