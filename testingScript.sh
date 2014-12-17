#!/bin/bash

source /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/5.6.2/init/bash
module load xrootd/4.1.1 2>&1
echo "Loaded XRootD"
source ./setStashCache.sh
bash ./stashcp $1 $2 