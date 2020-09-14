To avoid having to repeat shared requirements in several files, both system
requirements and python requirements have been split into several files
according to the "inheritance" tree below:

::

              ------------------------- engine
            /
    common -                    ------- admin
            \                 /
              ------- django -
                              \
                                ------- report