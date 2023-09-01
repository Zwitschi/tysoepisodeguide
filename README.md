# Episode Guide for the Take Your Shoes Off podcast

This is an episode guide for the Take Your Shoes Off podcast with Rick Glassman. The episode guide is available at [https://tysoepisodeguide.azurewebsites.net/](https://tysoepisodeguide.azurewebsites.net/).

## Sources

The episode guide is generated from [Rick Glassman's YouTube Channel](https://www.youtube.com/@rickglassman) using the [YouTube Data API](https://developers.google.com/youtube).

This python program is used to generate the episode guide from the YouTube channel by querying the YouTube Data API. 

All video information is internally stored in a sqlite database. The database is located in the `db` directory. The database is created and updated by the python program by running `python setup.py install`. The program will create the database if it does not exist, and update the database if it does exist. 

The episode guide markdown file is used to generate the episode guide HTML file, which is located in the `templates` directory. The episode guide HTML file is used by the Flask app to display the episode guide.

## Requirements

* [YouTube Data API](https://developers.google.com/youtube)
* Python 3.11+
    * Flask
    * request
    * markdown
    * gunicorn

## Prerequisites

* [Python 3.11+](https://www.python.org/downloads/)
* [YouTube Data API key](https://developers.google.com/youtube/v3/getting-started)

## Usage

1. Clone the repository
2. Install the requirements with `pip install -r requirements.txt`
3. Create and enable a virtual environment (venv) named "tyso" using the following steps:
    - Open a terminal or command prompt.
    - Navigate to the root directory of the repository using the `cd` command.
    - Run the command `python -m venv tyso` to create a virtual environment named "tyso".
    - On Windows, activate the virtual environment by running: 
      - For Command Prompt: `tyso\Scripts\activate.bat`
      - For PowerShell: `.\tyso\Scripts\Activate.ps1`
    - On macOS and Linux, activate the virtual environment by running: `source tyso/bin/activate`
4. Create a `.env` file in the root directory of the repository.
5. Add the following to the `.env` file: `API_KEY=<your_api_key>`
6. Run `python setup.py install` to generate the episode guide.
7. Run `python app.py` to run the Flask app.
8. Open `http://127.0.0.1:5000/` in a browser to view the episode guide.

## Contributions

Contributions are welcome. Please open an issue or submit a pull request.
To contribute, use the following steps:

1. Clone the repository
2. Install the requirements with `pip install -r requirements.txt`
3. Create and enable a virtual environment (venv) named "tyso" using the steps mentioned above.
4. Create a `.env` file in the root directory of the repository.
5. Add the following to the `.env` file: `API_KEY=<your_api_key>`
6. Run `python setup.py install` to generate the episode guide.
7. Make your changes.
8. Run `python app.py` to run the Flask app and test your changes.
9. Open `http://127.0.0.1:5000/` in a browser to view the episode guide and ensure your changes work as expected.
10. Submit a pull request, describing the changes you've made and any relevant information.

By following these steps, you can create a virtual environment, set up the necessary environment variables, and contribute to the project while maintaining a clean and isolated development environment.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

* [Zwitschi](https://zwitschi.net)
* [Rick Glassman](https://rickglassman.com)
* [Perry Grone](https://www.harryandmarv.co)
