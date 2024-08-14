import paramiko
from datetime import datetime, timedelta
from pytz import timezone, utc
from src.db_access import has_been_notified, record_notification, init_db
from src.sns_notify import send_sns_notification
from config.config import config
import traceback


def get_next_trading_date(current_date, holidays=None):
    if holidays is None:
        holidays = []

    # Ensure holidays are in datetime.date format
    holidays = [datetime.strptime(holiday, '%Y-%m-%d').date() if isinstance(holiday, str) else holiday for holiday in holidays]

    next_date = current_date + timedelta(days=1)

    # Skip weekends and holidays
    while next_date.weekday() >= 5 or next_date in holidays:
        next_date += timedelta(days=1)

    return next_date


def download_log_file(server_config):
    current_date = datetime.now()
    
    nyt_lead_lag = server_config['log_nyt_lead_lag']
    if int(nyt_lead_lag) == 1:
        log_date = get_next_trading_date(current_date)
    else:
        log_date = current_date

    tempname = server_config['log_filename']
    yyyy,mm,dd = log_date.strftime('%Y-%m-%d').split('-')
    log_filename = tempname.replace('YYYY', yyyy).replace('MM', mm).replace('DD', dd)
    remote_file_path = f"{server_config['log_file_dir']}/{log_filename}"
    local_file_path = f"{server_config['local_download_dir']}/{log_filename}"

    try:
        # SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            server_config['ip'], 
            port=server_config['port'], 
            username=server_config['username'], 
            key_filename=server_config['pem_file_path']
        )

        sftp = ssh.open_sftp()
        sftp.get(remote_file_path, local_file_path)
        sftp.close()
        ssh.close()

        if not has_been_notified(server_config['ip'], log_filename, "Log Exists"):
            send_sns_notification(f"Exists: {log_filename}", f"Log file created: {log_filename} from server {server_config['app']}")
            record_notification(server_config['ip'], log_filename, "Log Exists")

        # Check for error keywords
        with open(local_file_path, 'r') as file:
            log_lines = file.readlines()
            for line in log_lines:
                for error in server_config['error_keywords']:
                    if error.lower() in line.lower():
                        if all(ignore.lower() not in line.lower() for ignore in server_config['ignore_keywords']):
                            if not has_been_notified(server_config['ip'], log_filename, error):
                                print(f"Error Line: {line}")
                                send_sns_notification(f"ERROR Found {server_config['app']}",
                                                      f"Errors found in log file: {log_filename} from server {server_config['app']}")
                                record_notification(server_config['ip'], log_filename, error)
        
    except FileNotFoundError:
        traceback.print_exc()
        error_message = f"Log file {log_filename} not found on remote server {server_config['app']}."
        send_sns_notification(f"ERROR Found {server_config['app']}", error_message)
    except Exception as e:
        traceback.print_exc()
        error_message = f"An error occurred on server {server_config['app']}: {str(e)}"
        send_sns_notification("fERROR Found {server_config['app']}", error_message)


def should_check_file(server_config):
    local_tz = timezone(server_config['timezone'])
    start_time = datetime.strptime(server_config['start_time'], '%H:%M').time()
    end_time = datetime.strptime(server_config['end_time'], '%H:%M').time()
    current_time = datetime.now(local_tz).time()
    current_day = datetime.now(local_tz).strftime('%A')

    if start_time <= current_time <= end_time and current_day in server_config['days']:
        return True
    return False


def main():
    init_db()
    for server in config['servers']:
        if should_check_file(server):
            download_log_file(server)


if __name__ == "__main__":
    main()

