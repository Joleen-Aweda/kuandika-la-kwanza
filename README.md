# Kuandika — Darasa la Kwanza

Release-ready, offline-capable accessible pupil's book in Kiswahili.

Open `index.html` directly or serve this directory with a static web server.
The reading order is defined in `content/pages.json` and contains 122 pages,
including the front and back covers. Toolbar and video numbering starts at 1.

## Current release

- Responsive toolbar based on the Writing Standard 1 reader, with mobile
  accessibility sheets and Kiswahili labels.
- Audio controls adapt to narrow screens and remain anchored when resizing.
- Sign-language video stays clear of the navigation and audio controls.
- Unreferenced assets and development-only files have been removed. Runtime
  data, mapped media, legal notices, and repository metadata are retained.

The book is a static site: there is no server build or database migration.
`.nojekyll` is retained for static hosting. The existing LMS adapter is preserved;
no new ZIP or SCORM package is generated for this release.

Release checks include all page/resource links, both language media mappings,
offline-data consistency, JavaScript syntax, and browser navigation and controls
at desktop, tablet, and mobile sizes down to 320px. Historical development tools
and removed tracked assets remain recoverable from Git history. If a release
regression is found, revert the release commit and repeat these checks.
