# 🧳 Travel Planning and Flight Analysis
<div style="text-align: center;">
  <img src="assets/travel_scraping.png" alt="portada" />
</div>

## 📝 Project Overview

This project focuses on scraping and analyzing data from various travel-related platforms, including flights, accommodations, and activities. The goal is to provide insights into pricing trends, flight availability, accommodation costs, and activity options across different destinations, with the purpose of suggesting more tailored travel options to our customers.

Key questions we aim to address include:

1. What are the price trends for flights and accommodations across different cities?
2. How do flight durations compare between destinations?
3. What is the cost of accommodation per city, week and type of accommodation?
4. What types of accommodation are more available across different cities?
5. What are the top-rated activities available in key destinations?

The sources for this project feature 2 scraped websites and an API integration:
- Air scrapper (API): For airline prices 
- Booking (scraped website): For accommodation solutions
- Civitatis (scraped website): Source of activities data in each destination

## 📁 Project Structure

```bash
Travel-Planning-Analysis/
├── assets/              # Images and other assets
├── data/                # Raw and processed data
│   ├── accommodations/
│   ├── activities/
│   ├── airport_codes/
│   └── flights/
├── notebooks/           # Jupyter notebooks with data cleaning and extraction
│   ├── analysis.ipynb
│   ├── data_cleaning_.ipynb
│   └── data_extraction_.ipynb
├── src/                 # Scripts for data processing and analysis
│   ├── analysis_support.py
│   ├── data_cleaning_support.py
│   └── data_extraction_support.py
├── .env                 # Environment variables
├── .gitignore           # Ignored files for Git
├── Pipfile              # Dependency management file
├── Pipfile.lock         # Lockfile for exact versions of dependencies
└── README.md            # Project documentation (this file)
```

## 🛠️ Installation and Requirements

This project requires the following tools and libraries:

- **Python 3.11+**
- **pandas** (for data manipulation)
- **numpy** (for numerical operations)
- **selenium** (for web scraping and browser automation)
- **geopy** (for geolocation services)
- **requests** (for HTTP requests)
- **beautifulsoup4** (for web scraping)
- **webdriver-manager** (to automatically manage Selenium web drivers)
- **scipy** (for scientific computations)
- **matplotlib** (for data visualization)
- **seaborn** (for advanced visualizations)
- **tqdm** (for progress bars in loops)

**Documentation Links:**
- [Pipenv Documentation](https://pipenv.pypa.io/en/latest/)
- [pandas Documentation](https://pandas.pydata.org/)
- [NumPy Documentation](https://numpy.org/)
- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [Geopy Documentation](https://geopy.readthedocs.io/)
- [Requests Documentation](https://docs.python-requests.org/en/latest/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/)
- [Webdriver Manager Documentation](https://pypi.org/project/webdriver-manager/)
- [SciPy Documentation](https://scipy.org/)
- [Matplotlib Documentation](https://matplotlib.org/)
- [Seaborn Documentation](https://seaborn.pydata.org/)
- [tqdm Documentation](https://tqdm.github.io/)

### Setting up the Environment with Pipenv

Clone this repository by navigating to the desired folder with your command line and cloning the environment:

```bash
git clone https://github.com/MiguelLopezVirues/travel-planning-analysis


### Setting up the Environment with Pipenv

Clone this repository by navigating to the desired folder with your command line and cloning the environment:

```bash
git clone https://github.com/MiguelLopezVirues/travel-planning-analysis
```

To replicate the project's environment, you can use Pipenv with the included `Pipfile.lock`:

```bash
pipenv install
pipenv shell  
```

Alternatively, install the dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt  
```

## 📊 Results and Conclusions

Check the `analysis.ipynb` notebook for conclusions and recommendations on flight pricing trends, accommodation analysis, and activity insights.

## 🔄 Next Steps

- Add more filters to the URL builder for booking
- Add error handling to:
    - User input functions
    - Specify types for error handling, and verbosity option
- Add more adventures sources: Viator
- Add other transportation such as buses, trains and cars
- Add airbnb listings
- Create functionality to find the cheapest dates for flights (flight calendar + extract flights for those dates to check)
- Functionality: Optimize budget (if possible) to create th best holidays
- Functionality: Periodically (daily: morning, afternoon, small hours) check itinineraries that fulfill budget
- Harmonize extraction functions namings
- Add concurrency and multiprocessing capabilities

## 🤝 Contributions

Contributions are welcome. If you wish to improve the project, open a pull request or an issue.

## ✒️ Authors

Miguel López Virués - [GitHub Profile](https://github.com/MiguelLopezVirues)

## 📜 License

This project is licensed under the MIT License.
```

