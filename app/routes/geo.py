"""
GeoJSON API endpoints for ruches and ruchers.
"""
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import func
from geoalchemy2 import functions as geo_func
from app import db
from app.models import Ruche, Rucher
from app.utils.geojson import to_geojson
from app.utils.spatial import find_within_radius, cluster_points, get_point_coordinates

bp = Blueprint('geo', __name__, url_prefix='/geo')


@bp.route('/ruches', methods=['GET'])
def get_all_ruches():
    """
    Get GeoJSON for all hives (ruches).
    
    Query Parameters:
        - active: Filter by active status (true/false)
        - rucher_id: Filter by rucher (apiary) ID
        - cluster: Enable clustering (true/false)
        - radius: Filter by radius in meters (requires lat and lon)
        - lat: Latitude for radius search
        - lon: Longitude for radius search
    
    Returns:
        GeoJSON FeatureCollection
    """
    try:
        # Start with base query
        query = Ruche.query
        
        # Apply filters
        active = request.args.get('active')
        if active is not None:
            query = query.filter(Ruche.active == (active.lower() == 'true'))
        
        rucher_id = request.args.get('rucher_id')
        if rucher_id:
            try:
                query = query.filter(Ruche.rucher_id == int(rucher_id))
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid rucher_id parameter'}), 400
        
        # Radius search
        radius = request.args.get('radius')
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if radius and lat and lon:
            try:
                center_point = f'POINT({float(lon)} {float(lat)})'
                ruches = find_within_radius(Ruche, center_point, float(radius))
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid radius parameters'}), 400
        else:
            ruches = query.all()
        
        # Generate GeoJSON
        geojson = to_geojson(ruches)
        
        # Optional clustering
        if request.args.get('cluster', '').lower() == 'true':
            points = []
            for ruche in ruches:
                coords = get_point_coordinates(ruche.geom)
                if coords:
                    points.append(coords)
            
            if points:
                eps = current_app.config.get('CLUSTERING_EPS', 1000)
                min_samples = current_app.config.get('CLUSTERING_MIN_SAMPLES', 2)
                cluster_info = cluster_points(points, eps=eps, min_samples=min_samples)
                geojson['clustering'] = cluster_info
        
        return jsonify(geojson), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching ruches: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/ruches/<int:ruche_id>', methods=['GET'])
def get_ruche(ruche_id):
    """
    Get GeoJSON for a single hive (ruche).
    
    Args:
        ruche_id: ID of the ruche
    
    Returns:
        GeoJSON Feature
    """
    try:
        ruche = db.session.get(Ruche, ruche_id)
        
        if not ruche:
            return jsonify({'error': 'Ruche not found'}), 404
        
        geojson = to_geojson(ruche)
        
        if geojson is None:
            return jsonify({'error': 'Invalid geometry'}), 500
        
        return jsonify(geojson), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching ruche {ruche_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/ruchers', methods=['GET'])
def get_all_ruchers():
    """
    Get GeoJSON for all apiaries (ruchers).
    
    Query Parameters:
        - radius: Filter by radius in meters (requires lat and lon)
        - lat: Latitude for radius search
        - lon: Longitude for radius search
    
    Returns:
        GeoJSON FeatureCollection
    """
    try:
        # Radius search
        radius = request.args.get('radius')
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if radius and lat and lon:
            try:
                center_point = f'POINT({float(lon)} {float(lat)})'
                ruchers = find_within_radius(Rucher, center_point, float(radius))
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid radius parameters'}), 400
        else:
            ruchers = Rucher.query.all()
        
        geojson = to_geojson(ruchers)
        
        return jsonify(geojson), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching ruchers: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/ruchers/<int:rucher_id>', methods=['GET'])
def get_rucher(rucher_id):
    """
    Get GeoJSON for a single apiary (rucher).
    
    Args:
        rucher_id: ID of the rucher
    
    Returns:
        GeoJSON Feature
    """
    try:
        rucher = db.session.get(Rucher, rucher_id)
        
        if not rucher:
            return jsonify({'error': 'Rucher not found'}), 404
        
        geojson = to_geojson(rucher)
        
        if geojson is None:
            return jsonify({'error': 'Invalid geometry'}), 500
        
        return jsonify(geojson), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching rucher {rucher_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
