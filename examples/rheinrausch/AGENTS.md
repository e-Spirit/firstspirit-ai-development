# Rules for the assistant in this example

You help build the RheinRausch one-pager (`BRIEF.md`) in the person's own FirstSpirit project, over the REST API, with the skills
of the FirstSpirit AI Toolkit. The root `AGENTS.md` applies as well; these rules add to it. This folder is the working folder:
`decisions/`, `templates/<name>/` and `STATE.md` live here.

## How to build

1. **Specification = `decisions/<template>.md`**, written from the person's decisions, plus the fragment in
   `design-system/fragments/` for the markup. Use exactly the names, fields, editor types and mandatory flags there. Do not add
   templates or fields. If something is missing or contradicts, ask or say so in two lines; the decision file wins over the design
   package. When the person answers a question, update the decision file at once and change only what the answer changes.
2. **Render from the fragments, not from the whole reference page.** `design-system/reference/index.html` is the visual target only.
3. **Rules.** Write the mandatory flags from the decision file as rules in the same step as the template.
4. **Components.** Use the editor component the decision names. Do not swap it for another without telling the person.
5. **Content now.** After a template exists, create the page or section and fill it from `design-system/content/site.json` and
   `experiences.json`, so the person sees it in the preview. The markup the page script expects is described at the top of
   `design-system/js/page.js`.
6. **Media.** Reference media by uid (`$CMS_REF(media:"uid")$`), never by file name. Do not assume a uid, a path or a folder: list the
   media of the project and find a file by its file name, because someone may have moved or renamed it. Uid for an upload: the file
   name without extension, lower case; `-`, `.` and spaces become `_` (`pin-heart.svg` is `pin_heart`); the folder goes in front
   only if that uid is taken by a different file. JPEG and PNG are PICTURE, everything else FILE. When you change the content of a
   medium, read its metadata before and after: file type and extension must be unchanged (a stylesheet stays a CSS file).
7. **Names.** Follow `firstspirit-template-design`: reference names of templates, folders and media are short, English, lower snake
   case, with no type prefix and no project prefix (`experience_card`, not `rr_experience_card`). Variables carry the prefix of their
   template type (`pt_`, `st_`, `lt_`, `ps_`).

The REST skill owns what the API can and cannot do. If a step needs something it does not cover, say so and hand that step over.

## Details the skills leave open

Seen while this example was built `[observed]` (REST module 0.0.25-beta, 2026-10). Skills do not cover everything; when a skill
says otherwise, the skill is newer and wins.

- A GOM sent over REST has no `<FORM>` root: put the editors directly in `<CMS_MODULE>`. `FS_CATALOG` takes no `hFill` and must
  name its section templates (`<TEMPLATES type="section">`).
- A new catalog card needs a UUID as `id`; option editors take `{"key","value"}`; a reference to a medium needs `uidType`
  `MEDIASTORE_LEAF`.
- The server checks link-template references when it writes a form: create the link template first.
- REST cannot create media folders, set "parse file" on a medium, or create datasets and table templates. Hand those over.
