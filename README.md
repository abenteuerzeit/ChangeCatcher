# ChangeCatcher

ChangeCatcher is a Python-based monitoring system designed to detect changes on web pages. It provides real-time alerts via email whenever specified content changes or certain keywords are detected. This tool is perfect for tracking updates on websites without RSS or any formal notification systems.

## Features

- **Content Change Detection**: Monitors web pages and detects any changes in the content.
- **Keyword Alerts**: Sends notifications if predefined keywords are found on the page.
- **Email Notifications**: Configurable to send emails to any address upon detection of changes or keywords.
- **Custom Intervals**: Checks the web pages at user-defined intervals.
- **Logging**: Includes a robust logging system for monitoring activity and debugging.

## Getting Started

These instructions will help you set up ChangeCatcher on your local machine for development and testing purposes.

### Prerequisites

- Python 3.6+
- pip for installing dependencies

### Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/ChangeCatcher.git
   ```

2. Navigate to the cloned directory:

   ```sh
   cd ChangeCatcher
   ```

3. Install the required dependencies:

   ```sh
   pip install -r requirements.txt
   ```

### Configuration

1. Rename the `config.example.py` to `config.py`.
2. Edit `config.py` to set up your SMTP server details, the URL to monitor, and other configurations.

### Usage

Run the script with:

  ```sh
  python -m ChangeCatcher
  ```

## Development

Want to contribute? Great! You can follow these steps to submit your changes:

1. Fork the repo.
2. Create your feature branch (`git checkout -b feature/fooBar`).
3. Commit your changes (`git commit -am 'Add some fooBar'`).
4. Push to the branch (`git push origin feature/fooBar`).
5. Create a new Pull Request.

Project Link: [https://github.com/yourusername/ChangeCatcher](https://github.com/yourusername/ChangeCatcher)
