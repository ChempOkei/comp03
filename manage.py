import os
import sys
# from django.conf import settings

def check_env():
    if os.path.exists(".env"):
        return True
    print("setup .env please, иначе ничего толком работать не будет")
    return False
def main():
    state = check_env()
    if check_env():
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_platform.settings')

        from django.core.management import execute_from_command_line

        execute_from_command_line(sys.argv)
        size_data_base_orig = os.path.getsize("db.sqlite3")
        print("Size original database: ", size_data_base_orig)
        size_data_base_test = os.path.getsize("db_test.sqlite3")
        print("Size test database: ", size_data_base_test)
        print("Started, check please local server!")
        # start from server/server.py predict

# if settings.DEBUG:
#     print("DEBUGGER OPEN! TEST ON")


if __name__ == '__main__':
    main()