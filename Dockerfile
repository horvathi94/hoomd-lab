#FROM glotzerlab/software:working
FROM glotzerlab/software:2021.02.25-cuda10

ARG HOOMD_GID=${HOOMD_GID}


USER root
RUN groupadd hoomd --gid ${HOOMD_GID}
RUN pip3 install dataclasses
RUN mkdir -p /hoomd-examples/workdir \
	&& chown -R glotzerlab-software:hoomd /hoomd-examples/workdir
USER glotzerlab-software

#RUN export LC_ALL=C.UTF-8
#RUN export LANG=C.UTF-8

WORKDIR /hoomd-examples/workdir
COPY ./src /hoomd-examples/workdir/src
COPY ./main.py /hoomd-examples/workdir


CMD ["jupyter", "notebook", "--port", "8888", "--ip", "0.0.0.0", "--no-browser", "/hoomd-examples/workdir"]
