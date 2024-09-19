import mlflow
import mlflow.keras
from flask import Flask, request, jsonify
import numpy as np
from PIL import Image
import io

app = Flask(__name__)

# Model Configuration
mlflow.set_tracking_uri("http://localhost:5000")  # MLflow tracking server URI
experiment_name = "Fashion MNIST Classification"
mlflow.set_experiment(experiment_name)

# Model Loading
client = mlflow.tracking.MlflowClient()
experiment = client.get_experiment_by_name(experiment_name)
runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["attributes.start_time desc"],
    max_results=1
)

if runs:
    latest_run = runs[0]
    run_id = latest_run.info.run_id
    model = mlflow.keras.load_model(f"runs:/{run_id}/model")
    print(f"Loaded model from run: {run_id}")
else:
    raise Exception("No runs found for the experiment")

def preprocess_image(file):
    """
    Preprocess the input image for model prediction.
    
    Args:
        file: Input image file object.
    
    Returns:
        np.array: Preprocessed image array of shape (1, 28, 28).
    """
    img = Image.open(io.BytesIO(file.read())).convert('L').resize((28, 28))
    img_array = np.array(img) / 255.0
    return img_array.reshape(1, 28, 28)

@app.route('/predict', methods=['POST'])
def predict():
    """
    Endpoint for making predictions on input images.
    
    Returns:
        JSON response with predicted class.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    img = preprocess_image(file)
    
    # Model Inference
    with mlflow.start_run(run_id=run_id):
        predictions = model.predict(img)
        predicted_class = int(np.argmax(predictions, axis=1)[0])
        
        # Log prediction to MLflow
        mlflow.log_metric("prediction", predicted_class)
    
    return jsonify({'predicted_class': predicted_class})

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Using port 5001 to avoid conflict with MLflow UI