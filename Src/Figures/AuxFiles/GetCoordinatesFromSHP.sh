#!/bin/bash
SHP_IN=$1
ASCII_OUT=$2

rm tmp.csv
ogr2ogr -f "CSV" tmp.csv ${SHP_IN} -lco GEOMETRY=AS_WKT
cat tmp.csv|\
sed '1d'| sed 's/"LINESTRING (//' | sed 's/)",1//' | tr ',' '\n' > ${ASCII_OUT}

