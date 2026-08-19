# Content production pipeline

This repository contains the public, platform-neutral implementation layer for a multi-platform content system. Personal editorial memory, account state, real content, and publish records belong in a private vault, not in this repository.

## Canonical model

One topic produces one content package:

```text
source material and facts
  -> content master
  -> visual plan and reusable assets
  -> platform adapters
       -> WeChat article
       -> X Article
       -> Xiaohongshu note
       -> vertical video package
  -> validation
  -> draft or publish through an explicit platform gate
```

The content master is the source of truth for facts, evidence, terminology, claims, and narrative structure. Platform outputs may change tone, length, title, layout, and call to action, but must not silently change verified facts or conclusions.

## Stages

1. **Collect** public source material and preserve source links.
2. **Research** facts, evidence, uncertainty, and claims that need verification.
3. **Write the content master** with audience, thesis, outline, examples, terminology, visual anchors, and video points.
4. **Plan visuals** before rendering platform assets.
5. **Generate platform outputs** with independent adapters.
6. **Render and validate assets** for dimensions, overflow, and content consistency.
7. **Build the video package**: voiceover script, storyboard, captions, audio, and 1080×1920 MP4. The reusable asset-slide implementation is documented in [`docs/content-video-pipeline.md`](content-video-pipeline.md).
8. **Create drafts** and record output status.
9. **Publish only through an explicit gate** appropriate to the platform.
10. **Record results** outside this public repository in the private operating vault.

## Output contract

Each platform adapter should produce an inspectable package with:

- a platform-specific Markdown or structured text file;
- references to the shared `content_id`;
- platform-specific assets or asset references;
- validation output;
- an explicit status such as `draft`, `ready-to-publish`, `published`, or `failed`.

The repository can provide generic templates and code. A local orchestrator is responsible for selecting a topic, reading private editorial rules, supplying local paths, and deciding whether a publish gate may be opened.

## Platform strategy

| Output | Reuse from the master | Adapter-specific work |
|---|---|---|
| WeChat article | Main claims, outline, examples, diagrams | WeChat reading rhythm, tables, cover, CTA |
| X Article | Main claims, outline, body images, references | Faster opening, X context, links, Article editor |
| Xiaohongshu note | Key claims and visual facts | Short title, 6–9 cards, one point per card, topics |
| Vertical video | One thesis, examples, reusable visuals | Hook, voiceover, storyboard, captions, timing |

## Safety boundary

This public implementation must not contain:

- tokens, cookies, passwords, browser profiles, or API secrets;
- personal absolute paths;
- real account identifiers or private analytics;
- private source material or unpublished personal content;
- scripts that publish without an explicit local authorization policy.

The X Article adapter in `adapters/x/` is intentionally a draft-oriented reference implementation. Platform permission, DOM selectors, login state, and final publish authorization remain local concerns.
