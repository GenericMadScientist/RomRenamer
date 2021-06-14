# RomRenamer

A script for mass-renaming your ROMs (at least, it will soon).

## Install

You need Python installed. I've developed with Python 3.9.5, I imagine previous
versions will work up to some point but I've not tested with them and make no
guarantees.

Then download the DAT files for the systems you are interested in from
[Nointro](https://www.datomatic.no-intro.org/index.php?page=download) and
[Redump](http://www.redump.org/downloads). Place them in a DATs directory beside
the script.

## Usage

Run the script specifying your ROM directory, like so:

```
> python rom_renamer.py C:/ROMs
```

For now the script will list all files not contained in the DTAs and any games
that only have some of their files present (this can happen with PSX games for
example, if you have the right .bin but incorrect .cue). I plan to add renaming
and reorganising features soon.

## Contact

If you have any bug reports or feature requests I would prefer they be reported
on the GitHub page, but feel free to send them to me on Discord at
GenericMadScientist#5303.
