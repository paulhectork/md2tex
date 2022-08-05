# `md2tex` - a CLI to convert Markdown to TeXs

`md2tex` is a simple markdown to TeX converter. rather than using fancy object oriented libraries,
it locates elements of markdown syntax using regular expressions and translates them into TeX syntax.
it has only been tested with latin script so far. still a work in progress.

---
## features
- translation from markdown to TeX
- creation of a complete and valid TeX document
- saving to a custom file(path)

---
## markdown syntax
**currently supported**
- line breaks: paragraph changes using `\n\n`, `<br>` and `<br/>`
- **bold**, *italic* and `inline code` text. **warning**:
  - only bold and italics made using \* will be translated
- block quotes (lines beginning with `>`). **warning**: only non-nested block quotes -- or the outer
  level of a nested block quote --  will be rendered.
- multiline code; if possible, the code is colored thanks to `minted`
- ordrered and unordered lists, including nested lists. **warning** : 
  - this CLI is made to work with as-messy-as-possible data; 
    if your lists are messy (using different levels of space...),
    it will create messy nested lists too.
  - unordered lists will only be converted if they begin with `-`. any other list token
    will be ignored.
- titles and different title levels
- images
- URLs
- inline quotes : french and english style, nested quotes.
- footnose ; **warning**: loose footnotes (references in the body that point to nothing
  or footnote that point to nothing in the body) will be deleted.

**soon**
- ...?

**unsupported**
- markdown tables
- end-of-line backslashes to mark a line break
- strikethrough
- emojis
- tasks lists
- definition lists

---

## things that will mess with the output
- poorly formed markdown
- things that are currently not supported
- lists made using non-standart markdown syntax (lists not beginning with `-`...)
- multiple footnotes with the same key; for the footnote restructuration to work,
  there must be unique footnote numbers and only one note per footnote number.
- highly nested lists are not supported by default in LaTeX, but this can be changed in your preamble
- loose footnotes that point to nothing will be deleted

clean your file first ! you can also make the bulk of the translation using this cli and fine tune your `.tex` 
file later on.

---

## license
released under GNU GPL v3.
