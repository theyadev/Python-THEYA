from datetime import datetime

PATH = r"C:\Users\stagiaire.PORT-20B-11.000\Documents\Python-THEYA\logs.txt"

def clearLogs():
    with open(PATH, 'w', encoding='utf-8') as file:
        file.writelines('')

def writeLogs(id: int, artist: str, title: str, action: str) -> None:
    lines = ""

    with open(PATH, 'r', encoding='utf-8') as file:
        lines = file.read()
    
    date_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    lines = f"{artist} - {title} ({id}) has been {action} at {date_string} \n" + lines

    with open(PATH, 'w', encoding='utf-8') as file:
        file.writelines(lines)

if __name__ == '__main__':
    clearLogs()
    writeLogs(1, "AliA", "Kakurenbo", "Deleted")