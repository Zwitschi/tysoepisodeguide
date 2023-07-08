# Episode Guide for the Take Your Shoes Off podcast

This is an episode guide for the Take Your Shoes Off podcast with Rick Glassman. It is a work in progress.

## Source

The episode guide is generated from [Rick Glassman's YouTube Channel](https://www.youtube.com/@rickglassman) using the [YouTube Data API](https://developers.google.com/youtube).

This python program is used to generate the episode guide from the YouTube channel by querying the YouTube Data API. All video information is internally stored in a sqlite database. The database is located in the `db` directory. The database is created and updated by the python program. The database is not included in the repository and you will need to supply your own API key to generate the database.

## Requirements

* Python 3.9+
* [YouTube Data API](https://developers.google.com/youtube)

## Usage

1. Clone the repository
2. Install the requirements with `pip install -r requirements.txt`
3. Create a YouTube Data API key
4. Create a `.env` file in the root directory of the repository
5. Add the following to the `.env` file:
```bash
API_KEY=<your_api_key>
```
6. Run `python app.py` to generate the episode guide
7. Open `http://127.0.0.1:5000/` in a browser to view the episode guide

## Contributions

Contributions are welcome. Please open an issue or submit a pull request.
To contribute, use the following steps:

1. Clone the repository
2. Create a virtual environment with `python -m venv tyso`
3. Activate the virtual environment with `source tyso/bin/activate`
4. Install the requirements with `pip install -r requirements.txt`
5. Create a YouTube Data API key
6. Create a `.env` file in the root directory of the repository
7. Add the following to the `.env` file:
```bash
API_KEY=<your_api_key>
```
8. Run `python app.py` to generate the episode guide
9. Open `http://127.0.0.1:5000/` in a browser to view the episode guide
10. Make your changes
11. Run `python app.py` to generate the episode guide
12. Open `http://127.0.0.1:5000/` in a browser to view the episode guide
13. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
