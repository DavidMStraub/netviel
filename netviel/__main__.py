from .api import create_app


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the netviel app locally")
    parser.add_argument(
        "--port", type=int, help="Port to use (defaults to 5000)", default=5000
    )
    args = parser.parse_args()

    app = create_app()
    app.run(port=args.port)
