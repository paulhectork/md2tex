from ntpath import basename
import click
import sys
import re
import os

from utils.rgx import Regex


@click.command("md2tex")
@click.argument("inpath")
@click.option("-o", "--output-path", "outpath", default=None)
@click.option("-c", "--complete-tex-file", "tex", is_flag=True, default=False)
@click.option("-t", "--custom-tex-template", "template", default="utils/template.tex")
@click.option("-f", "--french-quote", "french_quote", is_flag=True, default=False)
@click.option("-e", "--endnote", "endnote", is_flag=True, default=False)
@click.option("-n", "--numbered-headers", "numbered", is_flag=True, default=True)
def md2tex(
        inpath: str,
        outpath=None,
        tex=False,
        template="utils/template.tex",
        french_quote=False,
        endnote=False,
        numbered=True
):
    """
    convert a markdown file to .tex.

    :param inpath: the path to the *.md file to convert to tex
    :param outpath: the path to save the file to
    :param tex: a flag indicating wether to create a full tex file,
                with preamble and table of contents
    :param template: a custom TeX template to use for the conversion, in order
                     to add extra packages and whatnot. the contents of
                     \begin{document} - \end{document} should be empty, except for a
                     title page; this part must contain a "@@BODYTOKEN@@" string to be
                     able to append the TeX body to the template.
    :param french_quotes: whether to translate "" and '' as english tex quotes (``")
                          or french quotes (\enquote{})
    :param endnote: translate the markdown footnotes (`[^\d+]`) as latex `\endnote{}`
                    instead of `\footnote`
    :param numbered: wether to convert headers as numbered chapters/sections (`\chapter{}`)
                     or as unnumbered ones (`\chapter*{}`). defaults to True:
                     the headers are numbered by default.
    :return: data, a string representation of the .md file converted to .tex
    """
    # ==================== PROCESS THE ARGUMENTS ==================== #
    if not re.search(r"\.md$", inpath):
        click.echo("file doesn't end with .md and doesn't seem to be a markdown file. exiting...")
        sys.exit(1)
    if not os.path.isfile(inpath):
        click.echo("input file not found. exiting...")
        sys.exit(1)
    if outpath is None:
        outpath = "output/" + re.sub(r'\..+?$', '.tex', basename(inpath))  # build default outpath
    elif "/" in outpath and "\\" in outpath:
        click.echo(
            "ERROR - Output file path contains '/' and '\\'. "
            + "please remove slashes or backslashes to continue."
            + "exiting..."
        )
    elif not re.search(r"\.tex$", outpath):
        # add a .tex extension if it doesn't exist or if a different extension was
        # provided by the user
        if re.search("\..*?$", outpath):
            outpath = re.sub(r"\..*?$", ".tex", outpath)
        else:
            outpath = re.sub(r"$", ".tex", outpath)
        click.echo("WARNING : file extension changed to .tex")
    click.echo(outpath)

    # open file and read contents
    with open(inpath, mode="r") as fh:
        data = fh.read()

    # ==================== CONVERT THE FILE ==================== #
    # complex replacements
    data = Regex.block_code(data)  # the contents of code blocks must be interpreted verbatim;
    #                                 this function comes first so that they won't be changed
    #                                 by `prepare_markdown()`
    data, codedict = Regex.prepare_markdown(data)  # escape special chars + remove code envs from the pipeline
    data = Regex.inline_quote(data, french_quote)
    data = Regex.block_quote(data)
    data = Regex.unordered_l(data)
    data = Regex.ordered_l(data)
    data = Regex.footnote(data, endnote)

    # "simple" replacements. simple_sub contains regexes as keys
    # and values, facilitating the regex replacement
    for k, v in Regex.simple_sub.items():
        data = re.sub(k, v, data, flags=re.M)
    data = Regex.clean_tex(data, codedict)  # clean the tex file + reinject the escaped code blocks

    # ==================== BUILD + WRITE OUTPUT TO FILE ==================== #
    if tex is True: # create full tex file.
        try:
            with open(template, mode="r") as fh:
                data = fh.read().replace("@@BODYTOKEN@@", data)
        except FileNotFoundError:
            click.echo("ERROR : custom template not found. exiting...")
            sys.exit(1)
    try:
        with open(outpath, mode="w") as fh:
            fh.write(data)
    except FileNotFoundError:
        click.echo("ERROR : output directory doesn't seem to exist. create it and start again...")
        sys.exit(1)
    return data


if __name__ == "__main__":
    md2tex()
