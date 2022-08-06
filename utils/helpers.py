import re

from .errors_warnings import IndentationException

# -----------------------------------------------
# helpful functions
# -----------------------------------------------


def process_list_indentation(lstext):
    """
    process the indentation levels to build nested LaTeX `itemize` or `enumerate` environments:
    check that the indentation is valid and replace absolute number of spaces by integers representing
    indentation levels

    process
    -------
    - represent the markdown list as a list of lists: `[markdown list item, its indentation level]`
    - check that the indentation is valid:
      - if all items are indented (no `^-`), then the shared leading spaces are removed
      - if the list items have different indentation levels, all indentation
        levels must be a multiple of the indentation of the 1st indented item
        (e.g., if the first indentation is 2, then all items must be indented by n*2 spaces
    - replace absolute number of spaces by indentation levels.
      - an item can only gain one indentation level at a time.
        if an item jumps indentation level, reset the indentation level: prev = n, new = n+1.
        (e.g.:
         - indentation multiplier = 2
         - previous item: indentation level = 2 => its absolute nesting level `n` is 1
         - current item: indentation level = 6
           => theoritically, its nesting level should be 3, but that doesn't make
              sense and doesn't work in markdown => we reset it to 2.)
      - in short: if n[current] - n[prev] > 1, then n[current] is redifined as n[prev] += 1
        (with n[current] the current indentation level and n[prev] the previous one

    :param lstext: the string representation of a markdown list (ordered or not), to process it
    :return: lsitems, a list with this structure:
             [
                ["markdown list item 1", indentation_level_1],
                ["markdown list item 2", indentation_level_2],
                ...
            ]
    """
    lsitems = []  # list of lists : [item content, indentation level]
    firstindent = len(re.search(r"^\s*", lstext)[0])  # base indentation level
    for item in re.split(r"\n", lstext):
        indent = len(re.search(r"^\s*", item)[0]) - firstindent
        if indent < 0:
            raise IndentationException(key="firstindent", lstext=lstext)  # raise an error, print error msg, exit
        else:
            lsitems.append([
                re.sub(r"^\s*-\s*", "", item),  # item content
                indent  # indentation (n° of spaces)
            ])

    # if there are different indentation levels,
    # - check that all levels have a common multiplier
    # - replace absolute number of spaces (li[1]) by indentation level (li[1] / mult)
    # - if an item jumps indentation level (e.g., goes from level 1 to level3), correct it
    if len(set([li[1] for li in lsitems])) > 1:  # if there are different indentation levels
        mult = next((li[1] for li in lsitems if li[1] != 0), 0)  # the first indented item is the multiplier

        for li in lsitems:
            # check that all list items have same multiplier;
            # `int(li[1] / mult) == li[1]` / mult checks that the division returns a round number
            if int(li[1] / mult) == li[1] / mult:
                li[1] = int(li[1] / mult)  # replace number of spaces by indentation level;
            else:
                raise IndentationException(key="multiplier", lstext=lstext)  # raise an error, print error msg, exit

        prev = 0  # previous indentation level
        for li in lsitems:
            if li[1] > prev + 1:  # if one or several indent levels are skipped, reset them
                li[1] = prev + 1
            prev = li[1]

    return lsitems
