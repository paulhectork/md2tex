from ntpath import basename
import click
import sys
import re

from utils.rgx import Regex


@click.command("md2tex")
@click.argument("input")
@click.option("-o", "--output-file", "output", default=None)
@click.option("-c", "--complete-tex-file", "tex", is_flag=True, default=False)
@click.option("-t", "--custom-tex-template", "template", default="utils/template.tex")
@click.option("-f", "--french-quotes", "french_quotes", is_flag=True, default=False)
def md2tex(input: str, output=None, tex=False, template="utils/template.tex", french_quotes=False):
    """
    convert a markdown file to .tex.

    :param input: the input file to convert to tex
    :param output: the destination to save the file to
    :param tex: a flag indicating wether to create a full tex file,
                with preamble and table of contents
    :param template: a custom TeX template to use for the conversion, in order
                     to add extra packages and whatnot. the contents of
                     \begin{document} - \end{document} should be empty, except for a
                     title page; this part must contain a "__BODYTOKEN__" string to be
                     able to append the TeX body to the template.
    :param french_quotes: whether to translate "" and '' as english tex quotes (``")
                          or french quotes (\enquote{})
    :return: data, a string representation of the .md file converted to .tex
    """
    # ==================== PROCESS THE ARGUMENTS ==================== #
    if not re.search(r"\.md$", input):
        click.echo("file doesn't seem to be a markdown file. exiting...")
    if output is None:
        output = "output/" + re.sub(r'\..+?$', '.tex', basename(input))  # rename output
    elif "/" in output and "\\" in output:
        click.echo(
            "ERROR - Output file path contains '/' and '\\'. "
            + "please remove slashes or backslashes to continue."
            + "exiting..."
        )
    elif not re.search(r"\.tex$", output):
        # add a .tex extension if it doesn't exist or if a different extension was
        # provided by the user
        if re.search("\..*?$", output):
            output = re.sub(r"\..*?$", ".tex", output)
        else:
            output = re.sub(r"$", ".tex", output)
        click.echo("WARNING : file extension changed to .tex")
    click.echo(output)

    # open file and read contents
    with open(input, mode="r") as fh:
        data = fh.read()

    # ==================== CONVERT THE FILE ==================== #
    # complex replacements
    data = Regex.block_quote(data)
    data = Regex.inline_quote(data, french_quotes)
    data = Regex.blockcode(data)
    data = Regex.unordered_l(data)
    data = Regex.ordered_l(data)

    # "simple" replacements. simple_sub contains regexes as keys
    # and values, facilitating the regex replacement
    for k, v in Regex.simple_sub.items():
        data = re.sub(k, v, data, flags=re.M)
    data = Regex.strip_space(data)

    # ==================== BUILD + WRITE OUTPUT TO FILE ==================== #
    if tex is True: # create full tex file.
        try:
            with open(template, mode="r") as fh:
                data = fh.read().replace("__BODYTOKEN__", data)
        except FileNotFoundError:
            click.echo("ERROR : custom template not found. exiting...")
            sys.exit(1)
    try:
        with open(output, mode="w") as fh:
            fh.write(data)
    except FileNotFoundError:
        click.echo("ERROR : output directory doesn't seem to exist. create it and start again...")
        sys.exit(1)
    return data


if __name__ == "__main__":
    md2tex()
