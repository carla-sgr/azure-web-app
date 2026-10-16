def main():
    """Entry point for the API activity application."""
    from azure_web_app.app import run_app

    run_app(debug=True)
