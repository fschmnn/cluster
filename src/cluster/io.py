import numpy as np
from pathlib import Path 
from astropy.io import fits
from astropy.nddata import NDData
from astropy.wcs import WCS 
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u 

def read_associations(folder,target,scalepc,HSTband='nuv',version='v1p1',data='all'):
    '''read the catalogue and spatial mask for the associations
    
    Parameters
    ----------

    folder : pathlib.Path object
            the parent folder (HST/)
    
    target : string
            the name of the target
    
    scalepc : float
    
    HSTband : string (nuv/v)

    version : string

    data : string
        'all', 'catalogue', 'mask'
    '''
    
    folder = folder/f'associations {version}'/'multi-scale stellar associations'
    
    # define basefolder and check if file exists 
    if not (folder/target).is_dir():
        print(f'target not available. Use\n{",".join([x.stem for x in folder.iterdir()])}')
        raise FileNotFoundError
    target_folder = folder/target/f'{target}_{HSTband}_tracerstars'
    if not (target_folder/f'{scalepc}pc').is_dir():
        print(f'scalepc={scalepc} not available. Use:')
        print([int(x.stem[:-2]) for x in target_folder.iterdir() if x.stem.endswith('pc')])
        raise FileNotFoundError
    folder = target_folder/f'{scalepc}pc'

    if data=='all' or data=='catalogue':
        # first the association catalogue
        catalogue_file = folder / f'{target}_phangshst_associations_{HSTband}_ws{scalepc}pc_{version}.fits'
        with fits.open(catalogue_file) as hdul:
            associations = Table(hdul[1].data)

        # modify table (rename the columns such that the clusters and associations are identical)
        associations['SkyCoord'] = SkyCoord(associations['reg_ra']*u.degree,associations['reg_dec']*u.degree)
        associations.rename_columns(['reg_id','reg_ra','reg_dec','reg_x','reg_y',
                                    'reg_dolflux_Age_MinChiSq','reg_dolflux_Mass_MinChiSq','reg_dolflux_Ebv_MinChiSq',
                                    'reg_dolflux_Age_MinChiSq_err','reg_dolflux_Mass_MinChiSq_err','reg_dolflux_Ebv_MinChiSq_err'],
                                    ['assoc_ID','RA','DEC','X','Y','age','mass','EBV','age_err','mass_err','EBV_err'])
        for col in list(associations.columns):
            if col.endswith('mjy'):
                associations[f'{col.split("_")[0]}_FLUX'] = 1e20*associations[col]*u.mJy.to(u.erg/u.s/u.cm**2/u.Hz)
            if col.endswith('mjy_err'):
                associations[f'{col.split("_")[0]}_FLUX_ERR'] = 1e20*associations[col]*u.mJy.to(u.erg/u.s/u.cm**2/u.Hz)



        if data=='catalogue':
            return associations

    if data=='all' or data=='mask':
        # next the spatial masks for the associations
        mask_file = folder / f'{target}_phangshst_associations_{HSTband}_ws{scalepc}pc_idmask_{version}.fits'
        with fits.open(mask_file) as hdul:
            mask = hdul[0].data.astype(float)
            mask[mask==0] = np.nan
            associations_mask = NDData(mask,
                                    mask=mask==0,
                                    meta=hdul[0].header,
                                    wcs=WCS(hdul[0].header))
        if data=='mask':
            return associations_mask

    return associations, associations_mask
