import sqlite3, os

class logHandler():
    status: dict

    def __init__(self):
        self.conn = sqlite3.connect('log.db', check_same_thread=False)
        cur = self.conn.cursor()
        cur.execute('''create table if not exists "log" (
            Name VARCHAR(255) NOT NULL,
            Operation CHAR(2),
            Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);''')
        self.conn.commit()
        cur.close()
        if os.path.isfile("student.log"):
            os.remove("student.log")

        self.status = {}

    def isIn(self, name):
        if name in self.status.keys():
            if self.status[name] == "in":
                self.status[name] = "out"
                return True
            else:
                self.status[name] = "in"
                return False
        else:
            self.status[name] = "in"
            return False

    def addRec(self, name):
        if self.isIn(name):
            ops = "In"
        else:
            ops = "Out"
        cur = self.conn.cursor()
        cur.execute(f'''INSERT INTO log (Name, Operation) VALUES ("{name}","{ops}");''')
        rowid = cur.lastrowid
        cur.execute("SELECT * FROM log WHERE rowid = ?", (rowid,))
        ist = cur.fetchone()
        open("student.log", "a").write(f"{ist[0]}\t{ist[1]}\t{ist[2]}\n")
        # self.logFile.write(f"{ist[0]}\t{ist[1]}\t{ist[2]}\n")
        cur.close()
