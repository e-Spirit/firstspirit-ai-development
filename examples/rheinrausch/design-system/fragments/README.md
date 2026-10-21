# Fragments

The reference page cut into one file per template.
Render from these, not from the whole page: they are short and each holds one template's markup.
Visual target stays `reference/index.html`. Do not edit these files; change the reference page and cut again.

| File | Becomes |
|---|---|
| `page-shell.html` | the page template: head, header, content area, footer, dialog, script |
| `header.html`, `footer.html` | the same on every page (global content, not editor content) |
| `detail-dialog.html` | once per page, in the page template |
| `hero.html` | hero section |
| `experience-card.html` | one card (the first of six) |
| `filters-and-grid.html` | grid section: filter chips and the card grid |
| `quote.html`, `goals.html`, `business.html` | further sections (not part of day 1) |
