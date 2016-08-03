#!/bin/bash

# sensor21 install script
#
# This script will help install dependencies for sensor21. It also
# sets up the SQLite database to abstract the low level hardware
# communications from server requests to eliminate bus collisions.

### List of packages to install
declare -a APT_PACKAGES=("python3-pip" "boinc-client")
declare -a PIP3_PACKAGES=("flask" "click" "PyYAML" "requests" "psutil" "pexpect")

# Helper functions: bash pretty printing, pip3 and apt-get package
# installers / uninstallers

# Pretty print helper functions
# Print program step + text coloring
print_step() {
    printf "\n\e[1;35m $1\e[0m\n"
}

# Print program error + text coloring
print_error() {
    printf "\n\e[1;31mError: $1\e[0m\n"
}

# Print program warning + text coloring
print_warning() {
    printf "\e[1;33m$1\e[0m\n"
}

# Print program good response + text coloring
print_good() {
    printf "\e[1;32m$1\e[0m\n"
}

# Program installation functions
# Check to see if a program exists on the local machine
program_exists() {
    if ! type "$1" > /dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Check to see if a pip3 package exists
pip_package_exists() {
	python3 -c "import $1" 2> /dev/null && return 0 || return 1
}

# Install apt packages
apt_installer() {
	if ! program_exists $1; then
		print_warning "Installing $1."
		sudo apt-get --force-yes --yes install $1
	else
		print_good "$1 installed."
	fi
}

# Install pip3 modules
pip3_installer() {
	# fix for python-periphery pip3 install vs package name
	if [ "$1" = "python-periphery" ]; then
		var="periphery"
		if ! pip_package_exists $var; then
			print_warning "Installing $1."
			sudo pip3 install $1
		else
			print_good "$1 installed."
		fi
	else
		if ! pip_package_exists $1; then
			print_warning "Installing $1."
			sudo pip3 install $1
		else
			print_good "$1 installed."
		fi
	fi
}

### Main program execution
print_good "Welcome to AlienSearchE16 installer!"

echo ""

## Overwrite path with present working directory.
print_warning "Gathering present working directory for AlienSearchE16."
print_warning "If you move TrancodeE16 to another folder, you must manually edit sqldb.py and update paths to your present working directory."

## Update apt-get package list
print_step "updating package list"
sudo apt-get update
echo ""

## Install prerequisites
print_step "checking/installing prerequisites"

# Loop through apt packages array and check if present, then install if not.
for var in "${APT_PACKAGES[@]}"
do
	# fix for pip3 install vs package name
	if [ "$var" = "python3-pip" ]; then
		var="pip3"
	fi
	apt_installer $var
done

# Loop through pip3 packages array and check if present, then install if not.
for var in "${PIP3_PACKAGES[@]}"
do
	pip3_installer $var
done

print_good "Prerequisites installed."

print_step "Setting up BOINC/SETI"

# Set up the SETI project - replace the key with your own here if you like
boinccmd --project_attach http://setiathome.berkeley.edu 10351529_9b9c95b7b79ab3f58c2dcc7156b5d8ac

# Stop the service and set it to only use 50% CPU in the config
sudo service boinc-client stop
sudo cp ./global_prefs_override.xml /var/lib/boinc-client/global_prefs_override.xml
sudo service boinc-client start

## Success!!!
print_good "Install complete."

echo ""

## Set up 21 account
print_good "Now running 21 status to verify user & wallet creation."
print_warning "If you have not signed up for an account yet, go to https://21.co/signup/"

21 status
