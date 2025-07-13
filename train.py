import os
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.optimizers import Adam

def build_model(input_shape):
    model = Sequential([
        Conv2D(32, (3,3), activation='relu', input_shape=input_shape),
        MaxPooling2D(2,2),
        Conv2D(64, (3,3), activation='relu'),
        MaxPooling2D(2,2),
        Conv2D(128, (3,3), activation='relu'),
        MaxPooling2D(2,2),
        Flatten(),
        Dense(128, activation='relu'),
        Dropout(0.5),
        Dense(1, activation='sigmoid')
    ])
    return model

def main():
    dataset_dir = "chest_xray"
    img_size = (150, 150)
    batch_size = 32
    epochs = 10

    train_path = os.path.join(dataset_dir, "train")
    val_path = os.path.join(dataset_dir, "val")
    test_path = os.path.join(dataset_dir, "test")

    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=15,
        shear_range=0.1,
        zoom_range=0.2,
        horizontal_flip=True
    )
    val_datagen = ImageDataGenerator(rescale=1./255)
    test_datagen = ImageDataGenerator(rescale=1./255)

    train_gen = train_datagen.flow_from_directory(
        train_path,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='binary'
    )
    val_gen = val_datagen.flow_from_directory(
        val_path,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='binary'
    )
    test_gen = test_datagen.flow_from_directory(
        test_path,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='binary'
    )

    model = build_model(input_shape=(*img_size, 3))
    model.compile(
        loss='binary_crossentropy',
        optimizer=Adam(learning_rate=1e-4),
        metrics=['accuracy']
    )

    history = model.fit(
        train_gen,
        epochs=epochs,
        validation_data=val_gen
    )

    loss, acc = model.evaluate(test_gen)
    print(f"Test accuracy: {acc*100:.2f}%")

    model.save("pneumonia_cnn_model.h5")
    print("Model saved as pneumonia_cnn_model.h5")

if __name__ == "__main__":
    main()
