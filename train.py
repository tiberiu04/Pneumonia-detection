import os
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.optimizers import Adam

def build_model(input_shape):
    # we are building a CNN with 3 convolution layers + fully connected layers at the end
    model = Sequential([
        # first conv layer: learns to detect lines, edges — simple stuff — 32 filters
        Conv2D(32, (3,3), activation='relu', input_shape=input_shape),
        MaxPooling2D(2,2),  # makes the image smaller and keeps only the important bits
        
        # second conv layer: picks up more complex shapes — corners, blobs — with 64 filters
        Conv2D(64, (3,3), activation='relu'),
        MaxPooling2D(2,2),
        
        # third conv layer: even more abstract patterns — full structures — 128 filters
        Conv2D(128, (3,3), activation='relu'),
        MaxPooling2D(2,2),
        
        # we flatten everything into a long vector so we can feed it to dense layers
        Flatten(),
        
        # fully connected layer: learns combinations of the features found before
        Dense(128, activation='relu'),
        
        # randomly shutting down 50% of neurons here so the model doesn’t just memorize
        Dropout(0.5),
        
        # final layer: just 1 neuron, sigmoid activation —
        # gives a score between 0 and 1 like a probability
        Dense(1, activation='sigmoid')
    ])
    return model


def main():
    dataset_dir = "chest_xray"
    img_size = (150, 150)      # we resize all images to this size
    batch_size = 32            # how many images we process at once
    epochs = 10                # how many times we go through the entire training set

    # paths to the folders with images
    train_path = os.path.join(dataset_dir, "train")
    val_path = os.path.join(dataset_dir, "val")
    test_path = os.path.join(dataset_dir, "test")

    # here we prepare the images for training and add some tricks
    # so the model doesn’t get bored and learns to generalize better
    train_datagen = ImageDataGenerator(
        rescale= 1./255,            # normalizing pixels
        rotation_range = 15,        # slightly rotate images randomly
        shear_range = 0.1,          # slightly distort them
        zoom_range = 0.2,           # zooming in and out randomly
        horizontal_flip = True      # sometimes flipping left-right (lungs are symmetrical)
    )
    # for validation and test we don’t mess with the images — just normalize them
    val_datagen = ImageDataGenerator(rescale = 1./255)
    test_datagen = ImageDataGenerator(rescale = 1./255)

    # grabbing images from folders, resizing them, and giving them to the model in batches
    train_gen = train_datagen.flow_from_directory(
        train_path,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='binary'    # labels will be 0 or 1
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

    # building the model
    model = build_model(input_shape=(*img_size, 3)) # images have 3 channels (RGB)

    # telling the model how to learn: loss function, optimizer, and what metric to show
    model.compile(
        loss='binary_crossentropy',
        optimizer = Adam(learning_rate = 1e-4),  # Adam optimizer with a small learning rate for stability
        metrics=['accuracy']                 # we care about how often it is right
    )

    # training the model: use training data and check validation set after each epoch
    history = model.fit(
        train_gen,
        epochs=epochs,
        validation_data=val_gen
    )

    # after training, we test the model on the test set
    loss, acc = model.evaluate(test_gen)
    print(f"Test accuracy: {acc*100:.2f}%")

    # save the model so we can use it later for predictions
    model.save("pneumonia_cnn_model.h5")
    print("Model saved as pneumonia_cnn_model.h5")

if __name__ == "__main__":
    main()
