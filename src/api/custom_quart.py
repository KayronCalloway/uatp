from quart import Quart


class CustomQuart(Quart):
    """A custom Quart application class with modified default configuration."""

    # By overriding the class attribute, we ensure the config is present
    # before the super().__init__ call where the error occurs.
    default_config = Quart.default_config.copy()
    default_config["PROVIDE_AUTOMATIC_OPTIONS"] = False
