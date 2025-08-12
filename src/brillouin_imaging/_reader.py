"""
This module is an example of a barebones numpy reader plugin for napari.

It implements the Reader specification, but your plugin may choose to
implement multiple readers or even other plugin contributions. see:
https://napari.org/stable/plugins/building_a_plugin/guides.html#readers
"""
import napari.layers
import numpy as np
import os

import napari
from napari.utils.notifications import show_info

from magicgui.widgets import ComboBox, PushButton, Container

import brimfile as brim


def napari_get_reader(path):
    """A basic implementation of a Reader contribution.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    function or None
        If the path is a recognized format, return a function that accepts the
        same path or list of paths, and returns a list of layer data tuples.
    """
    if isinstance(path, list):
        # reader plugins may be handed single path, or a list of paths.
        # the current version of the plugin only handles single files 
        show_info("Only single files are supported")
        return None

    # if we know we cannot read the file, we immediately return None.
    if path.endswith(".brim.zarr"):
        if not os.path.isdir(path):
            return None
    elif not path.endswith(".brim.zip"):
        return None    
    
    try:
        brim.File(path)
    except Exception as e:
        # if we cannot read the file, we return None.
        show_info(f"Cannot read {path} as a brim file: {e}")
        return None

    # otherwise we return the *function* that can read ``path``.
    return reader_function


def reader_function(path):
    """Take a path and show the widget to load the data.

    Parameters
    ----------
    path : str 
        Path to file

    Returns
    -------
    layer_data : list of tuples
        A list of LayerData tuples where each tuple in the list contains
        (data, metadata, layer_type), where data is a numpy array, metadata is
        a dict of keyword arguments for the corresponding viewer.add_* method
        in napari, and layer_type is a lower-case string naming the type of
        layer. Both "meta", and "layer_type" are optional. napari will
        default to layer_type=="image" if not provided
    """

    # show a widget to load the data, as suggested here: https://forum.image.sc/t/access-napari-viewer-and-launch-from-reader-plugin/88759    
    viewer = napari.current_viewer()

    file = brim.File(path)

    brim_load_widget = create_brim_widget(file)
    dock_widget = viewer.window.add_dock_widget(brim_load_widget, name="brim file loader", area="right")

    #trigger the data_combo changed event to update the controller
    brim_load_widget.data_groups.changed.emit(None)

    # Register a callback for when the widget is closed
    def on_widget_closed(*args, **kwargs):
        print("brim widget closed")
        file.close()    
    dock_widget.destroyed.connect(on_widget_closed)

    #The widget will take care of loading the relevant images, so return None
    return [(None,)]


def create_brim_widget(file: brim.File):
    data_groups = file.list_data_groups(retrieve_custom_name=True)
    dt_names = [x['custom_name'] for x in data_groups]
    ar_groups = []
    peak_types_choices = ('average', 'AntiStokes', 'Stokes')
    
    # Create individual controls
    data_combo = ComboBox(label="Data group", name="data_groups", choices=dt_names)
    analysis_results_combo = ComboBox(label="Analysis results", choices=[])
    quantity_combo = ComboBox(label="Quantity", choices=[])
    peak_types_combo = ComboBox(label="Peak type", choices=peak_types_choices)
    add_image_btn = PushButton(text="Add image")

    def get_current_data_group() -> brim.Data:
        selected_value = data_combo.value
        data_index = data_combo.choices.index(selected_value)
        data_index = data_groups[data_index]["index"]
        d = file.get_data(data_index)
        return d
    def get_current_analysis_results_index() -> int:
        selected_value = analysis_results_combo.value
        ar_index = analysis_results_combo.choices.index(selected_value)
        return ar_index

    def on_data_change(event):
        nonlocal ar_groups
        ar_groups = get_current_data_group().list_AnalysisResults()
        ar_list = [x["name"] for x in ar_groups]
        analysis_results_combo.choices = ar_list
        #trigger the analysis_results_combo changed event to update the controller
        analysis_results_combo.changed.emit(None)
    
    def on_analysis_results_change(event):
        d = get_current_data_group()
        ar = d.get_analysis_results(get_current_analysis_results_index())

        as_cls = brim.Data.AnalysisResults
        qts_aS = ar.list_existing_quantities(as_cls.PeakType.AntiStokes)
        qts_S = ar.list_existing_quantities(as_cls.PeakType.Stokes)
        qts = tuple(set(qts_aS) | set(qts_S))

        quantity_combo.choices = qts
        #trigger the on_quantity changed event
        quantity_combo.changed.emit(None)

    def on_quantity_change(event):
        d = get_current_data_group()
        ar = d.get_analysis_results(get_current_analysis_results_index())

        pt_cls = brim.Data.AnalysisResults.PeakType
        pt = ar.list_existing_peak_types()
        if len(pt)>1:
            peak_types_combo.choices = peak_types_choices
        elif pt[0] == pt_cls.AntiStokes:
            peak_types_combo.choices = [peak_types_choices[1],]
        elif pt[0] == pt_cls.Stokes:
            peak_types_combo.choices = [peak_types_choices[2],]
        else:
            raise ValueError(f"{pt[0]} is not a valid PeakType")
   
    def on_add_image_btn_pressed(event):
        d = get_current_data_group()
        ar = d.get_analysis_results(get_current_analysis_results_index())

        pt_cls = brim.Data.AnalysisResults.PeakType
        img = None
        px_size = None
        c_pt = peak_types_combo.value
        if c_pt == peak_types_choices[0]:
            img, px_size = ar.get_image(quantity_combo.value, pt_cls.average)
        elif c_pt == peak_types_choices[1]:
            img, px_size = ar.get_image(quantity_combo.value, pt_cls.AntiStokes)
        elif c_pt == peak_types_choices[2]:
            img, px_size = ar.get_image(quantity_combo.value, pt_cls.Stokes)
        else:
            raise ValueError(f"{peak_types_combo.value} is not a valid choice")        
        
        scale = tuple(x.value for x in px_size)

        napari.current_viewer().add_layer(
            napari.layers.Image(img, name=str(quantity_combo.value), scale=scale, units=px_size[0].units)
        )

        #trigger the data_combo changed event to reinitialize the widget
        #TODO understand why some of the combos go blank after pressing the button and thus it is necessary to reinitialize
        data_combo.changed.emit(None)

    # Connect callbacks
    data_combo.changed.connect(on_data_change)
    analysis_results_combo.changed.connect(on_analysis_results_change)
    quantity_combo.changed.connect(on_quantity_change)
    add_image_btn.changed.connect(on_add_image_btn_pressed)     

    # Combine controls into a container
    container = Container(widgets=[data_combo, analysis_results_combo, quantity_combo, peak_types_combo, add_image_btn])

    return container

