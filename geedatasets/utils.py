import sys
import hashlib
import numpy as np
from joblib import Parallel
from pyproj import CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info

epsg4326 = CRS.from_epsg(4326)

class mParallel(Parallel):
    """
    substitutes joblib.Parallel with richer verbose progress information
    """
    def _print(self, msg, msg_args):
        if self.verbose > 10:
            fmsg = '[%s]: %s' % (self, msg % msg_args)
            sys.stdout.write('\r ' + fmsg)
            sys.stdout.flush()

def split_python_code(codestr):
    """
    splits a string of python code in two parts, one containing the last
    statement and the other containing the rest. splitting is done by '\n'
    or by ';' and the last statement is cut with whichever '\n' or ';' 
    appear last.
    
    return: a tuple of two strings
            all_but_last_statement, last_statement
    """
    codestr = '\n'.join([i for i in codestr.split("\n") if len(i.strip())>0])

    last_statement_by_returns = [i for i in codestr.split("\n")][-1]
    last_statement_by_colons  = [i for i in codestr.split(";")][-1]
    last_retr  = codestr[::-1].find("\n")
    last_colon = codestr[::-1].find(";")

    if last_retr == last_colon == -1:
        last_statement = codestr
    elif last_retr == -1:
        last_statement = last_statement_by_colons
    elif last_colon == -1:
        last_statement = last_statement_by_returns
    elif last_colon < last_retr:
        last_statement = last_statement_by_colons
    else:
        last_statement = last_statement_by_returns
        
    all_but_last_statement = codestr[:-len(last_statement)]
    
    return all_but_last_statement, last_statement


def get_region_hash(region):
    """
    region: a shapely geometry
    returns a hash string for region using its coordinates
    """
    s = str(np.r_[region.envelope.boundary.coords].round(5))
    k = int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16) % 10**15
    k = str(hex(k))[2:].zfill(13)
    return k

def get_regionlist_hash(regionlist):
    """
    returns a hash string for a list of shapely geometries
    """
    s = [get_region_hash(i) for i in regionlist]
    s = " ".join(s)
    k = int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16) % 10**15
    k = str(hex(k))[2:].zfill(13)
    return k


def get_utm_crs(lon, lat):
    """
    returns a UTM CRS in meters with the zone corresponding to lon, lat
    """
    utm_crs_list = query_utm_crs_info(
        datum_name="WGS 84",
        area_of_interest=AreaOfInterest(
            west_lon_degree=lon,
            south_lat_degree=lat,
            east_lon_degree=lon,
            north_lat_degree=lat,
        ),
    )
    if len(utm_crs_list)==0:
        raise ValueError(f"could not get utm for lon/lat: {lon}, {lat}")
        
    utm_crs = CRS.from_epsg(utm_crs_list[0].code)
    return utm_crs