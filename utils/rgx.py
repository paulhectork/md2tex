import re


from .minted import languages


class Regex:
    r"""
    regular expressions and regex-related functions

    contains
    --------
    simple_sub: a dict mapping to a regular expression its replacement,
                to use with re.sub. only for simple elements of the markdown
                syntax, like "*", "`"...
    quote(): replace multiline markdown quotes (">") into latex \quote{}
    inline_quote(): transform markdown quotes (`"`, `'`) into latex french or anglo saxon quotes
    unoredered_l(): create latex `itemize` envs from md unnumbered lists
    ordered_l(): create latex `enumerate` envs from md numbered lists
    block_code(): create a latex minted or listings env from a md block of code
    footnote(): replace markdown footnotes (`[\^\d+]`) into latex `\footnote{}` or `\endnote{}`
    prepare_markdown(): replace markdown document by escaping special tex characters and
                        removing code blocks from the rest of the pipeline
    clean_tex(): clean the tex created and reinsert blocks of code at the end of the pipeline
    """
    simple_sub = {
        # code, bold, italics
        r"(?<!\*)\*{2}(?!\*)(.+?)(?<!\*)\*{2}(?!\*)": r"\\textbf{\1}",  # bold
        r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)": r"\\textit{\1}",  # italics
        r"(?<!`)`(?!`)(.+?)(?<!`)`(?!`)": r"\\texttt{\1}",  # inline code

        # titles
        r"^\s*(\\#){1}(?!\\#?)(.*?)$": r"\\chapter{\2}",  # 1st level title
        r"^\s*(\\#){2}(?!\\#?)(.*?)$": r"\\section{\2}",  # 2nd level title
        r"^\s*(\\#){3}(?!\\#?)(.*?)$": r"\\subsection{\2}",  # 3rd level title
        r"^\s*(\\#){4}(?!\\#?)(.*?)$": r"\\subsubsection{\2}",  # 4th level title
        r"^\s*(\\#){5,}(?!\\#?)(.*?)$": r"\n\n\\textbf{\2}\n\n",  # 5th+ level title

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
        r"<br>": "\n\n",
    }

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
            r"\\begin{displayquote} \n \1 \n \\end{displayquote}",
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

    @staticmethod
    def unordered_l(string: str):
        """
        translate a markdown unnumbered list into a latex `itemize` environment
        :param string:  the string representation of the markdown file
        :return: the updated string representation of a markdown file
        """
        lists = re.finditer(r"((^[ \t]*?-(?!-{2,}).*?\n)+(.+\n)*)+", string, flags=re.MULTILINE)
        for ls in lists:
            # prepare list building:
            # - extract list text
            # - replace list in source markdown by token
            # - if a list item is broken into several lines, group them into one line
            lstext = ls[0]  # extract list text
            string = string.replace(lstext, "@@LISTTOKEN@@")  # add token to source
            lstext = re.sub(r"\n(?!\s*-)", " ", lstext, flags=re.M)

            # count the spaces to build nested lists
            # - build a dict mapping to a list item the number of spaces at
            #   beginning of lines to see if there are nested lists
            lsdict = {}
            for l in re.split(r"\n", lstext):
                lsdict[re.sub(r"^\s*-\s*", "", l)] = len(re.match(r"^\s*", l)[0])

            levels = sorted(set(lsdict.values()))  # spaces determine list levels

            # update lsdict's values:
            # replace absolute number of spaces by nesting level.
            # from that we'll determine the n° of nested envs to build at each iteration:
            # base nesting level == 0, `itemize` inside `itemize` == 1...
            for k, v in lsdict.items():
                lsdict[k] = levels.index(v)

            # build the possibly nested `itemize`.
            if len(levels) != 0:
                # prev logs the nesting level of the previous item
                # to determine the number of nested `itemize` to build
                prev = 0
                items = ""
                for k, v in lsdict.items():
                    # open or close as many `itemize` as needed: difference of nesting
                    # between previous itemize and new one.
                    # if nesting_diff > 0, we need to create envs; if nesting_diff < 0, we need to close envs
                    nesting_diff = v - prev  # (levels.index(v) - prev)
                    if nesting_diff == 1:
                        # in this case, we just need to create an extra env
                        items += "\\begin{itemize} \n"
                    elif nesting_diff > 1:
                        # here, we need to create \items containing additional `itemize`s.
                        items += "\item\\begin{itemize} \n" * nesting_diff
                    elif nesting_diff < 0:
                        # if the difference is negative, we close as many envs as needed
                        items += "\end{itemize} \n" * (prev - v)
                    items += f"\item {k} \n"  # add item to list
                    prev = v  # to determine the number of `itemize` to build / destroy
                    items += "\end{itemize} \n" * prev  # close the nested envs
            else:
                items = ""
                for k in lsdict.keys():
                    items += f"\item {k} \n"  # build items list

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
            # prepare list building:
            # - extract list text
            # - replace list in source markdown by token
            # - if a list item is broken into several lines, group them into one line
            lstext = ls[0]  # extract list text
            string = string.replace(lstext, "@@LISTTOKEN@@")  # add token to source
            lstext = re.sub(r"\n(?!\s*\d+\.)", " ", lstext, flags=re.M)

            # count the spaces to build nested lists
            # - build a dict mapping to a list item the number of spaces at
            #   beginning of lines to see if there are nested lists
            lsdict = {}
            for l in re.split(r"\n", lstext):
                lsdict[re.sub(r"^\s*\d+\.\s*", "", l)] = len(re.match(r"^\s*", l)[0])

            levels = sorted(set(lsdict.values()))  # spaces determine list levels

            # update lsdict's values:
            # replace absolute number of spaces by nesting level.
            # from that we'll determine the n° of nested envs to build at each iteration:
            # base nesting level == 0, `enumerate` inside `enumerate` == 1...
            for k, v in lsdict.items():
                lsdict[k] = levels.index(v)

            # build the possibly nested `enumerate`.
            if len(levels) != 0:
                # prev logs the nesting level of the previous item
                # to determine the number of nested `enumerate` to build
                prev = 0
                items = ""
                for k, v in lsdict.items():
                    # open or close as many `enumerate` as needed: difference of nesting
                    # between previous enumerate and new one.
                    # if nesting_diff > 0, we need to create envs; if nesting_diff < 0, we need to close envs
                    nesting_diff = v - prev  # (levels.index(v) - prev)
                    if nesting_diff == 1:
                        # in this case, we just need to create an extra env
                        items += "\\begin{enumerate} \n"
                    elif nesting_diff > 1:
                        # here, we need to create \items containing the proper number of `enumerate` envs
                        items += "\item\\begin{enumerate} \n" * nesting_diff
                    elif nesting_diff < 0:
                        # if the difference is negative, we close as many envs as needed
                        items += "\end{enumerate} \n" * (prev - v)
                    items += f"\item {k} \n"  # add item to list
                    prev = v  # to determine the number of `enumerate` to build / destroy
                    first = False  # 1st iteration done
                items += "\end{enumerate} \n" * prev  # close the nested envs
            else:
                items = ""
                for k in lsdict.keys():
                    items += f"\item {k} \n"  # build items list

            # once the list of \item and possibly nested `enumerate` is built,
            # build the final enumerate, add it to the markdown string and that's it !
            enumerate = r"""
\begin{enumerate}
@@ITEMTOKEN@@
\end{enumerate}""".replace("@@ITEMTOKEN@@", items)
            string = string.replace("@@LISTTOKEN@@", enumerate)

        return string

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
                    string = string.replace(pointer, texnote)  # add the \footnote or \endnote to string
                    string = string.replace(fnote[1], "")  # delete the footnote key
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
        string = string.replace("\\", r"\backslash")
        string = string.replace(r"#", r"\#")
        string = string.replace("$", r"\$")
        string = string.replace("%", r"\%")
        string = string.replace(r"$", r"\&")
        string = string.replace(r"~", r"\~")
        string = string.replace("_", r"\_")
        string = string.replace("^", r"\^")
        string = string.replace(r"{", r"\{")
        string = string.replace(r"}", r"\}")

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

        string = string.replace("USERRESERVEDTOKEN", "@@")

        return string