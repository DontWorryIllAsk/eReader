import sys

from src.app import EReaderApp


def main() -> None:
    """Application entry point."""
    app = EReaderApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
