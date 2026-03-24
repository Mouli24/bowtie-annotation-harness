# Annotation Test Harness for python-jsonschema

This is my qualification task submission for GSoC 2026 
Bowtie: Add Support for Reporting on the Annotation Test Suite.

## What I Built

I wrote an annotation test harness for the `python-jsonschema` 
library. This harness lets Bowtie run the official JSON Schema 
Annotation Test Suite against python-jsonschema and check whether 
it correctly produces annotations.

Bowtie already had a validation harness for python-jsonschema, 
but there was no annotation harness. So I built one.

## What are Annotations?

In JSON Schema, annotations are metadata values that keywords 
attach to parts of your data during evaluation. For example:
```json
{
  "title": "User Name",
  "description": "Enter your full name",
  "type": "string"
}
```

Here `title` and `description` are annotations. They don't 
validate data — they describe it. Tools like documentation 
generators and form builders depend on these annotations.

## How It Works

The harness follows Bowtie's IHOP protocol — it reads JSON 
commands from stdin and writes results to stdout.

It supports 3 commands:

- `cmd_start` — returns implementation info
- `cmd_dialect` — sets which JSON Schema draft to use
- `cmd_run` — runs the test and collects annotations using 
  jsonschema's `iter_annotations()` API

## How to Run

Install dependencies:
```bash
pip install jsonschema packaging
```

Test it manually:
```bash
echo '{"cmd": "start", "version": 1}' | python bowtie_jsonschema_annotations.py
```

Or use the full test flow:
```powershell
@'
{"cmd": "start", "version": 1}
{"cmd": "dialect", "dialect": "https://json-schema.org/draft/2020-12/schema"}
{"cmd": "run", "seq": 1, "case": {"schema": {"title": "My Schema", 
"properties": {"name": {"description": "Your name"}}}, 
"tests": [{"instance": {"name": "Mouli"}}]}}
{"cmd": "stop"}
'@ | python bowtie_jsonschema_annotations.py
```

Expected output:
```json
{"seq": 1, "results": [{"valid": true, "annotations": [
  {"location": "", "keyword": "title", "value": "My Schema"},
  {"location": "/name", "keyword": "description", "value": "Your name"}
]}]}
```

## Supported Drafts

- JSON Schema Draft 2020-12
- JSON Schema Draft 2019-09

## Files
```
python-jsonschema-annotations/
├── bowtie_jsonschema_annotations.py  ← main harness file
└── Dockerfile                         ← for containerized use
```

## What I Learned

While working on this I learned how Bowtie's IHOP protocol works,
how annotations are different from validation, and how 
python-jsonschema's iter_annotations() API collects annotation 
values during schema evaluation.

This helped me understand the full picture of what this GSoC 
project is trying to solve — right now Bowtie can only test 
validation, but annotations are equally important and this 
harness is the first step toward fixing that.

## Demo Video
https://drive.google.com/file/d/1FFFcAb8WYniOY0ioh6Rzfrk4BZJDr-xT/view?usp=sharing