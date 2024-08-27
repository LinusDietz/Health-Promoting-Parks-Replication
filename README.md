# Replication Pack - Assessing the Health Potential of Parks in 35 Cities Worldwide
## Data

* `lexicon.csv` The lexicon of OSM tags and the corresponding health-promoting activity category.
* `scores_cities.csv` Park health scores of all cities.
* `fingerprints_cities.csv` All raw counts of elements and spaces in the parks of all cities.
* `ignored_keys.txt` Ignored OSM Keys
* `ignored_values.txt` Ignored OSM Values

All files can be found in the `data` folder.

## Setup

* Install [Python 3.9](https://www.python.org/downloads/release/python-390/).
* Install a current version of [R](https://www.r-project.org)
* Install and start a [couchDB](https://couchdb.apache.org/)
* Install Python dependencies: `pip install -r requirements.txt`
* Install R dependencies: `Rscript dependencies.R`

## Scripts:

* `curl -X PUT http://<USERNAME>:<PASSWORD>@127.0.0.1:5984/osm_tags_cache_osmium_<CITY_NAME>` create a database for each city
* `1-osm.py`: Extracts the parks and their elements and spaces from OpenStreetMap and stores them in a couchDB. Example
  invocation: `python 1-osm.py --couchdb http://<USERNAME>:<PASSWORD>@127.0.0.1:5984 --city vienna --osm_id 109166 --region europe/austria`
* `2-park_fingerprints.py`: Counts the elements and spaces within each park. Example invocation: `python 2-park_fingerprints.py --couchdb http://<USERNAME>:>PASSWORD>@127.0.0.1:5984 --city vienna`
* `3-park_scores.R`: Compute the park health scores. Example invocation: `Rscript 3-park-scores.R --city_name vienna`

## Visualization

The `visualization` folder contains a web-based interface to explore the park scores. It can be viewed by opening the `index.html` file.
