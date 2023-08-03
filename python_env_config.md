James Telzrow \
Warburton Lab \
2023-07-19 \
PyCDFT Driver Development Environment Configuration

## Introduction

This document describes how to set up a development environment to work on the PyCDFT driver for Quantum ESPRESSO.

### Loading Modules

In the Warburton Lab, we don't run simulations within a virtualenv.
Rather, we load the Python modules/packages we need using [Environment Modules](https://modules.sourceforge.net), and then run them using a Python interpreter also provided by Environment Modules.

But by default when one logs into a compute node, several modules 
must be used, unused, or loaded in order to use ASE and Quantum ESPRESSO, and we need them in order to work on the driver PyCDFT Driver for Quantum ESPRESSO. The commands that must be run are listed below: (taken from Professor Warburton's example ase_qe.slurm file)

```
module unuse /usr/local/easybuild_allnodes/modules/all
module use /usr/local/easybuild_icosa/modules/all
module load QuantumESPRESSO/6.8-foss-2021b
module load Python
module load SciPy-bundle/2022.05-foss-2022a
module load matplotlib
```

### Setting up Development Environment from Scratch on CWRU HPC Cluster

To set up a development environment from scratch in your home directory on the CWRU HPC Cluster, start by creating a new directory for the project:
```
mkdir -p $HOME/pycdft_driver_qe
```
Then create a new directory in which several dependencies of PyCDFT (which are not available as environment modules) can be installed as user packages:
```
mkdir -p $HOME/pycdft_driver_qe/deps
```
Then, set the `PYTHONUSERBASE` environment variable so that the Python interpreter can find the packages we will install in the directory we just created, by adding the following lines to `~/.bash_profile`
```
PYTHONUSERBASE=$HOME/pycdft_driver_qe/deps
export PYTHONUSERBASE
```
and then running
```
source ~/.bash_profile
```
so that the changes take effect.

Then get and install PyCDFT from source as an editable package: (as well as several unsatisfied dependencies as non-editable packages)
```
python3 -m pip install --user -e git+https://github.com/hema-ted/pycdft.git#egg=pycdft
```
We install PyCDFT in editable mode so that we can easily make changes to it if necessary.

### Remote Development on CWRU HPC Cluster using VSCode with Remote - SSH Extension

VSCode's [remote development](https://code.visualstudio.com/docs/remote/troubleshooting#_extension-tips) capabilities can make developing code on the HPC cluster significantly easier by allowing us to use VSCode's IntelliSense, debugging and linting capabilities right on the cluster.

To do this, you must first install the [Remote - SSH](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh) extension for VSCode.

Additionally, if you haven't already, you should add the five `module` commands given at the beginning of this tutorial to your `~/.bash_profile` file so that VSCode will discover the correct Python interpreter automatically when connecting to the HPC. After modifying your `~/.bash_profile`, you may need to log out of shell sessions or run `source ~/.bash_profile` so that your changes take  effect.

Then log into the HPC cluster, and create a new interactive job on a compute node: (Note: you **must** develop on a compute node, **not** a login node. Otherwise, you could seriously inconvenience everybody else trying to use the cluster.)

```
srun --pty --constraint icosa256gb -N 1 -n 40 --mem=0 /bin/bash
```

The options that we pass to this command are important; if they are  omitted, your code may crash. The `--constraint` option specifies which type of node we wish to use, the `-N` option specifies the number of nodes we wish to use, the `-n` option specifies the number of tasks to run, and `--mem=0` requests all available memory on the node.

Once the job starts and you are automatically connected to the compute node, get its IP address:
```
hostname -i
```
And then on your machine, (not the cluster) set up port forwarding from localhost port 4000 (on your machine) to port 22 on the compute node (in the HPC cluster) via a login node:
```
(on your machine) ssh -L 4000:{compute node's IP}:22 {your CWRU network ID here}@pioneer.case.edu
```
Then, open VSCode, open the "Remote Explorer" menu, click the "+" button to create a new SSH remote, and enter the command
```
ssh {your CWRU network ID here}@localhost -p 4000
```
and enter your CWRU network password when prompted to do so.

Then, open the "Explorer" menu, click "Open Folder", and enter the path
```
/home/{your CWRU network ID here}/pycdft_driver_qe
```
and enter your password again when prompted.

Finally, install the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) for VSCode.

You are now connected and ready to develop on the HPC cluster using VSCode.

When finished developing, one may want to remove the VSCode server (which VSCode installs and runs when you connect to the cluster for the first time) from the cluster using the [Cleaning up the VS Code Server on the remote](https://code.visualstudio.com/docs/remote/troubleshooting#_extension-tips) instructions.