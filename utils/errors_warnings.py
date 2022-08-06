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
                       + "`@@TOKEN@@` \n"
                       + "all items must be as indented than the first list item or more.",
        "multiplier": "ERROR. inconsistant indentation level in list \n"
                      + "`@@TOKEN@@` \nall list items must share a common indentation multiplier.\n"
                      + "the first indented item defines the indentation multiplier."

    }  # all possible error logs

    def __init__(self, key, lstext):
        """
        launch an IndentationException: return an error log and exit
        :param msg: the error key to print the proper log
        :param lstext: the text representation of the markdown list on which this error happened
        """
        click.echo(IndentationException.logs[key].replace("@@TOKEN@@", lstext))


class InputException(Exception):
    """
    base class for all errors caused by user input: files not found, invalid files...
    """
    logs = {
        "not_md": "ERROR - filename `@@TOKEN@@` doesn't end with `.md` "
                  + "and doesn't seem to be a markdown file. exiting...",
        "not_inpath": "ERROR - input file `@@TOKEN@@` not found. exiting...",
        "not_template": "ERROR - custom tex template `@@TOKEN@@` not found. exiting...",
        "template_no_token": "ERROR - custom tex template `@@TOKEN@@` does not contain a "
                        + "@@BODYTOKEN@@ key. cannot perform replacement.",
        "not_outpath": "ERROR - output directory or directories for path `@@TOKEN@@` don't "
                       + "seem to exist. create it and start again...",
        "outpath_slashes": "ERROR - output file path `@@TOKEN@@` contains '/' and '\\'. "
                           + "please remove slashes or backslashes to continue."
                           + "exiting...",
        "document_class": "ERROR - invalid value provided for argument `--document-class`: `@@TOKEN@@`. "
                          + "allowed values are `article` or `book`. exiting..."
    }  # all possible error logs

    def __init__(self, key, val=None):
        """
        launch an OSInpytException: return an error log and exit
        :param key: the error key to print the proper log
        :param val: the user inputted value which caused the error
        """
        click.echo(InputException.logs[key].replace("@@TOKEN@@", val))
        sys.exit(1)


class Warnings:
    """
    class to display custom warning errors
    """
    logs = {
        "outpath_extension": "WARNING - file extension of output file `@@TOKEN@@` changed to `.tex`",
        "list_deep_nesting": "WARNING - deep list nesting. you may need to change base tex options in the header."
    }

    def __init__(self, key, val=None):
        """
        display a warning message to the user.
        :param key: the key pointing to the message from Warnings.log to print
        :param val: a possible value for a custom warning message.
        """
        click.echo(Warnings.logs[key].replace("@@TOKEN@@", val))
