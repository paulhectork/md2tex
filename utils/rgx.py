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
    unnumbered_list(): create latex `itemize` envs from md unnumbered lists
    numbered_list(): create latex `enumerate` envs from md numbered lists
    blockcode(): create a latex minted or listings env from a md block of code
    """
    simple_sub = {
        # code, bold, italics
        r"(?<!\*)\*{2}(?!\*)(.+?)(?<!\*)\*{2}(?!\*)": r"\\textbf{\1}",  # bold
        r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)": r"\\textit{\1}",  # italics
        r"(?<!`)`(?!`)(.+?)(?<!`)`(?!`)": r"\\texttt{\1}",  # inline code

        # titles
        r"^\s*#([^#]*?)$": r"\\chapter{\1}",  # 1st level title
        r"^\s*#{2}([^#]*?)$": r"\\section{\1}",  # 2nd level title
        r"^\s*#{3}([^#]*?)$": r"\\subsection{\1}",  # 3rd level title
        r"^\s*#{4}([^#]*?)$": r"\\subsubsection{\1}",  # 4th level title
        r"^\s*#{5}([^#]*?)$": r"\\textbf{\1}\n\n",  # 5th level title

        # images and hyperlink
        r"(?<!!)\[(.*?)\]\((.*?)\)": r"\\href{\2}{\1}",  # hyperlink
        r"!\[(.*?)\]\((.*?)\)": r"""
\\begin{figure}
    \\centering
    \\includegraphics[width=\\linewidth]{\2}
    \\caption{\1}
\\end{figure}""",  # images


        r"-{3,}": r"\\par\\noindent\\rule{\\linewidth}{0.4pt}",  # horizontal line
    }

    @staticmethod
    def block_quote(string: str):
        """
        replace a markdown quote ">" with a latex quote (\quote{}).
        works in multiline mode.

        :param string:  the string representation of the markdown file
        :return:
        """
        string = re.sub(
            r"((>.+(\n|$))+)",
            r"\\begin{displayquote} \n \1 \n \\end{displayquote}",
            string, flags=re.M
        ).replace(">", " ")
        return string

    @staticmethod
    def inline_quote(string: str, french_quotes: bool):
        """
        convert the markdown quotes to LaTeX.
        :param string:
        :param french_quotes: translate the quotes as french quotes (\enquote{})
                              or anglo-saxon quotes (``'')
        :return: string
        """
        if french_quotes is True:
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
        :return:
        """
        lists = re.finditer(r"((^[ \t]*?-.*?\n)+(.+\n)*)+", string, flags=re.MULTILINE)
        for ls in lists:
            # prepare list building:
            # - extract list text
            # - replace list in source markdown by token
            # - if a list item is broken into several lines, group them into one line
            lstext = ls[0]  # extract list text
            string = string.replace(lstext, "__LISTTOKEN__")  # add token to source
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
__ITEMTOKEN__
\end{itemize}""".replace("__ITEMTOKEN__", items)
            string = string.replace("__LISTTOKEN__", itemize)

        return string

    @staticmethod
    def ordered_l(string: str):
        """
        translate a markdown numbered list into a latex `enumerate` environment
        the functionning is quite the same as `unnumbered_list()`
        :param string:  the string representation of the markdown file
        :return:
        """
        lists = re.finditer(r"((^[ \t]*?\d+\..*?\n?)+(.+\n?)*)+", string, flags=re.MULTILINE)
        for ls in lists:
            # prepare list building:
            # - extract list text
            # - replace list in source markdown by token
            # - if a list item is broken into several lines, group them into one line
            lstext = ls[0]  # extract list text
            string = string.replace(lstext, "__LISTTOKEN__")  # add token to source
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
__ITEMTOKEN__
\end{enumerate}""".replace("__ITEMTOKEN__", items)
            string = string.replace("__LISTTOKEN__", enumerate)

        return string


    @staticmethod
    def blockcode(string: str):
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
        :return:
        """
        matches = re.finditer(r"```((.|\n)*?)```", string, flags=re.M)
        for m in matches:
            code = m[0]  # isolate the block of code
            string = string.replace(code, "__MINTEDTOKEN__")  # to reinject code to string later

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
    \begin{minted}{__LANGTOKEN__}
__CODETOKEN__
    \end{minted}
\end{listing}"""  # env to add the code to; ugly indentation to avoid messing up the .tex file
                code = re.sub(r"```.*?\n((.|\n)+?)```", r"\1", code, flags=re.M)  # extract code body
                code = env.replace("__LANGTOKEN__", lang).replace("__CODETOKEN__", code)  # add code to the latex env

            # if the langage is not supported (or if the characters after the opening ```
            # aren't a language), only create a verbatim environment and reinject the code
            # in it
            else:
                env = r"""
\begin{verbatim}
__CODETOKEN__
\end{verbatim}
                """  # env to add the code to
                code = env.replace("__CODETOKEN__", re.sub(r"```", "", code, flags=re.M))  # reinject code block to env

            string = string.replace("__MINTEDTOKEN__", code)  # reinject latex code to string

        return string

    @staticmethod
    def strip_space(string: str):
        """
        clean spaces around latex commands + uneccessary spaces created during
        transformation
        :return:
        """
        string = re.sub(r"((?<!^ ) )+", " ", string, flags=re.M)
        string = re.sub(r"{\s+", r"{", string, flags=re.M)
        string = re.sub(r"\s+}", r"}", string, flags=re.M)
        return string