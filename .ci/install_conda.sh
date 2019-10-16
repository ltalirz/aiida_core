#!/bin/bash
# See https://conda.io/docs/user-guide/tasks/use-conda-with-travis-ci.html#the-travis-yml-file
if [[ "$TRAVIS_PYTHON_VERSION" == "2.7" ]]; then
  wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh -O miniconda.sh;
else
  wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh;
fi
bash miniconda.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"
hash -r
conda config --set always_yes yes --set changeps1 no
# --force-reinstall flag needed, see https://superuser.com/a/1407358/345438
conda update -q --force-reinstall conda
# Useful for debugging any issues with conda
conda info -a
