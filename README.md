# Replication Pack :: Examining Inequality in Park Quality for Promoting Health Across 35 Global Cities

## Data

* `scores_cities.csv` Park activities scores of all cities.
* `fingerprints_cities.csv` All raw counts of elements and spaces in the parks of all cities.
* `ignored_keys.txt` Ignored OSM Keys
* `ignored_keys.txt` Ignored OSM Values
* 
All files can be found in the `data` folder.

## Setup

* Install [Python 3.9](https://www.python.org/downloads/release/python-390/).
* Install a current version of [R](https://www.r-project.org)
* Install and start a [couchDB](https://couchdb.apache.org/)
* Install Python dependencies: `pip install -r requirements.txt`
* Install R dependencies: `Rscript dependencies.R`

## Scripts:

* `1-osm.py`: Extracts the parks and their elements and spaces from OpenStreetMap and stores them in a couchDB. `python 1-osm.py --couchdb http://USERNAME:PASSWORD@127.0.0.1:5984 --city vienna --osm_id 109166 --region europe/austria`
* `2-park_fingerprints.py`: Counts the elements and spaces within each park. Example invocation: `python 2-park_fingerprints.py --couchdb http://USERNAME:PASSWORD@127.0.0.1:5984 --city vienna`
* `3-park_scores.R`: Compute the park activity scores. Example invocation: `Rscript 3-park-scores.R --city_name vienna`