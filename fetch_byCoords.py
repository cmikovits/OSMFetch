#!/usr/bin/python3

import click
import logging
import os
import pathlib
import pandas as pd
import geopandas as gpd
import fiona
from OSMPythonTools.overpass import overpassQueryBuilder
from OSMPythonTools.overpass import Overpass
from shapely.geometry import Polygon

def fetchFeatures(areaId, osmkey, osmtype):
    overpass = Overpass()

    query = overpassQueryBuilder(area=areaId,
                                 elementType=['node', 'way', 'relation'],
                                 selector='"' + osmkey + '"="' + osmtype + '"',
                                 includeGeometry=True,
                                 out='center meta')
    logging.debug("OSM query: %s", query)
    return overpass.query(query, timeout=60)

def saveData(df, gdf, path, dataname):
    os.makedirs(os.path.join(path, dataname));
    #gdf.to_file(filename = os.path.join(path, dataname, 'power.geojson'), driver="GeoJSON")
    gdf.to_file(filename = os.path.join(path, dataname, 'power.shp'), driver = 'ESRI Shapefile')
    print("saving gpkg")
    #gdf.to_file(filename = os.path.join(path, dataname, 'power.gpkg'), layer = dataname, driver = 'GPKG')
    print("saving csv")
    df.to_csv(os.path.join(path, dataname, 'power.csv'))
    print("finished saving")
    return(0)

@click.command()
@click.option('-shape', '-s', help='shape input', default='BrazilSolar/solar-pv_UFV_BR_aneel_04-02-2022.shp', type=str)
@click.option('-loglevel', '-l', help='log level (INFO, DEBUG)', default='DEBUG', type=str)
def main(shape, loglevel):
    logging.basicConfig(format='%(asctime)s, %(message)s',
                       datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger().setLevel(loglevel)
    
    path = os.path.dirname(os.path.abspath(shape))
    sps = gpd.read_file(shape)
    sps = sps.to_crs(epsg=4326)
    mi = sps.geometry.bounds.min()
    mx = sps.geometry.bounds.max()
    bbox = [mi.miny, mi.minx, mx.miny, mx.minx]
    #print(sps)
    #exit(0)
    
    #query = overpassQueryBuilder(bbox=bbox, elementType='way', selector='"barrier"="fence"', out='body', includeGeometry=True)
    query = overpassQueryBuilder(bbox=bbox, elementType='way', selector='"plant:source"="solar"', out='body', includeGeometry=True)
    overpass = Overpass()
    fences = overpass.query(query, timeout = 1200)
    num = fences.countElements()
    print(num)
    
    gdf = gpd.GeoDataFrame()
    for n in range(0,num):
        #print(n)
        e = fences.elements()[n]
        #print(e)
        poly = e.geometry()['coordinates']
        #print(poly)
        try:
            geom = Polygon(poly)
        except:
            if len(poly[0]) < 6:
                continue
            geom = Polygon(poly[0])
        print(n,geom)
        gdfr = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[geom])
        gdf = pd.concat([gdf,gdfr], axis=0, ignore_index=True, sort=False)
    print(len(gdf))
    
    #gdf = gpd.GeoDataFrame(df, geometry=['geom'])
    gdf.to_file(filename = os.path.join(path, 'solarparks2.shp'), driver = 'ESRI Shapefile')

if __name__ == "__main__":
    main()