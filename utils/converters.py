import re

from .minted import languages
from .helpers import process_list_indentation


# ---------------------------------------------------------------
# regex based conversion from markdown to latex;
# main scrips for the conversion process
# functions are part of classes for clarity
# ---------------------------------------------------------------


class MDSimple:
    """
    simple substitutions that are done using a dict
    simple_sub: a dict mapping to a regular expression its replacement,
                to use with re.sub. only for simple elements of the markdown
                syntax, like "*", "`"...
    """
    simple_sub = {
        # code, bold, italics
        r"(?<!\*)\*{2}(?!\*)(.+?)(?<!\*)\*{2}(?!\*)": r"\\textbf{\1}",  # bold
        r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)": r"\\textit{\1}",  # italics
        r"(?<!`)`(?!`)(.+?)(?<!`)`(?!`)": r"\\texttt{\1}",  # inline code

        # images and hyperlink
        r"(?<!!)\[(.*?)\]\((.*?)\)": r"\\href{\2}{\1}",  # hyperlink
        r"!\[(.*?)\]\((.*?)\)": r"""
\\begin{figure}
    \\centering
    \\includegraphics[width=\\linewidth]{\2}
    \\caption{\1}
\\end{figure}""",  # images

        # separators
        r"-{3,}": r"\\par\\noindent\\rule{\\linewidth}{0.4pt}",  # horizontal line
        r"<br/?>": "\n\n",  # line breaks
    }

    @staticmethod
    def convert(string: str):
        """
        perform the conversion: replace markdown syntax by TeX syntax
        :param string: the string rpr of the markdown file to convert
        :return: string with the conversion performed
        """
        for k, v in MDSimple.simple_sub.items():
            string = re.sub(k, v, string, flags=re.M)
        return string


class MDHeader:
    """
    header substitutions

    contains
    --------
    title_unnumbered_sub: a dict to convert markdown headers to latex unnumbered sections
    title_numbered_sub: a dict to convert markdown headers to latex numbered sections
    """
    title_numbered_sub = {
        r"^\s*(\\#){1}(?!\\#?)(.*?)$": r"\\chapter{\2}\n",  # 1st level title
        r"^\s*(\\#){2}(?!\\#?)(.*?)$": r"\\section{\2}\n",  # 2nd level title
        r"^\s*(\\#){3}(?!\\#?)(.*?)$": r"\\subsection{\2}\n",  # 3rd level title
        r"^\s*(\\#){4}(?!\\#?)(.*?)$": r"\\subsubsection{\2}\n",  # 4th level title
        r"^\s*(\\#){5,}(?!\\#?)(.*?)$": r"\n\n\\textbf{\2}\n\n",  # 5th+ level title
    }
    title_unnumbered_sub = {
        r"^\s*(\\#){1}(?!\\#?)(.*?)$": r"\\chapter*{\2}\n\\addcontentsline{toc}{chapter}{\2}\n",
        r"^\s*(\\#){2}(?!\\#?)(.*?)$": r"\\section*{\2}\n\\addcontentsline{toc}{section}{\2}\n",
        r"^\s*(\\#){3}(?!\\#?)(.*?)$": r"\\subsection*{\2}\n\\addcontentsline{toc}{subsection}{\2}\n",
        r"^\s*(\\#){4}(?!\\#?)(.*?)$": r"\\subsubsection*{\2}\n\\addcontentsline{toc}{subsubsection}{\2}\n",
        r"^\s*(\\#){5,}(?!\\#?)(.*?)$": r"\n\n\\textbf*{\2}\n\n",
    }

    @staticmethod
    def convert(string: str, unnumbered: bool):
        """
        perform the conversion: replace markdown titles by numbered or unnumbered LaTeX titles
        :param string: the markdown representation of the string to convert
        :param unnumbered: flag argument indicating that the LaTeX headers should be unnumbered
        :return: processed string
        """
        if unnumbered is True:
            substitute = MDHeader.title_unnumbered_sub
        else:
            substitute = MDHeader.title_numbered_sub
        for k, v in substitute.items():
            string = re.sub(k, v, string, flags=re.M)
        return string


class MDQuote:
    """
    inline and block quote substitution

    contains
    --------
    block_quote(): replace multiline markdown quotes (">") into latex \quote{}
    inline_quote(): transform markdown quotes (`"`, `'`) into latex french or anglo saxon quotes
    """
    @staticmethod
    def block_quote(string: str):
        """
        replace a markdown quote ">" with a latex quote (\quote{}).
        works in multiline mode.

        :param string:  the string representation of the markdown file
        :return: the updated string representation of a markdown file
        """
        string = re.sub(
            r"^((>.+(\n|$))+)",
            r"\\begin{quotation} \n \1 \n \\end{quotation}",
            string, flags=re.M
        ).replace(">", " ")
        return string

    @staticmethod
    def inline_quote(string: str, french_quote: bool):
        """
        convert the markdown quotes to LaTeX.
        :param string: the string representation of the markdown file
        :param french_quote: translate the quotes as french quotes (\enquote{})
                              or anglo-saxon quotes (``'')
        :return: the updated string representation of a markdown file
        """
        if french_quote is True:
            string = re.sub(r"\"(.*)\"", r"\\enquote{\1}", string)
            string = re.sub(r"'(.*)'", r'``\1"', string)
        else:
            string = re.sub(r"\"(.*)\"", r'``\1"', string)
            string = re.sub(r"'(.*)'", r"`\1'", string)
        return string


class MDList:
    """
    list substitution: replace markdown nested lists by LaTeX nested lists

    contains
    --------
    unoredered_l(): create latex `itemize` envs from md unnumbered lists
    ordered_l(): create latex `enumerate` envs from md numbered lists
    """
    @staticmethod
    def unordered_l(string: str):
        """
        translate a markdown unnumbered list into a latex `itemize` environment
        :param string:  the string representation of the markdown file
        :return: the updated string representation of a markdown file
        """
        lists = re.finditer(r"((^[ \t]*?-(?!-{2,}).*?\n)+(.+\n)*)+", string, flags=re.MULTILINE)
        for ls in lists:
            # prepare list building
            lstext = ls[0]  # extract list text
            string = string.replace(lstext, "@@LISTTOKEN@@")  # add token to source
            lstext = re.sub(r"\n(?!\s*-)", " ", lstext, flags=re.M)  # group list item into one line

            lsitems = process_list_indentation(lstext)  # process the visual indentation

            # build the `\itemize{}`
            items = ""
            prev = 0  # previous indentation level
            for li in lsitems:
                # open/close the good number of envs
                if li[1] - prev > 0:  # if there are envs to open; shouldn't be > 1 env to open, but just in case
                    items += "\\begin{itemize} \n \\item " * (li[1] - prev)
                    items += li[0] + "\n"
                elif li[1] - prev < 0:  # if there are envs to close
                    items += "\\end{itemize}\n" * (prev - li[1])
                    items += "\\item " + li[0] + "\n"
                else:  # no envs to open/close
                    items += "\\item " + li[0] + "\n"
                prev = li[1]

            items += "\\end{itemize}\n" * prev  # close the remaining nested envs

            # once the list of \item and possibly nested `itemize` is built,
            # build the final itemize, add it to the markdown string and that's it !
            itemize = r"""
\begin{itemize}
@@ITEMTOKEN@@
\end{itemize}""".replace("@@ITEMTOKEN@@", items)
            string = string.replace("@@LISTTOKEN@@", itemize)

        return string

    @staticmethod
    def ordered_l(string: str):
        """
        translate a markdown numbered list into a latex `enumerate` environment
        the functionning is quite the same as `unnumbered_list()`
        :param string: the string representation of the markdown file
        :return: the updated string representation of a markdown file
        """
        lists = re.finditer(r"((^[ \t]*?\d+\..*?\n?)+(.+\n?)*)+", string, flags=re.MULTILINE)
        for ls in lists:
            # prepare list building
            lstext = ls[0]  # extract list text
            string = string.replace(lstext, "@@LISTTOKEN@@")  # replace source list by token
            lstext = re.sub(r"\n(?!\s*\d+\.)", " ", lstext, flags=re.M)  # group list items into single line

            lsitems = process_list_indentation(lstext)  # process the visual indentation

            # build the `\enumerate{}`
            items = ""
            prev = 0  # previous indentation level
            for li in lsitems:
                # open/close the good number of envs
                if li[1] - prev > 0:  # if there are envs to open; shouldn't be > 1 env to open, but just in case
                    items += "\\begin{enumerate} \n \\item " * (li[1] - prev)
                    items += li[0] + "\n"
                elif li[1] - prev < 0:  # if there are envs to close
                    items += "\\end{enumerate}\n" * (prev - li[1])
                    items += "\\item " + li[0] + "\n"
                else:  # no envs to open/close
                    items += "\\item " + li[0] + "\n"
                prev = li[1]

            items += "\\end{itemize}\n" * prev  # close the remaining nested envs

            # once the list of \item and possibly nested `enumerate` is built,
            # build the final enumerate, add it to the markdown string and that's it !
            enumerate = r"""
            \begin{enumerate}
            @@ITEMTOKEN@@
            \end{enumerate}""".replace("@@ITEMTOKEN@@", items)
            string = string.replace("@@LISTTOKEN@@", enumerate)

        return string

class MDCode:
    """
    block code substitution

    contains
    --------
    block_code(): create a latex minted or listings env from a md block of code
    """
    @staticmethod
    def block_code(string: str):
        """
        translate a markdown block of code into a minted or listing block.
        
        the function tries to match a md block code "```...```". if the
        block of code is matched, it extracts a code language and checks
        if it is supported by minted/pygments.
        - if it is supported, a `minted` env is created inside a `listing` 
          env; the code is included in this env and will be coloured in latex
        - if no language is supplied in the markdown file, then the whole block
          is included as is in a `listing` env. 
        :param string: the string representation of the markdown file
        :return: the updated string representation of a markdown file
        """
        matches = re.finditer(r"```((.|\n)*?)```", string, flags=re.M)
        for m in matches:
            code = m[0]  # isolate the block of code
            string = string.replace(code, "@@MINTEDTOKEN@@")  # to reinject code to string later

            # extract the code language; try...except to avoid errors if no language is matched
            try:
                lang = re.search(r"```([^\n]*)$", code, flags=re.M)[0].replace("```", "").strip()  # ugly but works
            except TypeError:
                lang = None

            # if the used language is supported by minted, create a minted inside
            # a listing environment to hold the code
            if lang in languages:
                env = r"""
\begin{listing}
    \begin{minted}{@@LANGTOKEN@@}
@@CODETOKEN@@
    \end{minted}
\end{listing}"""  # env to add the code to; ugly indentation to avoid messing up the .tex file
                code = re.sub(r"```.*?\n((.|\n)+?)```", r"\1", code, flags=re.M)  # extract code body
                code = env.replace("@@LANGTOKEN@@", lang).replace("@@CODETOKEN@@", code)  # add code to the latex env

            # if the langage is not supported (or if the characters after the opening ```
            # aren't a language), only create a verbatim environment and reinject the code
            # in it
            else:
                env = r"""
\begin{verbatim}
@@CODETOKEN@@
\end{verbatim}
                """  # env to add the code to
                code = env.replace("@@CODETOKEN@@", re.sub(r"```", "", code, flags=re.M))  # reinject code block to env

            string = string.replace("@@MINTEDTOKEN@@", code)  # reinject latex code to string

        return string


class MDReference:
    """
    substitutions for references inside a markdown document.
    currently only for footnote substitutions

    contains
    --------
    footnote(): replace markdown footnotes (`[\^\d+]`) into latex `\footnote{}` or `\endnote{}`
    """
    @staticmethod
    def footnote(string: str, endnote: bool):
        r"""
        translate a markdown footnode `[^\d+]` to a latex footnote (`\footnote{}` or `\endnote{}`)

        the structure of a markdown footnote:
        - This is the body of the text [^1] <-- body of the text
                                       ^^^^ <-- pointer to the footnote
        - [^1]: this is the footnote  <-- footnote
          ^^^^  <------------------------ pointer to the footnote mark
        in turn, what we need to do is remove the pointers, match the body of the
        footnote and add it to a `\footnote{}`

        :param string: the string representation of a markdown file
        :param endnote: a boolean. if true, use `\endnote{}` instead of `\footnote{}`
        :return: the updated string representation of a markdown file
        """
        footnotes = re.finditer(r"\[\\\^\d+\](?![ \t]*:)", string, flags=re.M)
        for match in footnotes:
            try:
                pointer = match[0]  # extract the footnote pointer (the pointer to the actual footnote
                key = re.search(r"\d+", pointer)[0]  # extract the footnote n°
                fnote = re.search(
                    fr"(\[\\\^%s\]:)(.+\n?)*" % key,
                    string, flags=re.M
                )  # match the proper footnote (with the good key)
                texnote = re.sub(r"\s+", " ", fnote[0].replace(fnote[1], ""))  # remove the pointer + normalize space

                if not re.search("^\s*$", texnote):  # if the note isn't empty; else, delete it
                    if endnote is True:
                        texnote = r"\endnote{" + texnote + "}"
                    else:
                        texnote = r"\footnote{" + texnote + "}"
                    string = string.replace(fnote[0], "")  # delete the markdown footnote
                    string = string.replace(pointer, texnote)  # add the \footnote or \endnote to string
                else:
                    # delete the footnote body and pointers
                    string = string.replace(pointer, "")
                    string = string.replace(fnote[0], "")

            except TypeError:
                # a footnote pointer may point to nothing; conversely, a footnote
                # may to have a ref in the body. in that case, pass now and delete every loose
                # footnote part right after
                pass
        # delete all loose footnote strings
        string = re.sub(r"\[\\\^\d+\](?![ \t]*:)", "", string, flags=re.M)
        string = re.sub(r"(\[\\\^\d+\]:)(.+\n?)*", "", string, flags=re.M)

        return string


class MDCleaner:
    """
    clean the input markdown and output LaTeX.

    contains
    --------
    prepare_markdown(): replace markdown document by escaping special tex characters and
                        removing code blocks from the rest of the pipeline
    clean_tex(): clean the tex created and reinsert blocks of code at the end of the pipeline
    """
    @staticmethod
    def prepare_markdown(string: str):
        """
        prepare markdown for the transformation:
        - strip empty lines (matching the expression `^[ \t]*\n`) by removing inline spaces.
          used at the beginning of the process, it will greatly simplify the following matches and replacement.
        - escape latex special characters. this is also useful because of our use of
          `_` in `@@*TOKEN*@@` strings used for replacements.

        this function is used after `block_code()` to avoid replacing
        special characters that should be interpreted verbatim by LaTeX.
        to escape all `minted` and `verbatim` code we use a dict that stores all
        these blocks of code.

        :param string: the string representation of a markdown file
        :return: the updated string representation of a markdown file
        """
        string = re.sub(r"^[ \t]*\n", r"\n\n", string, flags=re.M)
        string = string.replace("@@", "USERRESERVEDTOKEN")  # @@ is our special token, so we need to escape it
        #                                                     in case it is present in the user file

        # escape all code blocks so that their content isn't escaped.
        # for that, store all code blocks in a dict, replace them in `string`
        # with a special token. this token uses `+` because they aren't LaTeX
        # special characters
        codematch = re.finditer(r"\\begin\{(listing|verbatim)}(.|\n)*?\\end\{(listing|verbatim)}", string, flags=re.M)
        n = 0
        codedict = {}
        for match in codematch:
            block = match[0]  # extract text
            string = string.replace(block, f"@@CODETOKEN{n}@@")
            codedict[f"@@CODETOKEN{n}@@"] = block
            n += 1

        string = string.replace(r"{", r"\{")
        string = string.replace(r"}", r"\}")
        string = string.replace("\\", r"\textbackslash{}")
        string = string.replace(r"#", r"\#")
        string = string.replace("$", r"\$")
        string = string.replace("%", r"\%")
        string = string.replace(r"$", r"\&")
        string = string.replace(r"~", r"\~")
        string = string.replace("_", r"\_")
        string = string.replace("^", r"\^")

        return string, codedict

    @staticmethod
    def clean_tex(string: str, codedict: dict):
        """
        clean spaces around latex commands + uneccessary spaces created during
        transformation
        :param string: the string representation of the markdown file
        :param codedict: the dictionnary containing escaped code blocks
        :return: the updated string representation of a markdown file
        """
        # rebuild the string by reinjecting the code blocks
        for k, v in codedict.items():
            string = string.replace(k, v)

        # clean spaces
        string = re.sub(r"((?<!^ ) )+", " ", string, flags=re.M)
        string = re.sub(r"{\s+", r"{", string, flags=re.M)
        string = re.sub(r"\s+}", r"}", string, flags=re.M)
        string = re.sub(r"\n{2,}", r"\n\n", string, flags=re.M)

        string = string.replace("USERRESERVEDTOKEN", "@@")

        return string
