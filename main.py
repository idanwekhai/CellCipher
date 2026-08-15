"""Dev entrypoint: `uv run main.py` starts the API + web interface on :8000."""

import uvicorn


def main() -> None:
    uvicorn.run("biocrypt.api.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
