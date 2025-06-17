# HoopsFactory Downloader

A Python script to automatically download files from HoopsFactory based on configured parameters.

## Prerequisites

- Python 3.8.1 or higher
- Poetry (for dependency management)

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd download_hoopsfactory
   ```

2. Install required dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Install Playwright browser dependencies:
   ```bash
   poetry run playwright install
   ```

## Configuration

### Environment Variables

You need to set up the following environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `HOOPSFACTORY_URL` | Base URL for HoopsFactory | `https://example.hoopsfactory.com` |
| `HOOPSFACTORY_USERNAME` | Your username | `your_username` |
| `HOOPSFACTORY_PASSWORD` | Your password | `your_password` |
| `DOWNLOAD_PATH` | Directory to save downloads | `C:\Downloads\HoopsFactory` |

### Setting Environment Variables on Windows

#### Method 1: System Properties (Persistent)
1. Right-click "This PC" → Properties
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables" or "System variables", click "New"
5. Add each variable name and value
6. Click OK to save

#### Method 2: Command Prompt (Session only)
```cmd
set HOOPSFACTORY_URL=https://example.hoopsfactory.com
set HOOPSFACTORY_USERNAME=your_username
set HOOPSFACTORY_PASSWORD=your_password
set DOWNLOAD_PATH=C:\Downloads\HoopsFactory
```

#### Method 3: PowerShell (Session only)
```powershell
$env:HOOPSFACTORY_URL="https://example.hoopsfactory.com"
$env:HOOPSFACTORY_USERNAME="your_username"
$env:HOOPSFACTORY_PASSWORD="your_password"
$env:DOWNLOAD_PATH="C:\Downloads\HoopsFactory"
```

## Usage

### Manual Execution
```bash
poetry run python main.py
```

### Automated Execution with Windows Task Scheduler

#### Step 1: Create a Batch File
Create a file named `run_downloader.bat` in your project directory:

```batch
@echo off
cd /d "C:\path\to\your\download_hoopsfactory"
poetry run python main.py
pause
```

Or if Poetry is not in your system PATH, use the full path:

```batch
@echo off
cd /d "C:\path\to\your\download_hoopsfactory"
"C:\Users\%USERNAME%\AppData\Roaming\Python\Scripts\poetry.exe" run python main.py
pause
```

#### Step 2: Set Up Task Scheduler
1. Open Task Scheduler (search "Task Scheduler" in Start menu)
2. Click "Create Basic Task" in the right panel
3. **Name**: Enter "HoopsFactory Downloader"
4. **Description**: "Automatically downloads files from HoopsFactory"
5. **Trigger**: Choose your preferred schedule:
   - Daily: Runs every day at specified time
   - Weekly: Runs on specific days of the week
   - Monthly: Runs on specific days of the month
6. **Action**: Select "Start a program"
7. **Program/script**: Browse to your `run_downloader.bat` file
8. **Start in**: Enter the directory path: `C:\path\to\your\download_hoopsfactory`

#### Step 3: Advanced Settings (Optional)
1. After creating the task, right-click it and select "Properties"
2. **General tab**:
   - Check "Run whether user is logged on or not" (requires password)
   - Check "Run with highest privileges" if needed
3. **Conditions tab**:
   - Uncheck "Start the task only if the computer is on AC power" for laptops
   - Check "Wake the computer to run this task" if needed
4. **Settings tab**:
   - Check "Allow task to be run on demand"
   - Set appropriate timeout and retry settings

#### Step 4: Set Environment Variables for Task
If the task doesn't pick up your user environment variables:

1. Edit your `run_downloader.bat` file to include the environment variables:
```batch
@echo off
set HOOPSFACTORY_URL=https://example.hoopsfactory.com
set HOOPSFACTORY_USERNAME=your_username
set HOOPSFACTORY_PASSWORD=your_password
set DOWNLOAD_PATH=C:\Downloads\HoopsFactory

cd /d "C:\path\to\your\download_hoopsfactory"
poetry run python main.py
pause
```

Or with full Poetry path:
```batch
@echo off
set HOOPSFACTORY_URL=https://example.hoopsfactory.com
set HOOPSFACTORY_USERNAME=your_username
set HOOPSFACTORY_PASSWORD=your_password
set DOWNLOAD_PATH=C:\Downloads\HoopsFactory

cd /d "C:\path\to\your\download_hoopsfactory"
"C:\Users\%USERNAME%\AppData\Roaming\Python\Scripts\poetry.exe" run python main.py
pause
```

### Alternative: Using Poetry Script Directly in Task Scheduler
Instead of using a batch file, you can run the Poetry script directly:

1. **Program/script**: `poetry` or full path to Poetry executable
2. **Arguments**: `run hoopsfactory-downloader`
3. **Start in**: Your project directory path

## Logging

The script creates log files to track execution:
- Check the console output for real-time status
- Log files are saved in the project directory (if logging is implemented)

## Troubleshooting

### Common Issues

1. **Python not found**: Ensure Python is installed and added to system PATH
2. **Module not found**: Install required packages with `poetry install`
3. **Permission denied**: Run as administrator or check file permissions
4. **Task doesn't run**: Verify environment variables and file paths in Task Scheduler
5. **Authentication fails**: Double-check username and password in environment variables

### Testing Your Setup

1. Test environment variables:
```cmd
echo %HOOPSFACTORY_URL%
echo %HOOPSFACTORY_USERNAME%
```

2. Test script execution:
```bash
poetry run python main.py
```

3. Test batch file (if using):
```cmd
run_downloader.bat
```

## Security Notes

- Store sensitive credentials securely
- Consider using Windows Credential Manager for passwords
- Regularly update your credentials
- Monitor log files for any authentication issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.