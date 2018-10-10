#!/bin/bash

TREEISH=master
VERSION=0.8.0

git archive --format=tar.gz ${TREEISH} rastervision_qgis/ > rastervision_qgis-v${VERSION}.tar.gz
git archive --format=zip ${TREEISH} rastervision_qgis/ > rastervision_qgis-v${VERSION}.zip
