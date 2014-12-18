#!/usr/bin/env bash

#SBATCH --qos=express
#SBATCH --job-name=%TASK%
#SBATCH --output=%ECF_OUT%%ECF_NAME%.%ECF_TRYNO%
#SBATCH --error=%ECF_OUT%%ECF_NAME%.%ECF_TRYNO%
#SBATCH --time=00:15:00