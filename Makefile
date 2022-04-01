docker_py_vers := 5.0.3
websocket_vers := 0.58.0
tar_dirs := bin lib

all: download extract build

devel: download extract

clean:
	rm -f cache/
	rm -f check-docker.tar.gz
	rm -rf lib/
	rm -f sha512sum.txt

download:
	mkdir cache || true
	wget -q -O cache/docker-py-$(docker_py_vers).tar.gz https://github.com/docker/docker-py/archive/refs/tags/$(docker_py_vers).tar.gz
	wget -q -O cache/websocket-client-$(websocket_vers).tar.gz https://github.com/websocket-client/websocket-client/archive/refs/tags/v$(websocket_vers).tar.gz

extract: cache/docker-py-$(docker_py_vers).tar.gz cache/websocket-client-$(websocket_vers).tar.gz
	mkdir lib || true
	tar --strip 1 -C lib -xzvf cache/docker-py-$(docker_py_vers).tar.gz docker-py-$(docker_py_vers)/docker
	tar --strip 1 -C lib -xzvf cache/websocket-client-$(websocket_vers).tar.gz websocket-client-$(websocket_vers)/websocket

build: lib/docker lib/websocket
	tar --exclude .git -czvf check-docker.tar.gz $(tar_dirs)
	sha512sum check-docker.tar.gz | tee sha512sum.txt
