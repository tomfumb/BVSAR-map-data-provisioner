#!/bin/bash

# hard-code 093L area during development / testing, eventually swap-out for user input
mkdir $TILE_INPUT/093L/20000 && pushd $TILE_INPUT/093L/20000
wget -O 093L.html https://pub.data.gov.bc.ca/datasets/177864/tif/utm09/093l/
grep -o '"093L[0-9][0-9][0-9].zip"' 093L.html | sed  s'/"//g' | xargs -I {} wget https://pub.data.gov.bc.ca/datasets/177864/tif/utm09/093l/{}
rm 093L.html
ls -1 *.zip | xargs -I {} unzip {}
rm *.zip
rm *.txt
rm *.tfw

# gdal_merge
# $GDAL_SCRIPTS/gdal_merge.py -o merge.tif -n 0 093L001.tif 093L002.tif 093L003.tif 093L004.tif 093L005.tif 093L006.tif 093L007.tif 093L008.tif 093L009.tif 093L010.tif 093L011.tif 093L012.tif 093L013.tif 093L014.tif 093L015.tif 093L016.tif 093L017.tif 093L018.tif 093L019.tif 093L020.tif 093L021.tif 093L022.tif 093L023.tif 093L024.tif 093L025.tif 093L026.tif 093L027.tif 093L028.tif 093L029.tif 093L030.tif 093L031.tif 093L032.tif 093L033.tif 093L034.tif 093L035.tif 093L036.tif 093L037.tif 093L038.tif 093L039.tif 093L040.tif 093L041.tif 093L042.tif 093L043.tif 093L044.tif 093L045.tif 093L046.tif 093L047.tif 093L048.tif 093L049.tif 093L050.tif 093L051.tif 093L052.tif 093L053.tif 093L054.tif 093L055.tif 093L056.tif 093L057.tif 093L058.tif 093L059.tif 093L060.tif 093L061.tif 093L062.tif 093L063.tif 093L064.tif 093L065.tif 093L066.tif 093L067.tif 093L068.tif 093L069.tif 093L070.tif 093L071.tif 093L072.tif 093L073.tif 093L074.tif 093L075.tif 093L076.tif 093L077.tif 093L078.tif 093L079.tif 093L080.tif 093L081.tif 093L082.tif 093L083.tif 093L084.tif 093L085.tif 093L086.tif 093L087.tif 093L088.tif 093L089.tif 093L090.tif 093L091.tif 093L092.tif 093L093.tif 093L094.tif 093L095.tif 093L096.tif 093L097.tif 093L098.tif 093L099.tif 093L100.tif
