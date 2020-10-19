#! /bin/bash

set -x -e

function first() {
	apt-get update && apt-get dist-upgrade -y
	apt-get install -y git python3 build-essential gfortran curl unzip
	mkdir -p /opt/spack/install-tree
	cd /opt && git clone --branch dev https://github.com/FairRootGroup/FairSoft
	cd /opt/FairSoft
	. ./thisfairsoft.sh --setup
	cd spack
	# See: https://github.com/spack/spack/pull/17427
	curl 'https://github.com/spack/spack/commit/2b809a537469b39e44080d33899e6b0756956309.patch' \
		| patch -p1

	cat >etc/spack/config.yaml <<EOF
config:
  install_tree: /opt/spack/install-tree
EOF
	echo "source /opt/FairSoft/thisfairsoft.sh" > /etc/profile.d/90fairsoft.sh
}

function second() {
	cd /opt/FairSoft
	. ./thisfairsoft.sh --setup
	spack env create escape env/dev/sim/spack.yaml
	spack env activate escape
	spack install --fail-fast
}

case "$1" in
	first)
		first
		;;
	second)
		second
		;;
esac
