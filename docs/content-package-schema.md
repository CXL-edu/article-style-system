# Content package schema

This is a generic, sanitized schema for the public implementation. It is not a copy of a user's private content vault.

## Naming

```text
YYYYMMDD-NN-topic-short-name
```

- `YYYYMMDD`: package creation date;
- `NN`: two-digit sequence for packages created on that date;
- `topic-short-name`: a readable short topic, not a full publish title.

Do not put a precise timestamp in the directory name. Store it in frontmatter as `created_at`.

## Package layout

```text
content-package/YYYYMMDD-NN-topic-short-name/
├── source.md
├── content-master.md
├── fact-check.md
├── visual-plan.md
├── wechat/
│   ├── article.md
│   └── assets/
├── x-article/
│   ├── article.md
│   └── assets/
├── xiaohongshu/
│   ├── note.md
│   └── assets/
├── short-video/
│   ├── script.md
│   ├── storyboard.md
│   ├── captions.srt
│   ├── audio.mp3
│   ├── assets/
│   └── final.mp4
└── publish.md
```

The public repository uses English example paths for portability. A private vault may use localized filenames and folders while keeping the same logical fields.

## Content master frontmatter

```yaml
---
content_id: 20260818-01
title: Example topic
type: content-master
tags: [example, agent]
created: 2026-08-18
created_at: 2026-08-18T09:30:12+08:00
updated: 2026-08-18
revision: 1
status: master-draft
---
```

Required conceptual fields:

- `content_id`: stable ID shared by all platform outputs;
- `title`: working title;
- `type`: `content-master` for the canonical source;
- `created` and `updated`: date fields;
- `revision`: human-readable revision number;
- `status`: production state.

## Platform output frontmatter

Each platform output adds:

```yaml
platform: wechat|x-article|xiaohongshu|short-video
content_id: 20260818-01
status: draft
```

Recommended statuses:

```text
idea → researching → master-draft → fact-checked →
platform-draft → visual-ready → video-preview → ready-to-publish →
published → reviewing
```

## Asset naming

Use a stable sequence and a descriptive label:

```text
01-mechanism-flow.png
02-comparison-card.png
03-conclusion.png
```

For rendered videos, use a versioned filename and record the final selection in the publish record:

```text
final-v1.mp4
final-v2.mp4
```

## Implementation rules

- All outputs retain the same `content_id`.
- Platform adapters must not mutate the content master in place.
- Validation failures belong to the platform output status, not to the master facts.
- Local orchestrators may map these generic names to a private vault's localized names.
- Real credentials, login state, private assets, and personal publishing records remain outside this repository.
