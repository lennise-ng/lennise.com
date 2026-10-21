# lennise.com

A personal site. Plain HTML, built from Markdown files by one small Python script.
No framework, no database, no JavaScript, nothing that phones home.

## How it's laid out

```
content/            ← everything you write lives here
  about.md          ← the About page. Its first paragraph is also the homepage intro.
  margins.md        ← short notes. One file, newest at the top or bottom, doesn't matter.
  essays/           ← one Markdown file per essay
  letters/          ← reader replies, one file per essay, named after the essay
static/
  style.css         ← the whole design. Colours and fonts are at the top.
  images/           ← put pictures here
templates/          ← the HTML skeletons. You shouldn't need to touch these.
build.py            ← turns content/ into docs/
docs/               ← the finished website. GitHub serves this folder. Don't edit it by hand.
```

## Writing an essay

1. Copy `content/essays/_template.md` to a new file named `YYYY-MM-DD-a-few-words.md`.
   The date prefix keeps the folder sorted; the words become the web address
   (`2026-10-14-malacca-traders-trust.md` → `lennise.com/essays/malacca-traders-trust/`).
2. Fill in the block at the top:

   ```
   ---
   title: What Malacca's traders knew about trust
   subtitle: One line that shows under the title and on the homepage.
   date: 2026-10-14
   tags: History · Entrepreneurship
   image: /static/images/malacca.jpg         (optional)
   image_caption: Where the picture is from.  (optional)
   ---
   ```

3. Write below it in Markdown. Blank line between paragraphs. `## Heading` for sections,
   `*italics*`, `**bold**`, `> quote` for a pull quote, `[text](url)` for links.
4. Leave `draft: true` in the top block and the essay is skipped at build time.
   Remove that line when it's ready.

The newest essay (by `date`) is the big one on the homepage.

## Pictures

Drop the file into `static/images/` and refer to it as `/static/images/filename.jpg`.
Keep them under about 300 KB each — resize to 1600px wide before adding, the site doesn't
do it for you. Inside an essay, a picture is just Markdown:

```
![caption text](/static/images/filename.jpg)
```

## Margins (short notes)

Open `content/margins.md` and add an entry anywhere in the file:

```
## 2026-10-21
The note itself. Can be more than one paragraph.
```

The heading is the date and must be `YYYY-MM-DD`. The three newest show on the homepage;
all of them show on `/margins/`.

## Letters (reader replies)

Letters arrive by email. To publish one, open (or create) `content/letters/<essay-slug>.md`
— the slug is the essay's filename without the date — and add:

```
## Reader's name, City
What they wrote. Ask first.

## Lennise
Your reply, if you have one.
```

They show under that essay, and the two most recent letters show on the homepage.

## Building and publishing

```
pip install markdown        (once)
python3 build.py
git add -A
git commit -m "New essay: whatever it's called"
git push
```

`build.py` rewrites `docs/` from scratch each time. GitHub Pages serves `docs/`,
so the site updates a minute or so after the push. Always commit `docs/` along with
the content — the server doesn't build anything, it just serves the files.

To look at the site locally before pushing:

```
python3 build.py && python3 -m http.server -d docs 8000
```

then open http://localhost:8000 in a browser.

## Changing the design

Everything is in `static/style.css`. The colours and fonts are in the `:root` block at the top.
The accent colour is `--accent`; a few alternatives are noted beside it.
The site name, tagline and email address are at the top of `build.py`.
