"""Rebuild a clean road-centreline network from a rasterised street layer.

A ONE-OFF preprocessing helper, kept for provenance: this is how the
Arahama network was produced. It is NOT part of the simulation and is not
exercised by the test suite.

Needs the extra dependencies in requirements-tools.txt:
    pip install -r requirements-tools.txt

Run it from the folder containing the input shapefile.
"""

import geopandas as gpd
import rasterio
from rasterio import features
from rasterio.transform import from_origin
from skimage.morphology import skeletonize
import sknw
from shapely.geometry import LineString
import numpy as np

print("Rebuilding and smoothing the road network...")

# 1. Load the source shapefile
input_file = "Streets.shp"
streets_layer = gpd.read_file(input_file)

# 2. Control parameters
# Wide streets: raise the pixel size to 2.0. Narrow streets: lower it to 0.5.
pixel_size = 1.0
# The key parameter for removing the staircase artefact left by rasterising
# 2.0 to 5.0 metres straightens the steps out
smoothing_tolerance = 3.0

minx, miny, maxx, maxy = streets_layer.total_bounds
raster_width = int((maxx - minx) / pixel_size)
raster_height = int((maxy - miny) / pixel_size)
transformacion = from_origin(minx, maxy, pixel_size, pixel_size)

# 3. Rasterizar
geometrias = [(geom, 1) for geom in streets_layer.geometry]
imagen_raster = features.rasterize(
    geometrias,
    out_shape=(raster_height, raster_width),
    transform=transformacion,
    fill=0,
    dtype=np.uint8
)

# 4. Esqueletizacion
esqueleto = skeletonize(imagen_raster)

# 5. Vectorizacion
grafo = sknw.build_sknw(esqueleto)
lineas_resultado = []

for u, v, datos_arista in grafo.edges(data=True):
    puntos_pixeles = datos_arista['pts']
    puntos_mapa = [rasterio.transform.xy(transformacion, fila, col) for fila, col in puntos_pixeles]
    lineas_resultado.append(LineString(puntos_mapa))

# 6. Planchado final de las lineas
capa_final = gpd.GeoDataFrame(geometry=lineas_resultado, crs=streets_layer.crs)

print(f"Removing the staircase artefact, tolerance {smoothing_tolerance} m...")
capa_final["geometry"] = capa_final.simplify(tolerance=smoothing_tolerance, preserve_topology=True)

capa_final.to_file("Streets_Lineas_Limpias.shp")

print("Proceso finalizado. Red vial guardada sin escalones.")
