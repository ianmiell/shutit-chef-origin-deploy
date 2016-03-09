
# Overview

ShutIt script to deploy origin using Chef onto a centos7 Vagrant/Virtualbox VM.

# To run

```
# Assumes python-pip installed, eg apt-get install python-pip
# Wise (but not required) to have vagrant and virtualbox installed
pip install shutit
git clone https://github.com/ianmiell/shutit-chef-origin-deploy
cd shutit-chef-origin-deploy
git submodule init 
git submodule update
shutit -d bash -m shutit-library build
```
