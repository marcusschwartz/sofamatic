#!/bin/sh

BASE=`dirname $0`

while /bin/true; do
	$BASE/sofamatic.py >/dev/null 2>&1
done
