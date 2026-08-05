

document.addEventListener('DOMContentLoaded', function () {
    console.log('Road Damage Detection System Initialized');

    // Initialize upload form
    initializeUploadForm();

    // Initialize image preview
    initializeImagePreview();

    // Initialize GPS location
    initializeGPSLocation();
});



function initializeUploadForm() {
    const uploadForm = document.getElementById('uploadForm');

    if (!uploadForm) return;

    uploadForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        // Validate form
        if (!validateForm()) {
            return;
        }

        // Show loading spinner
        showLoading();

        // Prepare form data
        const formData = new FormData(uploadForm);

        try {
            // Submit form
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                // Show results
                displayResults(data);
            } else {
                // Show error
                showError(data.error || 'An error occurred');
            }
        } catch (error) {
            console.error('Error:', error);
            showError('Failed to connect to server. Please try again.');
        } finally {
            hideLoading();
        }
    });
}



function initializeImagePreview() {
    const imageInput = document.getElementById('imageInput');
    const imagePreview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');

    if (!imageInput || !imagePreview || !previewImg) return;

    imageInput.addEventListener('change', function (e) {
        const file = e.target.files[0];

        if (file) {
            // Validate file size (16MB max)
            if (file.size > 16 * 1024 * 1024) {
                alert('File size must be less than 16MB');
                imageInput.value = '';
                imagePreview.style.display = 'none';
                return;
            }

            // Validate file type
            const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp'];
            if (!allowedTypes.includes(file.type)) {
                alert('Invalid file type. Please upload JPG, JPEG, PNG, or BMP');
                imageInput.value = '';
                imagePreview.style.display = 'none';
                return;
            }

            // Show preview
            const reader = new FileReader();
            reader.onload = function (e) {
                previewImg.src = e.target.result;
                imagePreview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        } else {
            imagePreview.style.display = 'none';
        }
    });
}



function initializeGPSLocation() {
    const getLocationBtn = document.getElementById('getLocationBtn');
    const latInput = document.getElementById('latitude');
    const lonInput = document.getElementById('longitude');

    if (!getLocationBtn || !latInput || !lonInput) return;

    getLocationBtn.addEventListener('click', function () {
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by your browser');
            return;
        }

        // Show loading state
        getLocationBtn.disabled = true;
        getLocationBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Getting location...';

        navigator.geolocation.getCurrentPosition(
            function (position) {
                // Success
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                latInput.value = lat.toFixed(6);
                lonInput.value = lon.toFixed(6);

                // Validate Sri Lanka bounds
                if (lat < 5.9 || lat > 9.9 || lon < 79.5 || lon > 82.0) {
                    alert('Warning: Your location appears to be outside Sri Lanka. Please verify the coordinates.');
                }

                // Reset button
                getLocationBtn.disabled = false;
                getLocationBtn.innerHTML = '<i class="fas fa-location-arrow"></i> Get My Location';

                // Show success message
                showSuccessMessage('Location acquired successfully!');
            },
            function (error) {
                // Error
                console.error('Geolocation error:', error);

                let errorMessage = 'Unable to get location. ';
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage += 'Please allow location access.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage += 'Location information unavailable.';
                        break;
                    case error.TIMEOUT:
                        errorMessage += 'Location request timed out.';
                        break;
                    default:
                        errorMessage += 'Unknown error occurred.';
                }

                alert(errorMessage);

                // Reset button
                getLocationBtn.disabled = false;
                getLocationBtn.innerHTML = '<i class="fas fa-location-arrow"></i> Get My Location';
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    });
}


function validateForm() {
    const imageInput = document.getElementById('imageInput');
    const latInput = document.getElementById('latitude');
    const lonInput = document.getElementById('longitude');

    // Validate image
    if (!imageInput.files || imageInput.files.length === 0) {
        alert('Please select an image');
        return false;
    }

    // Validate GPS coordinates
    const lat = parseFloat(latInput.value);
    const lon = parseFloat(lonInput.value);

    if (isNaN(lat) || isNaN(lon)) {
        alert('Please provide valid GPS coordinates');
        return false;
    }

    // Validate Sri Lanka bounds
    if (lat < 5.9 || lat > 9.9 || lon < 79.5 || lon > 82.0) {
        const confirm = window.confirm(
            'Warning: GPS coordinates appear to be outside Sri Lanka bounds.\n\n' +
            'Sri Lanka bounds:\n' +
            'Latitude: 5.9°N to 9.9°N\n' +
            'Longitude: 79.5°E to 82.0°E\n\n' +
            'Do you want to continue anyway?'
        );

        if (!confirm) {
            return false;
        }
    }

    return true;
}


function showLoading() {
    const submitBtn = document.getElementById('submitBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultDisplay = document.getElementById('resultDisplay');

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
    }

    if (loadingSpinner) {
        loadingSpinner.style.display = 'block';
    }

    if (resultDisplay) {
        resultDisplay.style.display = 'none';
    }
}

function hideLoading() {
    const submitBtn = document.getElementById('submitBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');

    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-check-circle"></i> Analyze Road Condition';
    }

    if (loadingSpinner) {
        loadingSpinner.style.display = 'none';
    }
}



function displayResults(data) {
    const resultDisplay = document.getElementById('resultDisplay');
    const resultClass = document.getElementById('resultClass');
    const resultConfidence = document.getElementById('resultConfidence');
    const resultSeverity = document.getElementById('resultSeverity');
    const resultDamageType = document.getElementById('resultDamageType');
    const resultPriority = document.getElementById('resultPriority');
    const viewReportBtn = document.getElementById('viewReportBtn');

    if (!resultDisplay) return;

    // Set values
    if (resultClass) {
        resultClass.textContent = data.prediction_class.toUpperCase();
        resultClass.className = 'value badge ' +
            (data.prediction_class === 'damage' ? 'badge-danger' : 'badge-success') +
            ' large';
    }

    if (resultConfidence) {
        resultConfidence.textContent = data.confidence + '%';
        resultConfidence.style.color = getConfidenceColor(data.confidence);
    }

    if (resultSeverity) {
        resultSeverity.textContent = data.severity.toUpperCase();
        resultSeverity.className = 'value badge badge-severity-' + data.severity + ' large';
    }

    if (resultDamageType) {
        resultDamageType.textContent = data.damage_type;
    }

    if (resultPriority) {
        resultPriority.textContent = data.priority.toUpperCase();
        resultPriority.className = 'value badge badge-priority-' + data.priority + ' large';
    }

    if (viewReportBtn) {
        viewReportBtn.href = `/report/${data.report_id}`;
    }

    // Show result
    resultDisplay.style.display = 'block';

    // Scroll to result
    resultDisplay.scrollIntoView({ behavior: 'smooth', block: 'center' });

    // Show success message
    showSuccessMessage(data.message);
}



function showError(message) {
    alert('Error: ' + message);
}

function showSuccessMessage(message) {
    // You can implement a toast notification here
    console.log('Success:', message);
}



function getConfidenceColor(confidence) {
    if (confidence >= 90) return '#10b981'; // Green
    if (confidence >= 70) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
}



document.addEventListener('DOMContentLoaded', function () {
    const uploadAnotherBtn = document.getElementById('uploadAnotherBtn');

    if (uploadAnotherBtn) {
        uploadAnotherBtn.addEventListener('click', function () {
            // Reset form
            const uploadForm = document.getElementById('uploadForm');
            if (uploadForm) {
                uploadForm.reset();
            }

            // Hide preview and result
            const imagePreview = document.getElementById('imagePreview');
            const resultDisplay = document.getElementById('resultDisplay');

            if (imagePreview) imagePreview.style.display = 'none';
            if (resultDisplay) resultDisplay.style.display = 'none';

            // Scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
});