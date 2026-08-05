-- Insert a new report
INSERT INTO road_damage_reports (
    image_filename,
    image_path,
    latitude,
    longitude,
    location_name,
    prediction_class,
    confidence_score,
    severity,
    damage_type,
    status,
    priority
) VALUES (
    '20250207_143052_road.jpg',
    'static/uploads/20250207_143052_road.jpg',
    6.870000,
    79.860000,
    'Galle Road, Colombo',
    'damage',
    0.9548,
    'critical',
    'Severe Road Damage - Immediate Attention Required',
    'pending',
    'urgent'
);

-- Get the ID of inserted record
SELECT last_insert_rowid();

