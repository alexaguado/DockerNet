#!/bin/bash

ALL="$(ip link show | grep _l | awk '{print $2}' | xargs echo | tr -d :)"

UP="$(ip link show | grep _l | grep UP | awk '{print $2}' | xargs echo | tr -d :)"

#echo $ALL
#echo $UP

for id in $ALL; do
   if [[ $UP == *$id* ]]
   then
      echo "$id ok"
   else
      echo "$id seems down"
   fi
done
