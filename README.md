# Auto-CMT

This repository contains a Python script for interacting with the CMT (Conference Management Toolkit) system, specifically tailored for the IJCAI 2024 conference. The script allows you to fetch reviews, meta-reviews, discussion messages, and author feedback for the papers you are reviewing or meta-reviewing in the conference.

## Installation

Clone the repository:
```bash
git clone https://github.com/DominikPeters/auto-cmt.git
```
Navigate to the project directory:
```bash
cd auto-cmt
```
Install the required dependencies:
```bash
pip install requests rich
```

## Usage
Pull the latest changes from the repository to ensure you have the most up-to-date version:

```bash
git pull
```
Run the fetch.py script:

```bash
python fetch.py
```

The script will prompt you for the following information:
* Your CMT username (email)
* Your CMT password
* The conference ID (enter `IJCAI2024`)
* Whether you are a meta-reviewer (answer `Y` or `N`)
Note: The script will save your credentials and conference information locally for convenience. This allows you to quickly refetch the data when things have changed without re-entering the information.

After the fetch.py script completes, run the html.py script:
```bash
python html.py
```
This script generates an HTML file (`reviews.html`) that provides a quick overview of the reviews, meta-reviews, discussion messages, and author feedback for each paper.

Open the generated `reviews.html` file in a web browser to view the formatted review information.
The HTML file presents a summary of each paper, including the paper number, title, number of reviews, review scores, and the number of discussion messages. You can expand each paper's details to see the discussion messages and individual reviews. The reviews are summarized with the reviewer's recommendation, confidence, and knowledge level. Clicking on a reviewer's summary reveals more detailed information about their review.

By running these scripts, you can easily fetch and analyze the review information from the CMT system for the IJCAI 2024 conference, saving time and effort in navigating through the CMT interface.