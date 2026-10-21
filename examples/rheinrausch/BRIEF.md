# RheinRausch: the brief

*RheinRausch is fictitious. Everything below is made up for this example.*

> „We don't want another boring tourism website. We want people to see the Rhine and
> immediately think: **I NEED TO DO THAT.**"
> *(the RheinRausch CEO, fictional)*

## Who they are

**RheinRausch** turns Cologne into an interactive playground for tourists, locals and companies.
Colourful, energetic, a little cheeky. Tagline: **Erlebe Köln. Ganz neu.**

| Line | What it is |
|---|---|
| 🚲 **Rides** | Guided e-bike tours |
| 🛶 **River** | Kayak and SUP experiences on the Rhine |
| 🎭 **Nights** | Nightlife and culture tours |
| 🍻 **Kölsch Experience** | Brewery and food tours |
| 🧩 **Quest** | Gamified city scavenger hunts |
| 🏢 **Business** | Team events and corporate experiences |

## The situation

Today the offers are scattered across several websites, PDFs, booking systems and social media
channels. RheinRausch wants to become **the coolest digital destination for experiencing Cologne**:
a digital experience that inspires visitors before they arrive, helps them find the right
experience, and makes them want to book it immediately.

## Three business goals

| | Goal | In one line |
|---|---|---|
| 🌈 | **Inspire** | Make people want to experience Cologne. |
| 🎯 | **Personalize** | Help visitors find an experience that fits them. |
| 💸 | **Convert** | Turn inspiration into bookings. |

## What they need technically (deliberately vague)

> The new platform should be flexible enough to support new experiences, new channels and new
> partners without rebuilding the website every time.

How you read that is up to you: content model, APIs, headless or static, personalisation,
integrations, AI. Make a choice and be ready to explain it.

## Your task: you are the agency, not RheinRausch

You are the service provider trying to win this project. Build the page and make it
**a real, clickable demo**.

### The experience (what RheinRausch's customers would see)

A branded one-pager. The look is done for you (see "What you get"); your work is the
FirstSpirit side: templates, forms, content and the page in the preview.

- **Must:** hero with the tagline, the six experience lines as cards, one experience detail that opens on click.
- **Must:** the experiences are **content, not hard-coded HTML**. An editor adds a seventh experience without touching code.
- **Should:** help me find the right one. Filter chips, a short quiz or a "plan my day" widget (goal: Personalize).
- **Should:** a booking call to action that does something visible (goal: Convert).
- **Could:** search, a second language, images per experience, an AI-drafted experience description in the RheinRausch voice.

## What you get

Everything is in the folder `design-system/` next to this file. You do not design anything.

| What | Where |
|---|---|
| **Look to match**: finished one-pager as plain HTML | `design-system/reference/index.html` (open it in a browser, no server needed) |
| Design tokens, components, extras (`rr-` classes, Tailwind theme) | `design-system/css/` (tokens, components, extras, tailwind-theme, fonts) and `design-system/js/page.js` (filter, detail dialog, demo booking) |
| **Content to start from**: six experiences, hero, quote, goals | `design-system/content/experiences.json`, `design-system/content/site.json` |
| Logos (SVG), icons, ribbons, stickers | `design-system/logos/`, `icons/`, `ribbons/`, `stickers/` |
| Six images (AI-generated for this example) | `design-system/assets/` |
| The reference page cut into one file per template | `design-system/fragments/` (see its README) |

Branding in one breath: Rheinblau, cyan, pink, yellow and green on a warm paper background,
chunky headlines, big rounded corners, one ribbon and one tilted sticker per screen. Colours are a
starting point: remix them if your idea needs it.

Voice: short, warm, cheeky. Cologne in-jokes welcome. The page is in German.
