#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import logging
import datetime
import time
from typing import List, Optional, Tuple


class URLDatabase:
    
    
    def __init__(self, dbpath: str, dbname: str):
        
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Checking Database.")
        self.dbpath = dbpath
        self.dbname = dbname
        
        # Ensure directory exists
        os.makedirs(self.dbpath, exist_ok=True)
        
        db_file = os.path.join(self.dbpath, self.dbname)
        
        if not os.path.exists(db_file):
            self._create_database(db_file)
        else:
            # Ensure table exists even if DB exists
            self._create_database(db_file)
    
    def _create_database(self, db_file: str):
        
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "URL" (
                "id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                "type"	TEXT,
                "url"	TEXT,
                "title"	TEXT,
                "baseurl"	TEXT,
                "status"	TEXT,
                "count_status"	INTEGER,
                "source"	TEXT,
                "categorie"	TEXT,
                "score_categorie"	INTEGER,
                "keywords"	TEXT,
                "score_keywords"	INTEGER,
                "discovery_date"	DATE,
                "lastscan"	DATE,
                "full_match_categorie"	TEXT
            );
        """)
        conn.commit()
        conn.close()
    
    def compare(self, url: str) -> List[Tuple]:
        
        conn = sqlite3.connect(os.path.join(self.dbpath, self.dbname))
        cursor = conn.cursor()
        r = cursor.execute("SELECT * FROM URL WHERE url=?;", (url,))
        results = r.fetchall()
        conn.close()
        return results
    
    def save(
        self,
        url: str,
        source: str,
        type: str,
        baseurl: Optional[str] = None
    ):
        
        conn = sqlite3.connect(os.path.join(self.dbpath, self.dbname))
        cursor = conn.cursor()
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(
            "INSERT INTO URL (type,url,source,baseurl,discovery_date) VALUES (?,?,?,?,?);",
            (type, url, source, baseurl, date)
        )
        conn.commit()
        conn.close()
    
    def batch_save(
        self,
        urls: List[str],
        source: str,
        type: str,
        baseurl: Optional[str] = None
    ) -> int:
        
        if not urls:
            return 0
        
        conn = sqlite3.connect(os.path.join(self.dbpath, self.dbname))
        cursor = conn.cursor()
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Check which URLs already exist
        existing_urls = set()
        if urls:
            # Use IN clause for efficient checking
            placeholders = ','.join(['?' for _ in urls])
            cursor.execute(f"SELECT url FROM URL WHERE url IN ({placeholders});", urls)
            existing_urls = {row[0] for row in cursor.fetchall()}
        
        # Filter out existing URLs
        new_urls = [url for url in urls if url not in existing_urls]
        
        if not new_urls:
            conn.close()
            return 0
        
        # Prepare batch insert data
        insert_data = [
            (type, url, source, baseurl, date)
            for url in new_urls
        ]
        
        # Batch insert using executemany
        cursor.executemany(
            "INSERT INTO URL (type,url,source,baseurl,discovery_date) VALUES (?,?,?,?,?);",
            insert_data
        )
        conn.commit()
        conn.close()
        
        return len(new_urls)
    
    def select(
        self,
        score_categorie: Optional[int] = None,
        score_keywords: Optional[int] = None
    ) -> List[Tuple]:
        
        conn = sqlite3.connect(os.path.join(self.dbpath, self.dbname))
        cursor = conn.cursor()
        
        # Build query based on provided scores
        query = "SELECT * FROM URL WHERE (status IS NULL OR status != 'Offline')"
        params = []
        
        if score_categorie is not None:
            query += " AND (score_categorie >= ? OR score_categorie IS NULL)"
            params.append(score_categorie)
        
        if score_keywords is not None:
            query += " AND (score_keywords >= ? OR score_keywords IS NULL)"
            params.append(score_keywords)
        
        r = cursor.execute(query, params)
        results = r.fetchall()
        conn.close()
        return results
    
    def select_url(self, url: str) -> List[Tuple]:
        
        conn = sqlite3.connect(os.path.join(self.dbpath, self.dbname))
        cursor = conn.cursor()
        r = cursor.execute("SELECT * FROM URL WHERE url=?;", (url,))
        results = r.fetchall()
        conn.close()
        return results
    
    def update_status(
        self,
        id: int,
        url: str,
        result: int,
        count_categories: int
    ):
        
        if result == 404:
            existing = self.select_url(url=url)
            if existing and len(existing) > 0:
                current_count = existing[0][6] if existing[0][6] is not None else 0
                if current_count <= count_categories:
                    count_status = current_count + 1
                    status = "Unknown"
                else:
                    status = "Offline"
                    count_status = current_count + 1
            else:
                count_status = 1
                status = "Unknown"
        else:
            status = "Online"
            count_status = 0
        
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(os.path.join(self.dbpath, self.dbname))
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE URL
            SET status = ?, 
            count_status = ?, 
            lastscan = ?
            WHERE id = ?
            """,
            (status, count_status, date, id)
        )
        conn.commit()
        conn.close()
    
    def update_categorie(
        self,
        id: int,
        categorie: str,
        title: Optional[str],
        full_match_categorie: str,
        score_categorie: int,
        score_keywords: int,
        full_match_keywords: str
    ):
        
        conn = sqlite3.connect(os.path.join(self.dbpath, self.dbname))
        cursor = conn.cursor()
        
        if title is not None and len(title) > 0:
            title = title
        else:
            title = 'Untitled'
        
        cursor.execute(
            """
            UPDATE URL
            SET categorie = ?, 
            title = ?, 
            full_match_categorie = ?, 
            score_categorie = ?, 
            keywords = ?, 
            score_keywords = ?
            WHERE id = ?
            """,
            (categorie, title, full_match_categorie, score_categorie,
             full_match_keywords, score_keywords, id)
        )
        conn.commit()
        conn.close()
