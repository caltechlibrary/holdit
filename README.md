Holdit<img width="100px" align="right" src=".graphics/noun_1022878.svg">
======

_Hold it_ is a small application written for the Caltech Library's Circulation team to easily generate a printable "on hold" book list from the Caltech TIND server.

*Authors*:      [Michael Hucka](http://github.com/mhucka)<br>
*Repository*:   [https://github.com/caltechlibrary/urlup](https://github.com/caltechlibrary/@@REPO@@)<br>
*License*:      BSD/MIT derivative &ndash; see the [LICENSE](LICENSE) file for more information

☀ Introduction
-----------------------------

The Caltech Library's Circulation Desk handles, among other things, requests by patrons to put books or other materials on hold.  However, the software used for catalog management does not have a simple way to produce a printable list of items to hold.  The staff who go to the stacks to find the materials have to look up the information from the LIMS system used by Caltech (TIND) and write down the information on paper.

This software is aimed at make it possible to easily get the latest on-hold list.  It uses Shibboleth to log in to the Caltech Library system, extract the information from TIND, and produce the information in a more convenient format.


✺ Installation instructions
---------------------------

The following is probably the simplest and most direct way to install this software on your computer:
```sh
sudo pip3 install git+https://github.com/caltechlibrary/holdit.git
```

Alternatively, you can clone this GitHub repository and then run `setup.py`:
```sh
git clone https://github.com/caltechlibrary/holdit.git
cd holdit
sudo python3 -m pip install .
```

▶︎ Basic operation
------------------



⁇ Getting help and support
--------------------------

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/caltechlibrary/holdit/issues) for this repository.


☺︎ Acknowledgments
-----------------------

The vector artwork used as a logo for Holdit was created by [Yo! Baba](https://thenounproject.com/vectormarket01/) and obtained from the [Noun Project](https://thenounproject.com/search/?q=hold&i=1022878).  It is licensed under the Creative Commons [CC-BY 3.0](https://creativecommons.org/licenses/by/3.0/) license.


☮︎ Copyright and license
---------------------

Copyright (C) 2018, Caltech.  This software is freely distributed under a BSD/MIT type license.  Please see the [LICENSE](LICENSE) file for more information.
    
<div align="center">
  <a href="https://www.caltech.edu">
    <img width="100" height="100" src=".graphics/caltech-round.svg">
  </a>
</div>
