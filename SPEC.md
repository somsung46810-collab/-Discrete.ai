# Discrete.ai Pipeline Specification

## Signature

`CommitCompile(Clone, File) -> Result`

## Parameters

- `Clone`: repository working directory.
- `File`: repository-relative source file.

## Processing stages

1. Read the selected file as bytes.
2. Decode text using UTF-8.
3. Represent each byte in hexadecimal.
4. Split each byte into high and low four-bit fields.
5. Parse source text and report syntax errors.
6. Print a structured result.
7. Repeat through a read-evaluate-print loop.
8. Produce a commit manifest containing the path, digest, and commit message.

## Result fields

- repository path
- relative file path
- SHA-256 digest
- packed hexadecimal preview
- syntax evaluation
- compile status
- commit manifest

## Safety constraints

- Reject paths outside the repository root.
- Do not evaluate arbitrary source expressions.
- Do not invoke shell commands from the REPL.
- Require reviewed version-control actions for repository writes.
