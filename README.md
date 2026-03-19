# brillouin-imaging Napari plugin 

## What is it?

*brillouin-imaging* is a napari plugin to work with brim (**Br**illouin **im**aging) files, containing spectral data and metadata from Brillouin microscopy.

More information about the scope and definition of the brim file format can be found [here](https://github.com/prevedel-lab/Brillouin-standard-file).

The brillouin-imaging plugin implements three contributions:
- *reader*  
Allows to open brim files by implementing the [reader contribution](https://napari.org/stable/plugins/building_a_plugin/guides.html#readers).

- *sample_data*  
Provides some sample Brillouin data through the [sample data contribution](https://napari.org/stable/plugins/building_a_plugin/guides.html#sample-data). Data are hosted on a S3 bucket. 

- *Spectra Analysis Tools widget*  
Inspetion and analysis tools by adding the [widget contribution](https://napari.org/stable/plugins/building_a_plugin/guides.html#widgets). One can view metadata, inspect individual spectra, create images based on the AUC of the PSD, and use a labels layer to calculate average Brillouin spectra and statistics for annotated or segmented regions.

Example Screenshot of the Spectra Analysis Tools widget displaying the metadata of the opened drosophila_LSBM sample data: 

<img width="800" height="470" alt="brillouin-imaging-napari-screenshot" src="https://raw.githubusercontent.com/prevedel-lab/brillouin-imaging-napari/main/images/brillouin-imaging-napari-screenshot.png"/>

## How to install it

*brillouin-imaging* can be installed from the napari plugin manager, as any standard napari plugin. More info can be found [here](https://napari.org/stable/plugins/start_using_plugins/finding_and_installing_plugins.html).
