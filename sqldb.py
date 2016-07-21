#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import threading

DATABASE_FILE = "/mnt/web/TranscodeE16/jobs.db"

# DB lock for multithreaded use case
db_rlock = threading.RLock()


class TranscodeJobsSQL():
    """
    Class to interface with the db for transcoding jobs.
    """

    # Status defitions for the jobs
    STATUS_STARTED = "STATUS_STARTED"
    STATUS_TRANSCODING = "STATUS_TRANSCODING"
    STATUS_COMPLETE = "STATUS_COMPLETE"
    STATUS_ERROR = "STATUS_ERROR"

    def __init__(self):
        """
        Connect to jobs.db and sets up an sql cursor.
        """
        print("Connecting to DB.")
        self.conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def create_table(self):
        """
        Creates default table for logging barometer sensor output.
        """
        with db_rlock:
            print("Creating Table.")
            query = 'CREATE TABLE Jobs(Id TEXT, Status TEXT, Message TEXT, PercentComplete REAL, ElapsedTime REAL)'
            self.cursor.execute(query)

    def insert_new_job(self, inputs):
        """
        Insert inputs list into jobs.db.
        """
        with db_rlock:
            query = 'INSERT INTO Jobs(Id, Status, Message, PercentComplete, ElapsedTime) VALUES(?,?,?,?,?)'
            self.cursor.execute(query, (inputs))
            self.conn.commit()

    def update_job_status(self, jobId, status):
        """
        Update the Status for the specified job.
        """
        with db_rlock:
            query = 'UPDATE Jobs SET Status=? WHERE Id=?'
            self.cursor.execute(query, (status, jobId))
            self.conn.commit()

    def update_job_message(self, jobId, message):
        """
        Update the Message for the specified job.
        """
        with db_rlock:
            query = 'UPDATE Jobs SET Message=? WHERE Id=?'
            self.cursor.execute(query, (message, jobId))
            self.conn.commit()

    def update_job_percent_complete(self, jobId, percentComplete):
        """
        Update the Percent Complete for the specified job.
        """
        with db_rlock:
            query = 'UPDATE Jobs SET PercentComplete=? WHERE Id=?'
            self.cursor.execute(query, (percentComplete, jobId))
            self.conn.commit()

    def update_elapsed_time(self, jobId, elapsedTime):
        """
        Update the Completion Time for the specified job.
        """
        with db_rlock:
            query = 'UPDATE Jobs SET ElapsedTime=? WHERE Id=?'
            self.cursor.execute(query, (elapsedTime, jobId))
            self.conn.commit()

    def get_job_info(self, jobId):
        """
        Gets the details about the specified job.
        """
        with db_rlock:
            query = 'SELECT * FROM Jobs WHERE Id=?;'
            res = self.cursor.execute(query, (jobId,))
            return res.fetchone()

    def close_connection(self):
        """
        Close the sqlite3 handle.
        """
        print("Closing connection to DB.")
        self.conn.close()


def main():
    """
    Main function to set up the DB.
    """
    db_already_exists = os.path.exists(DATABASE_FILE)
    if db_already_exists is False:
        print("Creating Jobs DB.")
        db_setup = TranscodeJobsSQL()
        db_setup.create_table()
        db_setup.close_connection()
    else:
        print("Database file already exists.")

if __name__ == "__main__":
    main()
