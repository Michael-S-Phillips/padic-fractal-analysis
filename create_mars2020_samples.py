#!/usr/bin/env python3
"""
Mars 2020 Sample Locations - GeoPackage Generator
Extracts sample coordinates from Initial Reports Volume 4
No external dependencies required - uses only standard library sqlite3
"""

import sqlite3
import struct
from datetime import datetime

def create_gpkg(filename='mars2020_samples_volume4.gpkg'):
    """Create a GeoPackage with Mars 2020 sample locations"""
    
    # Sample data
    samples = [
    {
        "sample_id": "M2020-923-25",
        "name": "Pelican Point",
        "latitude": 18.48344692,
        "longitude": 77.35065098,
        "elevation": -2423.102833,
        "sol": 923,
        "date": "2023-09-23",
        "campaign": "Margin",
        "roi": "Mandu Wall",
        "lithology": "Moderately to poorly sorted medium to coarse grained sandstone"
    },
    {
        "sample_id": "M2020-949-26",
        "name": "Lefroy Bay",
        "latitude": 18.48867278,
        "longitude": 77.34704595,
        "elevation": -2407.641882,
        "sol": 949,
        "date": "2023-10-13",
        "campaign": "Margin",
        "roi": "Turquoise Bay",
        "lithology": "Moderately to poorly sorted medium to coarse grained sandstone"
    },
    {
        "sample_id": "M2020-1088-27",
        "name": "Comet Geyser",
        "latitude": 18.49186664,
        "longitude": 77.3272192,
        "elevation": -2382.434036,
        "sol": 1088,
        "date": "2024-03-11",
        "campaign": "Margin",
        "roi": "Western Margin",
        "lithology": "Moderately to poorly sorted coarse sandstone or altered igneous rock"
    },
    {
        "sample_id": "M2020-1215-28",
        "name": "Sapphire Canyon",
        "latitude": 18.49747434,
        "longitude": 77.30514915,
        "elevation": -2354.235808,
        "sol": 1215,
        "date": "2024-07-21",
        "campaign": "Margin",
        "roi": "Bright Angel",
        "lithology": "Fine-grained silicate rock with abundant calcium sulfate veins"
    }
]
    
    # Create/connect to database
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    
    # Set application_id for GeoPackage (required)
    cur.execute("PRAGMA application_id = 1196444487")
    
    # Create required GeoPackage tables
    
    # 1. gpkg_spatial_ref_sys - Spatial reference system
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gpkg_spatial_ref_sys (
            srs_name TEXT NOT NULL,
            srs_id INTEGER NOT NULL PRIMARY KEY,
            organization TEXT NOT NULL,
            organization_coordsys_id INTEGER NOT NULL,
            definition TEXT NOT NULL,
            description TEXT
        )
    """)
    
    # Insert Mars 2000 coordinate system (IAU Mars)
    # Using geographic coordinates (lat/lon in degrees)
    cur.execute("""
        INSERT OR REPLACE INTO gpkg_spatial_ref_sys VALUES (
            'Mars 2000',
            49900,
            'IAU',
            49900,
            'GEOGCS["Mars 2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.89444722361179]],PRIMEM["Reference_Meridian",0.0],UNIT["Degree",0.0174532925199433]]',
            'Mars 2000 geographic coordinate system'
        )
    """)
    
    # Also add WGS 84 for compatibility (even though this is Mars data)
    cur.execute("""
        INSERT OR REPLACE INTO gpkg_spatial_ref_sys VALUES (
            'WGS 84',
            4326,
            'EPSG',
            4326,
            'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]',
            'WGS 84 geographic coordinate system'
        )
    """)
    
    # 2. gpkg_contents - Table of contents
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gpkg_contents (
            table_name TEXT NOT NULL PRIMARY KEY,
            data_type TEXT NOT NULL,
            identifier TEXT UNIQUE,
            description TEXT DEFAULT '',
            last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            min_x DOUBLE,
            min_y DOUBLE,
            max_x DOUBLE,
            max_y DOUBLE,
            srs_id INTEGER,
            CONSTRAINT fk_gc_r_srs_id FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id)
        )
    """)
    
    # Calculate bounding box
    lons = [s['longitude'] for s in samples]
    lats = [s['latitude'] for s in samples]
    
    cur.execute("""
        INSERT OR REPLACE INTO gpkg_contents VALUES (
            'mars2020_samples',
            'features',
            'mars2020_samples',
            'Mars 2020 Perseverance Rover Sample Collection Locations - Volume 4 (Jezero Margin Campaign)',
            datetime('now'),
            ?, ?, ?, ?,
            49900
        )
    """, (min(lons), min(lats), max(lons), max(lats)))
    
    # 3. gpkg_geometry_columns
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gpkg_geometry_columns (
            table_name TEXT NOT NULL,
            column_name TEXT NOT NULL,
            geometry_type_name TEXT NOT NULL,
            srs_id INTEGER NOT NULL,
            z TINYINT NOT NULL,
            m TINYINT NOT NULL,
            CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name),
            CONSTRAINT fk_gc_tn FOREIGN KEY (table_name) REFERENCES gpkg_contents(table_name),
            CONSTRAINT fk_gc_srs FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys (srs_id)
        )
    """)
    
    cur.execute("""
        INSERT OR REPLACE INTO gpkg_geometry_columns VALUES (
            'mars2020_samples',
            'geom',
            'POINT',
            49900,
            0,
            0
        )
    """)
    
    # 4. Create the actual features table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mars2020_samples (
            fid INTEGER PRIMARY KEY AUTOINCREMENT,
            geom BLOB NOT NULL,
            sample_id TEXT NOT NULL,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            elevation REAL NOT NULL,
            sol INTEGER NOT NULL,
            date TEXT NOT NULL,
            campaign TEXT NOT NULL,
            roi TEXT NOT NULL,
            lithology TEXT
        )
    """)
    
    # Function to create WKB Point geometry
    def create_point_wkb(lon, lat):
        """
        Create Well-Known Binary (WKB) format for a 2D point
        Format: byte order (1 byte) + geometry type (4 bytes) + X (8 bytes) + Y (8 bytes)
        """
        # Little endian byte order (1), Point type (1), then X and Y as doubles
        return struct.pack('<BI dd', 1, 1, lon, lat)
    
    # Insert sample data
    for sample in samples:
        wkb = create_point_wkb(sample['longitude'], sample['latitude'])
        cur.execute("""
            INSERT INTO mars2020_samples 
            (geom, sample_id, name, latitude, longitude, elevation, sol, date, campaign, roi, lithology)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            wkb,
            sample['sample_id'],
            sample['name'],
            sample['latitude'],
            sample['longitude'],
            sample['elevation'],
            sample['sol'],
            sample['date'],
            sample['campaign'],
            sample['roi'],
            sample['lithology']
        ))
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ GeoPackage created successfully: {filename}")
    print(f"✓ {len(samples)} samples added to the database")
    print(f"\nSample locations included:")
    for s in samples:
        print(f"  • {s['sample_id']} - {s['name']}")
        print(f"    Location: {s['latitude']:.8f}°N, {s['longitude']:.8f}°E")
        print(f"    Elevation: {s['elevation']:.2f} m")
        print(f"    Date: {s['date']} (Sol {s['sol']})")
        print(f"    Region: {s['roi']}\n")
    
    print("\nYou can now open this file in:")
    print("  • QGIS (Add Vector Layer)")
    print("  • ArcGIS Pro")
    print("  • Any GIS software supporting GeoPackage format")

if __name__ == '__main__':
    create_gpkg()
