from datetime import datetime

PATH_1 = "./logs.txt"
PATH_2 = "..\logs.txt"

def clearLogs():
    try:
        with open(PATH_1, 'w', encoding='utf-8') as file:
            file.writelines('')
    except:
        with open(PATH_2, 'w', encoding='utf-8') as file:
            file.writelines('')

def readLogs():
    try:
        with open(PATH_1, 'r', encoding='utf-8') as file:
            return file.read()
    except:
        with open(PATH_2, 'r', encoding='utf-8') as file:
            return file.read()

def writeLogs(id: int, artist: str, title: str, action: str) -> None:
    lines = ""

    lines = readLogs()
    
    date_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    lines = f"{artist} - {title} ({id}) has been {action} at {date_string} \n" + lines

    try:
        with open(PATH_1, 'w', encoding='utf-8') as file:
            file.writelines(lines)
    except:
        with open(PATH_2, 'w', encoding='utf-8') as file:
            file.writelines(lines)

if __name__ == '__main__':
    clearLogs()
    writeLogs(1, "AliA", "Kakurenbo", "Deleted")