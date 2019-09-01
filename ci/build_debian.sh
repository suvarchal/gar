# install dependencies
sudo apt-get update -q
sudo apt-get install fakeroot -y 
sudo apt-get install debhelper -y
sudo apt-get install dh-python -y
sudo apt-get install devscripts -y
sudo apt-get install python3 -y
sudo apt-get install python3-setuptools -y
sudo apt-get install python3-pytest -y

# change changelog
export DEBEMAIL="suvarchal.kumar@gmail.com"
export DEBFULLNAME="Suvarchal K. Cheedela"
dch --package "gar" --create -v ${TRAVIS_TAG#"v"} -D stable "upstream release"

# build source and binary
debuild -us -uc -I -i
