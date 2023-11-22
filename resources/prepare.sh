#!/bin/bash

set -ex

here=$(dirname "$0")

get_tesseract_models() {
    mkdir -p "$here/downloads/tessdata"
    pushd "$here/downloads/tessdata"
    curl --location -o mrz.traineddata \
        https://github.com/DoubangoTelecom/tesseractMRZ/raw/master/tessdata_best/mrz.traineddata
}

get_tesseract_models
