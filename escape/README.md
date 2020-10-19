
## Intro

This is basically a Debian-10 with FairSoft (spack edition)
and the "dev" 'distro' (environment).


### X11 Forwarding

If your docker isn't configured with "user namespaces" for
security, then it's quite okay:

```
$ docker run -it --rm --network=host -e DISPLAY -v $HOME/.Xauthority:/root/.Xauthority:ro -v /tmp/.X11-unix:/tmp/.X11-unix escape:latest
```

Some short explanation:
* `--network=host`: Let docker have access to the localhost interface (`ssh -X` listens there)
* `-e DISPLAY`: Forward the DISPLAY environment variable
* `$HOME/.Xauthority:/root/.Xauthority:ro`: Get the X11 authorization tokens into the container
* `-v /tmp/.X11-unix:/tmp/.X11-unix` Get the unix domain sockets for the local X-Server into the container

If your docker is configured with user namespaces for security reasons, it's not so simple.
