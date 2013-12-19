#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "Please supply a valid handle."
    exit 0
elif [ $# -eq 1 ]
 then
    echo "Gathering top 20 trends for @$1."
    python fetchTweets.py $1
    python processTweets.py $1 20
    exit 0
else
    if ! [[ $2 != *[!0-9]* ]] ; then
      echo "Error: $2 is not a number"
      exit 1
    fi
    echo "Gathering top $2 trends for @$1."
    python fetchTweets.py $1
    python processTweets.py $1 $2
    exit 1
fi