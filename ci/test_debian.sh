TAG=${TRAVIS_TAG#"v"}
cwd=`pwd`
cd ci
cp ../../python3-gar_${TAG}_all.deb python3-gar_${TAG}_all.deb
#docker build --build-arg TAG=${TAG} --tag=buster . --target=buster

#docker build --build-arg TAG=${TAG} --tag=bullseye . --target=bullseye 

#docker build --build-arg TAG=${TAG} --tag=bionic . --target=bionic

cd $cwd
