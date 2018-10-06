# Raster Vision QGIS Plugin

This plugin works with [Raster Vision](https://github.com/azavea/raster-vision) in QGIS
to view experiment results and predict against imagery.

See https://readthedocs.org/projects/raster-vision/qgis usage for documentation.

See https://github.com/azavea/raster-vision-examples for examples of using the Raster Vision QGIS plugin in
deep learning model building workflows.

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
pyrcc5 -o rastervision_qgis/resources.py rastervision_qgis/resources.qrc
```
