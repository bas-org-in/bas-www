# bas-historic import notes

Base source: `mirrors/historic.bas.org.in/`

Imported:

- Static HTML archive for the old BAS content.
- 610 additional historic pages fetched from live `historic.bas.org.in` after
  the first link check showed they were referenced by `index.html` but missing
  from the original mirror.
- Selected BAS files under `files/` copied from `repos/bas-www/public/files`
  because old historic pages link to them.
- 7 unique old image/Gallery targets recovered from Wayback snapshots and
  stored under their old paths or `recovered-gallery/`.

Renamed:

Three pairs of posts have names that differ only in letter case. Windows
and the default macOS file system cannot hold both names of a pair in one
folder. One post of each pair has a new name with its date:

| Old name | New name | Other post, name kept |
| --- | --- | --- |
| `BAS_meeting.htm` | `BAS_meeting_2008-11-08.htm` | `BAS_Meeting.htm` |
| `Hi_everyone.htm` | `Hi_everyone_2008-03-29.htm` | `Hi_Everyone.htm` |
| `Venues.htm` | `Venues_2009-09-12.htm` | `VENUES.htm` |

`index.html` links to the new names. `public/.htaccess` sends the old
addresses to the new names with a permanent (301) redirect.

Excluded:

- `wget.log`
- duplicate alias mirror `mirrors/www.historic.bas.org.in/`, which matched
  `mirrors/historic.bas.org.in` byte-for-byte.

Known remaining issue:

- 33 unresolved internal links remain, all old Gallery/image assets that were
  not present in the source bundle, archive, mirror, probed live paths, or the
  checked Wayback host. See
  `provenance/evidence/source-inventory/unresolved-internal-links.md`.
