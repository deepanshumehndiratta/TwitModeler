#!/bin/bash

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root" 1>&2
  exit 1
fi

sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install ant mercurial openjdk-7-jdk -y
hg clone http://hg-iesl.cs.umass.edu/hg/mallet
cd mallet
ant