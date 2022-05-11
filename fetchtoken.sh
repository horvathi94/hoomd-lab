docker exec -it hoomd_glotzerlab_1 jupyter notebook list | sed 's/.*token=\(.*\)::.*/\1/'
