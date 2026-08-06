"""
Road Damage Detection System - Main Application
Sri Lanka Road Maintenance Monitoring System
Developer: AI Road Safety Team
"""

import requests
from flask import Flask, render_template, request, jsonify, url_for  # type: ignore
from flask_sqlalchemy import SQLAlchemy  # type: ignore
from werkzeug.utils import secure_filename  # type: ignore
from datetime import datetime
import os
import numpy as np  # type: ignore
# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

# Ensure required directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(
    os.path.dirname(
        app.config['SQLALCHEMY_DATABASE_URI'].replace(
            'sqlite:///',
            '')),
    exist_ok=True)
os.makedirs(os.path.join(app.config['BASE_DIR'], 'model'), exist_ok=True)

# Initialize database
db = SQLAlchemy(app)


class RoadDamageReport(db.Model):
    """Database model for road damage reports"""
    __tablename__ = 'road_damage_reports'

    id = db.Column(db.Integer, primary_key=True)

    # Image information
    image_filename = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)

    # GPS coordinates
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location_name = db.Column(db.String(500))

    # Prediction results
    prediction_class = db.Column(db.String(50), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)

    # Damage details
    severity = db.Column(db.String(50))
    damage_type = db.Column(db.String(100))

    # Additional information
    description = db.Column(db.Text)
    reported_by = db.Column(db.String(100))

    # Status tracking
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.String(50))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'image_filename': self.image_filename,
            'image_url': url_for('static', filename=f'uploads/{self.image_filename}'),
            'latitude': self.latitude,
            'longitude': self.longitude,
            'location_name': self.location_name or 'Unknown Location',
            'prediction_class': self.prediction_class,
            'confidence_score': round(self.confidence_score * 100, 2),
            'severity': self.severity,
            'damage_type': self.damage_type,
            'description': self.description,
            'reported_by': self.reported_by or 'Anonymous',
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


MODEL_SERVICE_URL = "http://localhost:5001"


def check_model_service():
    """Check if model service is available"""
    try:
        response = requests.get(f"{MODEL_SERVICE_URL}/status", timeout=2)
        return response.status_code == 200 and response.json().get('model_loaded', False)
    except BaseException:
        return False


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def validate_gps_coordinates(latitude, longitude):
    """Validate GPS coordinates for Sri Lanka"""
    return (app.config['SL_LAT_MIN'] <= latitude <= app.config['SL_LAT_MAX'] and
            app.config['SL_LON_MIN'] <= longitude <= app.config['SL_LON_MAX'])


def predict_damage(image_source):
    """Predict road damage via Model Service API"""
    try:
        # Handle file path strings
        if isinstance(image_source, str):
            with open(image_source, 'rb') as img_file:
                return _send_prediction_request(img_file)
        # Handle file objects (FileStorage)
        else:
            image_source.seek(0)
            return _send_prediction_request(image_source)

    except Exception as e:
        print(f"Error connecting to model service: {e}")
        return None, 0.0, None, None


def _send_prediction_request(file_obj):
    """Helper to send request to model service"""
    try:
        files = {'image': file_obj}
        response = requests.post(f"{MODEL_SERVICE_URL}/predict", files=files)

        if response.status_code == 200:
            data = response.json()
            return (
                data['prediction_class'],
                data['confidence'],
                data['severity'],
                data['damage_type']
            )
        else:
            print(f"Model service error: {response.text}")
            return None, 0.0, None, None
    except Exception as e:
        raise e


def get_priority(severity):
    """Map severity to priority"""
    priority_map = {
        'critical': 'urgent',
        'high': 'high',
        'medium': 'medium',
        'low': 'low',
        'none': 'low'
    }
    return priority_map.get(severity, 'medium')


@app.route('/')
def index():
    """Home page"""
    model_loaded = check_model_service()
    return render_template('index.html', model_loaded=model_loaded)


@app.route('/upload', methods=['POST'])
def upload_image():
    """Handle image upload and damage detection"""
    try:
        # Validate file upload
        if 'image' not in request.files:
            return jsonify(
                {'success': False, 'error': 'No file uploaded'}), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify(
                {'success': False, 'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, BMP'
            }), 400

        # Get GPS coordinates
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)

        if latitude is None or longitude is None:
            return jsonify(
                {'success': False, 'error': 'GPS coordinates required'}), 400

        # Validate GPS coordinates
        if not validate_gps_coordinates(latitude, longitude):
            return jsonify({
                'success': False,
                'error': 'GPS coordinates outside Sri Lanka bounds'
            }), 400

        # Get optional fields
        location_name = request.form.get('location_name', '')
        description = request.form.get('description', '')
        reported_by = request.form.get('reported_by', 'Anonymous')

        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        # Predict damage
        prediction_class, confidence, severity, damage_type = predict_damage(
            file_path)

        if prediction_class is None:
            return jsonify(
                {'success': False, 'error': 'Error processing image'}), 500

        # Get priority
        priority = get_priority(severity)

        # Create database record
        report = RoadDamageReport(
            image_filename=unique_filename,
            image_path=file_path,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            prediction_class=prediction_class,
            confidence_score=confidence,
            severity=severity,
            damage_type=damage_type,
            description=description,
            reported_by=reported_by,
            priority=priority,
            status='pending'
        )

        db.session.add(report)
        db.session.commit()

        # Return result
        return jsonify({
            'success': True,
            'report_id': report.id,
            'prediction_class': prediction_class,
            'confidence': round(confidence * 100, 2),
            'severity': severity,
            'damage_type': damage_type,
            'priority': priority,
            'message': 'Report submitted successfully!'
        })

    except Exception as e:
        print(f"Error in upload: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/dashboard')
def dashboard():
    """Dashboard showing all reports"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    severity_filter = request.args.get('severity', 'all')

    # Build query
    query = RoadDamageReport.query

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    if severity_filter != 'all':
        query = query.filter_by(severity=severity_filter)

    # Paginate
    reports = query.order_by(RoadDamageReport.created_at.desc()).paginate(
        page=page,
        per_page=app.config['REPORTS_PER_PAGE'],
        error_out=False
    )

    # Statistics
    total_reports = RoadDamageReport.query.count()
    damage_reports = RoadDamageReport.query.filter_by(
        prediction_class='damage').count()
    no_damage_reports = RoadDamageReport.query.filter_by(
        prediction_class='no_damage').count()
    pending_reports = RoadDamageReport.query.filter_by(
        status='pending').count()

    stats = {
        'total': total_reports,
        'damage': damage_reports,
        'no_damage': no_damage_reports,
        'pending': pending_reports
    }

    return render_template('dashboard.html',
                           reports=reports,
                           stats=stats,
                           status_filter=status_filter,
                           severity_filter=severity_filter)


@app.route('/report/<int:report_id>')
def view_report(report_id):
    """View detailed report"""
    report = RoadDamageReport.query.get_or_404(report_id)
    return render_template('report.html', report=report)


@app.route('/api/reports')
def api_reports():
    """API endpoint to get all reports"""
    reports = RoadDamageReport.query.all()
    return jsonify([report.to_dict() for report in reports])


@app.route('/api/report/<int:report_id>')
def api_report(report_id):
    """API endpoint to get specific report"""
    report = RoadDamageReport.query.get_or_404(report_id)
    return jsonify(report.to_dict())


@app.route('/api/update_status/<int:report_id>', methods=['POST'])
def update_status(report_id):
    """Update report status"""
    report = RoadDamageReport.query.get_or_404(report_id)

    data = request.get_json()
    new_status = data.get('status')

    if new_status in ['pending', 'in_progress', 'completed']:
        report.status = new_status
        report.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Status updated'})

    return jsonify({'success': False, 'error': 'Invalid status'}), 400


@app.route('/api/predict', methods=['POST'])
def predict_api():
    """API endpoint for image prediction"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image uploaded'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    try:
        # Predict directly from file object
        prediction_class, confidence, severity, damage_type = predict_damage(
            file)

        if prediction_class is None:
            return jsonify(
                {'success': False, 'error': 'Prediction failed'}), 500

        return jsonify({
            'success': True,
            'prediction': {
                'class': prediction_class,
                'confidence': round(confidence * 100, 2),
                'severity': severity,
                'damage_type': damage_type,
                'priority': get_priority(severity)
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/analysis')
def analysis():
    """Statistical analysis page"""
    all_reports = RoadDamageReport.query.all()

    total = len(all_reports)
    damage_count = sum(
        1 for r in all_reports if r.prediction_class == 'damage')

    severity_counts = {
        'critical': sum(1 for r in all_reports if r.severity == 'critical'),
        'high': sum(1 for r in all_reports if r.severity == 'high'),
        'medium': sum(1 for r in all_reports if r.severity == 'medium'),
        'low': sum(1 for r in all_reports if r.severity == 'low'),
    }

    status_counts = {
        'pending': sum(1 for r in all_reports if r.status == 'pending'),
        'in_progress': sum(1 for r in all_reports if r.status == 'in_progress'),
        'completed': sum(1 for r in all_reports if r.status == 'completed'),
    }

    avg_confidence = np.mean(
        [r.confidence_score for r in all_reports]) if all_reports else 0

    analysis_data = {
        'total_reports': total,
        'damage_reports': damage_count,
        'damage_percentage': round((damage_count / total * 100) if total > 0 else 0, 2),
        'severity_counts': severity_counts,
        'status_counts': status_counts,
        'avg_confidence': round(avg_confidence * 100, 2),
        'model_accuracy': 90.5  # Fixed value or fetch from API if needed
    }

    return render_template('analysis.html', data=analysis_data)


@app.route('/api/export/csv')
def export_csv():
    """Export reports as CSV"""
    import csv
    from io import StringIO

    reports = RoadDamageReport.query.all()

    si = StringIO()
    writer = csv.writer(si)

    writer.writerow(['ID',
                     'Date',
                     'Latitude',
                     'Longitude',
                     'Location',
                     'Class',
                     'Confidence %',
                     'Severity',
                     'Damage Type',
                     'Status',
                     'Priority'])

    for report in reports:
        writer.writerow([
            report.id,
            report.created_at.strftime('%Y-%m-%d %H:%M') if report.created_at else 'Unknown',
            report.latitude,
            report.longitude,
            report.location_name or 'N/A',
            report.prediction_class,
            round(report.confidence_score * 100, 2),
            report.severity,
            report.damage_type,
            report.status,
            report.priority
        ])

    output = si.getvalue()
    si.close()

    return app.response_class(
        output,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=road_damage_reports.csv'})


def init_db():
    """Initialize database"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")


if __name__ == '__main__':
    init_db()

    print("\n" + "=" * 80)
    print("ROAD DAMAGE DETECTION SYSTEM - SRI LANKA")
    print("=" * 80)
    print("Server starting on port 5000...")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Check model service
    service_active = check_model_service()
    if service_active:
        print("Model Service: CONNECTED (Port 5001)")
    else:
        print("WARNING: Model Service: NOT DETECTED (Please run model_service.py)")

    print("=" * 80 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
