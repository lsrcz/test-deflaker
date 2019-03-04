#!/bin/bash

awk -F"\"" '{ if($2 == "ninja") print $4}' historical_project_versions.csv | xargs -t  -n 1 -I{} ./ninjarun.sh {}
