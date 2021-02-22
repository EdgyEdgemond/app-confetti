import dotenv


def fetch_to_env(override=True):
    """Searches for an .env file recursively up the tree from cwd to root.

    The env var should contain standard VARIABLE="VALUE" lines. Lines prefixed
    with a # are ignored as comments. White space is ignored.

    The contents of the env file will be loaded in to os.environ
    """
    dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True), override=override)
