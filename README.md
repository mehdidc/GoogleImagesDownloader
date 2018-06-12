# How to install requirements

First, you need to install phantomjs.

Then the rest is in requirements.txt:

```pip install -r requirements.txt```

# How to use

Usage example:

```python download.py  keywords_file.txt --out-folder=out --nb-per-class=1000```

where keywords_file.txt contains a list of keywords, one per line.
The script download.py will create a folder for each keyword containing the images.


