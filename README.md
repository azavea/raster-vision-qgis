# Raster Vision QGIS Plugin

This plugin allows you to work with [Raster Vision](https://github.com/azavea/raster-vision) in QGIS
to view experiment results  and predict against imagery.

Table of Contents:
- [Installation](#installation)
- [Loading Experiments](#loading-experiments)
- [Prediction](#prediction)
- [Style Profiles](#prediction)
- [Configuration](#prediction)
- [Tutorial: View SpaceNet Building Chip Classification](#tutorial-view-spacenet-building-chip-classification)
- [Developing](#developing)


## Installation

TODO

## Load Experiments

Load an experiment by providing the `experiment_uri`.
Optionally select a style profile.

TODO

## Prediction

TODO

## Style Profiles

Set up style profiles so that when you load an experiment, layers are automatically styled with given SLDs.

The best way to do this is to styl each of the types of layers you want after first loading an experiment. Export an SLD of style for each layer by using the `Style` -> `Save Style` command in the `Symbology` section of the layer properties. Then, create a style profile for that experiment group, and point it to the appropriate SLD files. Now you'll be able to select the style profile when loading new experiments and making predictions.

## Configure

Configure the plugin with a working directory and an AWS profile (option, it will use your default profile if none is specified).  If the files live on S3, this plugin will download files as necessary to your local working directory. If the file already exists in the working directory, the plugin will check the timestamps and overwrite the local file if the file on S3 is newer.

### Using with AWS

You'll need to set your AWS_PROFILE in the QGIS environment if you're not using the defaul profile.

### Using with docker

To run predict through docker, make sure that the docker command is on the `PATH` environment variable used  by docker.

## Tutorial: View SpaceNet Building Chip Classification

TODO

![QGIS results explorer](img/qgis-spacenet-cc.png)

## Developing

Link the repo directory into your QGIS plugin directory. I use the [Plugin Reloader](https://github.com/borysiasty/plugin_reloader) to reload for testing.

e.g., on Mac OSX:
```
ln -s `pwd`/rastervision_qgis  /Users/rob/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/
```

I'm using QT Creator to design the dialog UIs. Just drag over the `*.ui` files into QT Creator and it should open up the design component, where you can move things around, add controls, rename items, etc.

To compile the resources, run

```
pyrcc5 -o resources.py resources.qrc
```
