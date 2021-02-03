This collection of files contains the basis for a python experiment using both
ET and EGI at NeuroSpin — presumably with the baby eeg linux setup.

Note that:

* some of this code belongs to "Tobii" (everything in/related to "tobii_research")
* some is a port in python 3 from a port in python 2 from a thing written in
  C++ from another era. It looks like the original inspiration was here: https://code.google.com/archive/p/libnetstation/

  I am responsible for the `python 2` -> `python 3` conversion, but I only took
  care of what was useful for my experiment, and you may run into weird bugs.

Nothing here should be too mysterious. I used expyriment but it should be easy
to swap that for other frameworks.

## How to use any of this?

This is mostly intended as something to start from rather than a working
experiment. However, with the right packages installed, `python experiment.py
--help` should tell you that you need to give the script a `NIP` and
a participant number. In addition to this, for testing/debugging, you can ask
the script to run without an Eye Tracker connected (`--no-et`) or without the
EGI (`--no-egi`). And if you run `python experiment.py 999 9 --no-egi --no-et`
you should see what a calibration could look like.
