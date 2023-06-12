import os
from bs4 import BeautifulSoup

# Name of the folder where Hugo generates the website
public_folder = "public"  # default: "public"

# Iterate over all files and folders
for root, dirs, files in os.walk(public_folder):
    # For every file...
    for file in files:
        # If file ends with .html (e.g. index.html or _index.html)
        if file.endswith(".html"):
            # Parse HTML
            soup = BeautifulSoup(open(os.path.join(root, file)), "html.parser")
            # For every image...
            for image in soup.findAll('img'):
                # Exclude images with empty src attribute
                if not image['src'] == "":
                    # If src attribute is url, skip the checking
                    if image['src'].startswith("http"):
                        continue
                    # If src attribute is absolute path (e.g. src="/image-1.jpeg" -> www.domain.tld/image-1.jpeg)
                    elif os.path.isabs(image['src']):
                        # Define path to image
                        # strip(os.sep) removes the leading slash from the path defined in the src attribute (otherwise os.path.join would ignore all previous mentioned directories)
                        image_path = os.path.join(os.path.dirname(
                            __file__), public_folder, os.path.normpath(image['src'].strip(os.sep)))
                    # If src attribute is relative path (e.g. src="image-1.jpeg" -> www.domain.tld/slug-of-current-html/image.jpeg)
                    else:
                        # Define path to image
                        image_path = os.path.join(os.path.dirname(
                            __file__), root, os.path.normpath(image['src']))
                    # If file doesn't exist
                    if not os.path.isfile(image_path):
                        # Print error message
                        print("ERROR: " + image_path + " referenced in " +
                              os.path.join(root, file) + " wasn't found")
