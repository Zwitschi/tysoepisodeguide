# Episode Guide for the Take Your Shoes Off podcast

This is an episode guide for the Take Your Shoes Off podcast with Rick Glassman. The episode guide is available at [https://tysoepisodeguide.azurewebsites.net/](https://tysoepisodeguide.azurewebsites.net/). It is still a work in progress.

## Sources

The episode guide is generated from [Rick Glassman's YouTube Channel](https://www.youtube.com/@rickglassman) using the [YouTube Data API](https://developers.google.com/youtube).

This python program is used to generate the episode guide from the YouTube channel by querying the YouTube Data API. All video information is internally stored in a sqlite database. The database is located in the `db` directory. The database is created and updated by the python program. The database is not included in the repository and you will need to supply your own API key to generate the database.

## Requirements

* [YouTube Data API](https://developers.google.com/youtube)
* Python 3.11+
    * Flask
    * request
    * markdown
    * gunicorn
    * python-dotenv

## Prerequisites

* [Python 3.11+](https://www.python.org/downloads/)
* [YouTube Data API key](https://developers.google.com/youtube/v3/getting-started)

## Usage

1. Clone the repository
2. Install the requirements with `pip install -r requirements.txt`
3. Create a `.env` file in the root directory of the repository
4. Add the following to the `.env` file: `API_KEY=<your_api_key>`
5. Run `python setup.py install` to generate the episode guide
6. Run `python app.py` to run the Flask app
7. Open `http://127.0.0.1:5000/` in a browser to view the episode guide

## Contributions

Contributions are welcome. Please open an issue or submit a pull request.
To contribute, use the following steps:

1. Clone the repository
2. Install the requirements with `pip install -r requirements.txt`
3. Create a `.env` file in the root directory of the repository
4. Add the following to the `.env` file: `API_KEY=<your_api_key>`
5. Run `python setup.py install` to generate the episode guide
6. Make your changes
7. Run `python setup.py install` to generate the episode guide
8. Run `python app.py` to run the Flask app
9. Open `http://127.0.0.1:5000/` in a browser to view the episode guide
10. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

* [Zwitschi](https://zwitschi.net)
* [Rick Glassman](https://rickglassman.com)
* [Perry Grone](https://www.harryandmarv.co)
