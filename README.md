# Disc Tracker CLI

## Overview

Disc Tracker CLI is a Python Command Line Interface tool for tracking the prices and sell values of products (mainly disc like blu-rays and games) using the CeX API. The program allows users to:

- Add items to a local database by manually providing their product ID (due to API limitations).

- Store and view items along with their price and sell value.

- Update the database to track price changes.

## Features

1. Add Items to the Database

Uses the CeX Product ID to fetch the price and sell value from the CeX API and save it to the database.

2. View Items

Display all items stored in the database along with their current prices and sell values.

3. Update Items

Refresh the price and sell value of all items in the database to keep track of changes.

4. Track Price History

Maintain a record of price changes over time.

## Prerequisites

Python 3.8+

SQLite3 (used as the database for local storage)

pip (for installing dependencies)

## Installation

1. Clone the repository:

`git clone https://github.com/jakecreely/DiscTracker.git`

`cd cex-price-tracker-cli`

2. Install the dependencies:

`pip install -r requirements.txt`

3. Run the program:

`python main.py`

## Planned Improvements

### Enhanced Price History Display

Visualize price changes over time in a more user-friendly format (e.g., graphs or tables).

### Docker Containerization

Simplify deployment and ensure a consistent runtime environment by packaging the application into a Docker container.

### Automated Product ID Retrieval

Develop a feature to automate the retrieval of Product IDs from the CeX website.

### Web Interface

Build a lightweight web interface for easier interaction with the database.
