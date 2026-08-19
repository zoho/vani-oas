# Vani OpenAPI Specification (OAS) v1

OpenAPI 3.1 specifications for the [Vani](https://www.vanihq.com) REST API.

Use these files to explore the API, generate a client SDK in your language, or
drive Vani from a tool that speaks OpenAPI.

---

## Repository structure

```
v1/
  index.json             machine-readable catalogue of every document below

  bundled/
    vani-api.json        every operation, in one document
    README.md            when to use it, and when not to

  editions.json          Editions, subscription, templates
  teams.json             Teams, team members, team requests
  spaces.json            Spaces, space members, space requests
  zones.json             Zones, versions, per-zone sharing
  elements.json          Shapes, connectors, group shapes, frames, text
  search.json            Content search
  external-share.json    Public sharing of a space

  structures.json        Structured creation — mindmaps, flowcharts, kanban, tables
  layout.json            Placement, alignment, tidy, spatial queries, connections
  navigation.json        Relationships, traversal, visual navigation
  tables.json            Table and database-table operations
  text.json              Text mutation and styling
  data.json              Batch read/mutate escape hatch

python/
  sample_api_runner.py   authenticate and call the API, end to end
  requirements.txt       the one dependency the sample needs
```

**Every file is a complete, standalone OpenAPI document.** It carries its own
`servers`, `securitySchemes`, and exactly the component schemas its own
operations need — so you can import any one of them on its own without
resolving references into the others.

### Which file do I want?

| You want | Use |
|---|---|
| a client for one area of the API | that area's document, e.g. `v1/elements.json` |
| a client for the whole API | `v1/bundled/vani-api.json` |
| to decide without opening them | `v1/index.json` — every document with its operation and schema counts |

`bundled/vani-api.json` is the **same operations** as the per-resource documents,
collected into one file. Generate from the bundle *or* from the per-resource
documents — not both, or you will get two copies of every shared type. That is
why it sits in its own directory rather than beside them.

---

## Concepts

Vani nests four resources. Almost every path carries the whole chain:

| Resource | What it is |
|---|---|
| **Edition** | The top-level tenant. Everything belongs to an edition. |
| **Team** | A group of people inside an edition. |
| **Space** | A project — a container of related boards. |
| **Zone** | A single board (document), and the canvas objects on it. |

```
/vani/api/v1/editions/{edition_id}/spaces/{space_id}/zones/{zone_id}/shapes
```

---

## Getting started

### 1. Explore the spec

Import any file into [Swagger Editor](https://editor.swagger.io),
[Swagger API Hub](https://support.smartbear.com/swaggerhub/), or Postman —
paste the raw URL of the file, or upload it directly.

### 2. Pick your data centre

Every document declares one templated server:

```
https://api.app.vanihq.{dc}
```

`{dc}` is your edition's data-centre TLD — `com`, `eu`, `in`, `com.au`, `ca`,
`sa`, or `ae`. It defaults to `com`. Most tools
render this as a dropdown; set it to match the domain you sign in on.

### 3. Authenticate

Vani uses OAuth 2.0 (authorization code grant) through Zoho Accounts. Register
a client at the [Zoho API Console](https://api-console.zoho.com) to get a
**Client ID** and **Client Secret**, then exchange an authorization code for a
**refresh token**.

Scopes are granular and named `Vani.<resource>.<ACTION>` — for example
`Vani.spaces.READ` or `Vani.teams.UPDATE`. **Each operation declares exactly
the scopes it needs under `security`; request only those.** Reading them out of
the spec is more reliable than guessing from the path.

### 4. Generate an SDK

Any OpenAPI 3.1 generator works. With
[openapi-generator](https://openapi-generator.tech):

```bash
openapi-generator generate \
  -i v1/bundled/vani-api.json \
  -g python \
  -o ./vani-python-sdk
```

Swap `-g` for `java`, `typescript-axios`, `go`, and so on. To generate a
smaller client for one area, point `-i` at that area's file instead.

### 5. Run the sample

`python/sample_api_runner.py` shows the full loop — refresh the access token,
call the API, handle the response envelope. See the comments at the top of the
file for setup.

---

## Reading the spec

A few Vani-specific conventions worth knowing before you generate a client.

**Responses are enveloped.** Most endpoints return
`{"status": ..., "data": ..., "message": ...}`. The exception is
`GET /vani/api/v1/openapi`, which returns the OpenAPI document itself — an
OpenAPI document inside an envelope would no longer be one.

**Numbers are strings.** Every numeric field is typed `string` with the numeric
`format` preserved. Vani IDs are 64-bit, and JavaScript loses precision above
2^53, so numbers are stringified uniformly rather than field by field.

**Some parameters carry JSON as text.** A number of query parameters hold a
whole JSON document as a *string*. Those declare their shape the standard way:

```jsonc
{
  "type": "string",
  "contentMediaType": "application/json",
  "contentSchema": { "$ref": "#/components/schemas/SpaceOperation" },
  "x-vani-stringified": true
}
```

Send a JSON string, not a JSON object. `x-vani-stringified` is a duplicate
marker for tools that do not read `contentMediaType`.

**`x-vani-oneof-groups`** documents fields where exactly one of a set is
expected. It is documentation, not a JSON Schema `oneOf` constraint — a strict
`oneOf` would reject payloads the server accepts.

**Every operation says what it does before you call it.** Four extensions are
published on all 162 operations:

```jsonc
"x-vani-operation-type": "READ",        // READ · CREATE · UPDATE · DELETE
"x-vani-read-only":      true,          // safe to call speculatively
"x-vani-destructive":    false,         // removes data when true
"x-vani-throttle":       { "duration": "1M", "threshold": 60 }
```

`x-vani-throttle` is the **rate limit** for that operation — here, 60 requests
per minute, counted per user. Limits differ per endpoint, so read them from the
spec rather than assuming one global ceiling. Exceeding one returns `429`.

`x-vani-read-only` and `x-vani-destructive` are derived from the operation type,
not from the HTTP method: several endpoints delete through `POST` because the
request body describes what to remove. Trust the extensions over the verb.

**`x-enumDescriptions`** gives the meaning of each allowed value, alongside the
standard `enum`:

```jsonc
"enum": ["ALL_SPACES", "SHARED_SPACES", "FAVOURITES"],
"x-enumDescriptions": {
  "ALL_SPACES":    "All spaces within the edition.",
  "SHARED_SPACES": "Spaces shared with you.",
  "FAVOURITES":    "Spaces the user has marked as a favourite."
}
```

Not every enum carries it yet. Where it is absent the values are still valid;
they are simply not yet described.

**`x-vani-schema`** repeats the `contentSchema` of a stringified parameter for
tools that do not resolve `contentSchema`. Same target, no extra meaning.

**`x-vani-transitional`** marks operations under `/sdk/v1/` that do not yet
have a REST equivalent. They work and are supported, but their path and shape
may change once the REST version ships. Everything in `structures.json`,
`layout.json`, `navigation.json`, `tables.json`, `text.json`, and `data.json`
carries this marker.

**Response payloads are typed where we can prove the shape.** Every response
declares the envelope; 40 of the 162 operations also type the `data` payload.
The rest leave `data` unconstrained rather than guess, so a generated client
returns a loosely-typed object for those. This is being closed operation by
operation.

---

## Versioning

Specs are versioned by directory. `v1/` tracks the v1 API; a future major
version lands beside it as `v2/` rather than replacing it.

---

## Licence

Apache License 2.0 — see [LICENSE](LICENSE). You are free to use these
specifications, and any client code you generate from them, in your own
projects.

---

## Support

Full API documentation: <https://www.vanihq.com/resources/api/doc/>

These files are generated from the Vani server's own security and contract
definitions on every release, so they describe the API as deployed. Please
report anything that looks wrong against the documentation site above — a
mismatch is a bug in the generator, not a stale hand-edit.
