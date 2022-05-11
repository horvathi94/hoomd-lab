FROM glotzerlab/software:working

USER root
RUN groupadd hoomd --gid 1011
RUN pip3 install dataclasses click
USER glotzerlab-software

RUN export LC_ALL=C.UTF-8
RUN export LANG=C.UTF-8

WORKDIR /hoomd-examples/workdir/

CMD ["jupyter", "notebook", "--port", "8888", "--ip", "0.0.0.0", "--no-browser", "/hoomd-examples/workdir"]
