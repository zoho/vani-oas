# Bundled specification

`vani-api.json` is the whole Vani API in one document — 162 operations, 539 schemas.

Use it when you want a single client for the entire API:

```bash
openapi-generator generate \
  -i v1/bundled/vani-api.json \
  -g python -o ./vani-client
```

## Use this *or* the per-resource documents, not both

The documents in the parent directory — `editions.json`, `canvas.json`, and the
rest — are subsets of this file. Every operation here appears in exactly one of them.

Generating from this file **and** from a per-resource file into the same project gives
you two copies of every shared type. Pick one:

| You want | Use |
|---|---|
| a client for the whole API | this file |
| a smaller client for one area | the per-resource document for that area |

`../index.json` lists every document with its operation and schema counts, so you can
choose without opening them.
