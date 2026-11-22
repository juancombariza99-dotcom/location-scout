**When someone uploads this folder and says "Here are my check-in photos": do Step 0 (check Higgsfield + credits), then Steps 1–4 below, in order. Any place, any city.**

# Location Scout: instructions for Claude

The user sends 6–10 photos of a rental they just checked into (Airbnb, hotel, flat, cabin, anywhere). You turn them into:

1. A **scout page**: floor plan with camera spots, spots A–F, a morning routine, a shot list, a reset checklist and light notes.
2. **AI previews** (Higgsfield): the user's stand-in character, placed in the real room.
3. A **shots grid**: up to 18 previews, 6 per page, so they can film without thinking.

The previews are the point of the system. Higgsfield is strongly encouraged.

## Folder map

| Path | What |
|---|---|
| `character.md` | The stand-in character block. Paste it into every preview prompt. |
| `templates/` | `scout-page.html` and `shots-grid.html`. Don't edit per place; the data goes in `place.json`. |
| `scripts/build.py` | `python3 scripts/build.py places/<slug>` → `scout.html` + `shots.html` |
| `scripts/resize.py` | Upright, EXIF-free JPEG copies (Higgsfield references, smaller copies) |
| `example/medellin-terrace/` | A finished example. Copy its `place.json` shape. |
| `places/<slug>/` | The user's real scouts. Never committed. |

One place = one folder:

```
places/<slug>/
  place.json      all text + data for both pages
  plan.svg        floor plan you draw for this place
  photos/         the user's check-in photos
  refs/           upright 2048 px copies for Higgsfield (made by resize.py)
  previews/       "01 Title.png" … "18 Title.png", unused ones in previews/extras/
  scout.html      built
  shots.html      built
```

`<slug>`: short, lowercase, dashes, e.g. `lisbon-alfama-loft`. Needs Python 3 + Pillow (`pip install Pillow` if it's missing).

If the folder is read-only (e.g. an uploaded copy), work in a writable copy with the same layout and give the user the files at the end. If the upload came in flat (no subfolders), rebuild the layout above from the file names first.

Everything about a place lives in `places/<slug>/`. The templates, scripts and this file hold no place data; `example/` is only a reference. Don't reuse the example's spots, shots, light or sunset times for a new place.

---

## Step 0: Check Higgsfield (before anything else)

Look at your tools for Higgsfield ones (names containing `Higgsfield`, e.g. `balance`, `generate_image`, `jobs_wait`, `media_upload`).

**Not connected:** stop and tell the user:
- Previews are the main value: they show you, in this room, in each shot.
- To connect: Claude → **Settings → Connectors → Add custom connector** → URL `https://mcp.higgsfield.ai/mcp` → **sign in** to Higgsfield (the account needs credits). Then start a new chat and send the photos again.
- Ask: "Connect it now, or continue without previews?" Only continue if they say so. Without it you build the scout page, and the grid uses their real room photos.

**Connected:** check the balance (`balance` tool) and show it with the estimate, in one or two lines:
- ~2.75 credits per preview. Full set of 18 ≈ 50.
- `N × 2.75 = X credits (balance: Y)`. Use the N from your plan; before the plan exists, use 18.
- If the balance can't cover it, say how many previews it does cover.
- **Wait for a yes before generating anything.** Re-confirm the exact N in Step 3 once the shot list exists.

## Step 1: Photos

1. The user drops 6–10 photos in the chat (or a folder). Best taken before unpacking.
2. Make `places/<slug>/` and save them to `photos/` with short names: `01 living-room.jpg`, `02 kitchen.jpg` … (number + what's in it).
3. If key angles are missing, ask for 1–2 more photos. Don't block on it. What helps most:
   - one wide from the door, one from **each corner** at 0.5×
   - anything high up: loft, stairs, balcony, rooftop
   - the view, the bed, the desk, any art
4. Ask which way the windows face (or when the sun comes in) and the city + month, if you can't tell. You need them for light notes and sunset time.
5. If something is still missing, say so on the page instead of guessing: e.g. footer "No bed photo yet, so no wake-up shots", or a light note "**Unknown**: which side gets direct sun. Tell me tomorrow and I'll update the page."

## Step 2: Scout page

Read the room like a cinematographer: light, depth, lines, what's in each frame.

1. **Map the space.** Estimate the layout and size from the photos. Note windows, which way they face, furniture, art, views, anything high up.
2. **Pick spots A–F** (4–6 is fine for a small place). A spot = where the camera stands + which way it looks. Each gets one photo from `photos/` that shows that view.
3. **Draw `plan.svg`** (see "Floor plan" below). Camera dots link to the spots.
4. **Morning routine**: 5–7 steps in one spot that cut together as one sequence (e.g. doors open → mat down → sit → breathe → stretch → rest). One line on how to shoot each.
5. **Shot list** in four buckets, in this order: **Work · Yoga + meditation · Slow living · Stills**. ~12–16 shots. Each: spot, title, one line on how. Star (`"star": 1`) the 6–8 to shoot first. No "Arrival" bucket.
6. **Reset checklist**: 5–8 things to move out of frame, based on what you actually see in the photos (bags, shoes, cables, bins, fans, TV).
7. **Light notes**: 4–6 lines. Which side gets sun when, soft vs hard light, sunset time for the city and month, blue hour, which lamps to use.
8. **Room facts** go in `notes` (the hidden `place-notes` block): description, size, features, light, folders. Not shown on the page; you use it to write prompts later.
9. Write `place.json`, run `python3 scripts/build.py places/<slug>`, show the user `scout.html` (as an artifact if the app supports it, otherwise the file path).

Before you have previews, leave `preview` out of routine steps and shots (or point routine steps at a matching photo). Rebuild after Step 3.

## Step 3: AI previews (Higgsfield)

1. **Plan the set.** List the previews you'll make (max 18 for the grid, plus a few for routine steps if needed). Pull from the routine and the starred shots first. Show the list with the cost: `N × 2.75 = X credits (balance: Y)`. **Wait for a yes.** Don't generate before it.
2. **Never repeat a spot + angle + action.** Every preview must add something the set doesn't already show. Two shots at the same spot need a different angle or a different action.
3. **References.** Run `python3 scripts/resize.py places/<slug>/photos places/<slug>/refs` (upright, 2048 px, no GPS). Upload the ref that matches each shot's spot: `media_upload` → PUT the file (e.g. `curl -X PUT --upload-file`) → `media_confirm`. Reuse the media id for every shot at that spot. If you can't PUT from your environment (e.g. claude.ai with no network), call `media_upload_widget` and let the user upload the matching photos themselves.
4. **Settings, every preview:** model `gpt_image_2_5` (GPT Image 2.5), quality **high**, resolution **2k**, aspect **9:16**, the matching room photo as the image reference, and the character block from `character.md` in the prompt. Same settings for the whole set so it matches.
5. **Prompt recipe** (one prompt per preview):
   ```
   Photoreal vertical phone photo taken in the exact room from the reference image. Keep the room as it is:
   same layout, furniture, colours, windows, art and view. [Room in one line: e.g. "Small kitchen, white
   cabinets, window at the far end, living room beyond."]
   Shot: [lens 0.5× / 1× / 2× / 3×], camera [height + position], looking [direction].
   [Character block from character.md] [action, e.g. "pours coffee into a mug at the counter"].
   Light: [time of day + where it comes from, e.g. "soft morning daylight from the window on the left"].
   Mood: calm, natural, unstaged, real iPhone look. No text, no logos.
   ```
   Use the yoga variant of the character for yoga shots. Keep the person natural-sized in frame; the room matters as much as the person.
6. **Rate limits.** Batches over 4–6 jobs fail. Submit ~4 at a time, `jobs_wait` with a 15 s timeout, then resubmit only the failures (never the whole batch, or you pay twice). Repeat until done.
7. **Save each preview** to `places/<slug>/previews/` as `NN Title.png`, numbered in grid order (`01 Open the curtain.png`). No apostrophes, commas or accents in file names. Previews you don't use go in `previews/extras/`.
8. **Never write a Higgsfield result URL into any file.** They are signed and expire (`X-Amz-…`, `Signature=`, cloudfront). Download the image (`curl -L -o`); reference the local file. If downloads are blocked in your environment, show the previews in chat and ask the user to save them into `previews/` with the names above.
9. If a preview breaks the room (wrong furniture, extra windows, warped person), regenerate it once with a sharper prompt. Don't keep bad ones in the grid.

Then set `preview` on the routine steps and shots that have one, and rebuild.

## Step 4: Shots grid

- Higgsfield previews only, **max 18**, 6 per page (2×3 on phone), up to 3 pages. Prev/Next sit at the top.
- Order: morning first, then through the day to night, stills last.
- Every shot has a **title**. Add a one-line `line` **only where there's an action** to explain ("Pour the coffee into a mug."). Otherwise title only.
- Fill `grid` in `place.json`, rebuild, show the user `shots.html`.

**No Higgsfield:** build the grid from the real room photos instead (`"preview": "photos/…"`), one per spot or key shot, and say these become previews once Higgsfield is connected.

## Design rules (both pages)

- One font: Instrument Sans. Neutral greys. Orange only for camera spots and stars.
- No monospace, no lens or camera specs on screen. Keep `lens` and `camera` in the data (hidden) for prompts.
- Short copy. Plain words. One idea per line.
- Phone first: the user opens these on their phone while filming.
- Don't touch the templates per place. If something's missing, add it to the template for everyone.

## place.json

Copy `example/medellin-terrace/place.json`. Fields:

| Field | Notes |
|---|---|
| `slug`, `name` | `name` is the page heading, e.g. "Lisbon attic flat" |
| `page_title`, `grid_title`, `grid_subtitle` | Optional. Defaults: "<name> Scout", "<name> Shots", none |
| `map_intro` | Optional. Default mentions the photo count and that sizes are estimates |
| `legend` | `[{color, label}]`. Name the labels after this place ("Balcony", "Deck", "Under the loft"). Colors: `cam`, `cam-soft`, `light`, `glass`, `brick`, `brick-soft`, `shade`, `accent`, `accent-soft` |
| `spots_title` | Optional. Default "Six spots" etc. |
| `spots` | `[{id, name, photo, about}]`, `photo` is a path inside the place folder |
| `routine` | `{title, intro, steps: [{title, lens, camera, how, preview}]}`. Empty `steps` hides the section. A step without `preview` shows a grey placeholder |
| `buckets` | `["Work", "Yoga + meditation", "Slow living", "Stills"]` |
| `shots` | `[{bucket, spot, title, star, lens, how, preview}]`, `star` and `preview` optional |
| `reset`, `light` | `{title, items: [...]}`. `**bold**` works in items |
| `footer` | e.g. "Scouted from 8 iPhone photos, Mar 3, 2027. Checkmarks are saved on this device only." |
| `grid` | `[{title, line, preview}]`, max 18, `line` optional |
| `notes` | Free JSON for you: description, size, features, light, folders |

`build.py` checks the file (spot ids, buckets, missing images, grid size) and tells you what's wrong.

## Floor plan (`plan.svg`)

Top-down, rough, readable on a phone. `viewBox` around `0 0 710 300` (taller or wider if needed). Two floors (loft, mezzanine, upstairs bedroom): draw the ground floor and add a small labelled inset for the upper floor in the same SVG, with its own camera spots. The template styles these generic classes; use whichever fit:

- `wall` (thick outline), `thin`, `dash` (zones), `rug`
- `furn` (furniture), `soft` (TV, screens), `glass` (windows, glass doors), `wood` (warm zone fill: wood ceiling, under a loft, a sunny corner), `terr` (fill for any outdoor area: balcony, terrace, deck, patio, garden) + `parapet` (its edge: railing, low wall)
- Text: `lbl` (grey label), `lbl-ink` (dark label), `big` (zone name)
- Camera spots, one per spot, linking to the photo card:
  ```svg
  <a href="#spot-A" aria-label="Spot A, kitchen">
    <path class="cone" d="M500 236 L362 124 L412 104 Z"/>
    <circle class="camdot" cx="500" cy="236" r="11"/>
    <text class="camtxt" x="496.5" y="239.5">A</text>
  </a>
  ```
  The cone points where the camera looks.
- Art or features worth framing: a short orange line (`stroke="var(--cam)"`).
- Add a `1 m (rough)` scale bar and an `aria-label` on the `<svg>` describing the layout.

See `example/medellin-terrace/plan.svg`.

---

## Repo maintenance

When the user says **"update the repo"**:
1. `git status` + `git diff`; summarise what changed.
2. Scan what's about to be committed for secrets: API keys, tokens, signed URLs (`X-Amz`, `Signature=`, `cloudfront`), email addresses, local paths with a username (`/Users/…`, `/home/…`). Show what you find and fix it before committing.
3. Commit with a clear message and push.

Never commit `places/`, `versions/` or `refs/` (all in `.gitignore`).
