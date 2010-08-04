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
dh_make -s -b -p manpages-cpp

cp dev/rules dev/control debian
cd debian
rm *.ex *.EX README.*
dch -e
cd ..

if [ "$1" == "deb" ]; then
  dpkg-buildpackage -rfakeroot
elif [ "$1" == "ppa" ]; then
  debuild -S
fi
