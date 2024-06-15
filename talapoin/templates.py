from jinja2 import Loader, Environment

class FallbackLoader(Loader):
    """
    A Jinja loader that first tries a function to load the template,
    then falls back to the filesystem loader.
    """

    def __init__(self, load_func, filesystem_loader):
        self.load_func = load_func
        self.filesystem_loader = filesystem_loader

    def get_source(self, environment, template):
        """
        Attempts to load the template from the load_func first.
        If that fails, falls back to the filesystem loader.
        """
        try:
            source, filename, uptodate = self.load_func(template)
            return source, filename, uptodate
        except (LookupError, NameError):
            # Template not found with the function, try filesystem
            return self.filesystem_loader.get_source(environment, template)

def custom_template_loader(template_name):
    # Implement your custom logic to load the template here
    # This example just raises an exception for demonstration
    raise LookupError("Template not found with custom logic")

# Create the filesystem loader
filesystem_loader = FileSystemLoader("templates")

# Combine the loaders
combined_loader = FallbackLoader(custom_template_loader, filesystem_loader)

# Create the Jinja environment with the combined loader
env = Environment(loader=combined_loader)
