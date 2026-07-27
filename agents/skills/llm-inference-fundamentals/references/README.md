# LLM inference handbook source map

The knowledge base keeps both source editions intact beneath one skill:

| Edition | Snapshot | Entry point | License |
| --- | --- | --- | --- |
| BentoML | `ea07b2ccd9b35db810763fc76980b26be1d2b871` | [BentoML introduction](bentoml/introduction.md) | [CC BY 4.0](bentoml/LICENSE) |
| Modular | `317b9816ec3080031333ed9ee44dfce919763bf7` | [Modular introduction](modular/index.md) | [CC BY 4.0](modular/LICENSE) |

BentoML joined Modular through an acquisition announced on 2026-02-10, and the
editions share Git ancestry. They remain separately attributed because their
snapshots use different branding and content. Files are not combined line by
line because that would obscure provenance and removed material. `../SKILL.md`
provides unified terminology and benchmark rules. It also defines metric usage,
the tuning sequence and paired topic routes.

Use the Modular snapshot for its newer explanations and expanded topics. Check
the BentoML snapshot for the earlier treatment and for useful material that was
later removed or reframed. When they differ, cite the edition and snapshot. Do
not present one wording as a consensus claim.

The directory structure below each edition mirrors that edition's handbook:

- `llm-inference-basics/`
- `getting-started/`
- `model-preparation/`
- `model-interaction/`
- `inference-optimization/`
- `kernel-optimization/`
- `infrastructure-and-operations/`

See [UPSTREAM.md](../UPSTREAM.md) for repository URLs and transformation
details, plus licenses and the reproducible import command.
