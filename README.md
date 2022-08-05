# `md2tex` - a CLI to convert Markdown to TeX

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
- **bold**, *italic* and `inline code` text
- block quotes (lines beginning with `>`)
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

**soon**
- footnotes
- ...?

**unsupported**
- markdown tables

---
## License
released under GNU GPL v3.
