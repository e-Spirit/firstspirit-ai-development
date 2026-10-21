# Decisions

This folder starts empty on purpose. In the guided path you and the assistant fill it, one file per template, before the
template is built. The assistant builds from these files and the fragments in `design-system/fragments/`, not from memory.

A decision file names, for one template:

| What | Example |
|---|---|
| The template and its type | `hero`, section template |
| Each field: name, editor type, mandatory or not, and the key in `design-system/content/` it is filled from | `st_headline`, `CMS_INPUT_TEXT`, mandatory, `headline` |
| Anything fixed in the template and not editable | the arrow icon in a button |
| Where shared parts live | header and footer in a global content page |

Answers are written down the moment they are given, with the date. A skipped question is recorded as a default, so it can be revisited.
