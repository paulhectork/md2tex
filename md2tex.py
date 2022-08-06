from ntpath import basename
import click
import re
import os

from utils.converters import MDSimple, MDQuote, MDList, MDCode, MDCleaner, MDReference, MDHeader
from utils.errors_warnings import InputException, Warnings


@click.command("md2tex")
@click.argument("inpath")
@click.option("-o", "--output-path", "outpath", default=None,
              help="optional. a custom output path. defaults to `output/{input_file_name}.md`.")
@click.option("-c", "--complete-tex-file", "tex", is_flag=True, default=False,
              help="optional. if provided, a complete TeX file will be created from a template (with "
              + "preamble and tables of content). if not provided, only the contents of the markdown "
              + "file are translated. can be used with `-t` to use a custom, user-provided TeX template. "
              + "defaults to `False`.")
@click.option("-t", "--custom-tex-template", "template", default="utils/template.tex",
              help="optional. if provided, a custom TeX template will be used to create a complete TeX file. "
                   + "this argument must be used with `-c` and the TeX template must contain a "
                   + "`@@BODYTOKEN@@` between its `\\begin{document}` and `\\end{document}` "
                   + "to perform the replacement. "
                   + "defaults to `utils/template.tex`")
@click.option("-f", "--french-quote", "french_quote", is_flag=True, default=False,
              help="optional. if provided, the Markdown inline quotes will be converted"
                   " as french quotes `\\enquote{}` instead of anglo-saxon quotes."
                   + "defaults to `False`: quotes are translated as anglo-saxon quotes.")
@click.option("-e", "--endnote", "endnote", is_flag=True, default=False,
              help="optional. if provided, the Markdown footnotes will be translated as TeX endnotes (`\\endnote{}`)"
                   + "instead of the usual `\\footnote{}`."
                   + "defaults to `False`: Markdown footnotes are translated as TeX footnotes.")
@click.option("-u", "--unumbered-headers", "unnumbered", is_flag=True, default=False,
              help="optional. if provided, Markdown headers will be translated as TeX unnumbered headers/sections"
                   + "defaults to False: the headers are numbered by default.")
@click.option("-d", "--document-class", "document_class", default="article",
              help="optional. sets the class of the TeX document. possible values "
                   + "are: `book`|`article`. defaults to `article`")
def md2tex(
        inpath: str,
        outpath=None,
        tex=False,
        template="utils/template.tex",
        french_quote=False,
        endnote=False,
        unnumbered=False,
        document_class="article"
):
    """
    convert a Markdown file to a TeX file.

    \b
    parameters (see options if you are in `--help` mode):
    -----------------------------------------------------
    :param inpath: the path to the *.md file to convert to tex
    :param outpath: the path to save the file to
    :param tex: a flag indicating wether to create a full tex file,
                with preamble and table of contents
    :param template: a custom TeX template to use for the conversion, in order
                     to add extra packages and whatnot. the contents of
                     \begin{document} - \end{document} should be empty, except for a
                     title page; this part must contain a "@@BODYTOKEN@@" string to be
                     able to append the TeX body to the template.
    :param french_quote: whether to translate "" and '' as english tex quotes (``")
                          or french quotes (\enquote{})
    :param endnote: translate the markdown footnotes (`[^\d+]`) as latex `\endnote{}`
                    instead of `\footnote`
    :param unnumbered: wether to convert headers as numbered chapters/sections (`\chapter{}`)
                     or as unnumbered ones (`\chapter*{}`). defaults to False:
                     the headers are numbered by default.
    :param make_out_dirs: wether or not to create non-existant output directories
    :param document_class: the document class of the tex document. defaults to `article`
    :return: data, a string representation of the .md file converted to .tex
    """
    # ==================== PROCESS THE ARGUMENTS ==================== #
    if not re.search(r"\.md$", inpath):
        raise InputException("not_md", inpath)
    if not os.path.isfile(inpath):
        raise InputException("not_inpath", inpath)
    if outpath is None:
        outpath = "output/" + re.sub(r'\..+?$', '.tex', basename(inpath))  # build default outpath
    elif "/" in outpath and "\\" in outpath:
        raise InputException("outpath_slashes", outpath)  # gnu-linux escapes backslashes so this shouldn't be called
    elif os.path.isdir(outpath):  # if the output path is a dir and not a file, save the file to that dir
        outpath = f"{outpath}/{basename(inpath)}"
    if not re.search(r"\.tex$", outpath):
        # add a .tex extension if it doesn't exist or if a different extension was
        # provided by the user
        Warnings("outpath_extension", outpath)
        outpath = re.sub(r"$", ".tex", outpath)
    if not re.search("^(book|article)$", document_class):
        InputException("document_class", document_class)

    # build output directory
    if not os.path.exists("./output"):
        os.makedirs("./output")

    # open file and read contents
    with open(inpath, mode="r") as fh:
        data = fh.read()

    # ==================== CONVERT THE FILE ==================== #
    # complex replacements
    data = MDCode.block_code(data)  # the contents of code blocks must be interpreted verbatim;
    #                                 this function comes first so that they won't be changed
    #                                 by `prepare_markdown()`
    data, codedict = MDCleaner.prepare_markdown(data)  # escape special chars + remove code envs from the pipeline
    data = MDQuote.inline_quote(data, french_quote)
    data = MDQuote.block_quote(data)
    data = MDList.unordered_l(data)
    data = MDList.ordered_l(data)
    data = MDReference.footnote(data, endnote)
    data = MDHeader.convert(data, unnumbered, document_class)

    # "simple" replacements. simple_sub contains regexes as keys
    # and values, facilitating the regex replacement
    data = MDSimple.convert(data)
    data = MDCleaner.clean_tex(data, codedict)  # clean the tex file + reinject the escaped code blocks

    # ==================== BUILD + WRITE OUTPUT TO FILE ==================== #
    if tex is True:  # create full tex file.
        try:
            with open(template, mode="r") as fh:
                tex_template = fh.read()
                if "@@BODYTOKEN@@" not in tex_template:
                    raise InputException("template_no_token", template)
                else:
                    data = tex_template.replace("@@BODYTOKEN@@", data)
                    data = data.replace("@@DOCUMENTCLASSTOKEN@@", document_class)
        except FileNotFoundError:
            raise InputException("not_template", template)
    try:
        with open(outpath, mode="w") as fh:
            fh.write(data)
    except FileNotFoundError:
        raise InputException("not_outpath", outpath)

    click.echo(f"FINISHED - file conversion completed and saved to `{outpath}`")
    return data
