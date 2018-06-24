# Raster Vision QGIS Plugin

This plugin allows you to see experiment results from [Raster Vision](https://github.com/azavea/raster-vision) in QGIS.

This plugin was initialized with [QGIS Plugin Builder](http://g-sherman.github.io/Qgis-Plugin-Builder/).

## How it works

Configure the plugin with a working directory and an AWS profile (option, it will use your default profile if none is specified). Then, load an experiment by providing the `rv_root` and workflow JSON URI. These can be local or on S3. If the files live on S3, this plugin will download files as necessary to your local working directory. If the file already exists in the working directory, the plugin will check the timestamps and overwrite the local file if the file on S3 is newer.

## Developing

Link the repo directory into your QGIS plugin directory. I use the [Plugin Reloader](https://github.com/borysiasty/plugin_reloader) to reload for testing.

e.g., on Mac OSX:
```
ln -s `pwd`/raster-vision-qgis  /Users/rob/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/
```

I'm using QT Creator to design the dialog UIs. Just drag over the `*.ui` files into QT Creator and it should open up the design component, where you can move things around, add controls, rename items, etc.
