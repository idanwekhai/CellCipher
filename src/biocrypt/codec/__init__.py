"""Framework-agnostic text <-> DNA codec. No FastAPI/pydantic imports here --
this package is usable standalone (CLI, notebook, tests) and is what both
`biocrypt.api` and any future frontend-embedded runtime should call through.
"""
