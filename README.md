# brillouin-imaging Napari plugin 

## What is it?

*brillouin-imaging* is a napari plugin to work with brim (**Br**illouin **im**aging) files, containing spectral data and metadata from Brillouin microscopy.

More information about the scope and definition of the brim file format can be found [here](https://github.com/prevedel-lab/Brillouin-standard-file).

The brillouin-imaging plugin implements three contributions:
- *reader*  
Allows to open brim files by implementing the [reader contribution](https://napari.org/stable/plugins/building_a_plugin/guides.html#readers).

- *sample_data*  
Provides some sample Brillouin data through the [sample data contribution](https://napari.org/stable/plugins/building_a_plugin/guides.html#sample-data). These are hosted

- *Spectra Analysis Tools widget*  
View metadata, inspect individual spectra, create images based on the AUC of the PSD, use label layer to calculate average Brillouin spectra and statistics for annotated or segmented regions.


## How to install it

*brillouin-imaging* can be installed from the napari plugin manager, as any standard napari plugin. More info can be found [here](https://napari.org/stable/plugins/start_using_plugins/finding_and_installing_plugins.html).
