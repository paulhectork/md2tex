import click
import sys


# -------------------------------------------------------
# custom error and warnings classes to display custom
# messages
# ------------------------------------------------------


class ParsingException(Exception):
    """
    base class for all parsing exceptions
    """


class IndentationException(ParsingException):
    """
    error logs relative to list indentation
    """
    logs = {
        "firstindent": "ERROR. - inconsistant indentation in markdown list \n"
                       + "@@TOKEN@@ \n"
                       + "all items must be as indented than the first list item or more.",
        "multiplier": "ERROR. inconsistant indentation level in list \n"
                      + "@@TOKEN@@ \nall list items must share a common indentation multiplier.\n"
                      + "the first indented item defines the indentation multiplier."

    }  # all possible error logs

    def __init__(self, key, lstext):
        """
        launch an IndentationException: return an error log and exit
        :param msg: the error key to print the proper log
        :param lstext: the text representation of the markdown list on which this error happened
        """
        click.echo(IndentationException.logs[key].replace("@@TOKEN@@", lstext))


class OSInputException(Exception):
    """
    base class for all OS errors caused by user input: files not found, invalid files...
    """
    logs = {
        "not_md": "ERROR - filename @@TOKEN@@ doesn't end with `.md` "
                  + "and doesn't seem to be a markdown file. exiting...",
        "not_inpath": "ERROR - input file @@TOKEN@@ not found. exiting...",
        "not_tex": "ERROR - custom tex template @@TOKEN@@ not found. exiting...",
        "not_outpath": "ERROR - output directory(ies) for path @@TOKEN@@ doesn't "
                       + "seem to exist. create it and start again...",
        "outpath_slashes": "ERROR - output file path @@TOKEN@@ contains '/' and '\\'. "
                           + "please remove slashes or backslashes to continue."
                           + "exiting...",
    }  # all possible error logs

    def __init__(self, key, fpath):
        """
        launch an OSInpytException: return an error log and exit
        :param key: the error key to print the proper log
        :param fpath: the user inputted file path which caused the error
        """
        click.echo(OSInputException.logs[key].replace("@@TOKEN@@", fpath))
        sys.exit(1)


class Warnings:
    """
    class to display custom warning errors
    """
    logs = {
        "outpah_extension": "WARNING - file extension changed to .tex",
        "list_deep_nesting": "WARNING - deep list nesting. you may need to change base tex options in the header."
    }

    def __init__(self, msg):
        click.echo(Warnings.logs[msg])
