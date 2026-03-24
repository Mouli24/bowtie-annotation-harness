#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
from typing import TYPE_CHECKING
import json
import platform
import sys
import traceback

from jsonschema.validators import validator_for
from packaging.version import parse

jsonschema_version = metadata.version("jsonschema")
use_referencing_library = parse(jsonschema_version) >= parse("4.18.0")

if use_referencing_library:
    import referencing.jsonschema
else:
    from jsonschema.validators import RefResolver

if TYPE_CHECKING:
    import io
    from jsonschema.protocols import Validator


ANNOTATION_KEYWORDS = [
    "title", "description", "default", "examples",
    "readOnly", "writeOnly", "deprecated", "format"
]


def collect_annotations(schema, instance, inst_path="", schema_path=""):
    """Recursively collect annotations from schema matching instance."""
    results = []

    if not isinstance(schema, dict):
        return results

    # Collect annotation keywords at this level
    for kw in ANNOTATION_KEYWORDS:
        if kw in schema:
            results.append({
                "location": inst_path,
                "keyword": kw,
                "value": schema[kw],
                "schema_path": schema_path,
            })

    # Recurse into properties
    if "properties" in schema and isinstance(instance, dict):
        for prop, subschema in schema["properties"].items():
            if prop in instance:
                results.extend(collect_annotations(
                    subschema,
                    instance[prop],
                    inst_path=f"{inst_path}/{prop}",
                    schema_path=f"{schema_path}/properties/{prop}",
                ))

    # Recurse into items (array)
    if "items" in schema and isinstance(instance, list):
        for idx, item in enumerate(instance):
            results.extend(collect_annotations(
                schema["items"],
                item,
                inst_path=f"{inst_path}/{idx}",
                schema_path=f"{schema_path}/items",
            ))

    # Recurse into $defs / definitions
    for defs_key in ("$defs", "definitions"):
        if defs_key in schema and isinstance(schema[defs_key], dict):
            for def_name, def_schema in schema[defs_key].items():
                results.extend(collect_annotations(
                    def_schema,
                    instance,
                    inst_path=inst_path,
                    schema_path=f"{schema_path}/{defs_key}/{def_name}",
                ))

    # Recurse into if/then/else
    for keyword in ("if", "then", "else", "allOf", "anyOf", "oneOf"):
        if keyword in schema:
            sub = schema[keyword]
            if isinstance(sub, list):
                for i, s in enumerate(sub):
                    results.extend(collect_annotations(
                        s, instance,
                        inst_path=inst_path,
                        schema_path=f"{schema_path}/{keyword}/{i}",
                    ))
            elif isinstance(sub, dict):
                results.extend(collect_annotations(
                    sub, instance,
                    inst_path=inst_path,
                    schema_path=f"{schema_path}/{keyword}",
                ))

    return results


@dataclass
class Runner:
    _started: bool = False
    _stdout: object = None
    _DefaultValidator: object = None
    _default_spec: object = None

    def __post_init__(self):
        self._stdout = sys.stdout

    def run(self, stdin=sys.stdin):
        for line in stdin:
            each = json.loads(line)
            cmd = each.pop("cmd")
            response = getattr(self, f"cmd_{cmd}")(**each)
            self._stdout.write(f"{json.dumps(response)}\n")
            self._stdout.flush()

    def cmd_start(self, version):
        assert version == 1
        self._started = True
        return dict(
            version=1,
            implementation=dict(
                language="python",
                name="jsonschema-annotations",
                version=jsonschema_version,
                homepage="https://python-jsonschema.readthedocs.io/",
                documentation="https://python-jsonschema.readthedocs.io/",
                issues="https://github.com/python-jsonschema/jsonschema/issues",
                source="https://github.com/python-jsonschema/jsonschema",
                dialects=[
                    "https://json-schema.org/draft/2020-12/schema",
                    "https://json-schema.org/draft/2019-09/schema",
                ],
                os=platform.system(),
                os_version=platform.release(),
                language_version=platform.python_version(),
            ),
        )

    def cmd_dialect(self, dialect):
        assert self._started, "Not started!"
        self._DefaultValidator = validator_for({"$schema": dialect})
        if use_referencing_library:
            self._default_spec = referencing.jsonschema.specification_with(dialect)
        return dict(ok=True)

    def cmd_run(self, case, seq):
        assert self._started, "Not started!"
        schema = case["schema"]
        try:
            Validator = validator_for(schema, self._DefaultValidator)
            assert Validator is not None

            if use_referencing_library:
                registry = referencing.Registry().with_contents(
                    case.get("registry", {}).items(),
                    default_specification=self._default_spec,
                )
                validator = Validator(schema, registry=registry)
            else:
                registry = case.get("registry", {})
                resolver = RefResolver.from_schema(schema, store=registry)
                validator = Validator(schema, resolver=resolver)

            results = []
            for test in case["tests"]:
                instance = test["instance"]

                try:
                    annotations = collect_annotations(schema, instance)
                except Exception:
                    annotations = []

                results.append({
                    "valid": validator.is_valid(instance),
                    "annotations": annotations,
                })

            return dict(seq=seq, results=results)

        except Exception:
            return dict(
                errored=True,
                seq=seq,
                context={"traceback": traceback.format_exc()},
            )

    def cmd_stop(self):
        assert self._started, "Not started!"
        sys.exit(0)


Runner().run()