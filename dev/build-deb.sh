#!/bin/bash

echo 'Version: '
read ver

./chver.sh $ver
cd ../../
cp -r manpages-cpp manpages-cpp-$ver
mv manpages-cpp-$ver manpages-cpp/dev
cd manpages-cpp/dev/
tar -zcf manpages-cpp_$ver.orig.tar.gz manpages-cpp-$ver

cd manpages-cpp-$ver
dh_make -s -b

echo `pwd`
cp dev/rules dev/control debian
cd debian
rm *.ex *.EX README.*
cd ..
dpkg-buildpackage -rfakeroot
