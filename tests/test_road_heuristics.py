import pytest
from src.minecraft_pipeline.exporter import resolve_road_properties

def test_resolve_road_properties_expressway():
    # Expressway/Highway (from name or highway type)
    props1 = resolve_road_properties("Carretera Mexicali - Tijuana", "residential")
    assert props1["width"] == 12.0
    assert props1["lanes"] == 4
    assert props1["surface"] == "asphalt"
    assert props1["marking_type"] == "highway"
    assert not props1["is_rural"]

    props2 = resolve_road_properties("Autopista Centinela", "residential")
    assert props2["width"] == 12.0
    assert props2["lanes"] == 4
    
    props3 = resolve_road_properties("Unnamed Road", "motorway")
    assert props3["width"] == 12.0
    assert props3["lanes"] == 4

def test_resolve_road_properties_boulevard():
    # Boulevard
    props = resolve_road_properties("Boulevard Benito Juárez", "residential")
    assert props["width"] == 14.0
    assert props["lanes"] == 4
    assert props["surface"] == "asphalt_clean"
    assert props["marking_type"] == "boulevard"
    assert not props["is_rural"]

    props2 = resolve_road_properties("Blvrd. Federico", "residential")
    assert props2["width"] == 14.0

def test_resolve_road_properties_avenida():
    # Avenida / Paseo
    props = resolve_road_properties("Avenida 5 de Mayo", "residential")
    assert props["width"] == 9.0
    assert props["lanes"] == 2
    assert props["surface"] == "asphalt"
    assert props["marking_type"] == "avenida"
    assert not props["is_rural"]

    props2 = resolve_road_properties("Paseo Rio Tecate", "residential")
    assert props2["width"] == 9.0

def test_resolve_road_properties_calle():
    # Calle / Callejón
    props = resolve_road_properties("Calle 1 de Mayo", "residential")
    assert props["width"] == 6.0
    assert props["lanes"] == 2
    assert props["surface"] == "asphalt_light"
    assert props["marking_type"] == "calle"
    assert not props["is_rural"]

    props2 = resolve_road_properties("Callejón Libertad", "residential")
    assert props2["width"] == 6.0

def test_resolve_road_properties_unnamed_minor():
    # Unnamed and minor highway type -> rural/unpaved
    props = resolve_road_properties("", "service")
    assert props["width"] == 4.0
    assert props["lanes"] == 1
    assert props["surface"] == "gravel"
    assert props["marking_type"] == "none"
    assert props["is_rural"]

    props2 = resolve_road_properties("", "unclassified")
    assert props2["width"] == 4.0
    assert props2["is_rural"]

def test_resolve_road_properties_fallback():
    # Fallback to standard primary/secondary types
    props = resolve_road_properties("Something Else", "primary")
    assert props["width"] == 10.0
    assert props["lanes"] == 2
    assert props["marking_type"] == "avenida"

    props2 = resolve_road_properties("Something Else", "secondary")
    assert props2["width"] == 8.0
    assert props2["lanes"] == 2
    assert props2["marking_type"] == "calle"
