FROM debian:latest

COPY do-install.sh /opt/tools/do-install.sh

RUN /opt/tools/do-install.sh first

COPY packages_from_apt.py /opt/tools/packages_from_apt.py

RUN \
	apt-get install -y python3-apt python3-ruamel.yaml \
	&& apt-get install -y \
		gettext \
		pkgconf libncurses-dev libreadline-dev libssl-dev \
		rsync m4 autoconf automake flex bison ninja-build \
		libexpat1-dev libxerces-c-dev libxml2-dev libpcre3-dev \
		libzmq3-dev libmsgpack-dev \
		zlib1g-dev liblzma-dev libbz2-dev liblz4-dev libzstd-dev \
		libxxhash-dev \
		libgdbm-dev libsqlite3-dev \
		xcb-proto libxau-dev libxcb1-dev libx11-dev \
		libsm-dev libice-dev \
		libxext-dev libxrender-dev \
		libfontconfig1-dev libfreetype6-dev libxft-dev \
		libgl1-mesa-dev libglu1-mesa-dev libglew-dev \
		libftgl-dev \
		libxpm-dev libjpeg62-turbo-dev \
		davix-dev \
		libpmix-dev libffi-dev \
		libgsl-dev libopenblas-dev \
	&& mkdir -p /etc/spack \
	&& /opt/tools/packages_from_apt.py -o /etc/spack/packages.yaml \
	&& sleep 5

RUN /opt/tools/do-install.sh second

CMD ["bash", "-l"]
