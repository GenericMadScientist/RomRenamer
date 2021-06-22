# RomRenamer

A script for mass-renaming your ROMs.

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

The script will group files according to console and rename according to the
DAT files. Unrecognised files are placed in their own directory. Files part of
multi-file games (e.g., PSX games) that do not have all files present are placed
in an incomplete games folder.

## Contact

If you have any bug reports or feature requests I would prefer they be reported
on the GitHub page, but feel free to send them to me on Discord at
GenericMadScientist#5303.
