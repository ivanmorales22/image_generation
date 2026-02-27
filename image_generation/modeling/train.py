import os
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from tensorflow import keras
from PIL import Image
from tensorflow.keras import layers
import mlflow
import mlflow.tensorflow
from dotenv import load_dotenv
from mlflow.models.signature import infer_signature

load_dotenv(override=True)

# --- DATABRICKS CONFIGURATION ---
MODEL_REGISTRY_NAME = "workspace.default.image_generation_models"
EXPERIMENT_NAME = "/Users/rafaeltakata0105@gmail.com/image_generation_experiment"

mlflow.set_tracking_uri("databricks")
mlflow.set_experiment(EXPERIMENT_NAME)

class VAEWrapper(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        self.vae = keras.models.load_model(context.artifacts["vae_model"])

    def predict(self, context, model_input):
        return self.vae.predict(model_input)

def build_conv_vae(input_shape=(256, 256, 3), latent_dim=128):
    # Encoder
    encoder_inputs = keras.Input(shape=input_shape)
    x = layers.Conv2D(32, 3, activation="relu", strides=2, padding="same")(encoder_inputs)
    x = layers.Conv2D(64, 3, activation="relu", strides=2, padding="same")(x)
    x = layers.Flatten()(x)
    z_mean = layers.Dense(latent_dim)(x)
    z_log_var = layers.Dense(latent_dim)(x)

    def sampling(args):
        z_m, z_lv = args
        eps = tf.random.normal(shape=tf.shape(z_m))
        return z_m + tf.exp(0.5 * z_lv) * eps

    z = layers.Lambda(sampling)([z_mean, z_log_var])
    encoder = keras.Model(encoder_inputs, [z_mean, z_log_var, z], name="encoder")

    # Decoder
    latent_inputs = keras.Input(shape=(latent_dim,))
    x = layers.Dense(64 * 64 * 64, activation="relu")(latent_inputs)
    x = layers.Reshape((64, 64, 64))(x)
    x = layers.Conv2DTranspose(64, 3, activation="relu", strides=2, padding="same")(x)
    x = layers.Conv2DTranspose(32, 3, activation="relu", strides=2, padding="same")(x)
    decoder_outputs = layers.Conv2DTranspose(3, 3, activation="sigmoid", padding="same")(x)
    decoder = keras.Model(latent_inputs, decoder_outputs, name="decoder")

    vae = keras.Model(encoder_inputs, decoder(encoder(encoder_inputs)[2]), name="vae")
    return vae

def train():
    # 1. Carga y preparación de datos
    data_dir = "data/processed"
    files = [os.path.join(data_dir, img) for img in os.listdir(data_dir) if img.endswith(('.png', '.jpg', '.jpeg'))]
    data = [np.array(Image.open(img).convert("RGB")) for img in files]
    
    print(f"Data loaded: {len(data)} images.")
    input_shape = (256, 256, 3)
    latent_dim = 128
    
    # Split y normalización
    all_images = np.array(data) / 255.0
    split_idx = int(0.8 * len(all_images))
    x_train, x_test = all_images[:split_idx], all_images[split_idx:]

    vae = build_conv_vae(input_shape, latent_dim)
    vae.compile(optimizer='adam', loss='mse')

    with mlflow.start_run() as run:
        # Registro de parámetros básicos
        mlflow.log_params({
            "epochs": 5,
            "batch_size": 8,
            "latent_dim": latent_dim
        })

        # Registro de Arquitectura
        with open("architecture.txt", "w") as f:
            vae.summary(print_fn=lambda x: f.write(x + '\n'))
        mlflow.log_artifact("architecture.txt")

        # 2. Entrenamiento
        history = vae.fit(x_train, x_train, epochs=5, batch_size=8, validation_split=0.1)

        # 3. EVALUACIÓN CON TEST (Métrica)
        test_mse = vae.evaluate(x_test, x_test, verbose=0)
        mlflow.log_metric("test_mse", test_mse)
        print(f"Test MSE logged: {test_mse}")

        # 4. Gráfica de Loss
        plt.figure(figsize=(10, 6))
        plt.plot(history.history['loss'], label='Train Loss')
        if 'val_loss' in history.history:
            plt.plot(history.history['val_loss'], label='Val Loss')
        plt.title('VAE Loss Function')
        plt.legend()
        plt.savefig("loss_chart.png")
        mlflow.log_artifact("loss_chart.png")

        # 5. Comparación Real vs Reconstrucción (usando imágenes de TEST)
        n = 5
        preds = vae.predict(x_test[:n])
        plt.figure(figsize=(15, 6))
        for i in range(n):
            # Real
            ax = plt.subplot(2, n, i + 1)
            plt.imshow(x_test[i])
            plt.title("Real (Test)")
            plt.axis("off")
            # Reconstrucción
            ax = plt.subplot(2, n, i + 1 + n)
            plt.imshow(preds[i])
            plt.title("Reconstructed")
            plt.axis("off")
        plt.savefig("test_comparison.png")
        mlflow.log_artifact("test_comparison.png")

        # 6. Guardado y Registro de Modelo
        vae.save("vae_model.h5")
        signature = infer_signature(x_test, vae.predict(x_test))

        mlflow.pyfunc.log_model(
            artifact_path="vae_bundle",
            python_model=VAEWrapper(),
            artifacts={"vae_model": "vae_model.h5"},
            registered_model_name=MODEL_REGISTRY_NAME,
            signature=signature,
            input_example=x_test[0:1]
        )
        print("Model and metrics successfully logged to Databricks.")

if __name__ == "__main__":
    train()
